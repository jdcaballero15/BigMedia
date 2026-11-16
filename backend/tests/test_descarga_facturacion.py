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
def test_descarga_respeta_los_filtros_y_excluye_los_anulados(operativo_client):
    _item("Noviembre", neto=Decimal("1"))
    _item("Octubre", neto=Decimal("1"), mes=date(2026, 10, 1))
    _item("Anulado", neto=Decimal("1"), estado=ItemFacturacion.Estado.ANULADO)
    _item("Facturado", neto=Decimal("1"), estado="facturado", numero_factura="A-0001")
    _, filas = _descargar(operativo_client, "?mes=2026-11")
    clientes = [fila["CLIENTE (RAZON SOCIAL)"] for fila in _filas_de_items(filas)]
    assert sorted(clientes) == ["Facturado SA", "Noviembre SA"]
    _, filas = _descargar(operativo_client, "?mes=2026-11&estado=borrador")
    assert [fila["CLIENTE (RAZON SOCIAL)"] for fila in _filas_de_items(filas)] == ["Noviembre SA"]


@pytest.mark.django_db
def test_descarga_filtrada_por_anulados_sale_vacia(operativo_client):
    _item("Anulado", neto=Decimal("1"), estado=ItemFacturacion.Estado.ANULADO)
    _, filas = _descargar(operativo_client, "?estado=anulado")
    assert _filas_de_items(filas) == []


@pytest.mark.django_db
def test_descarga_no_cambia_el_estado_de_los_items(operativo_client):
    item = _item("Alfa", neto=Decimal("1"))
    _descargar(operativo_client, "?mes=2026-11")
    item.refresh_from_db()
    assert item.estado == ItemFacturacion.Estado.BORRADOR


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
def test_descarga_con_estado_desconocido_se_rechaza(operativo_client):
    assert operativo_client.get(f"{PLANILLA}?estado=otro").status_code == 400


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
