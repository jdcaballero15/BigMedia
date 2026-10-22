import json
from datetime import date
from decimal import Decimal

import pytest
from django.test import Client

from apps.campanias.models import Campania
from apps.costos.models import Costo
from apps.inventario.models import Cartel, EstadoCartel, Formato, Proveedor, Zona
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


@pytest.mark.django_db
def test_lista_costos_sin_filtro_incluye_cartel_y_campania(operativo_client):
    res = reserva()
    res.campania.nombre = "Lanzamiento"
    res.campania.save()
    crear(operativo_client, reserva=res.pk, tipo="impresion", monto="200.00")
    fila = operativo_client.get("/api/costos/costos/").json()[0]
    assert fila["cartel_nombre"] == res.cartel.nombre_visible
    assert fila["campania"] == res.campania_id
    assert fila["campania_nombre"] == "Lanzamiento"


@pytest.mark.django_db
def test_lista_costos_campania_sin_nombre_muestra_numero(operativo_client):
    res = reserva()
    crear(operativo_client, reserva=res.pk, tipo="otro", monto="10.00")
    fila = operativo_client.get("/api/costos/costos/").json()[0]
    assert fila["campania_nombre"] == f"Campaña #{res.campania_id}"


@pytest.mark.django_db
def test_lista_costos_filtro_tipo_devuelve_solo_ese_tipo(operativo_client):
    res = reserva()
    crear(operativo_client, reserva=res.pk, tipo="impresion", monto="200.00")
    crear(operativo_client, reserva=res.pk, tipo="fijacion", monto="100.00")
    filas = operativo_client.get("/api/costos/costos/?tipo=fijacion").json()
    assert [fila["tipo"] for fila in filas] == ["fijacion"]


@pytest.mark.django_db
def test_lista_costos_filtro_tipo_invalido_da_400(operativo_client):
    respuesta = operativo_client.get("/api/costos/costos/?tipo=nada")
    assert respuesta.status_code == 400
    assert "tipo" in respuesta.json()


@pytest.mark.django_db
def test_lista_costos_filtro_proveedor_devuelve_solo_ese_proveedor(operativo_client):
    res = reserva()
    imprenta = Proveedor.objects.create(nombre="Imprenta Uno")
    crear(operativo_client, reserva=res.pk, tipo="impresion", monto="200.00", proveedor=imprenta.pk)
    crear(operativo_client, reserva=res.pk, tipo="fijacion", monto="100.00")
    filas = operativo_client.get(f"/api/costos/costos/?proveedor={imprenta.pk}").json()
    assert [fila["proveedor_nombre"] for fila in filas] == ["Imprenta Uno"]


@pytest.mark.django_db
def test_lista_costos_filtro_proveedor_no_numerico_da_400(operativo_client):
    respuesta = operativo_client.get("/api/costos/costos/?proveedor=abc")
    assert respuesta.status_code == 400
    assert "proveedor" in respuesta.json()
