"""Planilla .xlsx del envío a facturar (HU-066, criterios 3 y 5; HU-062 y HU-064)."""

import io
import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.test import Client
from openpyxl import load_workbook

from apps.clientes.models import Cliente, Marca
from apps.costos.models import Costo
from apps.facturacion.models import CostoDeItem, GrupoFactura, ItemFacturacion, Sector, TipoVenta

URL = "/api/facturacion/envios/"

REALES = [
    "CLIENTE (RAZON SOCIAL)",
    "IMPORTE NETO TOTAL",
    "COSTOS INCLUIDOS EN FC",
    "DETALLE COSTO",
    "TIPO DE VENTA (F/V)",
    "GOB/PRIV",
    "TIPO (cartel/led/ppl/sextuples)",
]
COLUMNAS = [
    *REALES,
    "Mes",
    "Cliente",
    "CUIT",
    "Marca",
    "Descripción",
    "Período desde",
    "Período hasta",
    "Cantidad",
    "Precio unitario",
    "Alícuota IVA",
    "IVA",
    "Total",
    "Tipo de servicio",
    "Notas",
    "Orden de compra",
    "Fecha OC",
    "Grupo de factura",
    "Neto final",
    "Reenviado",
]
TITULOS = 3  # período, «CARTELERIA» y los títulos de columna (RN-024)


def _enviar(client: Client) -> int:
    respuesta = client.post(
        URL, data=json.dumps({"mes": "2026-11"}), content_type="application/json"
    )
    assert respuesta.status_code == 201, respuesta.json()
    envio_id: int = respuesta.json()["envio"]["id"]
    return envio_id


def _planilla(client: Client, envio_id: int) -> tuple[Any, list[list[Any]]]:
    respuesta = client.get(f"{URL}{envio_id}/planilla/")
    assert respuesta.status_code == 200
    hoja = load_workbook(io.BytesIO(respuesta.content)).active
    assert hoja is not None
    return respuesta, [list(fila) for fila in hoja.iter_rows(values_only=True)]


def _items(filas: list[list[Any]]) -> list[dict[str, Any]]:
    """Las filas de ítems, entre los títulos y el pie (que no lleva cliente)."""
    items = []
    for fila in filas[TITULOS:]:
        if fila[0] is None:
            break
        items.append(dict(zip(COLUMNAS, fila, strict=True)))
    return items


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_planilla_con_las_columnas_y_los_importes_como_numeros(operativo_client):
    cliente = Cliente.objects.create(nombre="Zeta SA")
    marca = Marca.objects.create(nombre="Marca Z", cliente=cliente)
    ItemFacturacion.objects.create(
        mes=date(2026, 11, 1),
        cliente=cliente,
        cuit_facturacion="20123456786",
        marca=marca,
        descripcion="Alquiler noviembre",
        periodo_desde=date(2026, 11, 1),
        periodo_hasta=date(2026, 11, 30),
        cantidad=Decimal("10"),
        precio_unitario=Decimal("1000"),
        neto=Decimal("10000.00"),
        tipo_servicio="alquiler",
        tipo_soporte="Gran Formato",
        sector=Sector.objects.get(nombre="Privado"),
        tipo_venta=TipoVenta.objects.get(nombre="F"),
        notas="Facturar con la OC anterior",
    )
    respuesta, filas = _planilla(operativo_client, _enviar(operativo_client))
    assert respuesta["Content-Type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert respuesta["Content-Disposition"].startswith('attachment; filename="facturacion-2026-11-')
    assert filas[TITULOS - 1] == COLUMNAS
    fila = _items(filas)[0]
    assert fila["Mes"] == "2026-11"
    assert (fila["Cliente"], fila["CUIT"], fila["Marca"]) == ("Zeta SA", "20123456786", "Marca Z")
    assert fila["Período desde"].date() == date(2026, 11, 1)
    assert (fila["IMPORTE NETO TOTAL"], fila["IVA"], fila["Total"]) == (10000, 2100, 12100)
    assert isinstance(fila["IMPORTE NETO TOTAL"], int | float)
    assert fila["Alícuota IVA"] == 21
    assert (fila["Tipo de servicio"], fila["GOB/PRIV"], fila["TIPO DE VENTA (F/V)"]) == (
        "Alquiler",
        "Privado",
        "F",
    )
    assert (fila["Orden de compra"], fila["Fecha OC"], fila["Grupo de factura"]) == (
        None,
        None,
        None,
    )


@pytest.mark.django_db
def test_planilla_solo_con_los_items_del_envio_ordenados_por_cliente(operativo_client):
    for nombre in ("Zeta SA", "Alfa SA"):
        ItemFacturacion.objects.create(
            mes=date(2026, 11, 1),
            cliente=Cliente.objects.create(nombre=nombre),
            neto=Decimal("1.00"),
        )
    ItemFacturacion.objects.create(
        mes=date(2026, 11, 1), cliente=Cliente.objects.create(nombre="Anulado SA"), estado="anulado"
    )
    _, filas = _planilla(operativo_client, _enviar(operativo_client))
    assert [fila["Cliente"] for fila in _items(filas)] == ["Alfa SA", "Zeta SA"]


@pytest.mark.django_db
def test_planilla_de_envio_inexistente_da_404(lector_client):
    assert lector_client.get(f"{URL}999999/planilla/").status_code == 404


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_planilla_con_la_orden_de_compra_y_el_grupo(operativo_client):
    grupo = GrupoFactura.objects.create(mes=date(2026, 11, 1))
    ItemFacturacion.objects.create(
        mes=date(2026, 11, 1),
        cliente=Cliente.objects.create(nombre="Alfa SA"),
        neto=Decimal("1.00"),
        orden_compra_numero="OC-77",
        orden_compra_fecha=date(2026, 10, 20),
        grupo=grupo,
    )
    _, filas = _planilla(operativo_client, _enviar(operativo_client))
    fila = _items(filas)[0]
    assert fila["Orden de compra"] == "OC-77"
    assert fila["Fecha OC"].date() == date(2026, 10, 20)
    assert fila["Grupo de factura"] == f"G-{grupo.pk}"


@pytest.mark.django_db
def test_los_items_de_un_grupo_salen_juntos(operativo_client):
    """HU-064 criterio 3 y HU-066 criterio 3: juntos y con el mismo identificador."""
    grupo = GrupoFactura.objects.create(mes=date(2026, 11, 1))
    alfa, beta, zeta = (Cliente.objects.create(nombre=n) for n in ("Alfa SA", "Beta SA", "Zeta SA"))
    for cliente, en_grupo in ((alfa, True), (beta, False), (zeta, True), (alfa, False)):
        ItemFacturacion.objects.create(
            mes=date(2026, 11, 1),
            cliente=cliente,
            neto=Decimal("1.00"),
            grupo=grupo if en_grupo else None,
        )
    _, filas = _planilla(operativo_client, _enviar(operativo_client))
    codigo = f"G-{grupo.pk}"
    assert [(fila["Cliente"], fila["Grupo de factura"]) for fila in _items(filas)] == [
        ("Alfa SA", codigo),
        ("Zeta SA", codigo),
        ("Alfa SA", None),
        ("Beta SA", None),
    ]


@pytest.mark.django_db
def test_planilla_con_el_cuit_del_item_distinto_del_cliente(operativo_client):
    """HU-064 criterio 4: el cliente no cambia y la planilla muestra el CUIT del ítem."""
    cliente = Cliente.objects.create(nombre="Alfa SA", cuit="20123456786")
    ItemFacturacion.objects.create(
        mes=date(2026, 11, 1), cliente=cliente, cuit_facturacion="27123456780", neto=Decimal("1")
    )
    _, filas = _planilla(operativo_client, _enviar(operativo_client))
    fila = _items(filas)[0]
    assert fila["CUIT"] == "27123456780"
    cliente.refresh_from_db()
    assert cliente.cuit == "20123456786"


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_planilla_con_los_costos_y_el_neto_final_al_final(operativo_client):
    """HU-063 y HU-066 criterio 1: costos y neto final del ítem, sin los costos anulados."""
    item = ItemFacturacion.objects.create(
        mes=date(2026, 11, 1),
        cliente=Cliente.objects.create(nombre="Alfa SA"),
        neto=Decimal("10000"),
    )
    for porcentaje, anulado in (("15", False), ("5", True)):
        costo = Costo.objects.create(
            tipo="comision",
            porcentaje=Decimal(porcentaje),
            monto=Decimal(porcentaje) * 100,
            fecha=date(2026, 11, 1),
            anulado=anulado,
        )
        CostoDeItem.objects.create(item=item, costo=costo)
    ItemFacturacion.objects.create(
        mes=date(2026, 11, 1), cliente=Cliente.objects.create(nombre="Beta SA"), neto=Decimal("1")
    )
    _, filas = _planilla(operativo_client, _enviar(operativo_client))
    assert [(fila["COSTOS INCLUIDOS EN FC"], fila["Neto final"]) for fila in _items(filas)] == [
        (1500, 8500),
        (0, 1),
    ]


# --- Forma de la planilla real de Administración (RN-024) ---


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_planilla_con_periodo_y_titulo_arriba(operativo_client):
    ItemFacturacion.objects.create(
        mes=date(2026, 11, 1), cliente=Cliente.objects.create(nombre="Alfa SA"), neto=Decimal("1")
    )
    _, filas = _planilla(operativo_client, _enviar(operativo_client))
    assert filas[0][:2] == ["PERIODO:", "2026/11"]
    assert filas[1][0] == "CARTELERIA"


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_planilla_con_las_siete_columnas_reales_primero(operativo_client):
    ItemFacturacion.objects.create(
        mes=date(2026, 11, 1), cliente=Cliente.objects.create(nombre="Alfa SA"), neto=Decimal("1")
    )
    _, filas = _planilla(operativo_client, _enviar(operativo_client))
    assert filas[TITULOS - 1][: len(REALES)] == REALES


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_planilla_cliente_con_razon_social_o_su_nombre(operativo_client):
    for nombre, razon_social in (("Alfa", "Alfa Sociedad Anónima"), ("Beta SA", "")):
        ItemFacturacion.objects.create(
            mes=date(2026, 11, 1),
            cliente=Cliente.objects.create(nombre=nombre, razon_social=razon_social),
            neto=Decimal("1"),
        )
    _, filas = _planilla(operativo_client, _enviar(operativo_client))
    assert [fila["CLIENTE (RAZON SOCIAL)"] for fila in _items(filas)] == [
        "Alfa Sociedad Anónima",
        "Beta SA",
    ]


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_planilla_detalle_costo_lista_los_costos_no_anulados(operativo_client):
    item = ItemFacturacion.objects.create(
        mes=date(2026, 11, 1), cliente=Cliente.objects.create(nombre="Alfa SA"), neto=Decimal("1")
    )
    for tipo, destinatario, anulado in (
        ("comision", "Agencia Prueba", False),
        ("impresion", "", False),
        ("otro", "Anulado SRL", True),
    ):
        costo = Costo.objects.create(
            tipo=tipo,
            destinatario=destinatario,
            monto=Decimal("10"),
            fecha=date(2026, 11, 1),
            anulado=anulado,
        )
        CostoDeItem.objects.create(item=item, costo=costo)
    _, filas = _planilla(operativo_client, _enviar(operativo_client))
    assert _items(filas)[0]["DETALLE COSTO"] == "Comisión Agencia Prueba; Impresión"


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_planilla_tipo_junta_soporte_y_descripcion(operativo_client):
    for nombre, soporte, descripcion in (
        ("Alfa SA", "Gran Formato", "Cartel 12 x 4"),
        ("Beta SA", "Séxtuple", ""),
        ("Gama SA", "", "5 PP noviembre"),
    ):
        ItemFacturacion.objects.create(
            mes=date(2026, 11, 1),
            cliente=Cliente.objects.create(nombre=nombre),
            tipo_soporte=soporte,
            descripcion=descripcion,
            neto=Decimal("1"),
        )
    _, filas = _planilla(operativo_client, _enviar(operativo_client))
    assert [fila["TIPO (cartel/led/ppl/sextuples)"] for fila in _items(filas)] == [
        "Gran Formato · Cartel 12 x 4",
        "Séxtuple",
        "5 PP noviembre",
    ]


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_planilla_con_totales_y_neto_abajo(operativo_client):
    for nombre in ("Alfa SA", "Beta SA"):
        ItemFacturacion.objects.create(
            mes=date(2026, 11, 1), cliente=Cliente.objects.create(nombre=nombre), neto=Decimal("1")
        )
    _, filas = _planilla(operativo_client, _enviar(operativo_client))
    # Ítems en las filas 4 y 5 de Excel; totales en la 6, una vacía y el neto en la 8.
    assert filas[5][:3] == [None, "=SUM(B4:B5)", "=SUM(C4:C5)"]
    assert all(valor is None for valor in filas[6])
    assert filas[7][:2] == ["Neto", "=B6-C6"]
    assert len(filas) == 8
