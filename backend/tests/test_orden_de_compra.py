"""Orden de compra del ítem: número, fecha de aprobación y PDF (HU-062)."""

import json
from datetime import date
from typing import Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart

from apps.auditoria.models import RegistroAuditoria
from apps.facturacion.models import ItemFacturacion, OrdenCompraPdf

URL = "/api/facturacion/items/"
PDF = b"%PDF-1.4\n%prueba\n"


def _post(client: Client, data: dict[str, Any]) -> Any:
    return client.post(URL, data=json.dumps(data), content_type="application/json")


def _patch(client: Client, pk: int, data: dict[str, Any]) -> Any:
    return client.patch(f"{URL}{pk}/", data=json.dumps(data), content_type="application/json")


def _url_pdf(item: ItemFacturacion) -> str:
    return f"{URL}{item.pk}/orden-compra-pdf/"


def _subir(
    client: Client, item: ItemFacturacion, contenido: bytes = PDF, nombre: str = "oc.pdf"
) -> Any:
    archivo = SimpleUploadedFile(nombre, contenido, content_type="application/pdf")
    # El cliente de pruebas no codifica solo un PUT multipart: se arma como en un POST.
    cuerpo = encode_multipart(BOUNDARY, {"archivo": archivo})
    return client.put(_url_pdf(item), data=cuerpo, content_type=MULTIPART_CONTENT)


# --- Criterio 1: número, fecha y PDF quedan guardados y el PDF se abre ---


@pytest.mark.django_db
def test_numero_y_fecha_de_la_orden_de_compra_se_guardan(operativo_client):
    respuesta = _post(
        operativo_client,
        {"orden_compra_numero": " OC-123 ", "orden_compra_fecha": "2026-10-20"},
    )
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert (cuerpo["orden_compra_numero"], cuerpo["orden_compra_fecha"]) == (
        "OC-123",
        "2026-10-20",
    )
    assert cuerpo["orden_compra_pdf"] is None


@pytest.mark.django_db
def test_el_pdf_se_guarda_y_se_abre_desde_el_item(operativo_client):
    item = ItemFacturacion.objects.create()
    respuesta = _subir(operativo_client, item)
    assert respuesta.status_code == 200, respuesta.content
    assert respuesta.json() == {"nombre": "oc.pdf", "tamanio": len(PDF)}

    abierto = operativo_client.get(_url_pdf(item))
    assert abierto.status_code == 200
    assert abierto["Content-Type"] == "application/pdf"
    assert abierto["Content-Disposition"] == 'inline; filename="oc.pdf"'
    assert abierto.content == PDF

    detalle = operativo_client.get(f"{URL}{item.pk}/").json()
    assert detalle["orden_compra_pdf"] == {"nombre": "oc.pdf", "tamanio": len(PDF)}


@pytest.mark.django_db
def test_subir_otro_pdf_reemplaza_el_anterior(operativo_client):
    item = ItemFacturacion.objects.create()
    _subir(operativo_client, item)
    _subir(operativo_client, item, PDF + b"v2", "oc-v2.pdf")
    assert OrdenCompraPdf.objects.get().nombre == "oc-v2.pdf"


@pytest.mark.django_db
def test_quitar_el_pdf_lo_saca_del_item_y_queda_auditado(operativo_client):
    item = ItemFacturacion.objects.create()
    _subir(operativo_client, item)
    assert operativo_client.delete(_url_pdf(item)).status_code == 204
    assert not OrdenCompraPdf.objects.exists()
    assert operativo_client.get(_url_pdf(item)).status_code == 404
    cambios = RegistroAuditoria.objects.filter(
        entidad="item_facturacion", entidad_id=item.pk, campo="orden_compra_pdf"
    ).values_list("valor_anterior", "valor_nuevo")
    assert list(cambios.order_by("id")) == [("", "oc.pdf"), ("oc.pdf", "")]


@pytest.mark.django_db
def test_lectura_abre_el_pdf_pero_no_lo_sube_ni_lo_quita(operativo_client, lector_client):
    item = ItemFacturacion.objects.create()
    _subir(operativo_client, item)
    assert lector_client.get(_url_pdf(item)).status_code == 200
    assert _subir(lector_client, item).status_code == 403
    assert lector_client.delete(_url_pdf(item)).status_code == 403


@pytest.mark.django_db
def test_sin_sesion_no_se_abre_el_pdf(client):
    item = ItemFacturacion.objects.create()
    assert client.get(_url_pdf(item)).status_code in (401, 403)


@pytest.mark.django_db
def test_pdf_de_un_item_inexistente_da_404(operativo_client):
    assert operativo_client.get(f"{URL}999999/orden-compra-pdf/").status_code == 404


# --- Criterio 2: número repetido avisa con el ítem coincidente y guarda igual ---


@pytest.mark.django_db
def test_numero_repetido_avisa_con_el_item_coincidente_y_guarda(operativo_client):
    existente = ItemFacturacion.objects.create(
        orden_compra_numero="OC-123", descripcion="Alquiler octubre"
    )
    respuesta = _post(operativo_client, {"orden_compra_numero": "oc-123"})
    assert respuesta.status_code == 201
    assert respuesta.json()["avisos"] == {
        "orden_compra": [{"id": existente.pk, "descripcion": "Alquiler octubre"}]
    }
    assert ItemFacturacion.objects.filter(orden_compra_numero="oc-123").exists()


@pytest.mark.django_db
def test_editar_con_numero_repetido_avisa_sin_contarse_a_si_mismo(operativo_client):
    otro = ItemFacturacion.objects.create(orden_compra_numero="OC-9")
    item = ItemFacturacion.objects.create(orden_compra_numero="OC-9")
    respuesta = _patch(operativo_client, item.pk, {"descripcion": "Cambio"})
    assert respuesta.status_code == 200
    assert [a["id"] for a in respuesta.json()["avisos"]["orden_compra"]] == [otro.pk]


@pytest.mark.django_db
def test_un_item_anulado_no_cuenta_como_duplicado(operativo_client):
    ItemFacturacion.objects.create(orden_compra_numero="OC-1", estado="anulado")
    respuesta = _post(operativo_client, {"orden_compra_numero": "OC-1"})
    assert respuesta.json()["avisos"] == {"orden_compra": []}


# --- Criterio 3: no PDF o demasiado grande se rechaza con mensaje ---


@pytest.mark.django_db
def test_un_archivo_que_no_es_pdf_se_rechaza(operativo_client):
    item = ItemFacturacion.objects.create()
    respuesta = _subir(operativo_client, item, b"hola", "oc.pdf")
    assert respuesta.status_code == 400
    assert respuesta.json() == {"archivo": ["El archivo tiene que ser un PDF."]}
    respuesta = _subir(operativo_client, item, PDF, "oc.docx")
    assert respuesta.status_code == 400
    assert not OrdenCompraPdf.objects.exists()


@pytest.mark.django_db
@override_settings(FACTURACION_OC_MAX_MB=1)
def test_un_pdf_que_supera_el_tamano_maximo_se_rechaza(operativo_client):
    item = ItemFacturacion.objects.create()
    respuesta = _subir(operativo_client, item, PDF + b"0" * (1024 * 1024))
    assert respuesta.status_code == 400
    assert respuesta.json() == {"archivo": ["El PDF supera el tamaño máximo de 1 MB."]}


@pytest.mark.django_db
def test_subir_sin_archivo_se_rechaza(operativo_client):
    item = ItemFacturacion.objects.create()
    cuerpo = encode_multipart(BOUNDARY, {"otro": "dato"})
    respuesta = operativo_client.put(_url_pdf(item), data=cuerpo, content_type=MULTIPART_CONTENT)
    assert respuesta.status_code == 400
    assert respuesta.json() == {"archivo": ["Adjuntá el PDF de la orden de compra."]}


# --- Criterio 4: sin orden de compra se guarda ---


@pytest.mark.django_db
def test_un_item_sin_orden_de_compra_se_guarda(operativo_client):
    respuesta = _post(operativo_client, {"descripcion": "Sin OC"})
    assert respuesta.status_code == 201
    assert respuesta.json()["orden_compra_numero"] == ""
    assert respuesta.json()["avisos"] == {"orden_compra": []}


# --- La orden de compra es un dato del ítem: solo se edita en Borrador ---


@pytest.mark.django_db
def test_fuera_de_borrador_no_se_cambia_la_orden_de_compra(operativo_client):
    item = ItemFacturacion.objects.create(estado="enviado")
    respuesta = _patch(operativo_client, item.pk, {"orden_compra_numero": "OC-2"})
    assert respuesta.status_code == 400
    assert _subir(operativo_client, item).status_code == 400
    assert operativo_client.delete(_url_pdf(item)).status_code in (400, 404)


@pytest.mark.django_db
def test_el_listado_informa_el_pdf_sin_traer_el_contenido(operativo_client):
    item = ItemFacturacion.objects.create(mes=date(2026, 11, 1))
    _subir(operativo_client, item)
    ItemFacturacion.objects.create(mes=date(2026, 11, 1))
    filas = operativo_client.get(URL, {"mes": "2026-11"}).json()
    pdfs = sorted((f["orden_compra_pdf"] is not None) for f in filas)
    assert pdfs == [False, True]
