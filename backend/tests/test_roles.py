import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.test import Client
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from apps.usuarios.services import ROL_ADMINISTRADOR, ROL_LECTURA, ROL_OPERATIVO, rol_de
from config.permisos import SoloAdministrador

pytestmark = pytest.mark.django_db

ENDPOINTS_DE_NEGOCIO = [
    "/api/inventario/carteles/",
    "/api/inventario/proveedores/",
    "/api/clientes/clientes/",
    "/api/clientes/marcas/",
    "/api/clientes/rubros/",
    "/api/clientes/grupos/",
    "/api/campanias/campanias/",
    "/api/reservas/reservas/",
    "/api/costos/costos/",
]


def _usuario(username: str, *grupos: str, superusuario: bool = False) -> User:
    modelo = get_user_model()
    if superusuario:
        user = modelo.objects.create_superuser(username=username, password="clave-segura-123")
    else:
        user = modelo.objects.create_user(username=username, password="clave-segura-123")
    for grupo in grupos:
        user.groups.add(Group.objects.get(name=grupo))
    return user


class _VistaDeAdministracion(APIView):
    permission_classes = [SoloAdministrador]

    def post(self, _request: Request) -> Response:
        return Response({"status": "ok"})


def _post_a_vista_de_administracion(user: User) -> int:
    request = APIRequestFactory().post("/admin-de-prueba/")
    force_authenticate(request, user=user)
    return _VistaDeAdministracion.as_view()(request).status_code


def test_rol_superusuario_es_administrador():
    assert rol_de(_usuario("admin", superusuario=True)) == ROL_ADMINISTRADOR


def test_rol_grupo_operativo_es_operativo():
    assert rol_de(_usuario("operativo", "Operativo")) == ROL_OPERATIVO


def test_rol_operativo_y_gerencia_es_operativo():
    assert rol_de(_usuario("seba", "Operativo", "Gerencia")) == ROL_OPERATIVO


def test_rol_sin_grupos_es_lectura():
    assert rol_de(_usuario("lector")) == ROL_LECTURA


def test_rol_gerencia_sola_es_lectura():
    assert rol_de(_usuario("gerente", "Gerencia")) == ROL_LECTURA


def test_rol_grupo_lectura_es_lectura():
    assert rol_de(_usuario("consulta", "Lectura")) == ROL_LECTURA


@pytest.mark.parametrize("endpoint", ENDPOINTS_DE_NEGOCIO)
def test_lectura_crear_por_api_responde_403(lector_client, endpoint):
    assert lector_client.post(endpoint, data={}, content_type="application/json").status_code == 403


@pytest.mark.parametrize("endpoint", ENDPOINTS_DE_NEGOCIO)
def test_lectura_editar_por_api_responde_403(lector_client, endpoint):
    response = lector_client.patch(f"{endpoint}1/", data={}, content_type="application/json")

    assert response.status_code == 403


@pytest.mark.parametrize("endpoint", ENDPOINTS_DE_NEGOCIO)
def test_lectura_consultar_por_api_responde_200(lector_client, endpoint):
    assert lector_client.get(endpoint).status_code == 200


def test_operativo_accion_de_administrador_responde_403():
    assert _post_a_vista_de_administracion(_usuario("operativo", "Operativo")) == 403


def test_lectura_accion_de_administrador_responde_403():
    assert _post_a_vista_de_administracion(_usuario("lector")) == 403


def test_administrador_accion_de_administrador_responde_200():
    assert _post_a_vista_de_administracion(_usuario("admin", superusuario=True)) == 200


def test_operativo_no_entra_al_admin_de_django():
    client = Client()
    client.force_login(_usuario("operativo", "Operativo"))

    response = client.get("/admin/")

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]


def test_cambio_de_rol_rige_en_la_proxima_peticion():
    user = _usuario("operativo", "Operativo")
    client = Client()
    client.force_login(user)
    endpoint = "/api/clientes/rubros/"
    assert client.post(endpoint, data={}, content_type="application/json").status_code != 403

    user.groups.remove(Group.objects.get(name="Operativo"))

    assert client.post(endpoint, data={}, content_type="application/json").status_code == 403
    assert client.get("/api/auth/me/").json()["rol"] == ROL_LECTURA


@pytest.mark.parametrize(
    ("grupos", "superusuario", "rol"),
    [
        ((), True, ROL_ADMINISTRADOR),
        (("Operativo",), False, ROL_OPERATIVO),
        (("Gerencia",), False, ROL_LECTURA),
    ],
)
def test_me_devuelve_rol(grupos, superusuario, rol):
    client = Client()
    client.force_login(_usuario("persona", *grupos, superusuario=superusuario))

    assert client.get("/api/auth/me/").json()["rol"] == rol


def test_migracion_crea_grupo_lectura():
    assert Group.objects.filter(name="Lectura").exists()
