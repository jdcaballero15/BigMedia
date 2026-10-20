from datetime import date
from decimal import Decimal

import pytest
from django.test import Client

from apps.campanias.models import Campania
from apps.costos.models import Costo
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva


def reserva(campania: Campania, total: str, estado: str = "confirmada") -> Reserva:
    cartel = Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion=f"Dir {Cartel.objects.count() + 1}",
        capacidad=1,
        tarifa_lista=Decimal(total),
    )
    r = Reserva(
        campania=campania,
        cartel=cartel,
        fecha_inicio=date(2026, 11, 1),
        fecha_fin=date(2026, 11, 30),
        precio_alquiler=Decimal(total),
        estado=estado,
    )
    r.save()
    return r


def rollup(client: Client, campania_id: int):
    return client.get(f"/api/costos/campania/?campania={campania_id}")


@pytest.mark.django_db
def test_totales_y_margen_de_campania(operativo_client):
    camp = Campania.objects.create()
    r1 = reserva(camp, "1000.00")
    reserva(camp, "500.00")
    Costo.objects.create(
        reserva=r1, tipo="impresion", monto=Decimal("600.00"), fecha=date(2026, 11, 1)
    )
    datos = rollup(operativo_client, camp.pk).json()
    assert datos["cantidad_reservas"] == 2
    assert Decimal(datos["ingreso"]) == Decimal("1500.00")
    assert Decimal(datos["costo"]) == Decimal("600.00")
    assert Decimal(datos["margen"]) == Decimal("900.00")
    assert datos["porcentaje"] == 60.0


@pytest.mark.django_db
def test_cancelada_no_suma(operativo_client):
    camp = Campania.objects.create()
    reserva(camp, "1000.00")
    reserva(camp, "999.00", estado="cancelada")
    datos = rollup(operativo_client, camp.pk).json()
    assert datos["cantidad_reservas"] == 1
    assert Decimal(datos["ingreso"]) == Decimal("1000.00")


@pytest.mark.django_db
def test_sin_ingreso_no_rompe(operativo_client):
    camp = Campania.objects.create()
    datos = rollup(operativo_client, camp.pk).json()
    assert datos["cantidad_reservas"] == 0
    assert Decimal(datos["ingreso"]) == Decimal("0.00")
    assert datos["porcentaje"] is None


@pytest.mark.django_db
def test_campania_param_invalido(operativo_client):
    assert operativo_client.get("/api/costos/campania/?campania=abc").status_code == 400


@pytest.mark.django_db
def test_campania_sin_reservas_da_ceros(operativo_client):
    datos = rollup(operativo_client, 99999).json()
    assert datos["cantidad_reservas"] == 0
    assert Decimal(datos["ingreso"]) == Decimal("0.00")


@pytest.mark.django_db
def test_anonimo_no_puede_consultar():
    assert Client().get("/api/costos/campania/?campania=1").status_code in (401, 403)
