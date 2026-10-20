"""Reparto de ingresos por día (HU-051)."""

from datetime import date
from decimal import Decimal

import pytest
from django.test import Client

from apps.campanias.models import Campania
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva


def cartel() -> Cartel:
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion=f"Dir {Cartel.objects.count() + 1}",
        capacidad=1,
        tarifa_lista="100.00",
    )


def reservar(inicio: date, fin: date, total: str) -> Reserva:
    r = Reserva(
        campania=Campania.objects.create(),
        cartel=cartel(),
        fecha_inicio=inicio,
        fecha_fin=fin,
        precio_alquiler=Decimal(total),
    )
    r.save()
    return r


def reparto(client: Client, reserva: int | str):
    return client.get(f"/api/reservas/reparto/?reserva={reserva}")


@pytest.mark.django_db
def test_reparto_tres_meses_proporcional_a_los_dias(operativo_client):
    # Sep (30) + Oct (31) + Nov (30) = 91 días sobre 100000.00 (HU-051, criterio 1).
    reserva = reservar(date(2026, 9, 1), date(2026, 11, 30), "100000.00")
    datos = reparto(operativo_client, reserva.id).json()
    assert [(d["mes"], d["etiqueta"], Decimal(str(d["monto"]))) for d in datos] == [
        ("2026-09", "Sep 2026", Decimal("32967.03")),
        ("2026-10", "Oct 2026", Decimal("34065.93")),
        ("2026-11", "Nov 2026", Decimal("32967.04")),
    ]


@pytest.mark.django_db
def test_reparto_suma_exacta_al_total(operativo_client):
    # El último mes absorbe el redondeo: la suma coincide al centavo (HU-051, criterio 3).
    reserva = reservar(date(2026, 9, 1), date(2026, 11, 30), "100000.00")
    datos = reparto(operativo_client, reserva.id).json()
    assert sum(Decimal(str(d["monto"])) for d in datos) == Decimal("100000.00")


@pytest.mark.django_db
def test_reparto_quince_dias_a_caballo_de_dos_meses(operativo_client):
    # 25/10 a 08/11: 7 días en octubre y 8 en noviembre sobre 1500.00 (HU-051, criterio 2).
    reserva = reservar(date(2026, 10, 25), date(2026, 11, 8), "1500.00")
    datos = reparto(operativo_client, reserva.id).json()
    assert [(d["mes"], Decimal(str(d["monto"]))) for d in datos] == [
        ("2026-10", Decimal("700.00")),
        ("2026-11", Decimal("800.00")),
    ]


@pytest.mark.django_db
def test_reparto_dentro_de_un_solo_mes_asigna_todo(operativo_client):
    reserva = reservar(date(2026, 10, 1), date(2026, 10, 15), "5000.00")
    datos = reparto(operativo_client, reserva.id).json()
    assert len(datos) == 1
    assert datos[0]["mes"] == "2026-10"
    assert datos[0]["etiqueta"] == "Oct 2026"
    assert Decimal(str(datos[0]["monto"])) == Decimal("5000.00")


@pytest.mark.django_db
def test_reparto_reserva_inexistente_devuelve_400(operativo_client):
    respuesta = reparto(operativo_client, 999999)
    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_reparto_anonimo_no_puede_consultar():
    assert Client().get("/api/reservas/reparto/?reserva=1").status_code in (401, 403)
