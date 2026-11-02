"""Creación de reservas en bloque desde la campaña (HU-057)."""

import json
import time
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.test import Client

from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import ParametrosDisponibilidad, Reserva

URL = "/api/reservas/reservas/en-bloque/"


@pytest.fixture
def formato() -> Formato:
    return Formato.objects.create(nombre="Gran Formato Prueba", modalidad="fija")


def _cartel(
    formato: Formato, direccion: str, tarifa: str | None = "1500.00", estado: str = "activo"
) -> Cartel:
    return Cartel.objects.create(
        formato=formato,
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo=estado),
        direccion=direccion,
        tamano="8x3",
        capacidad=1,
        tarifa_lista=Decimal(tarifa) if tarifa is not None else None,
    )


def _post(client: Client, destino: Campania, carteles: list[int], **extra: Any) -> Any:
    datos = {
        "campania": destino.pk,
        "fecha_inicio": "2026-11-01",
        "fecha_fin": "2026-11-30",
        "carteles": carteles,
        **extra,
    }
    return client.post(URL, data=json.dumps(datos), content_type="application/json")


def _campania_con_marca() -> Campania:
    cliente = Cliente.objects.create(nombre="Cliente Prueba")
    marca = Marca.objects.create(nombre="Marca Prueba", cliente=cliente)
    return Campania.objects.create(nombre="Verano", marca=marca)


# --- Criterio 2: Pendiente con tarifa de lista y nombre ---


@pytest.mark.django_db
def test_crea_pendientes_con_tarifa_de_lista_y_nombre(operativo_client, formato):
    campania = _campania_con_marca()
    uno = _cartel(formato, "Av. Uno 100")
    sin_tarifa = _cartel(formato, "Av. Dos 200", tarifa=None)

    respuesta = _post(operativo_client, campania, [uno.pk, sin_tarifa.pk])
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert [item["cartel"] for item in cuerpo["creadas"]] == [uno.pk, sin_tarifa.pk]
    assert cuerpo["existentes"] == []
    assert cuerpo["fallidas"] == []

    reserva = Reserva.objects.get(cartel=uno)
    assert reserva.estado == Reserva.Estado.PENDIENTE
    assert reserva.campania_id == campania.pk
    assert (reserva.fecha_inicio, reserva.fecha_fin) == (date(2026, 11, 1), date(2026, 11, 30))
    assert reserva.precio_alquiler == Decimal("1500.00")
    assert reserva.total == Decimal("1500.00")
    assert reserva.nombre == "Marca Prueba - Av. Uno 100 · 8x3 - Nov 2026"
    assert cuerpo["creadas"][0]["reserva"] == reserva.pk
    assert Reserva.objects.get(cartel=sin_tarifa).precio_alquiler == Decimal("0.00")


@pytest.mark.django_db
def test_campania_sin_marca_genera_nombre_sin_marca(operativo_client, formato):
    cartel = _cartel(formato, "Av. Uno 100")
    assert _post(operativo_client, Campania.objects.create(), [cartel.pk]).status_code == 200
    assert Reserva.objects.get().nombre.startswith("Sin marca - ")


# --- Criterio 1: 200 posiciones en menos de un minuto ---


@pytest.mark.django_db
def test_tanda_de_200_se_crea_en_menos_de_un_minuto(operativo_client, formato):
    campania = Campania.objects.create()
    carteles = [_cartel(formato, f"Av. Tanda {numero}").pk for numero in range(200)]
    inicio = time.monotonic()
    for desde in range(0, 200, 50):
        respuesta = _post(operativo_client, campania, carteles[desde : desde + 50])
        assert respuesta.status_code == 200
        assert len(respuesta.json()["creadas"]) == 50
    assert time.monotonic() - inicio < 60
    assert Reserva.objects.filter(campania=campania).count() == 200


# --- Criterio 3: fallidas con motivo ---


@pytest.mark.django_db
def test_fallidas_informan_el_motivo_y_no_frenan_al_resto(operativo_client, formato):
    campania = Campania.objects.create()
    bueno = _cartel(formato, "Av. Buena 1")
    baja = _cartel(formato, "Av. Baja 2", estado="baja")

    cuerpo = _post(operativo_client, campania, [baja.pk, 999999, bueno.pk]).json()
    assert [item["cartel"] for item in cuerpo["creadas"]] == [bueno.pk]
    assert cuerpo["fallidas"] == [
        {"cartel": baja.pk, "motivo": "El cartel está de baja: no se puede reservar."},
        {"cartel": 999999, "motivo": "No existe el cartel."},
    ]
    assert Reserva.objects.count() == 1


# --- Criterios 4 y 5: idempotencia ---


@pytest.mark.django_db
def test_reintentar_no_duplica_lo_ya_creado(operativo_client, formato):
    campania = Campania.objects.create()
    primero = _cartel(formato, "Av. Uno 1")
    segundo = _cartel(formato, "Av. Dos 2")
    creada = _post(operativo_client, campania, [primero.pk]).json()["creadas"][0]

    cuerpo = _post(operativo_client, campania, [primero.pk, segundo.pk, segundo.pk]).json()
    assert cuerpo["existentes"] == [{"cartel": primero.pk, "reserva": creada["reserva"]}]
    assert [item["cartel"] for item in cuerpo["creadas"]] == [segundo.pk]
    assert Reserva.objects.filter(campania=campania).count() == 2


@pytest.mark.django_db
def test_una_cancelada_no_cuenta_como_existente(operativo_client, formato):
    campania = Campania.objects.create()
    cartel = _cartel(formato, "Av. Uno 1")
    reserva = Reserva(
        campania=campania,
        cartel=cartel,
        fecha_inicio=date(2026, 11, 1),
        fecha_fin=date(2026, 11, 30),
        estado=Reserva.Estado.CANCELADA,
    )
    reserva.save()
    cuerpo = _post(operativo_client, campania, [cartel.pk]).json()
    assert len(cuerpo["creadas"]) == 1


@pytest.mark.django_db
def test_otras_fechas_u_otra_campania_no_cuentan_como_existente(operativo_client, formato):
    campania = Campania.objects.create()
    cartel = _cartel(formato, "Av. Uno 1")
    assert len(_post(operativo_client, campania, [cartel.pk]).json()["creadas"]) == 1
    otras_fechas = _post(
        operativo_client, campania, [cartel.pk], fecha_inicio="2026-12-01", fecha_fin="2026-12-31"
    )
    assert len(otras_fechas.json()["creadas"]) == 1
    otra = _post(operativo_client, Campania.objects.create(), [cartel.pk])
    assert len(otra.json()["creadas"]) == 1


@pytest.mark.django_db
@pytest.mark.regla("RN-002")
def test_con_tentativa_bloqueante_crea_igual_las_pendientes(operativo_client, formato):
    ParametrosDisponibilidad.objects.filter(pk=1).update(tentativa_bloquea=True)
    cartel = _cartel(formato, "Av. Llena 1")
    ocupante = Reserva(
        campania=Campania.objects.create(),
        cartel=cartel,
        fecha_inicio=date(2026, 11, 1),
        fecha_fin=date(2026, 11, 30),
        estado=Reserva.Estado.CONFIRMADA,
    )
    ocupante.save()
    # Como el alta individual: crear una Pendiente no valida cupo; eso pasa al confirmar.
    cuerpo = _post(operativo_client, Campania.objects.create(), [cartel.pk]).json()
    assert len(cuerpo["creadas"]) == 1


# --- Validaciones del pedido y permisos ---


@pytest.mark.django_db
def test_pedido_invalido_se_rechaza(operativo_client, formato):
    campania = Campania.objects.create()
    cartel = _cartel(formato, "Av. Uno 1").pk
    casos: list[tuple[dict[str, Any], str]] = [
        ({"carteles": []}, "carteles"),
        ({"carteles": list(range(1, 52))}, "carteles"),
        ({"fecha_inicio": "2026-11-30", "fecha_fin": "2026-11-01"}, "fecha_fin"),
        ({"fecha_inicio": None}, "fecha_inicio"),
        ({"campania": 999999}, "campania"),
    ]
    for extra, campo in casos:
        carteles = extra.pop("carteles", [cartel])
        respuesta = _post(operativo_client, campania, carteles, **extra)
        assert respuesta.status_code == 400, extra
        assert campo in respuesta.json(), extra
    assert not Reserva.objects.exists()


@pytest.mark.django_db
def test_lector_no_puede_crear_en_bloque(lector_client, formato):
    cartel = _cartel(formato, "Av. Uno 1")
    respuesta = _post(lector_client, Campania.objects.create(), [cartel.pk])
    assert respuesta.status_code == 403
    assert not Reserva.objects.exists()
