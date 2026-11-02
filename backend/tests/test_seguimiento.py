"""Seguimiento de lo solicitado, reservado y faltante por formato (HU-058, criterios 1 y 2)."""

from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.test import Client

from apps.campanias.models import Campania, LineaFormato
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva

URL = "/api/reservas/seguimiento/"


def _formato(nombre: str) -> Formato:
    return Formato.objects.create(nombre=nombre, modalidad="fija")


def _reservas(
    campania: Campania, formato: Formato, cantidad: int, estado: str = "pendiente"
) -> None:
    for _ in range(cantidad):
        cartel = Cartel.objects.create(
            formato=formato,
            zona=Zona.objects.get(nombre="Ciudad"),
            estado=EstadoCartel.objects.get(codigo="activo"),
            direccion=f"Dir {Cartel.objects.count() + 1}",
            capacidad=1,
        )
        Reserva(
            campania=campania,
            cartel=cartel,
            fecha_inicio=date(2026, 11, 1),
            fecha_fin=date(2026, 11, 30),
            precio_alquiler=Decimal("100.00"),
            estado=estado,
        ).save()


def _seguimiento(client: Client, campania: Campania) -> Any:
    respuesta = client.get(f"{URL}?campania={campania.pk}")
    assert respuesta.status_code == 200
    return respuesta.json()


@pytest.mark.django_db
def test_seguimiento_con_100_solicitadas_y_60_reservadas_faltan_40(operativo_client):
    campania = Campania.objects.create()
    formato = _formato("Gran Formato Prueba")
    linea = LineaFormato.objects.create(campania=campania, formato=formato, cantidad=100)
    _reservas(campania, formato, 30, estado="pendiente")
    _reservas(campania, formato, 25, estado="confirmada")
    _reservas(campania, formato, 5, estado="finalizada")
    assert _seguimiento(operativo_client, campania) == [
        {
            "linea": linea.pk,
            "formato": formato.pk,
            "formato_nombre": "Gran Formato Prueba",
            "solicitadas": 100,
            "reservadas": 60,
            "faltantes": 40,
            "excedente": 0,
        }
    ]


@pytest.mark.django_db
def test_seguimiento_de_linea_sin_cantidad_muestra_solo_reservadas(operativo_client):
    campania = Campania.objects.create()
    formato = _formato("LED Prueba")
    LineaFormato.objects.create(campania=campania, formato=formato)
    _reservas(campania, formato, 3)
    fila = _seguimiento(operativo_client, campania)[0]
    assert fila["solicitadas"] is None
    assert fila["reservadas"] == 3
    assert fila["faltantes"] is None
    assert fila["excedente"] is None


@pytest.mark.django_db
def test_seguimiento_no_cuenta_canceladas_ni_otras_campanias(operativo_client):
    campania = Campania.objects.create()
    formato = _formato("Gran Formato Prueba")
    LineaFormato.objects.create(campania=campania, formato=formato, cantidad=5)
    _reservas(campania, formato, 2)
    _reservas(campania, formato, 4, estado="cancelada")
    _reservas(Campania.objects.create(), formato, 3)
    fila = _seguimiento(operativo_client, campania)[0]
    assert (fila["reservadas"], fila["faltantes"]) == (2, 3)


@pytest.mark.django_db
def test_seguimiento_con_mas_reservadas_que_solicitadas_muestra_excedente(operativo_client):
    campania = Campania.objects.create()
    formato = _formato("Gran Formato Prueba")
    LineaFormato.objects.create(campania=campania, formato=formato, cantidad=2)
    _reservas(campania, formato, 7)
    fila = _seguimiento(operativo_client, campania)[0]
    assert (fila["faltantes"], fila["excedente"]) == (0, 5)


@pytest.mark.django_db
def test_seguimiento_muestra_aparte_los_formatos_sin_linea(operativo_client):
    campania = Campania.objects.create()
    con_linea, sin_linea = _formato("A Con línea"), _formato("B Sin línea")
    LineaFormato.objects.create(campania=campania, formato=con_linea, cantidad=1)
    _reservas(campania, sin_linea, 2)
    filas = _seguimiento(operativo_client, campania)
    assert [fila["formato_nombre"] for fila in filas] == ["A Con línea", "B Sin línea"]
    assert filas[1] == {
        "linea": None,
        "formato": sin_linea.pk,
        "formato_nombre": "B Sin línea",
        "solicitadas": None,
        "reservadas": 2,
        "faltantes": None,
        "excedente": None,
    }


@pytest.mark.django_db
def test_seguimiento_ignora_las_lineas_quitadas(operativo_client):
    campania = Campania.objects.create()
    formato = _formato("Gran Formato Prueba")
    LineaFormato.objects.create(campania=campania, formato=formato, cantidad=9, activa=False)
    _reservas(campania, formato, 1)
    fila = _seguimiento(operativo_client, campania)[0]
    assert (fila["linea"], fila["solicitadas"], fila["reservadas"]) == (None, None, 1)


@pytest.mark.django_db
def test_seguimiento_de_campania_sin_lineas_ni_reservas_es_vacio(lector_client):
    assert _seguimiento(lector_client, Campania.objects.create()) == []


@pytest.mark.django_db
@pytest.mark.parametrize("valor", ["", "abc", "0"])
def test_seguimiento_con_campania_invalida_se_rechaza(operativo_client, valor):
    respuesta = operativo_client.get(f"{URL}?campania={valor}")
    assert respuesta.status_code == 400
    assert "campania" in respuesta.json()


@pytest.mark.django_db
def test_seguimiento_de_campania_inexistente_da_404(operativo_client):
    assert operativo_client.get(f"{URL}?campania=999999").status_code == 404
