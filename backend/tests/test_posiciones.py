"""Vista Posiciones de "Agregar carteles": casilleros por slot como en la planilla (HU-071)."""

from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca
from apps.inventario.models import Cartel, EstadoCartel, Formato, Proveedor, Zona
from apps.reservas.models import Reserva
from apps.reservas.services import posiciones_de_formato, repartir_en_slots

URL = "/api/reservas/posiciones/"
DESDE = date(2026, 11, 1)
HASTA = date(2026, 11, 30)


@pytest.fixture
def formato() -> Formato:
    return Formato.objects.create(nombre="Séxtuple Prueba", modalidad="fija", por_cantidad=True)


def _cartel(formato: Formato, direccion: str, capacidad: int = 1, **extra: Any) -> Cartel:
    datos: dict[str, Any] = {
        "zona": Zona.objects.get(nombre="Ciudad"),
        "estado": EstadoCartel.objects.get(codigo="activo"),
        "tarifa_lista": Decimal("1000.00"),
        **extra,
    }
    return Cartel.objects.create(formato=formato, direccion=direccion, capacidad=capacidad, **datos)


def _campania(marca: str | None = None) -> Campania:
    if marca is None:
        return Campania.objects.create()
    cliente = Cliente.objects.create(nombre=f"Cliente {marca}")
    return Campania.objects.create(
        nombre=f"Campaña {marca}", marca=Marca.objects.create(nombre=marca, cliente=cliente)
    )


def _reserva(
    cartel: Cartel,
    inicio: str,
    fin: str,
    estado: str = "confirmada",
    campania: Campania | None = None,
) -> Reserva:
    reserva = Reserva(
        campania=campania or _campania(),
        cartel=cartel,
        fecha_inicio=date.fromisoformat(inicio),
        fecha_fin=date.fromisoformat(fin),
        estado=estado,
    )
    reserva.save()
    return reserva


def _posiciones(campania: Campania, formato: Formato, **filtros: Any) -> list[dict[str, Any]]:
    return posiciones_de_formato(campania, formato, DESDE, HASTA, filtros)


def _ids_por_slot(slots: list[list[Any]]) -> list[list[int]]:
    return [[ocupante.pk for ocupante in slot] for slot in slots]


# --- Reparto en casilleros ---


@pytest.mark.django_db
@pytest.mark.regla("RN-003")
def test_repartir_reservas_sucesivas_comparten_slot(formato):
    cartel = _cartel(formato, "Av. Reparto 1", capacidad=3)
    a = _reserva(cartel, "2026-11-01", "2026-11-10")
    b = _reserva(cartel, "2026-11-15", "2026-11-30")
    c = _reserva(cartel, "2026-11-01", "2026-11-30")

    slots = repartir_en_slots([c, b, a], 3, borde_inclusivo=True)

    assert len(slots) == 3
    assert sorted(_ids_por_slot(slots)) == sorted([[a.pk, b.pk], [c.pk], []])


@pytest.mark.django_db
@pytest.mark.regla("RN-001")
def test_repartir_dia_de_borde_segun_parametro(formato):
    cartel = _cartel(formato, "Av. Borde 1", capacidad=2)
    a = _reserva(cartel, "2026-11-01", "2026-11-10")
    b = _reserva(cartel, "2026-11-10", "2026-11-20")

    assert _ids_por_slot(repartir_en_slots([a, b], 2, borde_inclusivo=True)) == [[a.pk], [b.pk]]
    assert _ids_por_slot(repartir_en_slots([a, b], 2, borde_inclusivo=False)) == [
        [a.pk, b.pk],
        [],
    ]


# --- Filas de la vista ---


@pytest.mark.django_db
@pytest.mark.regla("RN-005")
def test_posiciones_cartel_lleno_se_incluye_marcado_lleno(formato):
    cartel = _cartel(formato, "Av. Llena 1")
    _reserva(cartel, "2026-11-01", "2026-11-30", campania=_campania("Schervosky"))

    [fila] = _posiciones(_campania(), formato)

    assert (fila["id"], fila["lleno"], fila["ocupados"]) == (cartel.pk, True, 1)
    assert fila["slots"][0][0]["marca_nombre"] == "Schervosky"
    assert fila["direccion"] == "Av. Llena 1"


@pytest.mark.django_db
@pytest.mark.regla("RN-003")
def test_posiciones_slots_tiene_largo_capacidad_y_ocupados_es_el_pico(formato):
    cartel = _cartel(formato, "Av. Ocho 1", capacidad=8)
    for _ in range(3):
        _reserva(cartel, "2026-11-01", "2026-11-30")

    [fila] = _posiciones(_campania(), formato)

    assert len(fila["slots"]) == 8
    assert fila["ocupados"] == 3
    assert fila["lleno"] is False
    assert sum(1 for slot in fila["slots"] if not slot) == 5


@pytest.mark.django_db
def test_posiciones_reserva_propia_que_bloquea_se_marca_en_su_slot(formato):
    campania = _campania("Propia")
    cartel = _cartel(formato, "Av. Propia 2")
    _reserva(cartel, "2026-11-01", "2026-11-30", campania=campania)

    [fila] = _posiciones(campania, formato)

    assert fila["lleno"] is True
    assert fila["slots"][0][0]["es_esta_campania"] is True
    assert fila["slots"][0][0]["campania_id"] == campania.pk


@pytest.mark.django_db
def test_posiciones_campania_sin_marca_devuelve_marca_nula(formato):
    cartel = _cartel(formato, "Av. Sin Marca 1")
    _reserva(cartel, "2026-11-01", "2026-11-30")

    [fila] = _posiciones(_campania(), formato)
    ocupante = fila["slots"][0][0]

    assert (ocupante["marca_id"], ocupante["marca_nombre"]) == (None, None)
    assert (ocupante["fecha_inicio"], ocupante["fecha_fin"]) == ("2026-11-01", "2026-11-30")


@pytest.mark.django_db
def test_posiciones_excluye_carteles_fuera_de_servicio_y_de_baja(formato):
    _cartel(formato, "Av. Baja 1", estado=EstadoCartel.objects.get(codigo="baja"))
    _cartel(formato, "Av. Apagado 1", estado=EstadoCartel.objects.get(codigo="apagado"))

    assert _posiciones(_campania(), formato) == []


@pytest.mark.django_db
def test_posiciones_filtros_zona_proveedor_y_direccion_se_combinan(formato):
    norte = Zona.objects.create(nombre="Zona Norte Prueba")
    proveedor = Proveedor.objects.create(nombre="Proveedor Prueba")
    buscado = _cartel(formato, "Avenida Córdoba 500", zona=norte, proveedor=proveedor)
    _cartel(formato, "Avenida Córdoba 600", zona=norte)
    _cartel(formato, "Calle Mitre 10", zona=norte, proveedor=proveedor)

    filas = _posiciones(
        _campania(), formato, zona=norte.pk, proveedor=proveedor.pk, direccion=" CORDOBA "
    )

    assert [fila["id"] for fila in filas] == [buscado.pk]


@pytest.mark.django_db
def test_posiciones_ordena_por_zona_y_direccion(formato):
    godoy = Zona.objects.create(nombre="AAA Primera Zona")
    b = _cartel(formato, "B Calle 1")
    a = _cartel(formato, "A Calle 1")
    z = _cartel(formato, "Z Calle 1", zona=godoy)

    assert [fila["id"] for fila in _posiciones(_campania(), formato)] == [z.pk, a.pk, b.pk]


# --- Endpoint ---


def _get(client: Client, campania: Campania, formato: Formato, **extra: Any) -> Any:
    params = {"campania": campania.pk, "formato": formato.pk, "desde": "2026-11-01"}
    return client.get(URL, {**params, "hasta": "2026-11-30", **extra})


@pytest.mark.django_db
def test_endpoint_posiciones_devuelve_filas_filtradas(operativo_client, formato):
    norte = Zona.objects.create(nombre="Zona Norte Prueba")
    buscado = _cartel(formato, "Avenida Córdoba 500", capacidad=2, zona=norte)
    _cartel(formato, "Avenida Córdoba 600")
    _reserva(buscado, "2026-11-01", "2026-11-30", campania=_campania("Fravega"))

    respuesta = _get(operativo_client, _campania(), formato, zona=norte.pk, q="cordoba")

    assert respuesta.status_code == 200
    [fila] = respuesta.json()
    assert fila["id"] == buscado.pk
    assert [[o["marca_nombre"] for o in slot] for slot in fila["slots"]] == [["Fravega"], []]


@pytest.mark.django_db
def test_endpoint_posiciones_fechas_faltantes_o_invertidas_dan_400(operativo_client, formato):
    campania = _campania()
    sin_hasta = operativo_client.get(
        URL, {"campania": campania.pk, "formato": formato.pk, "desde": "2026-11-01"}
    )
    assert sin_hasta.status_code == 400
    assert "hasta" in sin_hasta.json()
    invertidas = _get(operativo_client, campania, formato, desde="2026-12-01")
    assert invertidas.status_code == 400
    assert "hasta" in invertidas.json()


@pytest.mark.django_db
def test_endpoint_posiciones_ids_invalidos_dan_400_e_inexistentes_404(operativo_client, formato):
    campania = _campania()
    invalido = operativo_client.get(
        URL, {"campania": "x", "formato": formato.pk, "desde": "2026-11-01", "hasta": "2026-11-30"}
    )
    assert invalido.status_code == 400
    assert "campania" in invalido.json()
    inexistente = operativo_client.get(
        URL,
        {"campania": campania.pk, "formato": 999999, "desde": "2026-11-01", "hasta": "2026-11-30"},
    )
    assert inexistente.status_code == 404


@pytest.mark.django_db
def test_endpoint_posiciones_lector_puede_ver(lector_client, formato):
    _cartel(formato, "Av. Lectura 1")
    respuesta = _get(lector_client, _campania(), formato)
    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1


@pytest.mark.django_db
def test_endpoint_posiciones_sin_sesion_da_403(client, formato):
    assert _get(client, _campania(), formato).status_code in (401, 403)


@pytest.mark.django_db
def test_endpoint_posiciones_consultas_no_crecen_con_los_carteles(operativo_client, formato):
    campania = _campania()
    _reserva(_cartel(formato, "Av. Uno 1", capacidad=3), "2026-11-01", "2026-11-30")
    with CaptureQueriesContext(connection) as uno:
        assert _get(operativo_client, campania, formato).status_code == 200
    for numero in range(2, 7):
        cartel = _cartel(formato, f"Av. Muchos {numero}", capacidad=3)
        _reserva(cartel, "2026-11-01", "2026-11-30", campania=_campania(f"Marca {numero}"))
    with CaptureQueriesContext(connection) as muchos:
        assert len(_get(operativo_client, campania, formato).json()) == 6
    assert len(muchos.captured_queries) == len(uno.captured_queries)
