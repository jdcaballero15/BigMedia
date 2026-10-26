"""Aviso de marcas duplicadas (HU-019)."""

import json
from typing import Any

import pytest

from apps.clientes.models import Cliente, Marca
from config.texto import distancia_edicion, normalizar_comparacion

URL_MARCAS = "/api/clientes/marcas/"
URL_CLIENTES = "/api/clientes/clientes/"


def _post(client, url: str, data: dict[str, Any]) -> Any:
    return client.post(url, data=json.dumps(data), content_type="application/json")


def _patch(client, url: str, data: dict[str, Any]) -> Any:
    return client.patch(url, data=json.dumps(data), content_type="application/json")


def _agencia(nombre: str = "Agencia Andes") -> Cliente:
    return Cliente.objects.create(nombre=nombre, tipo=Cliente.Tipo.INTERMEDIARIO)


def _marca(nombre: str, activo: bool = True) -> Marca:
    return Marca.objects.create(nombre=nombre, cliente=_agencia(), activo=activo)


def _alta_marca(client, nombre: str, **extra: Any) -> Any:
    return _post(client, URL_MARCAS, {"nombre": nombre, "cliente": _agencia("Otra").pk, **extra})


# --- Utilidades de texto ---


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Coca Cola", "coca cola"),
        ("  Coca   Colá ", "coca cola"),
        ("coca-cola", "coca cola"),
        ("Café & Té.", "cafe te"),
        ("", ""),
    ],
)
def test_normalizar_comparacion_ignora_mayusculas_tildes_puntuacion_y_espacios(texto, esperado):
    assert normalizar_comparacion(texto) == esperado


@pytest.mark.parametrize(
    ("a", "b", "esperado"),
    [
        ("coca cola", "coca cola", 0),
        ("coca cola", "coca kola", 1),
        ("coca cola", "coca col", 1),
        ("quilmes", "quimles", 2),
        ("abc", "xyz", 3),
        ("", "abc", 3),
    ],
)
def test_distancia_edicion_cuenta_cambios_de_a_un_caracter(a, b, esperado):
    assert distancia_edicion(a, b, tope=5) == esperado


def test_distancia_edicion_corta_al_superar_el_tope():
    assert distancia_edicion("aaaaaaaa", "bbbbbbbb", tope=2) == 3


# --- Criterio 1: aviso con la marca coincidente ---


@pytest.mark.django_db
@pytest.mark.parametrize("nombre", ["coca cola", "  COCA   COLÁ ", "Coca-Cola"])
def test_marca_nombre_igual_normalizado_avisa_con_coincidente(operativo_client, nombre):
    _marca("Coca Cola")
    respuesta = _alta_marca(operativo_client, nombre)
    assert respuesta.status_code == 400
    assert respuesta.json()["posible_duplicado"] == ["Coca Cola — Agencia Andes (activa)"]
    assert Marca.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("existente", "nuevo"),
    [("Coca Cola", "Coca Kola"), ("Quilmes Cristal", "Quilmes Crystl"), ("Ala", "Alas")],
)
def test_marca_error_de_tipeo_avisa(operativo_client, existente, nuevo):
    _marca(existente)
    assert _alta_marca(operativo_client, nuevo).status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("existente", "nuevo"),
    [
        ("Coca Cola", "Pepsi"),
        ("Ala", "Alfa Beta"),
        ("Fiat", "Fiesta"),
        ("Movistar", "Movil Star X"),
    ],
)
def test_marca_nombre_distinto_no_avisa(operativo_client, existente, nuevo):
    _marca(existente)
    assert _alta_marca(operativo_client, nuevo).status_code == 201


@pytest.mark.django_db
def test_marca_avisa_contra_inactiva_con_su_estado(operativo_client):
    _marca("Coca Cola", activo=False)
    respuesta = _alta_marca(operativo_client, "Coca Cola")
    assert respuesta.json()["posible_duplicado"] == ["Coca Cola — Agencia Andes (inactiva)"]


@pytest.mark.django_db
def test_marca_avisa_con_todas_las_coincidentes(operativo_client):
    _marca("Coca Cola")
    _marca("Coca-Kola")
    respuesta = _alta_marca(operativo_client, "Coca Cola")
    assert len(respuesta.json()["posible_duplicado"]) == 2


# --- Criterio 2: confirmar que es otra marca ---


@pytest.mark.django_db
def test_marca_confirmada_distinta_se_guarda(operativo_client):
    _marca("Coca Cola")
    respuesta = _alta_marca(operativo_client, "Coca Kola", confirmar_distinta=True)
    assert respuesta.status_code == 201
    assert "confirmar_distinta" not in respuesta.json()
    assert Marca.objects.filter(nombre="Coca Kola").exists()


# --- Edición ---


@pytest.mark.django_db
def test_marca_edicion_sin_cambio_de_nombre_no_avisa(operativo_client):
    _marca("Coca Cola")
    otra = _marca("Coca Kola")
    respuesta = _patch(operativo_client, f"{URL_MARCAS}{otra.pk}/", {"activo": False})
    assert respuesta.status_code == 200


@pytest.mark.django_db
def test_marca_edicion_no_se_compara_consigo_misma(operativo_client):
    marca = _marca("Coca Cola")
    respuesta = _patch(operativo_client, f"{URL_MARCAS}{marca.pk}/", {"nombre": "Coca-Cola"})
    assert respuesta.status_code == 200


@pytest.mark.django_db
def test_marca_edicion_con_nombre_de_otra_avisa(operativo_client):
    _marca("Coca Cola")
    otra = _marca("Pepsi")
    respuesta = _patch(operativo_client, f"{URL_MARCAS}{otra.pk}/", {"nombre": "Coca Cola"})
    assert respuesta.status_code == 400
    assert Marca.objects.get(pk=otra.pk).nombre == "Pepsi"


# --- Marca homónima del cliente directo (HU-018) ---


@pytest.mark.django_db
def test_cliente_directo_marca_homonima_duplicada_avisa_y_confirmado_se_guarda(operativo_client):
    _marca("Coca Cola")
    datos = {"nombre": "Coca-Cola", "tipo": "directo"}

    respuesta = _post(operativo_client, URL_CLIENTES, datos)
    assert respuesta.status_code == 400
    assert respuesta.json()["posible_duplicado"] == ["Coca Cola — Agencia Andes (activa)"]
    assert not Cliente.objects.filter(nombre="Coca-Cola").exists()

    respuesta = _post(operativo_client, URL_CLIENTES, {**datos, "confirmar_distinta": True})
    assert respuesta.status_code == 201
    assert Marca.objects.filter(nombre="Coca-Cola").exists()


@pytest.mark.django_db
def test_cliente_intermediario_con_nombre_de_marca_no_avisa(operativo_client):
    _marca("Coca Cola")
    datos = {"nombre": "Coca Cola", "tipo": "intermediario"}
    assert _post(operativo_client, URL_CLIENTES, datos).status_code == 201


@pytest.mark.django_db
def test_cliente_directo_edicion_no_avisa(operativo_client):
    _marca("Coca Cola")
    cliente = Cliente.objects.create(nombre="Pepsi", tipo=Cliente.Tipo.DIRECTO)
    respuesta = _patch(operativo_client, f"{URL_CLIENTES}{cliente.pk}/", {"nombre": "Coca Cola"})
    assert respuesta.status_code == 200
