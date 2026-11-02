"""Confirmar en bloque las reservas Pendientes de una campaña (HU-059)."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, Group
from django.db import connection
from django.test import Client

from apps.auditoria.models import RegistroAuditoria
from apps.campanias.models import Campania
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import ParametrosDisponibilidad, Reserva

URL = "/api/reservas/reservas/confirmar-en-bloque/"


def _cartel(capacidad: int = 1) -> Cartel:
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion=f"Av. Bloque {Cartel.objects.count() + 1}",
        tamano="6x3",
        capacidad=capacidad,
    )


def _campania(nombre: str = "Verano", estado: str = "confirmada") -> Campania:
    return Campania.objects.create(nombre=nombre, estado=estado)


def _reserva(
    campania: Campania,
    cartel: Cartel,
    estado: str = "pendiente",
    inicio: str = "2026-11-01",
    fin: str = "2026-11-30",
) -> Reserva:
    reserva = Reserva(
        campania=campania,
        cartel=cartel,
        fecha_inicio=date.fromisoformat(inicio),
        fecha_fin=date.fromisoformat(fin),
        estado=estado,
    )
    reserva.save()
    return reserva


def _confirmar(client: Client, campania: Campania) -> Any:
    return client.post(
        URL, data=json.dumps({"campania": campania.pk}), content_type="application/json"
    )


# --- Criterio 3: 190 sin conflicto y 10 con conflicto ---


@pytest.mark.django_db
def test_confirma_las_libres_y_lista_cada_conflicto(operativo_client):
    campania = _campania()
    ocupante = _campania("Invierno")
    libres = [_reserva(campania, _cartel()) for _ in range(190)]
    en_conflicto = []
    for _ in range(10):
        cartel = _cartel()
        _reserva(ocupante, cartel, estado="confirmada")
        en_conflicto.append(_reserva(campania, cartel))

    respuesta = _confirmar(operativo_client, campania)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert sorted(cuerpo["confirmadas"]) == sorted(r.pk for r in libres)
    assert Reserva.objects.filter(campania=campania, estado="confirmada").count() == 190
    assert Reserva.objects.filter(campania=campania, estado="pendiente").count() == 10

    primero = en_conflicto[0]
    conflicto = next(c for c in cuerpo["conflictos"] if c["reserva"] == primero.pk)
    assert conflicto == {
        "reserva": primero.pk,
        "nombre": primero.nombre,
        "cartel_nombre": primero.cartel.nombre_visible,
        "fecha_inicio": "2026-11-01",
        "fecha_fin": "2026-11-30",
        "ocupada_por": [{"campania": ocupante.pk, "campania_nombre": "Invierno"}],
    }
    assert len(cuerpo["conflictos"]) == 10


@pytest.mark.django_db
@pytest.mark.regla("RN-003")
def test_usa_pico_diario_y_las_propias_compiten_entre_si(operativo_client):
    campania = _campania()
    led = _cartel(capacidad=2)
    _reserva(_campania("Otra"), led, estado="confirmada", inicio="2026-11-01", fin="2026-11-10")
    primera = _reserva(campania, led)
    segunda = _reserva(campania, led)
    cuerpo = _confirmar(operativo_client, campania).json()
    # Con capacidad 2 y una confirmada en parte del rango, entra solo una de las dos propias.
    assert cuerpo["confirmadas"] == [primera.pk]
    assert [c["reserva"] for c in cuerpo["conflictos"]] == [segunda.pk]
    nombres = {o["campania_nombre"] for o in cuerpo["conflictos"][0]["ocupada_por"]}
    assert nombres == {"Otra", "Verano"}


@pytest.mark.django_db
@pytest.mark.regla("RN-002")
def test_pendientes_de_otra_campania_bloquean_solo_con_el_parametro(operativo_client):
    cartel = _cartel()
    _reserva(_campania("Otra", estado="cotizada"), cartel)
    campania = _campania()
    propia = _reserva(campania, cartel)
    ParametrosDisponibilidad.objects.filter(pk=1).update(tentativa_bloquea=True)
    assert _confirmar(operativo_client, campania).json()["confirmadas"] == []

    ParametrosDisponibilidad.objects.filter(pk=1).update(tentativa_bloquea=False)
    assert _confirmar(operativo_client, campania).json()["confirmadas"] == [propia.pk]


# --- Criterio 5: repetir procesa solo lo que sigue Pendiente ---


@pytest.mark.django_db
def test_repetir_procesa_solo_las_que_siguen_pendientes(operativo_client):
    campania = _campania()
    libre = _reserva(campania, _cartel())
    cartel = _cartel()
    ocupante = _reserva(_campania("Otra"), cartel, estado="confirmada")
    bloqueada = _reserva(campania, cartel)
    assert _confirmar(operativo_client, campania).json()["confirmadas"] == [libre.pk]

    ocupante.estado = Reserva.Estado.CANCELADA
    ocupante.save()
    cuerpo = _confirmar(operativo_client, campania).json()
    assert cuerpo == {"confirmadas": [bloqueada.pk], "conflictos": []}
    assert _confirmar(operativo_client, campania).json() == {"confirmadas": [], "conflictos": []}


@pytest.mark.django_db
def test_no_toca_otras_campanias_ni_otros_estados(operativo_client):
    campania = _campania()
    cancelada = _reserva(campania, _cartel(), estado="cancelada")
    ajena = _reserva(_campania("Otra"), _cartel())
    assert _confirmar(operativo_client, campania).json()["confirmadas"] == []
    cancelada.refresh_from_db()
    ajena.refresh_from_db()
    assert (cancelada.estado, ajena.estado) == ("cancelada", "pendiente")


# --- Auditoría, precondiciones y permisos ---


@pytest.mark.django_db
def test_el_cambio_de_estado_queda_auditado_con_el_usuario(operativo_client):
    campania = _campania()
    reserva = _reserva(campania, _cartel())
    _confirmar(operativo_client, campania)
    registro = RegistroAuditoria.objects.get(entidad="reserva", entidad_id=reserva.pk)
    assert (registro.campo, registro.valor_anterior, registro.valor_nuevo) == (
        "estado",
        "pendiente",
        "confirmada",
    )
    assert registro.usuario is not None
    assert registro.usuario.username == "operativo"


@pytest.mark.django_db
@pytest.mark.parametrize("estado", ["cotizada", "cancelada", "perdida"])
def test_campania_no_confirmada_se_rechaza(operativo_client, estado):
    campania = _campania(estado=estado)
    reserva = _reserva(campania, _cartel())
    respuesta = _confirmar(operativo_client, campania)
    assert respuesta.status_code == 400
    assert respuesta.json()["campania"] == ["Primero confirmá la campaña."]
    reserva.refresh_from_db()
    assert reserva.estado == "pendiente"


@pytest.mark.django_db
def test_pedido_sin_campania_valida_se_rechaza(operativo_client):
    for datos in ({}, {"campania": 999999}):
        respuesta = operativo_client.post(
            URL, data=json.dumps(datos), content_type="application/json"
        )
        assert respuesta.status_code == 400
        assert "campania" in respuesta.json()


@pytest.mark.django_db
def test_lector_no_puede_confirmar_en_bloque(lector_client):
    campania = _campania()
    _reserva(campania, _cartel())
    assert _confirmar(lector_client, campania).status_code == 403
    assert Reserva.objects.get().estado == "pendiente"


# --- Criterio 4: dos campañas confirman a la vez el último cupo ---


def _operativo() -> AbstractBaseUser:
    user = get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    user.groups.add(Group.objects.get(name="Operativo"))
    return user


def _confirmar_en_hilo(user_pk: int, campania_pk: int) -> Any:
    """Confirma en bloque desde su propio hilo y conexión; devuelve el cuerpo de la respuesta."""
    try:
        client = Client()
        client.force_login(get_user_model().objects.get(pk=user_pk))
        respuesta = client.post(
            URL, data=json.dumps({"campania": campania_pk}), content_type="application/json"
        )
        return respuesta.json()
    finally:
        connection.close()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
@pytest.mark.regla("RN-003")
def test_dos_campanias_confirman_a_la_vez_el_ultimo_cupo():
    cartel = _cartel()
    user = _operativo()
    campanias = [_campania("A"), _campania("B")]
    for campania in campanias:
        _reserva(campania, cartel)
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(lambda c: _confirmar_en_hilo(user.pk, c.pk), campanias))
    assert sorted(len(r["confirmadas"]) for r in resultados) == [0, 1]
    assert sorted(len(r["conflictos"]) for r in resultados) == [0, 1]
    assert Reserva.objects.filter(cartel=cartel, estado="confirmada").count() == 1
    assert Reserva.objects.filter(cartel=cartel, estado="pendiente").count() == 1
