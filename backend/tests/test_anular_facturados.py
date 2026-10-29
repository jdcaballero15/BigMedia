"""Anular un ítem ya Facturado para corregirlo, con motivo y aviso (RN-026, HU-067)."""

import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.core import mail
from django.test import Client

from apps.auditoria.models import RegistroAuditoria
from apps.clientes.models import Cliente
from apps.facturacion.models import GrupoFactura, ItemFacturacion

URL = "/api/facturacion/items/"
CORREO = "administracion@example.com"


@pytest.fixture
def con_correo(settings):
    settings.FACTURACION_CORREO_ADMINISTRACION = CORREO
    settings.DEFAULT_FROM_EMAIL = "avisos@example.com"


def _anular(client: Client, item: ItemFacturacion, motivo: Any = "Nota de crédito NC-7") -> Any:
    return client.post(
        f"{URL}{item.pk}/anular-facturado/",
        data=json.dumps({"motivo": motivo}),
        content_type="application/json",
    )


def _facturado(**campos: Any) -> ItemFacturacion:
    datos = {
        "mes": date(2026, 11, 1),
        "cliente": Cliente.objects.create(nombre="Alfa SA"),
        "descripcion": "Alquiler noviembre",
        "neto": Decimal("10000.00"),
        "estado": "facturado",
        "numero_factura": "A-0001-123",
        **campos,
    }
    return ItemFacturacion.objects.create(**datos)


@pytest.mark.django_db
@pytest.mark.regla("RN-026")
def test_anular_facturado_con_motivo_lo_anula_y_conserva_el_numero(operativo_client):
    item = _facturado()
    respuesta = _anular(operativo_client, item, " Nota de crédito NC-7 ")
    assert respuesta.status_code == 200, respuesta.json()
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "anulado"
    assert cuerpo["numero_factura"] == "A-0001-123"
    assert (cuerpo["anulado_por_nombre"], cuerpo["motivo_anulacion"]) == (
        "operativo",
        "Nota de crédito NC-7",
    )
    assert cuerpo["anulado_en"] is not None


@pytest.mark.django_db
@pytest.mark.regla("RN-026")
@pytest.mark.parametrize("motivo", ["", "   ", None, 5])
def test_anular_facturado_sin_motivo_se_rechaza(operativo_client, motivo):
    item = _facturado()
    respuesta = _anular(operativo_client, item, motivo)
    assert respuesta.status_code == 400
    assert "motivo" in respuesta.json()
    item.refresh_from_db()
    assert item.estado == "facturado"


@pytest.mark.django_db
@pytest.mark.regla("RN-026")
@pytest.mark.parametrize("estado", ["borrador", "enviado", "anulado"])
def test_anular_facturado_un_item_que_no_esta_facturado_se_rechaza(operativo_client, estado):
    item = _facturado(estado=estado, numero_factura="")
    respuesta = _anular(operativo_client, item)
    assert respuesta.status_code == 400
    assert "estado" in respuesta.json()


@pytest.mark.django_db
@pytest.mark.regla("RN-026")
def test_anular_facturado_queda_auditado(operativo_client):
    item = _facturado()
    _anular(operativo_client, item)
    registros = RegistroAuditoria.objects.filter(entidad="item_facturacion", entidad_id=item.pk)
    assert set(registros.values_list("campo", "valor_anterior", "valor_nuevo")) == {
        ("estado", "facturado", "anulado"),
        ("motivo_anulacion", "", "Nota de crédito NC-7"),
    }


@pytest.mark.django_db
@pytest.mark.regla("RN-026")
@pytest.mark.usefixtures("con_correo")
def test_anular_facturado_avisa_a_administracion_al_confirmar(
    operativo_client, django_capture_on_commit_callbacks
):
    grupo = GrupoFactura.objects.create(mes=date(2026, 11, 1))
    item = _facturado(grupo=grupo)
    with django_capture_on_commit_callbacks(execute=True):
        _anular(operativo_client, item)
    assert len(mail.outbox) == 1
    aviso = mail.outbox[0]
    assert aviso.to == [CORREO]
    assert f"#{item.pk}" in aviso.subject
    for texto in (
        "Alquiler noviembre",
        "2026-11",
        "A-0001-123",
        "operativo",
        "Nota de crédito NC-7",
        grupo.codigo,
        "ítem nuevo",
    ):
        assert texto in aviso.body


@pytest.mark.django_db
@pytest.mark.regla("RN-026")
@pytest.mark.usefixtures("con_correo")
def test_anular_facturado_rechazado_no_avisa(operativo_client, django_capture_on_commit_callbacks):
    item = _facturado(estado="enviado", numero_factura="")
    with django_capture_on_commit_callbacks(execute=True):
        _anular(operativo_client, item)
    assert mail.outbox == []


@pytest.mark.django_db
@pytest.mark.regla("RN-026")
def test_anular_facturado_lo_saca_de_los_totales_del_mes(operativo_client):
    item = _facturado()
    _facturado(neto=Decimal("500.00"), numero_factura="A-0001-124")
    _anular(operativo_client, item)
    totales = operativo_client.get(f"{URL}totales/?mes=2026-11").json()
    assert totales["cantidad"] == 1
    assert Decimal(totales["neto"]) == Decimal("500.00")


@pytest.mark.django_db
@pytest.mark.regla("RN-026")
def test_patch_a_anulado_de_un_facturado_sigue_rechazado(operativo_client):
    item = _facturado()
    respuesta = operativo_client.patch(
        f"{URL}{item.pk}/", data=json.dumps({"estado": "anulado"}), content_type="application/json"
    )
    assert respuesta.status_code == 400
    item.refresh_from_db()
    assert item.estado == "facturado"


@pytest.mark.django_db
@pytest.mark.regla("RN-026")
def test_lectura_no_puede_anular_un_facturado(lector_client):
    assert _anular(lector_client, _facturado()).status_code == 403


@pytest.mark.django_db
@pytest.mark.regla("RN-026")
def test_anular_facturado_un_item_inexistente_da_404(operativo_client):
    respuesta = operativo_client.post(
        f"{URL}999999/anular-facturado/",
        data=json.dumps({"motivo": "x"}),
        content_type="application/json",
    )
    assert respuesta.status_code == 404
