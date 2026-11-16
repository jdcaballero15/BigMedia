"""Orden de publicidad de la campaña (HU-069, ADR-0011)."""

import json
from typing import Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart

from apps.auditoria.models import RegistroAuditoria
from apps.campanias.models import Campania, OrdenPublicidad
from apps.clientes.models import Cliente, Marca

URL = "/api/campanias/campanias/"
URL_ORDENES = "/api/campanias/ordenes-publicidad/"
PDF = b"%PDF-1.4\n%orden de publicidad\n"


@pytest.fixture(autouse=True)
def almacenamiento_en_memoria(settings: Any) -> None:
    """Los archivos van a memoria: los tests no tocan el disco ni la red (ADR-0011)."""
    settings.STORAGES = {
        **settings.STORAGES,
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    }
    settings.R2_BUCKET = ""
    settings.CAMPANIAS_OP_MAX_MB = 1


def _pdf(nombre: str = "orden.pdf", contenido: bytes = PDF) -> SimpleUploadedFile:
    return SimpleUploadedFile(nombre, contenido, content_type="application/pdf")


def _crear(client: Client, archivos: list[SimpleUploadedFile], **campos: Any) -> Any:
    return client.post(URL, data={**campos, "ordenes_publicidad": archivos})


def _editar(client: Client, pk: int, archivos: list[SimpleUploadedFile], **campos: Any) -> Any:
    # El cliente de pruebas no codifica solo un PATCH multipart: se arma como en un POST.
    cuerpo = encode_multipart(BOUNDARY, {**campos, "ordenes_publicidad": archivos})
    return client.patch(f"{URL}{pk}/", data=cuerpo, content_type=MULTIPART_CONTENT)


def _marca() -> Marca:
    cliente = Cliente.objects.create(nombre="Coca Cola", razon_social="Coca Cola S.A.")
    return Marca.objects.create(nombre="Sprite", cliente=cliente)


# --- Criterio 1: Nueva campaña con PDF ---


@pytest.mark.django_db
def test_crear_campania_con_pdf_guarda_la_orden(operativo_client):
    respuesta = _crear(operativo_client, [_pdf()], nombre="Verano")
    assert respuesta.status_code == 201, respuesta.content
    campania = Campania.objects.get()
    assert campania.nombre == "Verano"
    orden = OrdenPublicidad.objects.get()
    assert (orden.campania, orden.nombre, orden.tamanio, orden.activa) == (
        campania,
        "orden.pdf",
        len(PDF),
        True,
    )
    assert orden.archivo.read() == PDF


@pytest.mark.django_db
def test_crear_campania_multipart_con_campos_vacios_los_guarda_nulos(operativo_client):
    respuesta = _crear(operativo_client, [_pdf()], nombre="", marca="", fecha_inicio="")
    assert respuesta.status_code == 201, respuesta.content
    campania = Campania.objects.get()
    assert (campania.marca, campania.fecha_inicio) == (None, None)


# --- Criterio 2: la campaña muestra sus órdenes ---


@pytest.mark.django_db
def test_campania_expone_sus_ordenes_con_nombre_usuario_y_fecha(operativo_client):
    pk = _crear(operativo_client, [_pdf("op-cliente.pdf")]).json()["id"]
    ordenes = operativo_client.get(f"{URL}{pk}/").json()["ordenes_publicidad"]
    assert len(ordenes) == 1
    orden = ordenes[0]
    assert orden["nombre"] == "op-cliente.pdf"
    assert orden["tamanio"] == len(PDF)
    assert orden["subida_por_nombre"] == "operativo"
    assert orden["subida_en"]
    assert orden["activa"] is True


@pytest.mark.django_db
def test_abrir_la_orden_devuelve_el_pdf(operativo_client):
    _crear(operativo_client, [_pdf("op.pdf")])
    orden = OrdenPublicidad.objects.get()
    respuesta = operativo_client.get(f"{URL_ORDENES}{orden.pk}/archivo/")
    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "application/pdf"
    assert respuesta["Content-Disposition"] == 'inline; filename="op.pdf"'
    assert b"".join(respuesta.streaming_content) == PDF


@pytest.mark.django_db
def test_archivo_con_r2_redirige_a_url_firmada(operativo_client, settings):
    _crear(operativo_client, [_pdf()])
    orden = OrdenPublicidad.objects.get()
    settings.R2_BUCKET = "bigmedia-test"
    respuesta = operativo_client.get(f"{URL_ORDENES}{orden.pk}/archivo/")
    assert respuesta.status_code == 302
    assert respuesta["Location"] == orden.archivo.url


@pytest.mark.django_db
def test_clave_del_objeto_no_usa_el_nombre_original(operativo_client):
    _crear(operativo_client, [_pdf("Contrato Coca Cola.pdf")])
    clave = OrdenPublicidad.objects.get().archivo.name or ""
    campania_id = OrdenPublicidad.objects.get().campania_id
    assert clave.startswith(f"campanias/{campania_id}/ordenes-publicidad/")
    assert clave.endswith(".pdf")
    assert "Coca" not in clave


# --- Criterio 3: editar y sumar otra orden ---


@pytest.mark.django_db
def test_editar_campania_con_otro_pdf_conserva_las_dos(operativo_client):
    pk = _crear(operativo_client, [_pdf("v1.pdf")]).json()["id"]
    respuesta = _editar(operativo_client, pk, [_pdf("v2.pdf")], nombre="Verano")
    assert respuesta.status_code == 200, respuesta.content
    nombres = [orden["nombre"] for orden in respuesta.json()["ordenes_publicidad"]]
    assert nombres == ["v1.pdf", "v2.pdf"]
    assert Campania.objects.get().nombre == "Verano"


@pytest.mark.django_db
def test_crear_campania_con_dos_pdf_guarda_las_dos(operativo_client):
    _crear(operativo_client, [_pdf("a.pdf"), _pdf("b.pdf")])
    assert sorted(OrdenPublicidad.objects.values_list("nombre", flat=True)) == ["a.pdf", "b.pdf"]


# --- Criterio 4: un archivo inválido no guarda nada ---


@pytest.mark.django_db
@pytest.mark.parametrize(
    "archivo",
    [
        _pdf("orden.docx"),
        _pdf("orden.pdf", b"no es un pdf"),
    ],
)
def test_crear_campania_con_archivo_no_pdf_no_guarda_nada(operativo_client, archivo):
    respuesta = _crear(operativo_client, [_pdf("buena.pdf"), archivo], nombre="Verano")
    assert respuesta.status_code == 400
    assert respuesta.json()["ordenes_publicidad"] == ["El archivo tiene que ser un PDF."]
    assert not Campania.objects.exists()
    assert not OrdenPublicidad.objects.exists()


@pytest.mark.django_db
def test_crear_campania_con_pdf_mayor_al_maximo_no_guarda_nada(operativo_client):
    grande = _pdf("grande.pdf", PDF + b"0" * (1024 * 1024))
    respuesta = _crear(operativo_client, [grande], nombre="Verano")
    assert respuesta.status_code == 400
    assert respuesta.json()["ordenes_publicidad"] == [
        "El PDF «grande.pdf» supera el tamaño máximo de 1 MB."
    ]
    assert not Campania.objects.exists()


@pytest.mark.django_db
def test_editar_con_archivo_invalido_no_cambia_la_campania(operativo_client):
    pk = _crear(operativo_client, [], nombre="Verano").json()["id"]
    respuesta = _editar(operativo_client, pk, [_pdf("x.txt")], nombre="Invierno")
    assert respuesta.status_code == 400
    assert Campania.objects.get().nombre == "Verano"
    assert not OrdenPublicidad.objects.exists()


# --- Criterio 5: dar de baja ---


@pytest.mark.django_db
def test_dar_de_baja_orden_la_saca_de_vigentes_y_no_borra_el_archivo(operativo_client):
    _crear(operativo_client, [_pdf()])
    orden = OrdenPublicidad.objects.get()
    respuesta = operativo_client.post(f"{URL_ORDENES}{orden.pk}/dar-de-baja/")
    assert respuesta.status_code == 200, respuesta.content
    assert respuesta.json()["activa"] is False
    orden.refresh_from_db()
    assert orden.activa is False
    assert orden.dada_de_baja_por is not None
    assert orden.dada_de_baja_en is not None
    assert orden.archivo.storage.exists(orden.archivo.name or "")
    # Sigue en el histórico de la campaña.
    ordenes = operativo_client.get(f"{URL}{orden.campania_id}/").json()["ordenes_publicidad"]
    assert [o["activa"] for o in ordenes] == [False]


@pytest.mark.django_db
def test_dar_de_baja_dos_veces_no_cambia_la_primera_baja(operativo_client):
    _crear(operativo_client, [_pdf()])
    orden = OrdenPublicidad.objects.get()
    operativo_client.post(f"{URL_ORDENES}{orden.pk}/dar-de-baja/")
    orden.refresh_from_db()
    primera = orden.dada_de_baja_en
    operativo_client.post(f"{URL_ORDENES}{orden.pk}/dar-de-baja/")
    orden.refresh_from_db()
    assert orden.dada_de_baja_en == primera


@pytest.mark.django_db
def test_adjuntar_y_dar_de_baja_quedan_auditados(operativo_client):
    _crear(operativo_client, [_pdf("op.pdf")])
    orden = OrdenPublicidad.objects.get()
    operativo_client.post(f"{URL_ORDENES}{orden.pk}/dar-de-baja/")
    registros = RegistroAuditoria.objects.filter(
        entidad="campania", entidad_id=orden.campania_id, campo="orden_publicidad"
    ).order_by("id")
    assert [(r.valor_anterior, r.valor_nuevo) for r in registros] == [
        ("", "op.pdf"),
        ("op.pdf", ""),
    ]


# --- Criterios 6 y 7: permisos ---


@pytest.mark.django_db
def test_lectura_abre_la_orden_pero_no_adjunta_ni_da_de_baja(operativo_client, lector_client):
    pk = _crear(operativo_client, [_pdf()]).json()["id"]
    orden = OrdenPublicidad.objects.get()

    assert lector_client.get(f"{URL_ORDENES}{orden.pk}/archivo/").status_code == 200
    assert _editar(lector_client, pk, [_pdf("otra.pdf")]).status_code == 403
    assert lector_client.post(f"{URL_ORDENES}{orden.pk}/dar-de-baja/").status_code == 403
    assert OrdenPublicidad.objects.get().activa is True
    assert OrdenPublicidad.objects.count() == 1


@pytest.mark.django_db
def test_archivo_sin_sesion_se_niega(operativo_client):
    _crear(operativo_client, [_pdf()])
    orden = OrdenPublicidad.objects.get()
    respuesta = Client().get(f"{URL_ORDENES}{orden.pk}/archivo/")
    assert respuesta.status_code in (401, 403)


# --- Criterio 8: sin orden se guarda y se confirma igual ---


@pytest.mark.django_db
def test_crear_y_confirmar_campania_sin_orden_se_acepta(operativo_client):
    marca = _marca()
    creada = operativo_client.post(
        URL, data=json.dumps({"nombre": "Verano"}), content_type="application/json"
    )
    assert creada.status_code == 201
    assert creada.json()["ordenes_publicidad"] == []
    confirmada = operativo_client.patch(
        f"{URL}{creada.json()['id']}/",
        data=json.dumps(
            {
                "marca": marca.pk,
                "fecha_inicio": "2026-12-01",
                "fecha_fin": "2026-12-31",
                "estado": "confirmada",
            }
        ),
        content_type="application/json",
    )
    assert confirmada.status_code == 200, confirmada.content
    assert Campania.objects.get().estado == "confirmada"
