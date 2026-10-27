"""Mover las Pendientes cuando cambian las fechas de la campaña (HU-058, criterios 3 y 4)."""

import json
from datetime import date
from typing import Any

import pytest
from django.test import Client

from apps.auditoria.models import RegistroAuditoria
from apps.campanias.models import Campania
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva

URL = "/api/reservas/reservas/mover-pendientes/"


def _cartel() -> Cartel:
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion=f"Av. Mover {Cartel.objects.count() + 1}",
        capacidad=1,
    )


def _campania_movida() -> Campania:
    """Campaña que ya pasó de noviembre a diciembre."""
    return Campania.objects.create(
        nombre="Verano", fecha_inicio=date(2026, 12, 1), fecha_fin=date(2026, 12, 31)
    )


def _reserva(
    campania: Campania,
    estado: str = "pendiente",
    inicio: str = "2026-11-01",
    fin: str = "2026-11-30",
) -> Reserva:
    reserva = Reserva(
        campania=campania,
        cartel=_cartel(),
        fecha_inicio=date.fromisoformat(inicio),
        fecha_fin=date.fromisoformat(fin),
        estado=estado,
    )
    reserva.save()
    return reserva


def _mover(client: Client, destino: Campania, **extra: Any) -> Any:
    datos = {
        "campania": destino.pk,
        "fecha_inicio_anterior": "2026-11-01",
        "fecha_fin_anterior": "2026-11-30",
        **extra,
    }
    return client.post(URL, data=json.dumps(datos), content_type="application/json")


@pytest.mark.django_db
def test_mueve_solo_las_pendientes_con_las_fechas_anteriores(operativo_client):
    campania = _campania_movida()
    pendiente = _reserva(campania)
    otra_tanda = _reserva(campania, inicio="2026-11-15", fin="2026-11-30")
    ajena = _reserva(Campania.objects.create())

    respuesta = _mover(operativo_client, campania)
    assert respuesta.status_code == 200
    assert respuesta.json() == {"movidas": [pendiente.pk]}

    pendiente.refresh_from_db()
    assert (pendiente.fecha_inicio, pendiente.fecha_fin) == (date(2026, 12, 1), date(2026, 12, 31))
    assert pendiente.nombre.endswith("Dic 2026")
    otra_tanda.refresh_from_db()
    ajena.refresh_from_db()
    assert otra_tanda.fecha_inicio == date(2026, 11, 15)
    assert ajena.fecha_inicio == date(2026, 11, 1)


@pytest.mark.django_db
@pytest.mark.parametrize("estado", ["confirmada", "finalizada", "cancelada"])
def test_no_toca_las_reservas_que_no_estan_pendientes(operativo_client, estado):
    campania = _campania_movida()
    reserva = _reserva(campania, estado=estado)
    assert _mover(operativo_client, campania).json() == {"movidas": []}
    reserva.refresh_from_db()
    assert reserva.fecha_inicio == date(2026, 11, 1)


@pytest.mark.django_db
def test_repetir_no_mueve_nada_mas(operativo_client):
    campania = _campania_movida()
    _reserva(campania)
    assert len(_mover(operativo_client, campania).json()["movidas"]) == 1
    assert _mover(operativo_client, campania).json() == {"movidas": []}


@pytest.mark.django_db
def test_el_movimiento_queda_auditado(operativo_client):
    campania = _campania_movida()
    reserva = _reserva(campania)
    _mover(operativo_client, campania)
    campos = set(
        RegistroAuditoria.objects.filter(entidad="reserva", entidad_id=reserva.pk).values_list(
            "campo", flat=True
        )
    )
    assert campos == {"fecha_inicio", "fecha_fin"}


@pytest.mark.django_db
def test_campania_sin_fechas_se_rechaza(operativo_client):
    campania = Campania.objects.create()
    _reserva(campania)
    respuesta = _mover(operativo_client, campania)
    assert respuesta.status_code == 400
    assert respuesta.json()["campania"] == ["La campaña no tiene fechas."]


@pytest.mark.django_db
def test_pedido_invalido_se_rechaza(operativo_client):
    campania = _campania_movida()
    casos: list[tuple[dict[str, Any], str]] = [
        ({"fecha_inicio_anterior": None}, "fecha_inicio_anterior"),
        ({"fecha_fin_anterior": "30/11/2026"}, "fecha_fin_anterior"),
        ({"campania": 999999}, "campania"),
    ]
    for extra, campo in casos:
        respuesta = _mover(operativo_client, campania, **extra)
        assert respuesta.status_code == 400, extra
        assert campo in respuesta.json(), extra


@pytest.mark.django_db
def test_lector_no_puede_mover(lector_client):
    campania = _campania_movida()
    reserva = _reserva(campania)
    assert _mover(lector_client, campania).status_code == 403
    reserva.refresh_from_db()
    assert reserva.fecha_inicio == date(2026, 11, 1)
