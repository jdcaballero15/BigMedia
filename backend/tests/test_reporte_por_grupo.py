"""Reporte de ingresos y días-cupo por grupo económico de la marca (HU-050, criterio 2)."""

from datetime import date
from decimal import Decimal

import pytest
from django.test import Client

from apps.campanias.models import Campania
from apps.clientes.models import Cliente, GrupoEconomico, Marca
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva

pytestmark = pytest.mark.regla("RN-016")


def cartel() -> Cartel:
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion=f"Dir {Cartel.objects.count() + 1}",
        capacidad=1,
        tarifa_lista="100.00",
    )


def reservar(marca: Marca, inicio: date, fin: date, total: str, estado: str = "confirmada") -> None:
    Reserva(
        campania=Campania.objects.create(marca=marca),
        cartel=cartel(),
        fecha_inicio=inicio,
        fecha_fin=fin,
        precio_alquiler=Decimal(total),
        estado=estado,
    ).save()


def por_grupo(client: Client, desde: str | None = None, hasta: str | None = None):
    partes = [f"{k}={v}" for k, v in (("desde", desde), ("hasta", hasta)) if v]
    query = f"?{'&'.join(partes)}" if partes else ""
    return client.get(f"/api/facturacion/por-grupo/{query}")


OCTUBRE = (date(2026, 10, 1), date(2026, 10, 31))


@pytest.mark.django_db
def test_grupo_suma_marcas_de_clientes_distintos(gerencia_client):
    """El corte por grupo suma las marcas del grupo, aunque las facturen agencias distintas."""
    grupo = GrupoEconomico.objects.create(nombre="Grupo Andes")
    una = Marca.objects.create(
        nombre="A", cliente=Cliente.objects.create(nombre="Agencia 1"), grupo=grupo
    )
    otra = Marca.objects.create(
        nombre="B", cliente=Cliente.objects.create(nombre="Agencia 2"), grupo=grupo
    )
    reservar(una, *OCTUBRE, "1000.00")
    reservar(otra, *OCTUBRE, "500.00")

    datos = por_grupo(gerencia_client, "2026-10", "2026-10").json()

    assert datos["grupos"] == [
        {
            "grupo": grupo.pk,
            "nombre": "Grupo Andes",
            "ingresos": "1500.00",
            "dias_cupo": 62,
            "porcentaje_ocupacion": 100.0,
        }
    ]
    assert datos["total_ingresos"] == "1500.00"
    assert datos["total_dias_cupo"] == 62


@pytest.mark.django_db
def test_marca_sin_grupo_cae_en_sin_grupo_y_el_ranking_va_por_ingresos(gerencia_client):
    grupo = GrupoEconomico.objects.create(nombre="Grupo Chico")
    cliente = Cliente.objects.create(nombre="Cliente")
    reservar(
        Marca.objects.create(nombre="En grupo", cliente=cliente, grupo=grupo), *OCTUBRE, "100.00"
    )
    reservar(Marca.objects.create(nombre="Suelta", cliente=cliente), *OCTUBRE, "900.00")

    grupos = por_grupo(gerencia_client, "2026-10", "2026-10").json()["grupos"]

    assert [(g["grupo"], g["nombre"]) for g in grupos] == [
        (None, "Sin grupo"),
        (grupo.pk, "Grupo Chico"),
    ]
    assert [g["porcentaje_ocupacion"] for g in grupos] == [50.0, 50.0]


@pytest.mark.django_db
def test_respeta_el_periodo_y_no_cuenta_canceladas(gerencia_client):
    grupo = GrupoEconomico.objects.create(nombre="Grupo Andes")
    marca = Marca.objects.create(
        nombre="A", cliente=Cliente.objects.create(nombre="C"), grupo=grupo
    )
    reservar(marca, *OCTUBRE, "1000.00")
    reservar(marca, *OCTUBRE, "9999.00", estado="cancelada")
    reservar(marca, date(2026, 12, 1), date(2026, 12, 31), "7777.00")

    datos = por_grupo(gerencia_client, "2026-10", "2026-10").json()

    assert Decimal(datos["total_ingresos"]) == Decimal("1000.00")
    assert datos["total_dias_cupo"] == 31


@pytest.mark.django_db
def test_periodo_invertido_o_invalido_devuelve_400(gerencia_client):
    assert por_grupo(gerencia_client, "2026-11", "2026-10").status_code == 400
    assert por_grupo(gerencia_client, "2026-13").status_code == 400


@pytest.mark.django_db
def test_solo_gerencia_ve_el_reporte_por_grupo(operativo_client):
    assert por_grupo(operativo_client, "2026-10", "2026-10").status_code == 403
    assert Client().get("/api/facturacion/por-grupo/").status_code in (401, 403)
