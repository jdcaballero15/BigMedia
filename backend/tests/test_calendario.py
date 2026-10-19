"""Calendario de disponibilidad a futuro (HU-042)."""

from datetime import date

import pytest
from django.test import Client

from apps.campanias.models import Campania
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva


def cartel(capacidad: int = 1, formato: str = "LED", baja: bool = False) -> Cartel:
    estado = EstadoCartel.objects.get(codigo="baja" if baja else "activo")
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre=formato),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=estado,
        direccion=f"Dirección {Cartel.objects.count() + 1}",
        capacidad=capacidad,
        tarifa_lista="100000.00",
    )


def reservar(car: Cartel, inicio: str, fin: str, estado: str = "confirmada") -> Reserva:
    r = Reserva(
        campania=Campania.objects.create(),
        cartel=car,
        fecha_inicio=date.fromisoformat(inicio),
        fecha_fin=date.fromisoformat(fin),
        estado=estado,
    )
    r.save()
    return r


def calendario(client: Client, query: str):
    return client.get(f"/api/reservas/calendario/{query}")


@pytest.mark.django_db
def test_columnas_por_mes_del_rango(operativo_client):
    cartel()
    datos = calendario(operativo_client, "?desde=2026-10-01&hasta=2026-12-31").json()
    claves = [p["clave"] for p in datos["periodos"]]
    assert claves == ["2026-10", "2026-11", "2026-12"]


@pytest.mark.django_db
def test_celda_refleja_ocupacion_del_mes(operativo_client):
    car = cartel(capacidad=1)
    # Ocupa parte de noviembre; octubre y diciembre quedan libres.
    reservar(car, "2026-11-10", "2026-11-20")
    datos = calendario(operativo_client, "?desde=2026-10-01&hasta=2026-12-31").json()
    fila = next(f for f in datos["carteles"] if f["id"] == car.id)
    celdas = {c["periodo"]: c["ocupados"] for c in fila["celdas"]}
    assert celdas["2026-10"] == 0
    assert celdas["2026-11"] == 1
    assert celdas["2026-12"] == 0


@pytest.mark.django_db
def test_cancelada_no_ocupa(operativo_client):
    car = cartel(capacidad=1)
    reservar(car, "2026-11-01", "2026-11-30", estado="cancelada")
    datos = calendario(operativo_client, "?desde=2026-11-01&hasta=2026-11-30").json()
    fila = next(f for f in datos["carteles"] if f["id"] == car.id)
    assert fila["celdas"][0]["ocupados"] == 0


@pytest.mark.django_db
def test_multimarca_muestra_pico(operativo_client):
    car = cartel(capacidad=20)
    for _ in range(12):
        reservar(car, "2026-11-01", "2026-11-30")
    datos = calendario(operativo_client, "?desde=2026-11-01&hasta=2026-11-30").json()
    fila = next(f for f in datos["carteles"] if f["id"] == car.id)
    assert fila["capacidad"] == 20
    assert fila["celdas"][0]["ocupados"] == 12


@pytest.mark.django_db
def test_rango_por_defecto_tres_meses(operativo_client):
    cartel()
    datos = calendario(operativo_client, "").json()
    assert len(datos["periodos"]) == 3


@pytest.mark.django_db
def test_rango_mayor_a_doce_meses_se_rechaza(operativo_client):
    respuesta = calendario(operativo_client, "?desde=2026-01-01&hasta=2027-06-30")
    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_filtra_por_zona_y_excluye_bajas(operativo_client):
    activo = cartel()
    cartel(baja=True)
    datos = calendario(
        operativo_client, f"?desde=2026-10-01&hasta=2026-10-31&zona={activo.zona_id}"
    ).json()
    ids = {f["id"] for f in datos["carteles"]}
    assert ids == {activo.id}


@pytest.mark.django_db
def test_anonimo_no_puede_consultar():
    respuesta = Client().get("/api/reservas/calendario/?desde=2026-10-01&hasta=2026-10-31")
    assert respuesta.status_code in (401, 403)
