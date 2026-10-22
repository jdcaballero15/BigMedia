"""Reporte de ingresos y días-cupo por rubro de la marca (HU-050, criterio 1)."""

from datetime import date
from decimal import Decimal

import pytest
from django.test import Client

from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca, Rubro
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


def campania(marca: Marca | None = None) -> Campania:
    return Campania.objects.create(marca=marca)


def reservar(
    camp: Campania,
    inicio: date,
    fin: date,
    total: str,
    estado: str = "confirmada",
) -> Reserva:
    r = Reserva(
        campania=camp,
        cartel=cartel(),
        fecha_inicio=inicio,
        fecha_fin=fin,
        precio_alquiler=Decimal(total),
        estado=estado,
    )
    r.save()
    return r


def por_rubro(client: Client, desde: str | None = None, hasta: str | None = None):
    partes = [f"{k}={v}" for k, v in (("desde", desde), ("hasta", hasta)) if v]
    query = f"?{'&'.join(partes)}" if partes else ""
    return client.get(f"/api/facturacion/por-rubro/{query}")


@pytest.mark.django_db
def test_corta_por_rubro_de_la_marca_no_por_agencia(gerencia_client):
    """Una campaña de una agencia para una marca de Gastronomía corta por Gastronomía."""
    agencia = Cliente.objects.create(nombre="Agencia Test")
    rubro = Rubro.objects.create(nombre="Gastronomía")
    marca = Marca.objects.create(nombre="Marca Gastro", cliente=agencia, rubro=rubro)
    reservar(campania(marca=marca), date(2026, 10, 1), date(2026, 10, 31), "1000.00")

    datos = por_rubro(gerencia_client, "2026-10", "2026-10").json()
    assert len(datos["rubros"]) == 1
    fila = datos["rubros"][0]
    assert fila["rubro"] == rubro.id
    assert fila["nombre"] == "Gastronomía"


@pytest.mark.django_db
def test_ingresos_por_rubro_cuadran_con_suma_manual(gerencia_client):
    """Los ingresos del rubro cuadran contra la suma manual del reparto."""
    rubro = Rubro.objects.create(nombre="Retail")
    agencia = Cliente.objects.create(nombre="Agencia Retail")
    marca = Marca.objects.create(nombre="Marca Retail", cliente=agencia, rubro=rubro)
    reservar(campania(marca=marca), date(2026, 10, 1), date(2026, 10, 31), "2000.00")
    reservar(campania(marca=marca), date(2026, 10, 1), date(2026, 10, 31), "500.00")

    datos = por_rubro(gerencia_client, "2026-10", "2026-10").json()
    fila = datos["rubros"][0]
    assert Decimal(fila["ingresos"]) == Decimal("2500.00")
    assert Decimal(datos["total_ingresos"]) == Decimal("2500.00")


@pytest.mark.regla("RN-004")
@pytest.mark.django_db
def test_dias_cupo_cuadran_una_reserva_es_un_cupo(gerencia_client):
    """Los días-cupo cuadran: una reserva de 31 días = 31 días-cupo (RN-004)."""
    rubro = Rubro.objects.create(nombre="Automotriz")
    agencia = Cliente.objects.create(nombre="Agencia Auto")
    marca = Marca.objects.create(nombre="Marca Auto", cliente=agencia, rubro=rubro)
    reservar(campania(marca=marca), date(2026, 10, 1), date(2026, 10, 31), "1000.00")

    datos = por_rubro(gerencia_client, "2026-10", "2026-10").json()
    fila = datos["rubros"][0]
    assert fila["dias_cupo"] == 31
    assert datos["total_dias_cupo"] == 31


@pytest.mark.django_db
def test_porcentaje_ocupacion_suma_100_entre_rubros(gerencia_client):
    """El % de ocupación suma 100 entre rubros con ocupación."""
    rubro1 = Rubro.objects.create(nombre="Rubro A")
    rubro2 = Rubro.objects.create(nombre="Rubro B")
    agencia = Cliente.objects.create(nombre="Agencia Multi")
    marca1 = Marca.objects.create(nombre="Marca A", cliente=agencia, rubro=rubro1)
    marca2 = Marca.objects.create(nombre="Marca B", cliente=agencia, rubro=rubro2)
    reservar(campania(marca=marca1), date(2026, 10, 1), date(2026, 10, 15), "1000.00")
    reservar(campania(marca=marca2), date(2026, 10, 16), date(2026, 10, 31), "2000.00")

    datos = por_rubro(gerencia_client, "2026-10", "2026-10").json()
    total_pct = sum(fila["porcentaje_ocupacion"] for fila in datos["rubros"])
    assert abs(total_pct - 100.0) < 0.2


@pytest.mark.django_db
def test_reserva_sin_rubro_cae_en_bucket_sin_rubro(gerencia_client):
    """Reservas cuya marca no tiene rubro van al bucket 'Sin rubro'."""
    agencia = Cliente.objects.create(nombre="Agencia Sin Rubro")
    marca = Marca.objects.create(nombre="Marca Sin Rubro", cliente=agencia)
    reservar(campania(marca=marca), date(2026, 10, 1), date(2026, 10, 31), "800.00")

    datos = por_rubro(gerencia_client, "2026-10", "2026-10").json()
    assert len(datos["rubros"]) == 1
    assert datos["rubros"][0]["nombre"] == "Sin rubro"
    assert datos["rubros"][0]["rubro"] is None


@pytest.mark.django_db
def test_reserva_cancelada_no_cuenta(gerencia_client):
    """Las reservas canceladas no se incluyen en el reporte."""
    rubro = Rubro.objects.create(nombre="Tecnología")
    agencia = Cliente.objects.create(nombre="Agencia Tech")
    marca = Marca.objects.create(nombre="Marca Tech", cliente=agencia, rubro=rubro)
    reservar(campania(marca=marca), date(2026, 10, 1), date(2026, 10, 31), "1000.00")
    reservar(
        campania(marca=marca), date(2026, 10, 1), date(2026, 10, 31), "9999.00", estado="cancelada"
    )

    datos = por_rubro(gerencia_client, "2026-10", "2026-10").json()
    assert Decimal(datos["total_ingresos"]) == Decimal("1000.00")


@pytest.mark.django_db
def test_periodo_invertido_devuelve_400(gerencia_client):
    assert por_rubro(gerencia_client, "2026-11", "2026-10").status_code == 400


@pytest.mark.django_db
def test_periodo_con_formato_invalido_devuelve_400(gerencia_client):
    assert por_rubro(gerencia_client, "2026-13").status_code == 400


@pytest.mark.django_db
def test_operativo_recibe_403(operativo_client):
    assert por_rubro(operativo_client, "2026-10", "2026-10").status_code == 403


@pytest.mark.django_db
def test_anonimo_recibe_401_o_403():
    assert Client().get("/api/facturacion/por-rubro/").status_code in (401, 403)


@pytest.mark.django_db
def test_ranking_ordenado_por_ingresos_descendente(gerencia_client):
    """El primer rubro del ranking tiene los mayores ingresos."""
    rubro_alto = Rubro.objects.create(nombre="Alto")
    rubro_bajo = Rubro.objects.create(nombre="Bajo")
    agencia = Cliente.objects.create(nombre="Agencia Rank")
    marca_alto = Marca.objects.create(nombre="Marca Alto", cliente=agencia, rubro=rubro_alto)
    marca_bajo = Marca.objects.create(nombre="Marca Bajo", cliente=agencia, rubro=rubro_bajo)
    reservar(campania(marca=marca_bajo), date(2026, 10, 1), date(2026, 10, 31), "100.00")
    reservar(campania(marca=marca_alto), date(2026, 10, 1), date(2026, 10, 31), "5000.00")

    datos = por_rubro(gerencia_client, "2026-10", "2026-10").json()
    nombres = [f["nombre"] for f in datos["rubros"]]
    assert nombres[0] == "Alto"
    assert nombres[1] == "Bajo"
