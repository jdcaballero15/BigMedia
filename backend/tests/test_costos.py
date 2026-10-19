import json
from datetime import date
from decimal import Decimal

import pytest
from django.test import Client

from apps.campanias.models import Campania
from apps.costos.models import Costo
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva


def reserva(total_alquiler: str = "1000.00") -> Reserva:
    cartel = Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion=f"Dir {Cartel.objects.count() + 1}",
        capacidad=1,
        tarifa_lista=Decimal(total_alquiler),
    )
    r = Reserva(
        campania=Campania.objects.create(),
        cartel=cartel,
        fecha_inicio=date(2026, 11, 1),
        fecha_fin=date(2026, 11, 30),
        precio_alquiler=Decimal(total_alquiler),
    )
    r.save()
    return r


def crear(client: Client, **campos: object):
    return client.post(
        "/api/costos/costos/", data=json.dumps(campos), content_type="application/json"
    )


def margen(client: Client, reserva_id: int):
    return client.get(f"/api/costos/margen/?reserva={reserva_id}")


@pytest.mark.django_db
def test_crear_costo_en_reserva(operativo_client):
    res = reserva()
    creado = crear(operativo_client, reserva=res.pk, tipo="impresion", monto="200.00")
    assert creado.status_code == 201
    assert Costo.objects.filter(reserva=res, tipo="impresion").exists()


@pytest.mark.django_db
def test_rechaza_sin_tipo_o_monto_no_positivo(operativo_client):
    res = reserva()
    sin_tipo = crear(operativo_client, reserva=res.pk, monto="100.00")
    monto_cero = crear(operativo_client, reserva=res.pk, tipo="otro", monto="0.00")
    assert sin_tipo.status_code == 400
    assert "tipo" in sin_tipo.json()
    assert monto_cero.status_code == 400
    assert "monto" in monto_cero.json()


@pytest.mark.django_db
def test_margen_de_reserva(operativo_client):
    res = reserva("1000.00")
    crear(operativo_client, reserva=res.pk, tipo="impresion", monto="400.00")
    crear(operativo_client, reserva=res.pk, tipo="fijacion", monto="200.00")
    datos = margen(operativo_client, res.pk).json()
    assert Decimal(datos["ingreso"]) == Decimal("1000.00")
    assert Decimal(datos["costo"]) == Decimal("600.00")
    assert Decimal(datos["margen"]) == Decimal("400.00")
    assert datos["porcentaje"] == 40.0


@pytest.mark.django_db
def test_anulado_no_suma_al_margen(operativo_client):
    res = reserva("1000.00")
    creado = crear(operativo_client, reserva=res.pk, tipo="impresion", monto="400.00").json()
    anulado = operativo_client.patch(
        f"/api/costos/costos/{creado['id']}/",
        data=json.dumps({"anulado": True, "motivo_anulacion": "error de carga"}),
        content_type="application/json",
    )
    assert anulado.status_code == 200
    datos = margen(operativo_client, res.pk).json()
    assert Decimal(datos["costo"]) == Decimal("0.00")
    assert Decimal(datos["margen"]) == Decimal("1000.00")


@pytest.mark.django_db
def test_sin_ingreso_no_rompe(operativo_client):
    res = reserva("0.00")
    res.precio_alquiler = Decimal("0.00")
    res.save()
    datos = margen(operativo_client, res.pk).json()
    assert Decimal(datos["ingreso"]) == Decimal("0.00")
    assert datos["porcentaje"] is None


@pytest.mark.django_db
def test_sin_costos_margen_igual_al_ingreso(operativo_client):
    res = reserva("1000.00")
    datos = margen(operativo_client, res.pk).json()
    assert Decimal(datos["margen"]) == Decimal("1000.00")


@pytest.mark.django_db
def test_delete_no_permitido(operativo_client):
    res = reserva()
    creado = crear(operativo_client, reserva=res.pk, tipo="otro", monto="10.00").json()
    assert operativo_client.delete(f"/api/costos/costos/{creado['id']}/").status_code == 405


@pytest.mark.django_db
def test_anonimo_y_sin_permiso(lector_client):
    res = reserva()
    cuerpo = json.dumps({"reserva": res.pk, "tipo": "otro", "monto": "10.00"})
    assert Client().post(
        "/api/costos/costos/", data=cuerpo, content_type="application/json"
    ).status_code in (401, 403)
    assert (
        lector_client.post(
            "/api/costos/costos/", data=cuerpo, content_type="application/json"
        ).status_code
        == 403
    )
    assert Costo.objects.count() == 0
