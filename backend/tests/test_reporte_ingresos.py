"""Reporte de ingresos por cliente y marca (HU-049)."""

from datetime import date
from decimal import Decimal

import pytest
from django.test import Client

from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca
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


def campania(marca: Marca | None = None, cliente_fact: Cliente | None = None) -> Campania:
    return Campania.objects.create(marca=marca, cliente_facturacion=cliente_fact)


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


def ingresos(client: Client, desde: str | None = None, hasta: str | None = None):
    partes = [f"{k}={v}" for k, v in (("desde", desde), ("hasta", hasta)) if v]
    query = f"?{'&'.join(partes)}" if partes else ""
    return client.get(f"/api/facturacion/ingresos/{query}")


@pytest.mark.django_db
def test_cliente_con_dos_marcas_desglosa_y_suma(operativo_client):
    agencia = Cliente.objects.create(nombre="Agencia A")
    m1 = Marca.objects.create(nombre="Marca 1", cliente=agencia)
    m2 = Marca.objects.create(nombre="Marca 2", cliente=agencia)
    reservar(campania(marca=m1), date(2026, 10, 1), date(2026, 10, 31), "1000.00")
    reservar(campania(marca=m2), date(2026, 10, 1), date(2026, 10, 31), "500.00")
    datos = ingresos(operativo_client, "2026-10", "2026-10").json()
    cliente = datos["clientes"][0]
    assert cliente["cliente"] == agencia.id
    assert Decimal(str(cliente["total"])) == Decimal("1500.00")
    por_marca = {m["nombre"]: Decimal(str(m["total"])) for m in cliente["marcas"]}
    assert por_marca == {"Marca 1": Decimal("1000.00"), "Marca 2": Decimal("500.00")}
    assert sum(Decimal(str(m["total"])) for m in cliente["marcas"]) == Decimal(
        str(cliente["total"])
    )


@pytest.mark.django_db
def test_ranking_ordenado_por_total_y_total_global_cuadra(operativo_client):
    for nombre, total in (("A", "1000.00"), ("B", "3000.00"), ("C", "2000.00")):
        cl = Cliente.objects.create(nombre=f"Agencia {nombre}")
        marca = Marca.objects.create(nombre=f"Marca {nombre}", cliente=cl)
        reservar(campania(marca=marca), date(2026, 10, 1), date(2026, 10, 31), total)
    datos = ingresos(operativo_client, "2026-10", "2026-10").json()
    nombres = [c["nombre"] for c in datos["clientes"]]
    assert nombres == ["Agencia B", "Agencia C", "Agencia A"]
    assert Decimal(str(datos["total"])) == Decimal("6000.00")
    assert sum(Decimal(str(c["total"])) for c in datos["clientes"]) == Decimal(str(datos["total"]))


@pytest.mark.django_db
def test_filtro_por_periodo_toma_solo_el_mes_del_reparto(operativo_client):
    # Reserva de sep a nov (91 días) por 100000; octubre del reparto = 34065.93 (HU-051).
    agencia = Cliente.objects.create(nombre="Agencia Larga")
    marca = Marca.objects.create(nombre="Marca Larga", cliente=agencia)
    reservar(campania(marca=marca), date(2026, 9, 1), date(2026, 11, 30), "100000.00")
    datos = ingresos(operativo_client, "2026-10", "2026-10").json()
    assert datos["periodos"] == [{"mes": "2026-10", "etiqueta": "Oct 2026"}]
    assert Decimal(str(datos["total"])) == Decimal("34065.93")


@pytest.mark.django_db
def test_reserva_cancelada_no_factura(operativo_client):
    agencia = Cliente.objects.create(nombre="Agencia Cancela")
    marca = Marca.objects.create(nombre="Marca Cancela", cliente=agencia)
    reservar(campania(marca=marca), date(2026, 10, 1), date(2026, 10, 31), "1000.00")
    reservar(
        campania(marca=marca), date(2026, 10, 1), date(2026, 10, 31), "5000.00", estado="cancelada"
    )
    datos = ingresos(operativo_client, "2026-10", "2026-10").json()
    assert Decimal(str(datos["total"])) == Decimal("1000.00")


@pytest.mark.regla("RN-014")
@pytest.mark.django_db
def test_cliente_de_facturacion_de_la_campania_reemplaza_al_de_la_marca(operativo_client):
    cliente_marca = Cliente.objects.create(nombre="Cliente de la marca")
    cliente_propio = Cliente.objects.create(nombre="Cliente propio")
    marca = Marca.objects.create(nombre="Marca RN14", cliente=cliente_marca)
    reservar(
        campania(marca=marca, cliente_fact=cliente_propio),
        date(2026, 10, 1),
        date(2026, 10, 31),
        "2000.00",
    )
    datos = ingresos(operativo_client, "2026-10", "2026-10").json()
    assert [c["cliente"] for c in datos["clientes"]] == [cliente_propio.id]


@pytest.mark.django_db
def test_periodo_invertido_devuelve_400(operativo_client):
    assert ingresos(operativo_client, "2026-11", "2026-10").status_code == 400


@pytest.mark.django_db
def test_periodo_con_formato_invalido_devuelve_400(operativo_client):
    assert ingresos(operativo_client, "2026-13").status_code == 400


@pytest.mark.django_db
def test_anonimo_no_puede_consultar():
    assert Client().get("/api/facturacion/ingresos/").status_code in (401, 403)
