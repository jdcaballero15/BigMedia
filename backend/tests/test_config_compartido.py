import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from config.permisos import LecturaConSesionEdicionOperativo
from config.texto import normalizar_busqueda


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [("Maipú", "maipu"), ("  ÑANDÚ ", "  nandu "), ("Godoy Cruz", "godoy cruz"), ("", "")],
)
def test_normalizar_busqueda_con_tildes_y_mayusculas_devuelve_texto_plano(texto, esperado):
    assert normalizar_busqueda(texto) == esperado


def _permite(user, method) -> bool:
    request = getattr(APIRequestFactory(), method)("/")
    request.user = user
    return LecturaConSesionEdicionOperativo().has_permission(request, APIView())


def test_permiso_sin_sesion_rechaza_lectura():
    assert _permite(AnonymousUser(), "get") is False


@pytest.mark.django_db
def test_permiso_usuario_sin_grupo_lee_y_no_edita():
    user = get_user_model().objects.create_user(username="lector", password="clave-segura-123")
    assert _permite(user, "get") is True
    assert _permite(user, "post") is False


@pytest.mark.django_db
def test_permiso_operativo_o_superusuario_edita():
    operativo = get_user_model().objects.create_user(username="op", password="clave-segura-123")
    operativo.groups.add(Group.objects.get(name="Operativo"))
    admin = get_user_model().objects.create_superuser(username="adm", password="clave-segura-123")
    assert _permite(operativo, "patch") is True
    assert _permite(admin, "post") is True
