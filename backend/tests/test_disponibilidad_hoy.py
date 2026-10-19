"""Vista de ocupación de hoy (HU-041)."""

from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

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


def reservar(car: Cartel, estado: str = "confirmada", dias: int = 0) -> Reserva:
    hoy = timezone.localdate()
    r = Reserva(
        campania=Campania.objects.create(),
        cartel=car,
        fecha_inicio=hoy - timedelta(days=1),
        fecha_fin=hoy + timedelta(days=dias),
        estado=estado,
    )
    r.save()
    return r


def filas(client: Client, query: str = ""):
    respuesta = client.get(f"/api/reservas/disponibilidad/{query}")
    assert respuesta.status_code == 200, respuesta.content
    return respuesta.json()


@pytest.mark.django_db
def test_excluye_carteles_de_baja(operativo_client):
    activo = cartel()
    cartel(baja=True)
    ids = {fila["id"] for fila in filas(operativo_client)}
    assert ids == {activo.id}


@pytest.mark.django_db
def test_cuenta_ocupados_de_hoy_ignorando_canceladas(operativo_client):
    car = cartel(capacidad=20)
    for _ in range(12):
        reservar(car, estado="confirmada")
    reservar(car, estado="cancelada")  # no cuenta
    fila = next(f for f in filas(operativo_client) if f["id"] == car.id)
    assert fila["capacidad"] == 20
    assert fila["ocupados"] == 12
    assert fila["libre"] is True


@pytest.mark.django_db
def test_capacidad_1_ocupado_no_esta_libre(operativo_client):
    car = cartel(capacidad=1)
    reservar(car, estado="confirmada")
    fila = next(f for f in filas(operativo_client) if f["id"] == car.id)
    assert fila["ocupados"] == 1
    assert fila["libre"] is False


@pytest.mark.django_db
def test_acceso_rapido_libres_y_ocupados(operativo_client):
    libre = cartel(capacidad=1)
    ocupado = cartel(capacidad=1)
    reservar(ocupado, estado="confirmada")
    libres = {f["id"] for f in filas(operativo_client, "?ocupacion=libres")}
    ocupados = {f["id"] for f in filas(operativo_client, "?ocupacion=ocupados")}
    assert libre.id in libres
    assert ocupado.id not in libres
    assert ocupado.id in ocupados
    assert libre.id not in ocupados


@pytest.mark.django_db
def test_filtra_por_formato_y_modalidad(operativo_client):
    led = cartel(formato="LED")  # digital
    carteleras = cartel(formato="Carteleras")  # fija
    por_formato = {f["id"] for f in filas(operativo_client, f"?formato={led.formato_id}")}
    por_modalidad = {f["id"] for f in filas(operativo_client, "?modalidad=digital")}
    assert por_formato == {led.id}
    assert led.id in por_modalidad
    assert carteleras.id not in por_modalidad


@pytest.mark.django_db
def test_orden_por_cupos_libres(operativo_client):
    lleno = cartel(capacidad=1)
    reservar(lleno, estado="confirmada")
    libre = cartel(capacidad=5)
    resultado = [f["id"] for f in filas(operativo_client)]
    assert resultado.index(libre.id) < resultado.index(lleno.id)


@pytest.mark.django_db
def test_nombre_visible_segun_formato_y_tamano(operativo_client):
    sextuple = cartel(capacidad=6, formato="Séxtuples")
    con_tamano = cartel(formato="Carteleras")
    con_tamano.tamano = "6x3"
    con_tamano.save()
    por_id = {f["id"]: f["nombre_visible"] for f in filas(operativo_client)}
    assert "6 slots" in por_id[sextuple.id]
    assert por_id[con_tamano.id].endswith("· 6x3")


@pytest.mark.django_db
def test_anonimo_no_puede_consultar():
    respuesta = Client().get("/api/reservas/disponibilidad/")
    assert respuesta.status_code in (401, 403)
