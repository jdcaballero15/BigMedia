"""Gestión de usuarios desde la API (HU-005)."""

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.db import connection
from django.test import Client

from apps.auditoria.models import RegistroAuditoria

URL = "/api/usuarios/usuarios/"
URL_DEFINIR_CLAVE = "/api/usuarios/definir-clave/"
CLAVE_NUEVA = "otra-clave-larga-987"


def _admin(username: str = "admin") -> User:
    return get_user_model().objects.create_superuser(
        username=username, email=f"{username}@ejemplo.test", password="clave-segura-123"
    )


def _cliente_de(user: User) -> Client:
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(db):
    return _cliente_de(_admin())


def _post(client: Client, url: str, data: dict[str, object]) -> Any:
    return client.post(url, data=json.dumps(data), content_type="application/json")


def _patch(client: Client, url: str, data: dict[str, object]) -> Any:
    return client.patch(url, data=json.dumps(data), content_type="application/json")


def _alta(client: Client, **cambios: object) -> Any:
    datos: dict[str, object] = {
        "username": "ale",
        "first_name": "Ale",
        "last_name": "Prueba",
        "email": "ale@ejemplo.test",
        "rol": "operativo",
        "es_gerencia": True,
    }
    datos.update(cambios)
    return _post(client, URL, datos)


def _link(client: Client, usuario_id: int) -> tuple[str, str]:
    respuesta = _post(client, f"{URL}{usuario_id}/link-clave/", {})
    assert respuesta.status_code == 200
    params = parse_qs(urlparse(respuesta.json()["link"]).query)
    uid, token = params["definir-clave"][0].split(".", 1)
    return uid, token


def _definir(uid: str, token: str, clave: str = CLAVE_NUEVA) -> Any:
    return _post(Client(), URL_DEFINIR_CLAVE, {"uid": uid, "token": token, "clave": clave})


def _login(username: str, clave: str) -> int:
    respuesta = _post(Client(), "/api/auth/login/", {"username": username, "password": clave})
    return int(respuesta.status_code)


# --- Criterio 1: alta con nombre, correo y rol, y una forma segura de definir la contraseña ---


@pytest.mark.django_db
def test_crear_usuario_sin_clave_usable_y_rol_asignado(admin_client):
    respuesta = _alta(admin_client)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["rol"] == "operativo"
    assert cuerpo["es_gerencia"] is True
    assert cuerpo["activo"] is True
    assert cuerpo["tiene_clave"] is False
    user = get_user_model().objects.get(username="ale")
    assert not user.has_usable_password()
    assert user.groups.filter(name="Operativo").exists()
    assert user.groups.filter(name="Gerencia").exists()


@pytest.mark.django_db
def test_crear_usuario_administrador_marca_superusuario_y_staff(admin_client):
    assert _alta(admin_client, rol="administrador").status_code == 201
    user = get_user_model().objects.get(username="ale")
    assert user.is_superuser
    assert user.is_staff


@pytest.mark.django_db
def test_crear_usuario_sin_nombre_correo_o_rol_responde_400(admin_client):
    respuesta = _post(admin_client, URL, {"username": "ale"})
    assert respuesta.status_code == 400
    assert {"first_name", "email", "rol"} <= set(respuesta.json())


@pytest.mark.django_db
def test_crear_usuario_nombre_repetido_sin_distinguir_mayusculas_responde_400(admin_client):
    assert _alta(admin_client).status_code == 201
    respuesta = _alta(admin_client, username="ALE")
    assert respuesta.status_code == 400
    assert "username" in respuesta.json()


@pytest.mark.django_db
def test_link_clave_valido_define_clave_y_queda_usado(admin_client):
    usuario_id = _alta(admin_client).json()["id"]
    uid, token = _link(admin_client, usuario_id)
    assert _definir(uid, token).status_code == 200
    assert _login("ale", CLAVE_NUEVA) == 200
    # El mismo link ya no sirve: el token depende de la contraseña, que cambió.
    assert _definir(uid, token, "tercera-clave-larga-555").status_code == 400


@pytest.mark.django_db
def test_link_clave_token_invalido_rechaza(admin_client):
    usuario_id = _alta(admin_client).json()["id"]
    uid, _token = _link(admin_client, usuario_id)
    respuesta = _definir(uid, "token-falso")
    assert respuesta.status_code == 400
    assert not get_user_model().objects.get(pk=usuario_id).has_usable_password()


@pytest.mark.django_db
def test_link_clave_vencido_rechaza(admin_client, settings):
    usuario_id = _alta(admin_client).json()["id"]
    uid, token = _link(admin_client, usuario_id)
    settings.PASSWORD_RESET_TIMEOUT = -1
    assert _definir(uid, token).status_code == 400


@pytest.mark.django_db
def test_definir_clave_debil_responde_400_con_mensaje(admin_client):
    usuario_id = _alta(admin_client).json()["id"]
    uid, token = _link(admin_client, usuario_id)
    respuesta = _definir(uid, token, "123")
    assert respuesta.status_code == 400
    assert "clave" in respuesta.json()


@pytest.mark.django_db
def test_restablecer_clave_invalida_la_anterior(admin_client):
    usuario_id = _alta(admin_client).json()["id"]
    uid, token = _link(admin_client, usuario_id)
    assert _definir(uid, token).status_code == 200
    viejo_uid, viejo_token = _link(admin_client, usuario_id)
    assert _login("ale", CLAVE_NUEVA) == 401
    nuevo_uid, nuevo_token = _link(admin_client, usuario_id)
    # Generar otro link invalida el anterior.
    assert _definir(viejo_uid, viejo_token).status_code == 400
    assert _definir(nuevo_uid, nuevo_token, "tercera-clave-larga-555").status_code == 200
    assert _login("ale", "tercera-clave-larga-555") == 200


# --- Criterio 2: el inactivo no ingresa y se conserva su historial ---


@pytest.mark.django_db
def test_usuario_inactivo_login_rechazado_y_auditoria_conservada(admin_client):
    user = get_user_model().objects.create_user(username="ale", password=CLAVE_NUEVA)
    RegistroAuditoria(
        entidad="reserva", entidad_id=1, campo="estado", valor_nuevo="confirmada", usuario=user
    ).save()
    assert _patch(admin_client, f"{URL}{user.pk}/", {"activo": False}).status_code == 200
    assert _login("ale", CLAVE_NUEVA) == 401
    assert RegistroAuditoria.objects.filter(usuario=user, entidad="reserva").count() == 1


@pytest.mark.django_db
def test_usuario_inactivado_sesion_abierta_pierde_acceso(admin_client):
    user = get_user_model().objects.create_user(username="ale", password=CLAVE_NUEVA)
    sesion = _cliente_de(user)
    assert sesion.get("/api/auth/me/").status_code == 200
    assert _patch(admin_client, f"{URL}{user.pk}/", {"activo": False}).status_code == 200
    assert sesion.get("/api/auth/me/").status_code == 401


@pytest.mark.django_db
def test_api_usuarios_no_permite_delete(admin_client):
    user = get_user_model().objects.create_user(username="ale")
    assert admin_client.delete(f"{URL}{user.pk}/").status_code == 405
    assert get_user_model().objects.filter(pk=user.pk).exists()


# --- Criterio 3: siempre queda al menos un administrador activo ---


@pytest.mark.django_db
@pytest.mark.parametrize("cambio", [{"activo": False}, {"rol": "operativo"}, {"rol": "lectura"}])
def test_unico_admin_inactivar_o_cambiar_rol_rechaza(cambio):
    admin = _admin()
    respuesta = _patch(_cliente_de(admin), f"{URL}{admin.pk}/", cambio)
    assert respuesta.status_code == 400
    assert "administrador activo" in json.dumps(respuesta.json(), ensure_ascii=False)
    admin.refresh_from_db()
    assert admin.is_superuser
    assert admin.is_active


@pytest.mark.django_db
def test_admin_con_otro_activo_puede_dejar_de_serlo():
    admin = _admin()
    _admin("otro")
    respuesta = _patch(_cliente_de(admin), f"{URL}{admin.pk}/", {"rol": "operativo"})
    assert respuesta.status_code == 200
    admin.refresh_from_db()
    assert not admin.is_superuser
    assert not admin.is_staff
    assert admin.groups.filter(name="Operativo").exists()


@pytest.mark.django_db
def test_admin_inactivo_no_cuenta_como_administrador_activo():
    admin = _admin()
    otro = _admin("otro")
    otro.is_active = False
    otro.save()
    assert _patch(_cliente_de(admin), f"{URL}{admin.pk}/", {"activo": False}).status_code == 400


def _inactivar_en_hilo(autor_pk: int, objetivo_pk: int) -> int:
    """Inactiva un usuario en su propio hilo/conexión; devuelve el status HTTP."""
    try:
        client = _cliente_de(get_user_model().objects.get(pk=autor_pk))
        return int(_patch(client, f"{URL}{objetivo_pk}/", {"activo": False}).status_code)
    finally:
        connection.close()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_dos_admins_inactivacion_concurrente_deja_uno_activo():
    uno = _admin("uno")
    dos = _admin("dos")
    pares = [(uno.pk, dos.pk), (dos.pk, uno.pk)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(lambda par: _inactivar_en_hilo(*par), pares))
    activos = get_user_model().objects.filter(is_superuser=True, is_active=True).count()
    assert activos == 1
    # El segundo pedido puede fallar por la regla (400) o porque su autor ya quedó inactivo (403).
    assert 200 in resultados


# --- Permisos ---


@pytest.mark.django_db
@pytest.mark.parametrize("fixture", ["operativo_client", "lector_client", "gerencia_client"])
def test_no_admin_endpoints_usuarios_responde_403(request, fixture):
    client = request.getfixturevalue(fixture)
    otro = get_user_model().objects.create_user(username="ale")
    assert client.get(URL).status_code == 403
    assert _alta(client, username="nuevo").status_code == 403
    assert _patch(client, f"{URL}{otro.pk}/", {"activo": False}).status_code == 403
    assert _post(client, f"{URL}{otro.pk}/link-clave/", {}).status_code == 403


@pytest.mark.django_db
def test_sin_sesion_endpoints_usuarios_responde_403():
    assert Client().get(URL).status_code == 403


@pytest.mark.django_db
def test_listar_usuarios_devuelve_rol_y_gerencia(admin_client):
    lector = get_user_model().objects.create_user(username="lector")
    lector.groups.add(Group.objects.get(name="Gerencia"))
    respuesta = admin_client.get(URL)
    assert respuesta.status_code == 200
    por_nombre = {u["username"]: u for u in respuesta.json()}
    assert por_nombre["admin"]["rol"] == "administrador"
    assert por_nombre["lector"]["rol"] == "lectura"
    assert por_nombre["lector"]["es_gerencia"] is True
    assert "password" not in por_nombre["lector"]


@pytest.mark.django_db
def test_editar_username_no_se_permite(admin_client):
    user = get_user_model().objects.create_user(username="ale")
    assert _patch(admin_client, f"{URL}{user.pk}/", {"username": "otro"}).status_code == 200
    user.refresh_from_db()
    assert user.username == "ale"


# --- Auditoría ---


@pytest.mark.django_db
def test_cambio_de_rol_queda_auditado_sin_clave(admin_client):
    usuario_id = _alta(admin_client, es_gerencia=False).json()["id"]
    assert _patch(admin_client, f"{URL}{usuario_id}/", {"rol": "lectura"}).status_code == 200
    uid, token = _link(admin_client, usuario_id)
    assert _definir(uid, token).status_code == 200

    registros = RegistroAuditoria.objects.filter(entidad="usuario", entidad_id=usuario_id)
    cambio_rol = registros.get(campo="rol", valor_anterior="operativo")
    assert cambio_rol.valor_nuevo == "lectura"
    assert cambio_rol.usuario is not None
    assert cambio_rol.usuario.username == "admin"
    assert registros.filter(campo="username", valor_nuevo="ale").exists()
    assert not registros.filter(campo__in=["password", "clave"]).exists()


@pytest.mark.django_db
def test_editar_datos_y_quitar_gerencia_queda_auditado(admin_client):
    usuario_id = _alta(admin_client).json()["id"]
    cambios = {"first_name": "Alejandra", "last_name": "Otra", "email": "a@ejemplo.test"}
    respuesta = _patch(admin_client, f"{URL}{usuario_id}/", {**cambios, "es_gerencia": False})
    assert respuesta.status_code == 200
    assert respuesta.json()["es_gerencia"] is False
    user = get_user_model().objects.get(pk=usuario_id)
    assert (user.first_name, user.last_name, user.email) == ("Alejandra", "Otra", "a@ejemplo.test")
    gerencia = RegistroAuditoria.objects.get(
        entidad="usuario", entidad_id=usuario_id, campo="gerencia", valor_anterior="sí"
    )
    assert gerencia.valor_nuevo == "no"


@pytest.mark.django_db
def test_definir_clave_uid_invalido_responde_400(db):
    respuesta = _definir("no-es-base64!", "token")
    assert respuesta.status_code == 400
    assert "token" in respuesta.json()
