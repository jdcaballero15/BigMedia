"""Baja lógica en todo el sistema (HU-006, criterios 1 a 3)."""

import json
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca, Rubro
from apps.costos.models import Costo
from apps.inventario.models import Cartel, EstadoCartel, Formato, Proveedor, Zona
from apps.reservas.models import Reserva

RUTAS_CON_DETALLE = [
    "/api/inventario/proveedores/1/",
    "/api/inventario/formatos/1/",
    "/api/inventario/zonas/1/",
    "/api/inventario/estados/1/",
    "/api/inventario/carteles/1/",
    "/api/clientes/rubros/1/",
    "/api/clientes/clientes/1/",
    "/api/clientes/marcas/1/",
    "/api/campanias/campanias/1/",
    "/api/reservas/reservas/1/",
    "/api/costos/costos/1/",
    "/api/usuarios/usuarios/1/",
    "/api/auditoria/registros/1/",
]


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_superuser(username="adm", password="clave-segura-123")
    client = Client()
    client.force_login(user)
    return client


def cartel(baja: bool = False) -> Cartel:
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="baja" if baja else "activo"),
        direccion=f"Dir {Cartel.objects.count() + 1}",
        capacidad=1,
        tarifa_lista="100.00",
    )


def marca(nombre: str = "Sprite", activa: bool = True, rubro: Rubro | None = None) -> Marca:
    cliente = Cliente.objects.create(nombre=f"Cliente {nombre}", tipo="intermediario")
    return Marca.objects.create(nombre=nombre, cliente=cliente, rubro=rubro, activo=activa)


def reservar(car: Cartel, camp: Campania, inicio: date, fin: date) -> Reserva:
    r = Reserva(
        campania=camp,
        cartel=car,
        fecha_inicio=inicio,
        fecha_fin=fin,
        precio_alquiler=Decimal("1000.00"),
        estado="confirmada",
    )
    r.save()
    return r


def enviar(client: Client, metodo: str, url: str, **campos: object):
    return getattr(client, metodo)(url, data=json.dumps(campos), content_type="application/json")


# Criterio 1: no existe la acción de eliminar en la API.


@pytest.mark.django_db
@pytest.mark.parametrize("url", RUTAS_CON_DETALLE)
def test_api_delete_cualquier_entidad_devuelve_405(admin_client, url):
    assert admin_client.delete(url).status_code == 405


# Criterio 2: un inactivo no se ofrece ni se acepta en una carga nueva.


@pytest.mark.django_db
@pytest.mark.parametrize("campo", ["marca", "cliente_facturacion"])
def test_campania_con_inactivo_nuevo_rechaza(operativo_client, campo):
    inactiva = marca(activa=False)
    cliente = inactiva.cliente
    cliente.activo = False
    cliente.save()
    valor = inactiva.pk if campo == "marca" else cliente.pk

    respuesta = enviar(operativo_client, "post", "/api/campanias/campanias/", **{campo: valor})

    assert respuesta.status_code == 400
    assert campo in respuesta.json()


@pytest.mark.django_db
def test_campania_con_marca_que_se_inactivo_despues_permite_editar(operativo_client):
    original = marca()
    camp = Campania.objects.create(marca=original, cliente_facturacion=original.cliente)
    Marca.objects.filter(pk=original.pk).update(activo=False)
    Cliente.objects.filter(pk=original.cliente_id).update(activo=False)

    respuesta = enviar(
        operativo_client,
        "patch",
        f"/api/campanias/campanias/{camp.pk}/",
        nombre="Verano",
        marca=original.pk,
        cliente_facturacion=original.cliente_id,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Verano"


@pytest.mark.django_db
def test_costo_con_proveedor_inactivo_nuevo_rechaza(operativo_client):
    res = reservar(cartel(), Campania.objects.create(), date(2026, 11, 1), date(2026, 11, 30))
    proveedor = Proveedor.objects.create(nombre="Imprenta vieja", activo=False)

    respuesta = enviar(
        operativo_client,
        "post",
        "/api/costos/costos/",
        reserva=res.pk,
        tipo="impresion",
        proveedor=proveedor.pk,
        monto="100.00",
    )

    assert respuesta.status_code == 400
    assert "proveedor" in respuesta.json()


@pytest.mark.django_db
def test_costo_con_proveedor_que_se_inactivo_despues_permite_editar(operativo_client):
    res = reservar(cartel(), Campania.objects.create(), date(2026, 11, 1), date(2026, 11, 30))
    proveedor = Proveedor.objects.create(nombre="Imprenta")
    costo = Costo.objects.create(
        reserva=res, tipo="impresion", proveedor=proveedor, monto="100.00", fecha=date(2026, 11, 1)
    )
    Proveedor.objects.filter(pk=proveedor.pk).update(activo=False)

    respuesta = enviar(
        operativo_client,
        "patch",
        f"/api/costos/costos/{costo.pk}/",
        proveedor=proveedor.pk,
        monto="150.00",
    )

    assert respuesta.status_code == 200
    assert Decimal(respuesta.json()["monto"]) == Decimal("150.00")


@pytest.mark.django_db
def test_reserva_de_cartel_que_se_dio_de_baja_despues_permite_editar(operativo_client):
    car = cartel()
    res = reservar(car, Campania.objects.create(), date(2026, 11, 1), date(2026, 11, 30))
    Cartel.objects.filter(pk=car.pk).update(estado=EstadoCartel.objects.get(codigo="baja"))

    respuesta = enviar(
        operativo_client,
        "patch",
        f"/api/reservas/reservas/{res.pk}/",
        cartel=car.pk,
        precio_alquiler="1200.00",
    )

    assert respuesta.status_code == 200
    assert Decimal(respuesta.json()["precio_alquiler"]) == Decimal("1200.00")


@pytest.mark.django_db
def test_reserva_cambiar_a_cartel_de_baja_rechaza(operativo_client):
    res = reservar(cartel(), Campania.objects.create(), date(2026, 11, 1), date(2026, 11, 30))

    respuesta = enviar(
        operativo_client, "patch", f"/api/reservas/reservas/{res.pk}/", cartel=cartel(baja=True).pk
    )

    assert respuesta.status_code == 400
    assert "cartel" in respuesta.json()


@pytest.mark.django_db
def test_cartel_expone_si_esta_de_baja(operativo_client):
    activo, de_baja = cartel(), cartel(baja=True)

    filas = {
        f["id"]: f for f in operativo_client.get("/api/inventario/carteles/?incluir_bajas=1").json()
    }

    assert filas[activo.pk]["es_baja"] is False
    assert filas[de_baja.pk]["es_baja"] is True


# Criterio 3: un inactivo con reservas pasadas sigue en los reportes históricos.


@pytest.mark.django_db
def test_reporte_ocupacion_cartel_de_baja_con_reservas_en_el_periodo_lo_incluye(operativo_client):
    car = cartel()
    reservar(car, Campania.objects.create(), date(2026, 11, 1), date(2026, 11, 15))
    Cartel.objects.filter(pk=car.pk).update(estado=EstadoCartel.objects.get(codigo="baja"))

    datos = operativo_client.get(
        "/api/reservas/reporte-ocupacion/?desde=2026-11&hasta=2026-11"
    ).json()

    fila = next(f for f in datos["carteles"] if f["id"] == car.pk)
    assert fila["de_baja"] is True
    assert fila["ocupacion"] == 50.0


@pytest.mark.django_db
def test_reporte_ocupacion_cartel_de_baja_sin_reservas_en_el_periodo_lo_excluye(
    operativo_client,
):
    car = cartel(baja=True)
    reservar(car, Campania.objects.create(), date(2026, 10, 1), date(2026, 10, 15))
    activo = cartel()

    datos = operativo_client.get(
        "/api/reservas/reporte-ocupacion/?desde=2026-11&hasta=2026-11"
    ).json()

    assert [f["id"] for f in datos["carteles"]] == [activo.pk]
    assert datos["carteles"][0]["de_baja"] is False


@pytest.mark.django_db
def test_reporte_ingresos_cliente_y_marca_inactivos_los_incluye(gerencia_client):
    vieja = marca("Marca vieja")
    reservar(cartel(), Campania.objects.create(marca=vieja), date(2026, 11, 1), date(2026, 11, 30))
    Marca.objects.filter(pk=vieja.pk).update(activo=False)
    Cliente.objects.filter(pk=vieja.cliente_id).update(activo=False)

    datos = gerencia_client.get("/api/facturacion/ingresos/?desde=2026-11&hasta=2026-11").json()

    assert [c["cliente"] for c in datos["clientes"]] == [vieja.cliente_id]
    assert [m["nombre"] for m in datos["clientes"][0]["marcas"]] == ["Marca vieja"]


@pytest.mark.django_db
def test_reporte_por_rubro_rubro_inactivo_lo_incluye(gerencia_client):
    rubro = Rubro.objects.create(nombre="Rubro viejo")
    vieja = marca("Marca vieja", rubro=rubro)
    reservar(cartel(), Campania.objects.create(marca=vieja), date(2026, 11, 1), date(2026, 11, 30))
    Rubro.objects.filter(pk=rubro.pk).update(activo=False)

    datos = gerencia_client.get("/api/facturacion/por-rubro/?desde=2026-11&hasta=2026-11").json()

    assert "Rubro viejo" in json.dumps(datos, ensure_ascii=False)
