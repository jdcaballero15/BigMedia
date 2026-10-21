"""Reporte de ocupación en días-cupo (HU-048)."""

from datetime import date

import pytest
from django.test import Client

from apps.campanias.models import Campania
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva


def formato(modalidad: str) -> Formato:
    return Formato.objects.filter(modalidad=modalidad)[0]


def cartel(fmt: Formato, capacidad: int, zona: str = "Ciudad") -> Cartel:
    return Cartel.objects.create(
        formato=fmt,
        zona=Zona.objects.get(nombre=zona),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion=f"Dir {Cartel.objects.count() + 1}",
        capacidad=capacidad,
        tarifa_lista="100.00",
    )


def reservar(car: Cartel, inicio: date, fin: date, estado: str = "confirmada") -> Reserva:
    r = Reserva(
        campania=Campania.objects.create(),
        cartel=car,
        fecha_inicio=inicio,
        fecha_fin=fin,
        estado=estado,
    )
    r.save()
    return r


def ocupacion(client: Client, desde: str | None = None, hasta: str | None = None, **extra: str):
    pares = {"desde": desde, "hasta": hasta, **extra}
    query = "&".join(f"{k}={v}" for k, v in pares.items() if v)
    return client.get(f"/api/reservas/reporte-ocupacion/{'?' + query if query else ''}")


@pytest.mark.regla("RN-004")
@pytest.mark.django_db
def test_cartel_fijo_ocupado_15_de_30_dias_es_50(operativo_client):
    car = cartel(formato("fija"), 1)
    reservar(car, date(2026, 11, 1), date(2026, 11, 15))  # 15 días en noviembre (30 días)
    datos = ocupacion(operativo_client, "2026-11", "2026-11").json()
    fila = datos["carteles"][0]
    assert fila["ocupacion"] == 50.0
    celda = fila["celdas"][0]
    assert (celda["dias_ocupados"], celda["dias_disponibles"], celda["porcentaje"]) == (
        15,
        30,
        50.0,
    )


@pytest.mark.django_db
def test_led_con_10_cupos_todo_el_mes_es_50(operativo_client):
    car = cartel(formato("digital"), 20)
    for _ in range(10):  # 10 cupos ocupados los 30 días
        reservar(car, date(2026, 11, 1), date(2026, 11, 30))
    datos = ocupacion(operativo_client, "2026-11", "2026-11").json()
    fila = datos["carteles"][0]
    assert fila["celdas"][0]["dias_ocupados"] == 300  # 10 cupos x 30 días
    assert fila["ocupacion"] == 50.0


@pytest.mark.django_db
def test_ranking_ordena_por_ocupacion_descendente(operativo_client):
    lleno = cartel(formato("fija"), 1)
    reservar(lleno, date(2026, 11, 1), date(2026, 11, 30))  # 100 %
    medio = cartel(formato("fija"), 1)
    reservar(medio, date(2026, 11, 1), date(2026, 11, 15))  # 50 %
    datos = ocupacion(operativo_client, "2026-11", "2026-11").json()
    assert [f["ocupacion"] for f in datos["carteles"]] == [100.0, 50.0]


@pytest.mark.django_db
def test_totales_por_modalidad_no_mezclan_fijos_con_digitales(operativo_client):
    reservar(cartel(formato("fija"), 1), date(2026, 11, 1), date(2026, 11, 30))  # fija 100 %
    reservar(cartel(formato("digital"), 1), date(2026, 11, 1), date(2026, 11, 15))  # digital 50 %
    datos = ocupacion(operativo_client, "2026-11", "2026-11").json()
    por_modalidad = {m["modalidad"]: m["ocupacion"] for m in datos["modalidades"]}
    assert por_modalidad == {"fija": 100.0, "digital": 50.0}


@pytest.mark.django_db
def test_reserva_cancelada_no_ocupa(operativo_client):
    car = cartel(formato("fija"), 1)
    reservar(car, date(2026, 11, 1), date(2026, 11, 15))
    reservar(car, date(2026, 11, 16), date(2026, 11, 30), estado="cancelada")
    datos = ocupacion(operativo_client, "2026-11", "2026-11").json()
    assert datos["carteles"][0]["ocupacion"] == 50.0


@pytest.mark.django_db
def test_filtro_por_modalidad_acota(operativo_client):
    reservar(cartel(formato("fija"), 1), date(2026, 11, 1), date(2026, 11, 30))
    reservar(cartel(formato("digital"), 1), date(2026, 11, 1), date(2026, 11, 30))
    datos = ocupacion(operativo_client, "2026-11", "2026-11", modalidad="fija").json()
    assert {f["modalidad"] for f in datos["carteles"]} == {"fija"}


@pytest.mark.django_db
def test_filtro_por_zona_acota(operativo_client):
    ciudad = cartel(formato("fija"), 1, zona="Ciudad")
    reservar(ciudad, date(2026, 11, 1), date(2026, 11, 30))
    reservar(cartel(formato("fija"), 1, zona="Maipú"), date(2026, 11, 1), date(2026, 11, 30))
    datos = ocupacion(operativo_client, "2026-11", "2026-11", zona=str(ciudad.zona_id)).json()
    assert [f["id"] for f in datos["carteles"]] == [ciudad.id]


@pytest.mark.django_db
def test_periodo_invertido_devuelve_400(operativo_client):
    assert ocupacion(operativo_client, "2026-11", "2026-10").status_code == 400


@pytest.mark.django_db
def test_periodo_con_formato_invalido_devuelve_400(operativo_client):
    assert ocupacion(operativo_client, "2026-13").status_code == 400


@pytest.mark.django_db
def test_anonimo_no_puede_consultar():
    assert Client().get("/api/reservas/reporte-ocupacion/").status_code in (401, 403)
