"""Líneas de formato de la campaña: posiciones solicitadas por formato (HU-055)."""

import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.test import Client

from apps.campanias.models import Campania, LineaFormato
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva

URL = "/api/campanias/lineas-formato/"


def _post(client: Client, data: dict[str, Any]) -> Any:
    return client.post(URL, data=json.dumps(data), content_type="application/json")


def _patch(client: Client, pk: int, data: dict[str, Any]) -> Any:
    return client.patch(f"{URL}{pk}/", data=json.dumps(data), content_type="application/json")


def _formato(nombre: str = "Gran Formato Prueba", activo: bool = True) -> Formato:
    return Formato.objects.create(nombre=nombre, modalidad="fija", activo=activo)


def _reserva(campania: Campania, formato: Formato) -> Reserva:
    cartel = Cartel.objects.create(
        formato=formato,
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion=f"Dir {Cartel.objects.count() + 1}",
        capacidad=1,
    )
    reserva = Reserva(
        campania=campania,
        cartel=cartel,
        fecha_inicio=date(2026, 11, 1),
        fecha_fin=date(2026, 11, 30),
        precio_alquiler=Decimal("1000.00"),
    )
    reserva.save()
    return reserva


# --- Criterio 1: alta con formato y cantidad ---


@pytest.mark.django_db
def test_linea_con_formato_y_cantidad_se_guarda_y_se_lista(operativo_client):
    campania = Campania.objects.create()
    formato = _formato()
    respuesta = _post(
        operativo_client, {"campania": campania.pk, "formato": formato.pk, "cantidad": 100}
    )
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["formato_nombre"] == "Gran Formato Prueba"
    assert cuerpo["cantidad"] == 100
    assert cuerpo["activa"] is True

    lista = operativo_client.get(f"{URL}?campania={campania.pk}").json()
    assert [linea["id"] for linea in lista] == [cuerpo["id"]]


@pytest.mark.django_db
def test_lista_filtra_por_campania_y_oculta_las_quitadas(operativo_client):
    campania, otra = Campania.objects.create(), Campania.objects.create()
    visible = LineaFormato.objects.create(campania=campania, formato=_formato("A"))
    LineaFormato.objects.create(campania=campania, formato=_formato("B"), activa=False)
    LineaFormato.objects.create(campania=otra, formato=_formato("C"))
    lista = operativo_client.get(f"{URL}?campania={campania.pk}").json()
    assert [linea["id"] for linea in lista] == [visible.pk]


@pytest.mark.django_db
def test_lista_con_campania_invalida_se_rechaza(operativo_client):
    assert operativo_client.get(f"{URL}?campania=abc").status_code == 400


# --- Criterio 2: sin cantidad ---


@pytest.mark.django_db
def test_linea_sin_cantidad_se_acepta(operativo_client):
    campania = Campania.objects.create()
    respuesta = _post(operativo_client, {"campania": campania.pk, "formato": _formato().pk})
    assert respuesta.status_code == 201
    assert respuesta.json()["cantidad"] is None


@pytest.mark.django_db
def test_linea_con_cantidad_cero_se_rechaza(operativo_client):
    campania = Campania.objects.create()
    respuesta = _post(
        operativo_client, {"campania": campania.pk, "formato": _formato().pk, "cantidad": 0}
    )
    assert respuesta.status_code == 400
    assert "cantidad" in respuesta.json()


# --- Criterio 3: formato repetido ---


@pytest.mark.django_db
def test_formato_repetido_en_la_campania_se_rechaza_con_mensaje(operativo_client):
    campania = Campania.objects.create()
    formato = _formato()
    LineaFormato.objects.create(campania=campania, formato=formato, cantidad=10)
    respuesta = _post(operativo_client, {"campania": campania.pk, "formato": formato.pk})
    assert respuesta.status_code == 400
    assert respuesta.json()["formato"] == ["La campaña ya tiene una línea de Gran Formato Prueba."]
    assert LineaFormato.objects.count() == 1


@pytest.mark.django_db
def test_mismo_formato_en_otra_campania_se_acepta(operativo_client):
    formato = _formato()
    LineaFormato.objects.create(campania=Campania.objects.create(), formato=formato)
    respuesta = _post(
        operativo_client, {"campania": Campania.objects.create().pk, "formato": formato.pk}
    )
    assert respuesta.status_code == 201


@pytest.mark.django_db
def test_cambiar_el_formato_a_uno_ya_usado_se_rechaza(operativo_client):
    campania = Campania.objects.create()
    usado = _formato("Usado")
    LineaFormato.objects.create(campania=campania, formato=usado)
    linea = LineaFormato.objects.create(campania=campania, formato=_formato("Otro"))
    respuesta = _patch(operativo_client, linea.pk, {"formato": usado.pk})
    assert respuesta.status_code == 400
    assert "formato" in respuesta.json()


@pytest.mark.django_db
def test_formato_quitado_se_puede_volver_a_agregar(operativo_client):
    campania = Campania.objects.create()
    formato = _formato()
    LineaFormato.objects.create(campania=campania, formato=formato, activa=False)
    respuesta = _post(operativo_client, {"campania": campania.pk, "formato": formato.pk})
    assert respuesta.status_code == 201


@pytest.mark.django_db
def test_reactivar_una_linea_con_formato_ya_activo_se_rechaza(operativo_client):
    campania = Campania.objects.create()
    formato = _formato()
    quitada = LineaFormato.objects.create(campania=campania, formato=formato, activa=False)
    LineaFormato.objects.create(campania=campania, formato=formato)
    respuesta = _patch(operativo_client, quitada.pk, {"activa": True})
    assert respuesta.status_code == 400
    assert "formato" in respuesta.json()


@pytest.mark.django_db
def test_formato_inactivo_no_se_puede_agregar(operativo_client):
    campania = Campania.objects.create()
    respuesta = _post(
        operativo_client, {"campania": campania.pk, "formato": _formato(activo=False).pk}
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["formato"] == ["Seleccioná un formato activo."]


@pytest.mark.django_db
def test_linea_con_formato_que_se_inactivo_se_puede_editar(operativo_client):
    formato = _formato()
    linea = LineaFormato.objects.create(campania=Campania.objects.create(), formato=formato)
    formato.activo = False
    formato.save()
    respuesta = _patch(operativo_client, linea.pk, {"formato": formato.pk, "cantidad": 5})
    assert respuesta.status_code == 200
    assert respuesta.json()["cantidad"] == 5


# --- Criterio 4: cambiar o quitar no altera las reservas ---


@pytest.mark.django_db
def test_cambiar_cantidad_o_quitar_la_linea_no_altera_las_reservas(operativo_client):
    campania = Campania.objects.create()
    formato = _formato()
    linea = LineaFormato.objects.create(campania=campania, formato=formato, cantidad=10)
    reserva = _reserva(campania, formato)
    antes = Reserva.objects.values().get(pk=reserva.pk)

    assert _patch(operativo_client, linea.pk, {"cantidad": 3}).status_code == 200
    assert _patch(operativo_client, linea.pk, {"activa": False}).status_code == 200

    assert Reserva.objects.values().get(pk=reserva.pk) == antes
    linea.refresh_from_db()
    assert linea.cantidad == 3
    assert linea.activa is False


@pytest.mark.django_db
def test_la_campania_de_una_linea_no_se_puede_cambiar(operativo_client):
    campania = Campania.objects.create()
    linea = LineaFormato.objects.create(campania=campania, formato=_formato())
    otra = Campania.objects.create()
    respuesta = _patch(operativo_client, linea.pk, {"campania": otra.pk})
    assert respuesta.status_code == 200
    linea.refresh_from_db()
    assert linea.campania_id == campania.pk


# --- Permisos y baja lógica ---


@pytest.mark.django_db
def test_lineas_no_se_borran(operativo_client):
    linea = LineaFormato.objects.create(campania=Campania.objects.create(), formato=_formato())
    assert operativo_client.delete(f"{URL}{linea.pk}/").status_code == 405
    assert LineaFormato.objects.filter(pk=linea.pk).exists()


@pytest.mark.django_db
def test_lector_puede_ver_pero_no_crear(lector_client):
    campania = Campania.objects.create()
    assert lector_client.get(f"{URL}?campania={campania.pk}").status_code == 200
    respuesta = _post(lector_client, {"campania": campania.pk, "formato": _formato().pk})
    assert respuesta.status_code == 403
    assert not LineaFormato.objects.exists()


@pytest.mark.django_db
def test_str_de_la_linea():
    linea = LineaFormato(campania=Campania(), formato=Formato(nombre="LED Prueba"), cantidad=4)
    assert str(linea) == "LED Prueba: 4"
    linea.cantidad = None
    assert str(linea) == "LED Prueba: sin cantidad"
