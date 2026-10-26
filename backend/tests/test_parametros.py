"""Parámetros configurables del motor de disponibilidad (HU-001)."""

import json
from datetime import date
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client

from apps.auditoria.models import RegistroAuditoria
from apps.campanias.models import Campania
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import ParametrosDisponibilidad, Reserva

URL = "/api/reservas/parametros/"
URL_RESERVAS = "/api/reservas/reservas/"


def cartel(capacidad: int) -> Cartel:
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion="Av. San Martín 1234",
        tamano="6x3",
        capacidad=capacidad,
        tarifa_lista="100000.00",
    )


def reserva(car: Cartel, inicio: str, fin: str, estado: str = "confirmada") -> Reserva:
    r = Reserva(
        campania=Campania.objects.create(),
        cartel=car,
        fecha_inicio=date.fromisoformat(inicio),
        fecha_fin=date.fromisoformat(fin),
        estado=estado,
    )
    r.save()
    return r


def confirmar(client: Client, car: Cartel, inicio: str, fin: str) -> Any:
    """Crea una reserva pendiente y la confirma por la API; devuelve la respuesta del confirmar."""
    pendiente = reserva(car, inicio, fin, estado="pendiente")
    return client.patch(
        f"{URL_RESERVAS}{pendiente.pk}/",
        data=json.dumps({"estado": "confirmada"}),
        content_type="application/json",
    )


def _cliente(username: str, grupo: str | None = None, admin: bool = False) -> Client:
    User = get_user_model()
    if admin:
        user = User.objects.create_superuser(username=username, password="clave-segura-123")
    else:
        user = User.objects.create_user(username=username, password="clave-segura-123")
    if grupo is not None:
        user.groups.add(Group.objects.get(name=grupo))
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(db):
    return _cliente("admin", admin=True)


def _patch(client: Client, data: dict[str, object]) -> Any:
    return client.patch(URL, data=json.dumps(data), content_type="application/json")


@pytest.mark.django_db
def test_parametros_fila_inicial_tiene_los_valores_provisorios(admin_client):
    respuesta = admin_client.get(URL)
    assert respuesta.status_code == 200
    assert respuesta.json() == {"borde_inclusivo": True, "tentativa_bloquea": False}
    assert ParametrosDisponibilidad.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.regla("RN-001")
def test_parametros_cambio_de_borde_rige_en_la_siguiente_validacion(admin_client, operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-01", "2026-11-15")
    assert confirmar(operativo_client, car, "2026-11-15", "2026-11-30").status_code == 400

    assert _patch(admin_client, {"borde_inclusivo": False}).status_code == 200

    assert confirmar(operativo_client, car, "2026-11-15", "2026-11-30").status_code == 200


@pytest.mark.django_db
@pytest.mark.regla("RN-002")
def test_parametros_tentativa_bloquea_rige_en_la_siguiente_validacion(
    admin_client, operativo_client
):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-01", "2026-11-15", estado="pendiente")
    reserva(car, "2026-12-01", "2026-12-15", estado="pendiente")
    assert confirmar(operativo_client, car, "2026-11-01", "2026-11-15").status_code == 200

    assert _patch(admin_client, {"tentativa_bloquea": True}).status_code == 200

    assert confirmar(operativo_client, car, "2026-12-01", "2026-12-15").status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("username", "grupo"),
    [("operativo", "Operativo"), ("lector", "Lectura"), ("gerente", "Gerencia")],
)
def test_parametros_no_administrador_no_accede(username, grupo):
    client = _cliente(username, grupo)
    assert client.get(URL).status_code == 403
    assert _patch(client, {"borde_inclusivo": False}).status_code == 403
    assert ParametrosDisponibilidad.objects.get().borde_inclusivo is True


@pytest.mark.django_db
def test_parametros_sin_sesion_no_accede():
    assert Client().get(URL).status_code == 403


@pytest.mark.django_db
def test_parametros_cambio_queda_auditado_con_usuario(admin_client):
    assert _patch(admin_client, {"tentativa_bloquea": True}).status_code == 200
    registro = RegistroAuditoria.objects.get(entidad="parametros")
    assert registro.campo == "tentativa_bloquea"
    assert (registro.valor_anterior, registro.valor_nuevo) == ("False", "True")
    assert registro.usuario is not None
    assert registro.usuario.username == "admin"


@pytest.mark.django_db
def test_parametros_patch_sin_cambios_no_audita(admin_client):
    assert _patch(admin_client, {"borde_inclusivo": True}).status_code == 200
    assert not RegistroAuditoria.objects.filter(entidad="parametros").exists()


@pytest.mark.django_db
def test_parametros_valor_no_booleano_responde_400(admin_client):
    assert _patch(admin_client, {"borde_inclusivo": "quizas"}).status_code == 400


@pytest.mark.django_db
def test_parametros_post_y_delete_devuelven_405(admin_client):
    assert admin_client.post(URL, data="{}", content_type="application/json").status_code == 405
    assert admin_client.delete(URL).status_code == 405


@pytest.mark.django_db
def test_parametros_modelo_fuerza_una_sola_fila():
    otra = ParametrosDisponibilidad(borde_inclusivo=False)
    otra.save()
    assert ParametrosDisponibilidad.objects.count() == 1
    assert ParametrosDisponibilidad.objects.get().borde_inclusivo is False
    with pytest.raises(ValueError, match="no se borran"):
        otra.delete()
