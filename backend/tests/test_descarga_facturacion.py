"""Costos escritos en el ítem (HU-060) y «Descargar Excel» de la lista sin enviar (HU-070)."""

import io
import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.db import IntegrityError, transaction
from django.test import Client
from openpyxl import load_workbook

from apps.clientes.models import Cliente
from apps.costos.models import Costo
from apps.facturacion.models import ItemFacturacion, Sector, TipoVenta

ITEMS = "/api/facturacion/items/"
PLANILLA = f"{ITEMS}planilla/"

SIETE = [
    "CLIENTE (RAZON SOCIAL)",
    "IMPORTE NETO TOTAL",
    "COSTOS INCLUIDOS EN FC",
    "DETALLE COSTO",
    "TIPO DE VENTA (F/V)",
    "GOB/PRIV",
    "TIPO (cartel/led/ppl/sextuples)",
]


def _descargar(client: Client, consulta: str = "") -> tuple[Any, list[list[Any]]]:
    respuesta = client.get(f"{PLANILLA}{consulta}")
    assert respuesta.status_code == 200
    hoja = load_workbook(io.BytesIO(respuesta.content)).active
    assert hoja is not None
    return respuesta, [list(fila) for fila in hoja.iter_rows(values_only=True)]


def _filas_de_items(filas: list[list[Any]]) -> list[dict[str, Any]]:
    """Las filas entre los títulos de columna y el pie de totales (que no lleva cliente)."""
    inicio = filas.index(SIETE) + 1
    items = []
    for fila in filas[inicio:]:
        if fila[0] is None:
            break
        items.append(dict(zip(SIETE, fila, strict=True)))
    return items


def _item(cliente: str, **datos: Any) -> ItemFacturacion:
    datos.setdefault("mes", date(2026, 11, 1))
    return ItemFacturacion.objects.create(
        cliente=Cliente.objects.create(nombre=cliente, razon_social=f"{cliente} SA"), **datos
    )


# --- Costos incluidos y detalle escritos en el ítem (HU-060) ---


@pytest.mark.django_db
def test_item_con_costos_escritos_a_mano_se_guarda_tal_cual(operativo_client):
    respuesta = operativo_client.post(
        ITEMS,
        data=json.dumps(
            {"neto": "10000.00", "costos_incluidos": "1500.00", "detalle_costo": "Comisión 15 %"}
        ),
        content_type="application/json",
    )
    assert respuesta.status_code == 201, respuesta.json()
    datos = respuesta.json()
    assert (datos["costos_incluidos"], datos["detalle_costo"]) == ("1500.00", "Comisión 15 %")
    item = ItemFacturacion.objects.get(pk=datos["id"])
    assert item.costos_incluidos == Decimal("1500.00")
    assert Costo.objects.count() == 0


@pytest.mark.django_db
def test_item_con_costos_incluidos_negativos_se_rechaza(operativo_client):
    respuesta = operativo_client.post(
        ITEMS, data=json.dumps({"costos_incluidos": "-1"}), content_type="application/json"
    )
    assert respuesta.status_code == 400
    assert "costos_incluidos" in respuesta.json()


@pytest.mark.django_db
def test_item_con_costos_incluidos_negativos_lo_rechaza_la_base():
    with pytest.raises(IntegrityError), transaction.atomic():
        ItemFacturacion.objects.create(costos_incluidos=Decimal("-1"))


@pytest.mark.django_db
def test_item_sin_costos_escritos_se_guarda_vacio(operativo_client):
    respuesta = operativo_client.post(ITEMS, data="{}", content_type="application/json")
    assert respuesta.status_code == 201
    assert (respuesta.json()["costos_incluidos"], respuesta.json()["detalle_costo"]) == (None, "")


# --- «Descargar Excel» de la lista (HU-070) ---


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_descarga_con_solo_las_siete_columnas_y_los_datos_del_item(operativo_client):
    _item(
        "Zeta",
        neto=Decimal("10000.00"),
        costos_incluidos=Decimal("1500.00"),
        detalle_costo="Comisión agencia",
        tipo_venta=TipoVenta.objects.get(nombre="F"),
        sector=Sector.objects.get(nombre="Privado"),
        tipo_soporte="Séxtuples",
        descripcion="No va en la descarga",
    )
    respuesta, filas = _descargar(operativo_client, "?mes=2026-11")
    assert respuesta["Content-Type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert respuesta["Content-Disposition"] == 'attachment; filename="facturacion-2026-11.xlsx"'
    assert SIETE in filas
    assert all(len([valor for valor in fila if valor is not None]) <= 7 for fila in filas)
    assert _filas_de_items(filas) == [
        {
            "CLIENTE (RAZON SOCIAL)": "Zeta SA",
            "IMPORTE NETO TOTAL": 10000,
            "COSTOS INCLUIDOS EN FC": 1500,
            "DETALLE COSTO": "Comisión agencia",
            "TIPO DE VENTA (F/V)": "F",
            "GOB/PRIV": "Privado",
            "TIPO (cartel/led/ppl/sextuples)": "Séxtuples",
        }
    ]


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_descarga_con_periodo_arriba_y_totales_abajo(operativo_client):
    _item("Alfa", neto=Decimal("1000"), costos_incluidos=Decimal("100"))
    _item("Beta", neto=Decimal("500"))
    _, filas = _descargar(operativo_client, "?mes=2026-11")
    assert filas[0][:2] == ["PERIODO:", "2026/11"]
    assert filas[1][0] == "CARTELERIA"
    fin = filas.index(SIETE) + 1 + 2
    assert filas[fin][1:3] == [f"=SUM(B{fin - 1}:B{fin})", f"=SUM(C{fin - 1}:C{fin})"]
    assert filas[fin + 2][:2] == ["Neto", f"=B{fin + 1}-C{fin + 1}"]


@pytest.mark.django_db
def test_descarga_sin_mes_no_lleva_periodo(operativo_client):
    _item("Alfa", neto=Decimal("1000"))
    respuesta, filas = _descargar(operativo_client)
    assert respuesta["Content-Disposition"] == 'attachment; filename="facturacion.xlsx"'
    assert filas[0][0] == "CARTELERIA"
    assert len(_filas_de_items(filas)) == 1


@pytest.mark.django_db
def test_descarga_respeta_los_filtros_y_excluye_los_dados_de_baja(operativo_client):
    _item("Noviembre", neto=Decimal("1"))
    _item("Octubre", neto=Decimal("1"), mes=date(2026, 10, 1))
    _item("Anulado", neto=Decimal("1"), estado=ItemFacturacion.Estado.ANULADO)
    _item("Facturado", neto=Decimal("1"), estado="facturado", numero_factura="A-0001")
    _, filas = _descargar(operativo_client, "?mes=2026-11")
    clientes = [fila["CLIENTE (RAZON SOCIAL)"] for fila in _filas_de_items(filas)]
    assert sorted(clientes) == ["Facturado SA", "Noviembre SA"]


@pytest.mark.django_db
def test_descarga_de_lista_vacia_trae_solo_los_titulos(operativo_client):
    _, filas = _descargar(operativo_client, "?mes=2026-11")
    assert SIETE in filas
    assert _filas_de_items(filas) == []


@pytest.mark.django_db
def test_descarga_la_puede_usar_lectura(lector_client):
    _item("Alfa", neto=Decimal("1"))
    _, filas = _descargar(lector_client, "?mes=2026-11")
    assert len(_filas_de_items(filas)) == 1


@pytest.mark.django_db
def test_descarga_sin_sesion_se_rechaza(client):
    assert client.get(PLANILLA).status_code in (401, 403)


@pytest.mark.django_db
def test_lista_de_items_trae_la_razon_social_del_cliente_o_su_nombre(lector_client):
    _item("Zeta")
    ItemFacturacion.objects.create(cliente=Cliente.objects.create(nombre="Sin razón"))
    ItemFacturacion.objects.create()
    datos = lector_client.get(ITEMS).json()
    assert sorted(str(item["cliente_razon_social"]) for item in datos) == [
        "None",
        "Sin razón",
        "Zeta SA",
    ]


# --- Formato de la planilla real de Administración (HU-070, RN-024) ---

FORMATO_PESOS = '"$" #,##0'


def _hoja(client: Client, consulta: str = "") -> Any:
    respuesta = client.get(f"{PLANILLA}{consulta}")
    assert respuesta.status_code == 200
    return load_workbook(io.BytesIO(respuesta.content)).active


def _color(celda: Any) -> str:
    return str(celda.fill.fgColor.rgb)[-6:]


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_descarga_periodo_y_titulo_con_los_colores_de_la_planilla(operativo_client):
    hoja = _hoja(operativo_client, "?mes=2026-11")
    assert [_color(hoja["A1"]), _color(hoja["B1"])] == ["FFC000", "FFC000"]
    assert hoja["A1"].font.b
    assert hoja["B1"].font.b
    assert "A2:G2" in {str(rango) for rango in hoja.merged_cells.ranges}
    assert _color(hoja["A2"]) == "92D050"
    assert hoja["A2"].font.b
    assert hoja["A2"].alignment.horizontal == "center"


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_descarga_titulos_de_columna_en_negrita_centrados_y_amarillos(operativo_client):
    hoja = _hoja(operativo_client, "?mes=2026-11")
    for celda in hoja[3]:
        assert celda.font.b
        assert celda.alignment.horizontal == "center"
        assert celda.alignment.wrap_text
        assert _color(celda) == "FFF2CC"
    assert hoja.column_dimensions["A"].width == 30
    assert hoja.column_dimensions["G"].width == 50


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_descarga_importes_con_formato_de_pesos_sin_decimales(operativo_client):
    _item("Alfa", neto=Decimal("450000.50"), costos_incluidos=Decimal("68700"))
    hoja = _hoja(operativo_client, "?mes=2026-11")
    fila, totales, neto = 4, 5, 7
    assert hoja.cell(fila, 2).value == 450000.5
    for numero in (fila, totales):
        assert hoja.cell(numero, 2).number_format == FORMATO_PESOS
        assert hoja.cell(numero, 3).number_format == FORMATO_PESOS
    assert hoja.cell(neto, 1).value == "Neto"
    assert hoja.cell(neto, 2).number_format == FORMATO_PESOS


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_descarga_tabla_con_bordes_y_totales_en_durazno(operativo_client):
    _item("Alfa", neto=Decimal("1000"))
    _item("Beta", neto=Decimal("500"))
    hoja = _hoja(operativo_client, "?mes=2026-11")
    totales = 6
    for numero in range(3, totales + 1):
        for celda in hoja[numero][:7]:
            lados = (celda.border.left, celda.border.right, celda.border.top, celda.border.bottom)
            assert all(lado.style == "thin" for lado in lados), celda.coordinate
    assert all(_color(celda) == "FCE4D6" for celda in hoja[totales][:7])
    assert hoja.cell(totales, 2).font.b
    assert hoja.cell(totales, 3).font.b


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_descarga_sin_mes_tiene_el_titulo_en_la_primera_fila(operativo_client):
    hoja = _hoja(operativo_client)
    assert hoja["A1"].value == "CARTELERIA"
    assert "A1:G1" in {str(rango) for rango in hoja.merged_cells.ranges}
    assert all(_color(celda) == "FFF2CC" for celda in hoja[2])
