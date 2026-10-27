"""Lista de "Agregar carteles": carteles de un formato con cupo libre en el rango (HU-056)."""

from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from apps.campanias.models import Campania
from apps.inventario.models import Cartel, EstadoCartel, Formato, Proveedor, Zona
from apps.reservas.models import ParametrosDisponibilidad, Reserva

URL = "/api/reservas/carteles-para-tanda/"


@pytest.fixture
def formato() -> Formato:
    return Formato.objects.create(nombre="Gran Formato Prueba", modalidad="fija")


def _cartel(formato: Formato, direccion: str, capacidad: int = 1, **extra: Any) -> Cartel:
    datos: dict[str, Any] = {
        "zona": Zona.objects.get(nombre="Ciudad"),
        "estado": EstadoCartel.objects.get(codigo="activo"),
        "tamano": "8x3",
        "tarifa_lista": Decimal("1000.00"),
        **extra,
    }
    return Cartel.objects.create(formato=formato, direccion=direccion, capacidad=capacidad, **datos)


def _reserva(
    cartel: Cartel,
    inicio: str,
    fin: str,
    estado: str = "confirmada",
    campania: Campania | None = None,
) -> Reserva:
    reserva = Reserva(
        campania=campania or Campania.objects.create(),
        cartel=cartel,
        fecha_inicio=date.fromisoformat(inicio),
        fecha_fin=date.fromisoformat(fin),
        estado=estado,
    )
    reserva.save()
    return reserva


def _lista(
    client: Client,
    campania: Campania,
    formato: Formato,
    desde: str = "2026-11-01",
    hasta: str = "2026-11-30",
    **filtros: Any,
) -> Any:
    params = {"campania": campania.pk, "formato": formato.pk, "desde": desde, "hasta": hasta}
    respuesta = client.get(URL, {**params, **filtros})
    assert respuesta.status_code == 200, respuesta.json()
    return respuesta.json()


def _ids(filas: list[dict[str, Any]]) -> list[int]:
    return [fila["id"] for fila in filas]


# --- Criterio 1: solo el formato y con cupo libre ---


@pytest.mark.django_db
def test_lista_solo_carteles_del_formato_con_cupo_libre(operativo_client, formato):
    libre = _cartel(formato, "Av. Libre 100")
    ocupado = _cartel(formato, "Av. Ocupada 200")
    _reserva(ocupado, "2026-11-10", "2026-11-20")
    _reserva(libre, "2026-12-01", "2026-12-31")
    otro_formato = Formato.objects.create(nombre="Otro Formato", modalidad="fija")
    _cartel(otro_formato, "Av. Otro 300")

    filas = _lista(operativo_client, Campania.objects.create(), formato)
    assert _ids(filas) == [libre.pk]
    assert filas[0] == {
        "id": libre.pk,
        "nombre_visible": "Av. Libre 100 · 8x3",
        "zona_nombre": "Ciudad",
        "proveedor_nombre": None,
        "tarifa_lista": "1000.00",
        "capacidad": 1,
        "ocupados": 0,
        "tentativas": 0,
        "en_campania": False,
    }


@pytest.mark.django_db
@pytest.mark.regla("RN-003")
def test_lista_cuenta_el_pico_diario(operativo_client, formato):
    led = _cartel(formato, "Av. LED 1", capacidad=2)
    _reserva(led, "2026-11-01", "2026-11-10")
    _reserva(led, "2026-11-20", "2026-11-30")
    lleno = _cartel(formato, "Av. LED 2", capacidad=2)
    _reserva(lleno, "2026-11-01", "2026-11-15")
    _reserva(lleno, "2026-11-10", "2026-11-30")

    filas = _lista(operativo_client, Campania.objects.create(), formato)
    assert _ids(filas) == [led.pk]
    assert filas[0]["ocupados"] == 1


@pytest.mark.django_db
@pytest.mark.regla("RN-001")
def test_lista_respeta_el_dia_de_borde(operativo_client, formato):
    cartel = _cartel(formato, "Av. Borde 1")
    _reserva(cartel, "2026-10-01", "2026-11-01")
    campania = Campania.objects.create()
    assert _lista(operativo_client, campania, formato) == []

    ParametrosDisponibilidad.objects.filter(pk=1).update(borde_inclusivo=False)
    assert _ids(_lista(operativo_client, campania, formato)) == [cartel.pk]


@pytest.mark.django_db
@pytest.mark.regla("RN-002")
def test_pendientes_de_otra_campania_se_marcan_o_bloquean_segun_el_parametro(
    operativo_client, formato
):
    cartel = _cartel(formato, "Av. Tentativa 1")
    _reserva(cartel, "2026-11-05", "2026-11-25", estado="pendiente")
    _reserva(cartel, "2026-11-05", "2026-11-25", estado="cancelada")
    campania = Campania.objects.create()

    filas = _lista(operativo_client, campania, formato)
    assert _ids(filas) == [cartel.pk]
    assert (filas[0]["tentativas"], filas[0]["ocupados"]) == (1, 0)

    ParametrosDisponibilidad.objects.filter(pk=1).update(tentativa_bloquea=True)
    assert _lista(operativo_client, campania, formato) == []


@pytest.mark.django_db
def test_carteles_de_baja_no_aparecen(operativo_client, formato):
    _cartel(formato, "Av. Baja 1", estado=EstadoCartel.objects.get(codigo="baja"))
    assert _lista(operativo_client, Campania.objects.create(), formato) == []


@pytest.mark.django_db
def test_cartel_ya_reservado_por_la_campania_se_marca(operativo_client, formato):
    campania = Campania.objects.create()
    cartel = _cartel(formato, "Av. Propia 1")
    _reserva(cartel, "2026-11-01", "2026-11-30", estado="pendiente", campania=campania)
    cancelada = _cartel(formato, "Av. Propia 2")
    _reserva(cancelada, "2026-11-01", "2026-11-30", estado="cancelada", campania=campania)

    filas = {fila["id"]: fila for fila in _lista(operativo_client, campania, formato)}
    assert (filas[cartel.pk]["en_campania"], filas[cartel.pk]["tentativas"]) == (True, 0)
    assert filas[cancelada.pk]["en_campania"] is False


# --- Criterio 3: filtros ---


@pytest.mark.django_db
def test_filtros_por_zona_proveedor_y_direccion_se_combinan(operativo_client, formato):
    norte = Zona.objects.create(nombre="Zona Norte Prueba")
    proveedor = Proveedor.objects.create(nombre="Proveedor Prueba")
    buscado = _cartel(formato, "Avenida Córdoba 500", zona=norte, proveedor=proveedor)
    _cartel(formato, "Avenida Córdoba 600", zona=norte)
    _cartel(formato, "Avenida Córdoba 700", proveedor=proveedor)
    _cartel(formato, "Calle Mitre 10", zona=norte, proveedor=proveedor)

    filas = _lista(
        operativo_client,
        Campania.objects.create(),
        formato,
        zona=norte.pk,
        proveedor=proveedor.pk,
        q="  CORDOBA ",
    )
    assert _ids(filas) == [buscado.pk]
    assert filas[0]["proveedor_nombre"] == "Proveedor Prueba"


# --- Criterio 2 y validaciones ---


@pytest.mark.django_db
@pytest.mark.parametrize("faltante", ["desde", "hasta"])
def test_sin_fechas_se_rechaza(operativo_client, formato, faltante):
    params = {
        "campania": Campania.objects.create().pk,
        "formato": formato.pk,
        "desde": "2026-11-01",
        "hasta": "2026-11-30",
    }
    params.pop(faltante)
    respuesta = operativo_client.get(URL, params)
    assert respuesta.status_code == 400
    assert faltante in respuesta.json()


@pytest.mark.django_db
def test_fechas_invertidas_o_invalidas_se_rechazan(operativo_client, formato):
    campania = Campania.objects.create()
    base = {"campania": campania.pk, "formato": formato.pk}
    invertidas = operativo_client.get(URL, {**base, "desde": "2026-11-30", "hasta": "2026-11-01"})
    assert invertidas.status_code == 400
    assert "hasta" in invertidas.json()
    invalida = operativo_client.get(URL, {**base, "desde": "01/11/2026", "hasta": "2026-11-30"})
    assert invalida.status_code == 400
    assert "desde" in invalida.json()


@pytest.mark.django_db
def test_campania_o_formato_inexistentes_dan_404(operativo_client, formato):
    fechas = {"desde": "2026-11-01", "hasta": "2026-11-30"}
    campania = Campania.objects.create()
    sin_campania = operativo_client.get(URL, {"campania": 999999, "formato": formato.pk, **fechas})
    assert sin_campania.status_code == 404
    sin_formato = operativo_client.get(URL, {"campania": campania.pk, "formato": 999999, **fechas})
    assert sin_formato.status_code == 404


@pytest.mark.django_db
def test_ids_invalidos_se_rechazan(operativo_client, formato):
    respuesta = operativo_client.get(
        URL, {"campania": "x", "formato": formato.pk, "desde": "2026-11-01", "hasta": "2026-11-30"}
    )
    assert respuesta.status_code == 400
    assert "campania" in respuesta.json()


@pytest.mark.django_db
def test_lector_puede_ver_la_lista(lector_client, formato):
    _cartel(formato, "Av. Lectura 1")
    assert len(_lista(lector_client, Campania.objects.create(), formato)) == 1


@pytest.mark.django_db
def test_consultas_no_crecen_con_la_cantidad_de_carteles(operativo_client, formato):
    campania = Campania.objects.create()
    _reserva(_cartel(formato, "Av. Uno 1", capacidad=3), "2026-11-01", "2026-11-30")
    with CaptureQueriesContext(connection) as uno:
        _lista(operativo_client, campania, formato)
    for numero in range(2, 12):
        cartel = _cartel(formato, f"Av. Muchos {numero}", capacidad=3)
        _reserva(cartel, "2026-11-01", "2026-11-30")
    with CaptureQueriesContext(connection) as muchos:
        assert len(_lista(operativo_client, campania, formato)) == 11
    assert len(muchos.captured_queries) == len(uno.captured_queries)
