"""No se carga a mano una reserva que ya terminó, salvo que Parámetros lo permita (RN-012)."""

import json
from datetime import date
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.campanias.models import Campania
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas import services
from apps.reservas.models import ParametrosDisponibilidad, Reserva

URL = "/api/reservas/reservas/"
HOY = date(2026, 6, 15)
MENSAJE = "La reserva termina antes de hoy: no se puede cargar con fecha pasada."


@pytest.fixture(autouse=True)
def hoy_fijo(monkeypatch):
    monkeypatch.setattr(services, "hoy", lambda: HOY)


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_superuser(username="adm", password="clave-segura-123")
    client = Client()
    client.force_login(user)
    return client


def _cartel() -> Cartel:
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion=f"Av. Pasada {Cartel.objects.count() + 1}",
        capacidad=1,
    )


def _post(client: Client, url: str, datos: dict[str, Any]) -> Any:
    return client.post(url, data=json.dumps(datos), content_type="application/json")


def _patch(client: Client, url: str, datos: dict[str, Any]) -> Any:
    return client.patch(url, data=json.dumps(datos), content_type="application/json")


def _alta(client: Client, inicio: str, fin: str) -> Any:
    datos = {
        "campania": Campania.objects.create().pk,
        "cartel": _cartel().pk,
        "fecha_inicio": inicio,
        "fecha_fin": fin,
    }
    return _post(client, URL, datos)


def _reserva(inicio: str, fin: str) -> Reserva:
    reserva = Reserva(
        campania=Campania.objects.create(),
        cartel=_cartel(),
        fecha_inicio=date.fromisoformat(inicio),
        fecha_fin=date.fromisoformat(fin),
    )
    reserva.save()
    return reserva


def _permitir() -> None:
    parametros = services.parametros_disponibilidad()
    parametros.permitir_fecha_pasada = True
    parametros.save()


@pytest.mark.django_db
@pytest.mark.regla("RN-012")
def test_alta_de_reserva_que_termina_antes_de_hoy_se_rechaza(operativo_client):
    response = _alta(operativo_client, "2026-06-01", "2026-06-14")

    assert response.status_code == 400
    assert response.json()["fecha_fin"] == [MENSAJE]
    assert not Reserva.objects.exists()


@pytest.mark.django_db
@pytest.mark.regla("RN-012")
@pytest.mark.parametrize(
    ("inicio", "fin"), [("2026-06-01", "2026-06-15"), ("2026-06-10", "2026-07-10")]
)
def test_alta_de_reserva_que_termina_hoy_o_despues_se_acepta_aunque_empiece_antes(
    operativo_client, inicio, fin
):
    assert _alta(operativo_client, inicio, fin).status_code == 201


@pytest.mark.django_db
@pytest.mark.regla("RN-012")
def test_edicion_que_lleva_el_fin_a_antes_de_hoy_se_rechaza(operativo_client):
    reserva = _reserva("2026-06-01", "2026-06-30")

    response = _patch(operativo_client, f"{URL}{reserva.pk}/", {"fecha_fin": "2026-06-10"})

    assert response.status_code == 400
    assert response.json()["fecha_fin"] == [MENSAJE]
    reserva.refresh_from_db()
    assert reserva.fecha_fin == date(2026, 6, 30)


@pytest.mark.django_db
@pytest.mark.regla("RN-012")
def test_edicion_de_otro_campo_de_reserva_terminada_se_acepta(operativo_client):
    reserva = _reserva("2026-05-01", "2026-05-31")

    response = _patch(operativo_client, f"{URL}{reserva.pk}/", {"precio_alquiler": "5000.00"})

    assert response.status_code == 200
    reserva.refresh_from_db()
    assert str(reserva.precio_alquiler) == "5000.00"


@pytest.mark.django_db
@pytest.mark.regla("RN-012")
def test_creacion_en_bloque_que_termina_antes_de_hoy_se_rechaza_entera(operativo_client):
    datos = {
        "campania": Campania.objects.create().pk,
        "carteles": [_cartel().pk, _cartel().pk],
        "fecha_inicio": "2026-06-01",
        "fecha_fin": "2026-06-14",
    }

    response = _post(operativo_client, f"{URL}en-bloque/", datos)

    assert response.status_code == 400
    assert response.json()["fecha_fin"] == [MENSAJE]
    assert not Reserva.objects.exists()


def _mover(client: Client) -> tuple[Any, Reserva]:
    campania = Campania.objects.create(fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 10))
    reserva = Reserva(
        campania=campania,
        cartel=_cartel(),
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 20),
    )
    reserva.save()
    datos = {
        "campania": campania.pk,
        "fecha_inicio_anterior": "2026-06-01",
        "fecha_fin_anterior": "2026-06-20",
    }
    return _post(client, f"{URL}mover-pendientes/", datos), reserva


@pytest.mark.django_db
@pytest.mark.regla("RN-012")
def test_mover_pendientes_a_una_campania_terminada_antes_de_hoy_se_rechaza(operativo_client):
    response, reserva = _mover(operativo_client)

    assert response.status_code == 400
    assert response.json()["fecha_fin"] == [MENSAJE]
    reserva.refresh_from_db()
    assert reserva.fecha_fin == date(2026, 6, 20)


@pytest.mark.django_db
@pytest.mark.regla("RN-012")
def test_con_el_parametro_prendido_se_permite_la_fecha_pasada(operativo_client):
    _permitir()
    reserva = _reserva("2026-06-01", "2026-06-30")

    assert _alta(operativo_client, "2026-06-01", "2026-06-14").status_code == 201
    response = _patch(operativo_client, f"{URL}{reserva.pk}/", {"fecha_fin": "2026-06-10"})
    assert response.status_code == 200
    datos = {
        "campania": Campania.objects.create().pk,
        "carteles": [_cartel().pk],
        "fecha_inicio": "2026-06-01",
        "fecha_fin": "2026-06-14",
    }
    assert _post(operativo_client, f"{URL}en-bloque/", datos).status_code == 200
    response, movida = _mover(operativo_client)
    assert response.status_code == 200
    movida.refresh_from_db()
    assert movida.fecha_fin == date(2026, 6, 10)


@pytest.mark.django_db
@pytest.mark.regla("RN-012")
def test_parametros_exponen_y_cambian_permitir_fecha_pasada(admin_client):
    url = "/api/reservas/parametros/"
    assert admin_client.get(url).json()["permitir_fecha_pasada"] is False

    response = _patch(admin_client, url, {"permitir_fecha_pasada": True})

    assert response.status_code == 200
    assert ParametrosDisponibilidad.objects.get().permitir_fecha_pasada is True
