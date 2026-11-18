"""La campaña nace Confirmada y el estado de sus reservas lo lleva el sistema (HU-024, HU-035)."""

import importlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Any

import pytest
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.test import Client

from apps.auditoria.models import RegistroAuditoria
from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva

# El conftest fija "hoy" en 2026-01-01.
HOY = date(2026, 1, 1)


def _marca() -> Marca:
    cliente = Cliente.objects.create(nombre=f"Cliente {Cliente.objects.count() + 1}")
    return Marca.objects.create(nombre=f"Marca {Marca.objects.count() + 1}", cliente=cliente)


def _campania(estado: str = "confirmada") -> Campania:
    return Campania.objects.create(
        nombre="Verano",
        marca=_marca(),
        fecha_inicio=date(2026, 2, 1),
        fecha_fin=date(2026, 2, 28),
        estado=estado,
    )


def _cartel(capacidad: int = 1) -> Cartel:
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion=f"Av. Siempre {Cartel.objects.count() + 1}",
        tamano="6x3",
        capacidad=capacidad,
    )


def _reserva(campania: Campania, cartel: Cartel, inicio: str, fin: str, **extra: Any) -> Reserva:
    reserva = Reserva(
        campania=campania,
        cartel=cartel,
        fecha_inicio=date.fromisoformat(inicio),
        fecha_fin=date.fromisoformat(fin),
        **extra,
    )
    reserva.save()
    return reserva


def _post(client: Client, url: str, datos: dict[str, Any]) -> Any:
    return client.post(url, data=json.dumps(datos), content_type="application/json")


def _patch(client: Client, url: str, datos: dict[str, Any]) -> Any:
    return client.patch(url, data=json.dumps(datos), content_type="application/json")


# --- Campaña ---


@pytest.mark.django_db
@pytest.mark.regla("RN-011")
def test_campania_nace_confirmada(operativo_client):
    marca = _marca()
    respuesta = _post(
        operativo_client,
        "/api/campanias/campanias/",
        {"marca": marca.pk, "fecha_inicio": "2026-02-01", "fecha_fin": "2026-02-28"},
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "confirmada"


@pytest.mark.django_db
@pytest.mark.regla("RN-011")
def test_crear_campania_sin_marca_cliente_o_fechas_rechaza(operativo_client):
    respuesta = _post(operativo_client, "/api/campanias/campanias/", {"nombre": "Incompleta"})
    assert respuesta.status_code == 400
    errores = respuesta.json()
    assert {"marca", "cliente_facturacion", "fecha_inicio", "fecha_fin"} <= set(errores)
    assert Campania.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.regla("RN-011")
def test_editar_campania_sin_marca_rechaza(operativo_client):
    campania = _campania()
    respuesta = _patch(
        operativo_client, f"/api/campanias/campanias/{campania.pk}/", {"marca": None}
    )
    assert respuesta.status_code == 400
    assert "marca" in respuesta.json()


@pytest.mark.django_db
def test_editar_estado_de_campania_por_patch_se_ignora(operativo_client):
    campania = _campania()
    respuesta = _patch(
        operativo_client, f"/api/campanias/campanias/{campania.pk}/", {"estado": "cancelada"}
    )
    assert respuesta.status_code == 200
    campania.refresh_from_db()
    assert campania.estado == "confirmada"


@pytest.mark.django_db
@pytest.mark.regla("RN-006")
def test_cancelar_campania_cancela_futuras_termina_en_curso_y_no_toca_terminadas(
    operativo_client,
):
    campania = _campania()
    futura = _reserva(campania, _cartel(), "2026-02-01", "2026-02-28")
    en_curso = _reserva(campania, _cartel(), "2025-12-15", "2026-01-20")
    terminada = _reserva(campania, _cartel(), "2025-11-01", "2025-11-30")

    respuesta = _post(
        operativo_client,
        "/api/reservas/reservas/cancelar-campania/",
        {"campania": campania.pk},
    )

    assert respuesta.status_code == 200
    campania.refresh_from_db()
    futura.refresh_from_db()
    en_curso.refresh_from_db()
    terminada.refresh_from_db()
    assert campania.estado == "cancelada"
    assert futura.estado == "cancelada"
    assert (en_curso.estado, en_curso.fecha_fin) == ("confirmada", HOY)
    assert (terminada.estado, terminada.fecha_fin) == ("confirmada", date(2025, 11, 30))
    assert RegistroAuditoria.objects.filter(entidad="campania", entidad_id=campania.pk).exists()
    assert RegistroAuditoria.objects.filter(entidad="reserva", entidad_id=futura.pk).exists()


@pytest.mark.django_db
def test_cancelar_campania_cancelada_rechaza(operativo_client):
    campania = _campania(estado="cancelada")
    respuesta = _post(
        operativo_client,
        "/api/reservas/reservas/cancelar-campania/",
        {"campania": campania.pk},
    )
    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_cancelar_campania_lector_no_puede(lector_client):
    campania = _campania()
    respuesta = _post(
        lector_client, "/api/reservas/reservas/cancelar-campania/", {"campania": campania.pk}
    )
    assert respuesta.status_code == 403
    campania.refresh_from_db()
    assert campania.estado == "confirmada"


# --- Quitar una reserva ---


def _quitar(client: Client, reserva: Reserva) -> Any:
    return _post(client, f"/api/reservas/reservas/{reserva.pk}/quitar/", {})


@pytest.mark.django_db
@pytest.mark.regla("RN-006")
def test_quitar_reserva_futura_la_cancela(operativo_client):
    reserva = _reserva(_campania(), _cartel(), "2026-02-01", "2026-02-28")
    respuesta = _quitar(operativo_client, reserva)
    assert respuesta.status_code == 200
    reserva.refresh_from_db()
    assert reserva.estado == "cancelada"


@pytest.mark.django_db
@pytest.mark.regla("RN-006")
def test_quitar_reserva_en_curso_la_termina_hoy(operativo_client):
    reserva = _reserva(_campania(), _cartel(), "2025-12-15", "2026-01-20")
    respuesta = _quitar(operativo_client, reserva)
    assert respuesta.status_code == 200
    reserva.refresh_from_db()
    assert (reserva.estado, reserva.fecha_fin) == ("confirmada", HOY)
    assert RegistroAuditoria.objects.filter(entidad="reserva", entidad_id=reserva.pk).exists()


@pytest.mark.django_db
def test_quitar_reserva_terminada_o_cancelada_rechaza(operativo_client):
    campania = _campania()
    terminada = _reserva(campania, _cartel(), "2025-11-01", "2025-11-30")
    cancelada = _reserva(campania, _cartel(), "2026-02-01", "2026-02-28", estado="cancelada")
    assert _quitar(operativo_client, terminada).status_code == 400
    assert _quitar(operativo_client, cancelada).status_code == 400


# --- Las reservas nacen Confirmadas ---


@pytest.mark.django_db
def test_alta_individual_nace_confirmada_y_valida_cupo(operativo_client):
    campania = _campania()
    cartel = _cartel()
    datos = {
        "campania": campania.pk,
        "cartel": cartel.pk,
        "fecha_inicio": "2026-02-01",
        "fecha_fin": "2026-02-28",
    }
    primera = _post(operativo_client, "/api/reservas/reservas/", datos)
    assert primera.status_code == 201
    assert primera.json()["estado"] == "confirmada"

    segunda = _post(
        operativo_client, "/api/reservas/reservas/", {**datos, "campania": _campania().pk}
    )
    assert segunda.status_code == 400
    assert "disponibilidad" in segunda.json()


@pytest.mark.django_db
def test_estado_de_reserva_no_se_edita(operativo_client):
    reserva = _reserva(_campania(), _cartel(), "2026-02-01", "2026-02-28")
    respuesta = _patch(
        operativo_client, f"/api/reservas/reservas/{reserva.pk}/", {"estado": "cancelada"}
    )
    assert respuesta.status_code == 200
    reserva.refresh_from_db()
    assert reserva.estado == "confirmada"


def _tanda(client: Client, campania: Campania, carteles: list[int]) -> Any:
    return _post(
        client,
        "/api/reservas/reservas/en-bloque/",
        {
            "campania": campania.pk,
            "fecha_inicio": "2026-02-01",
            "fecha_fin": "2026-02-28",
            "carteles": carteles,
        },
    )


@pytest.mark.django_db
def test_tanda_nace_confirmada_y_sin_cupo_va_a_fallidas(operativo_client):
    campania = _campania()
    libre = _cartel()
    lleno = _cartel()
    ocupante = _campania()
    _reserva(ocupante, lleno, "2026-02-10", "2026-02-20")

    respuesta = _tanda(operativo_client, campania, [libre.pk, lleno.pk])

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert [item["cartel"] for item in cuerpo["creadas"]] == [libre.pk]
    assert Reserva.objects.get(campania=campania, cartel=libre).estado == "confirmada"
    [fallida] = cuerpo["fallidas"]
    assert fallida["cartel"] == lleno.pk
    assert "sin cupo" in fallida["motivo"]
    assert not Reserva.objects.filter(campania=campania, cartel=lleno).exists()


@pytest.mark.django_db
def test_campania_cancelada_no_admite_reservas(operativo_client):
    campania = _campania(estado="cancelada")
    cartel = _cartel()
    individual = _post(
        operativo_client,
        "/api/reservas/reservas/",
        {
            "campania": campania.pk,
            "cartel": cartel.pk,
            "fecha_inicio": "2026-02-01",
            "fecha_fin": "2026-02-28",
        },
    )
    assert individual.status_code == 400
    assert "campania" in individual.json()
    tanda = _tanda(operativo_client, campania, [cartel.pk])
    assert tanda.status_code == 400
    assert not Reserva.objects.filter(campania=campania).exists()


@pytest.mark.django_db
def test_estado_visible_finalizada_por_fecha(operativo_client):
    campania = _campania()
    terminada = _reserva(campania, _cartel(), "2025-11-01", "2025-11-30")
    vigente = _reserva(campania, _cartel(), "2026-02-01", "2026-02-28")
    filas = operativo_client.get(f"/api/reservas/reservas/?campania={campania.pk}").json()
    visibles = {fila["id"]: fila["estado_visible"] for fila in filas}
    assert visibles == {terminada.pk: "finalizada", vigente.pk: "confirmada"}


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_tanda_dos_pedidos_al_ultimo_cupo_uno_falla():
    cartel = _cartel()
    campanias = [_campania(), _campania()]
    usuario = get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    usuario.groups.add(Group.objects.get(name="Operativo"))

    def pedir(campania: Campania) -> Any:
        client = Client()
        client.force_login(usuario)
        try:
            return _tanda(client, campania, [cartel.pk]).json()
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(pedir, campanias))

    creadas = sum(len(r["creadas"]) for r in resultados)
    fallidas = sum(len(r["fallidas"]) for r in resultados)
    assert (creadas, fallidas) == (1, 1)
    assert Reserva.objects.filter(cartel=cartel, estado="confirmada").count() == 1


# --- Migración de datos ---


@pytest.mark.django_db
def test_migracion_pasa_cotizadas_perdidas_y_pendientes_a_canceladas():
    cotizada = Campania.objects.create(nombre="Cotizada", estado="cotizada")
    perdida = Campania.objects.create(nombre="Perdida", estado="perdida")
    confirmada = _campania()
    pendiente = _reserva(confirmada, _cartel(), "2026-02-01", "2026-02-28", estado="pendiente")
    vigente = _reserva(confirmada, _cartel(), "2026-02-01", "2026-02-28")

    campanias = importlib.import_module(
        "apps.campanias.migrations.0008_campania_siempre_confirmada_datos"
    )
    reservas = importlib.import_module("apps.reservas.migrations.0006_reserva_sin_pendientes_datos")
    campanias.cotizadas_y_perdidas_a_canceladas(django_apps, None)
    reservas.pendientes_a_canceladas(django_apps, None)

    estados = dict(Campania.objects.values_list("pk", "estado"))
    assert estados[cotizada.pk] == estados[perdida.pk] == "cancelada"
    assert estados[confirmada.pk] == "confirmada"
    pendiente.refresh_from_db()
    vigente.refresh_from_db()
    assert (pendiente.estado, vigente.estado) == ("cancelada", "confirmada")
