"""Panel principal (HU-047)."""

from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from apps.campanias.models import Campania
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva


def cartel(baja: bool = False) -> Cartel:
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="baja" if baja else "activo"),
        direccion=f"Dir {Cartel.objects.count() + 1}",
        capacidad=1,
        tarifa_lista="100.00",
    )


def reservar(car: Cartel, fin_en_dias: int, estado: str = "confirmada") -> Reserva:
    hoy = timezone.localdate()
    r = Reserva(
        campania=Campania.objects.create(),
        cartel=car,
        fecha_inicio=hoy - timedelta(days=1),
        fecha_fin=hoy + timedelta(days=fin_en_dias),
        estado=estado,
    )
    r.save()
    return r


def panel(client: Client):
    return client.get("/api/reservas/panel/")


@pytest.mark.django_db
def test_cuenta_carteles_libres_y_ocupados(operativo_client):
    ocupado = cartel()
    reservar(ocupado, 10)  # vigente hoy -> ocupa (capacidad 1)
    cartel()  # libre
    cartel(baja=True)  # excluido
    datos = panel(operativo_client).json()
    assert datos["carteles_ocupados"] == 1
    assert datos["carteles_libres"] == 1


@pytest.mark.django_db
def test_campanias_activas_son_confirmadas(operativo_client):
    Campania.objects.create(estado="confirmada")
    Campania.objects.create(estado="confirmada")
    Campania.objects.create(estado="cotizada")
    Campania.objects.create(estado="cancelada")
    datos = panel(operativo_client).json()
    assert datos["campanias_activas"] == 2


@pytest.mark.django_db
def test_reservas_por_vencer_en_la_ventana(operativo_client):
    car = cartel()
    cerca = reservar(car, 10)  # vence en 10 días -> entra
    reservar(cartel(), 40)  # vence en 40 días -> fuera
    reservar(cartel(), 5, estado="pendiente")  # no confirmada -> fuera
    datos = panel(operativo_client).json()
    ids = [r["id"] for r in datos["por_vencer"]]
    assert ids == [cerca.id]


@pytest.mark.django_db
def test_anonimo_no_puede_consultar():
    assert Client().get("/api/reservas/panel/").status_code in (401, 403)
