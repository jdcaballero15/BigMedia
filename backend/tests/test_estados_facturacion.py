"""Estados del ítem a facturar y número de factura (HU-065)."""

import json
from decimal import Decimal
from typing import Any

import pytest
from django.test import Client

from apps.auditoria.models import RegistroAuditoria
from apps.facturacion.models import ItemFacturacion

URL = "/api/facturacion/items/"


def _patch(client: Client, pk: int, data: dict[str, Any]) -> Any:
    return client.patch(f"{URL}{pk}/", data=json.dumps(data), content_type="application/json")


def _item(estado: str = "borrador") -> ItemFacturacion:
    numero = "A-0001" if estado == "facturado" else ""
    return ItemFacturacion.objects.create(
        estado=estado, numero_factura=numero, neto=Decimal("1000.00")
    )


@pytest.mark.django_db
@pytest.mark.regla("RN-022")
def test_enviado_pasa_a_facturado_con_numero(operativo_client):
    item = _item("enviado")
    respuesta = _patch(
        operativo_client, item.pk, {"estado": "facturado", "numero_factura": " A-0001-00012345 "}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["numero_factura"] == "A-0001-00012345"
    assert respuesta.json()["estado"] == "facturado"


@pytest.mark.django_db
def test_facturado_sin_numero_se_rechaza(operativo_client):
    item = _item("enviado")
    for datos in ({"estado": "facturado"}, {"estado": "facturado", "numero_factura": "  "}):
        respuesta = _patch(operativo_client, item.pk, datos)
        assert respuesta.status_code == 400
        assert respuesta.json()["numero_factura"] == [
            "Cargá el número de factura para pasar el ítem a Facturado."
        ]
    item.refresh_from_db()
    assert item.estado == "enviado"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("actual", "nuevo"),
    [("borrador", "anulado"), ("enviado", "anulado")],
)
def test_transiciones_validas(operativo_client, actual, nuevo):
    item = _item(actual)
    assert _patch(operativo_client, item.pk, {"estado": nuevo}).status_code == 200
    item.refresh_from_db()
    assert item.estado == nuevo


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("actual", "nuevo"),
    [
        ("borrador", "enviado"),
        ("borrador", "facturado"),
        ("enviado", "borrador"),
        ("facturado", "anulado"),
        ("facturado", "borrador"),
        ("anulado", "borrador"),
    ],
)
def test_transiciones_invalidas(operativo_client, actual, nuevo):
    item = _item(actual)
    datos: dict[str, Any] = {"estado": nuevo, "numero_factura": "A-1"}
    respuesta = _patch(operativo_client, item.pk, datos)
    assert respuesta.status_code == 400
    assert "estado" in respuesta.json()
    item.refresh_from_db()
    assert item.estado == actual


@pytest.mark.django_db
def test_numero_de_factura_solo_al_facturar(operativo_client):
    item = _item("borrador")
    respuesta = _patch(operativo_client, item.pk, {"numero_factura": "A-1"})
    assert respuesta.status_code == 400
    assert "numero_factura" in respuesta.json()


@pytest.mark.django_db
def test_cambios_de_estado_e_importes_quedan_auditados(operativo_client):
    item = _item("borrador")
    _patch(operativo_client, item.pk, {"neto": "2000.00", "alicuota_iva": "10.5"})
    _patch(operativo_client, item.pk, {"descripcion": "No se audita"})
    _patch(operativo_client, item.pk, {"estado": "anulado"})
    registros = RegistroAuditoria.objects.filter(entidad="item_facturacion", entidad_id=item.pk)
    cambios = {(r.campo, r.valor_anterior, r.valor_nuevo) for r in registros}
    assert cambios == {
        ("neto", "1000.00", "2000.00"),
        ("alicuota_iva", "21.00", "10.50"),
        ("estado", "borrador", "anulado"),
    }
    assert {r.usuario.username for r in registros if r.usuario} == {"operativo"}
