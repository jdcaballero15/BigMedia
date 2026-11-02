"""Circuitos (Séxtuples, Banderolas, PPL) en la importación y en el catálogo (RN-005, HU-009)."""

import json
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona

URL = "/api/inventario/importaciones/"
CON_SLOTS = "formato,direccion,slots,zona,proveedor,tarifa_lista,estado,foto_url,ref_origen,confirmar_distinto"
CON_TAMANO = "formato,direccion,tamano,zona,proveedor,tarifa_lista,estado,foto_url,ref_origen,confirmar_distinto"


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_superuser(username="admin", password="clave-segura-123")
    client = Client()
    client.force_login(user)
    return client


def _importar(client: Client, formato: str, contenido: str) -> Any:
    archivo = SimpleUploadedFile("circuito.csv", contenido.encode(), content_type="text/csv")
    return client.post(URL, {"archivo": archivo, "formato": Formato.objects.get(nombre=formato).pk})


@pytest.mark.django_db
def test_catalogo_deja_gran_formato_y_ppl_separados():
    nombres = set(Formato.objects.values_list("nombre", flat=True))
    assert {"Gran Formato", "PPL"} <= nombres
    assert "PPL/Gran Formato" not in nombres
    circuitos = set(Formato.objects.filter(por_cantidad=True).values_list("nombre", flat=True))
    assert circuitos == {"Séxtuples", "Banderolas", "PPL"}
    assert Formato.objects.get(nombre="PPL").modalidad == Formato.Modalidad.FIJA


@pytest.mark.django_db
@pytest.mark.regla("RN-005")
@pytest.mark.parametrize("formato", ["Banderolas", "PPL"])
def test_importar_circuito_crea_carteles_con_capacidad_igual_a_slots(admin_client, formato):
    respuesta = _importar(
        admin_client,
        formato,
        f"{CON_SLOTS}\n{formato},Calle Ficticia 100,5,Ciudad,,,,,Fila 5,\n",
    )

    assert respuesta.status_code == 200
    cartel = Cartel.objects.get()
    assert (cartel.capacidad, cartel.tamano) == (5, "")
    assert cartel.nombre_visible == "Calle Ficticia 100 · 5 unidades"


@pytest.mark.django_db
@pytest.mark.regla("RN-005")
def test_importar_formato_por_cantidad_pide_la_columna_slots(admin_client):
    respuesta = _importar(
        admin_client, "Banderolas", f"{CON_TAMANO}\nBanderolas,Calle 1,1x2,Ciudad,,,,,,\n"
    )

    assert respuesta.status_code == 400
    assert "slots" in respuesta.json()["archivo"][0]


@pytest.mark.django_db
def test_importar_formato_comun_pide_tamano(admin_client):
    respuesta = _importar(
        admin_client, "Monocolumnas", f"{CON_SLOTS}\nMonocolumnas,Calle 1,3,Ciudad,,,,,,\n"
    )
    correcta = _importar(
        admin_client,
        "Monocolumnas",
        f'{CON_TAMANO}\nMonocolumnas,Ruta Ficticia 1,"10 x 6",Godoy Cruz,,,,,,\n',
    )

    assert respuesta.status_code == 400
    assert "tamano" in respuesta.json()["archivo"][0]
    assert correcta.status_code == 200
    assert Cartel.objects.get().nombre_visible == "Ruta Ficticia 1 · 10x6"


@pytest.mark.django_db
@pytest.mark.regla("RN-005")
def test_un_formato_marcado_por_cantidad_se_importa_con_slots(admin_client):
    Formato.objects.filter(nombre="Carteleras").update(por_cantidad=True)

    respuesta = _importar(
        admin_client, "Carteleras", f"{CON_SLOTS}\nCarteleras,Calle Ficticia 9,4,Ciudad,,,,,,\n"
    )

    assert respuesta.status_code == 200
    assert Cartel.objects.get().capacidad == 4


@pytest.mark.django_db
@pytest.mark.regla("RN-005")
def test_nombre_visible_de_circuito_muestra_unidades_y_sextuples_slots():
    zona = Zona.objects.get(nombre="Ciudad")
    activo = EstadoCartel.objects.get(codigo="activo")

    def nuevo(formato: str) -> Cartel:
        return Cartel.objects.create(
            formato=Formato.objects.get(nombre=formato),
            zona=zona,
            estado=activo,
            direccion="Calle Ficticia 100",
            capacidad=4,
        )

    assert nuevo("Séxtuples").nombre_visible == "Calle Ficticia 100 · 4 slots"
    assert nuevo("PPL").nombre_visible == "Calle Ficticia 100 · 4 unidades"
    assert nuevo("Gran Formato").nombre_visible == "Calle Ficticia 100"


@pytest.mark.django_db
def test_formato_por_cantidad_es_editable(operativo_client, lector_client):
    formato = Formato.objects.get(nombre="Carteleras")
    url = f"/api/inventario/formatos/{formato.pk}/"

    lectura = lector_client.patch(
        url, data=json.dumps({"por_cantidad": True}), content_type="application/json"
    )
    respuesta = operativo_client.patch(
        url, data=json.dumps({"por_cantidad": True}), content_type="application/json"
    )

    assert lectura.status_code == 403
    assert respuesta.status_code == 200
    assert respuesta.json()["por_cantidad"] is True
    formato.refresh_from_db()
    assert formato.por_cantidad is True
