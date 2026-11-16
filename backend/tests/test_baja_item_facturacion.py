"""Facturación sin estados: el ítem se edita siempre y se da de baja sin borrarse (HU-060)."""

import io
import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.test import Client
from openpyxl import load_workbook

from apps.auditoria.models import RegistroAuditoria
from apps.clientes.models import Cliente
from apps.facturacion.models import ItemFacturacion

ITEMS = "/api/facturacion/items/"
MES = "2026-11"


def _item(**datos: Any) -> ItemFacturacion:
    datos.setdefault("mes", date(2026, 11, 1))
    datos.setdefault("neto", Decimal("1000.00"))
    return ItemFacturacion.objects.create(
        cliente=Cliente.objects.create(nombre="Alfa", razon_social="Alfa SA"), **datos
    )


def _dar_de_baja(client: Client, item: ItemFacturacion) -> Any:
    return client.post(f"{ITEMS}{item.pk}/dar-de-baja/")


@pytest.mark.django_db
def test_dar_de_baja_item_lo_saca_de_la_lista_los_totales_y_el_excel(operativo_client):
    vigente = _item(neto=Decimal("500.00"))
    baja = _item()
    assert _dar_de_baja(operativo_client, baja).status_code == 200
    baja.refresh_from_db()
    assert baja.estado == ItemFacturacion.Estado.ANULADO
    lista = operativo_client.get(f"{ITEMS}?mes={MES}").json()
    assert [fila["id"] for fila in lista] == [vigente.pk]
    totales = operativo_client.get(f"{ITEMS}totales/?mes={MES}").json()
    assert (totales["cantidad"], totales["neto"]) == (1, "500.00")
    excel = operativo_client.get(f"{ITEMS}planilla/?mes={MES}")
    hoja = load_workbook(io.BytesIO(excel.content)).active
    assert hoja is not None
    clientes = [fila[0] for fila in hoja.iter_rows(min_row=4, values_only=True) if fila[0]]
    assert clientes == ["Alfa SA", "Neto"]


@pytest.mark.django_db
def test_dar_de_baja_queda_auditado_con_usuario_y_fecha(operativo_client):
    item = _item()
    _dar_de_baja(operativo_client, item)
    item.refresh_from_db()
    assert item.anulado_en is not None
    assert item.anulado_por is not None
    assert item.anulado_por.username == "operativo"
    registro = RegistroAuditoria.objects.get(
        entidad="item_facturacion", entidad_id=item.pk, campo="estado"
    )
    assert registro.valor_nuevo == "anulado"
    assert registro.usuario == item.anulado_por


@pytest.mark.django_db
def test_dar_de_baja_dos_veces_se_rechaza(operativo_client):
    item = _item()
    _dar_de_baja(operativo_client, item)
    assert _dar_de_baja(operativo_client, item).status_code == 404


@pytest.mark.django_db
def test_item_dado_de_baja_no_se_edita(operativo_client):
    item = _item()
    _dar_de_baja(operativo_client, item)
    respuesta = operativo_client.patch(
        f"{ITEMS}{item.pk}/", data=json.dumps({"neto": "1"}), content_type="application/json"
    )
    assert respuesta.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("estado", ["enviado", "facturado"])
def test_item_enviado_o_facturado_se_edita_como_cualquiera(operativo_client, estado):
    item = _item(estado=estado, numero_factura="A-0001-00000001")
    respuesta = operativo_client.patch(
        f"{ITEMS}{item.pk}/",
        data=json.dumps({"neto": "2000.00", "detalle_costo": "Comisión"}),
        content_type="application/json",
    )
    assert respuesta.status_code == 200, respuesta.json()
    item.refresh_from_db()
    assert (item.neto, item.detalle_costo) == (Decimal("2000.00"), "Comisión")


@pytest.mark.django_db
def test_estado_y_numero_de_factura_no_se_cambian_desde_la_api(operativo_client):
    item = _item()
    respuesta = operativo_client.patch(
        f"{ITEMS}{item.pk}/",
        data=json.dumps({"estado": "anulado", "numero_factura": "A-1"}),
        content_type="application/json",
    )
    assert respuesta.status_code == 200
    item.refresh_from_db()
    assert (item.estado, item.numero_factura) == ("borrador", "")


@pytest.mark.django_db
def test_lectura_no_puede_dar_de_baja(lector_client):
    item = _item()
    assert _dar_de_baja(lector_client, item).status_code == 403
    item.refresh_from_db()
    assert item.estado == ItemFacturacion.Estado.BORRADOR


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("metodo", "ruta"),
    [
        ("get", "/api/facturacion/envios/?mes=2026-11"),
        ("post", "/api/facturacion/envios/"),
        ("post", "{items}{id}/reabrir/"),
        ("post", "{items}{id}/anular-facturado/"),
    ],
)
def test_no_hay_envios_ni_reabrir_ni_anular_facturado(operativo_client, metodo, ruta):
    item = _item(estado="enviado")
    url = ruta.format(items=ITEMS, id=item.pk)
    assert getattr(operativo_client, metodo)(url).status_code == 404


@pytest.mark.django_db
def test_filtro_por_estado_ya_no_existe(operativo_client):
    _item()
    lista = operativo_client.get(f"{ITEMS}?mes={MES}&estado=facturado").json()
    assert len(lista) == 1
