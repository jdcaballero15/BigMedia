import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client

from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca


def crear_cliente(nombre: str = "Coca Cola") -> Cliente:
    return Cliente.objects.create(nombre=nombre, razon_social=f"{nombre} S.A.", tipo="directo")


def crear_marca(nombre: str = "Sprite", cliente: Cliente | None = None) -> Marca:
    return Marca.objects.create(nombre=nombre, cliente=cliente or crear_cliente())


def crear(client: Client, **campos: object):
    return client.post(
        "/api/campanias/campanias/",
        data=json.dumps(campos),
        content_type="application/json",
    )


def editar(client: Client, campania_id: int, **campos: object):
    return client.patch(
        f"/api/campanias/campanias/{campania_id}/",
        data=json.dumps(campos),
        content_type="application/json",
    )


@pytest.mark.django_db
def test_crear_campania_sin_datos_se_guarda(operativo_client):
    creada = crear(operativo_client)
    assert creada.status_code == 201
    cuerpo = creada.json()
    assert cuerpo["estado"] == "cotizada"
    assert Campania.objects.filter(pk=cuerpo["id"]).exists()


@pytest.mark.django_db
def test_campania_con_marca_muestra_cliente_que_factura(operativo_client):
    cliente = crear_cliente("Unilever")
    marca = crear_marca("Axe", cliente)
    creada = crear(operativo_client, marca=marca.pk)
    assert creada.status_code == 201
    cuerpo = creada.json()
    assert cuerpo["cliente_factura"] == cliente.pk
    assert cuerpo["cliente_factura_nombre"] == cliente.nombre_visible


@pytest.mark.django_db
def test_cliente_facturacion_propio_reemplaza_la_deduccion(operativo_client):
    cliente_marca = crear_cliente("Agencia Vieja")
    marca = crear_marca("Pepsi", cliente_marca)
    pagador = crear_cliente("Agencia Nueva")
    creada = crear(operativo_client, marca=marca.pk, cliente_facturacion=pagador.pk)
    assert creada.status_code == 201
    assert creada.json()["cliente_factura"] == pagador.pk


@pytest.mark.django_db
@pytest.mark.regla("RN-011")
def test_confirmar_exige_marca_cliente_y_fechas(operativo_client):
    creada = crear(operativo_client)
    campania_id = creada.json()["id"]

    incompleta = editar(operativo_client, campania_id, estado="confirmada")
    assert incompleta.status_code == 400
    assert "estado" in incompleta.json()
    assert Campania.objects.get(pk=campania_id).estado == "cotizada"

    marca = crear_marca("Quilmes")
    editar(
        operativo_client,
        campania_id,
        marca=marca.pk,
        fecha_inicio="2026-11-01",
        fecha_fin="2026-11-30",
    )
    completa = editar(operativo_client, campania_id, estado="confirmada")
    assert completa.status_code == 200
    assert Campania.objects.get(pk=campania_id).estado == "confirmada"


@pytest.mark.django_db
def test_canceladas_y_perdidas_siguen_en_la_lista(operativo_client):
    perdida = crear(operativo_client).json()["id"]
    cancelada = crear(operativo_client).json()["id"]
    editar(operativo_client, perdida, estado="perdida")
    editar(operativo_client, cancelada, estado="cancelada")

    estados = {
        fila["id"]: fila["estado"]
        for fila in operativo_client.get("/api/campanias/campanias/").json()
    }
    assert estados[perdida] == "perdida"
    assert estados[cancelada] == "cancelada"


@pytest.mark.django_db
def test_filtro_por_estado(operativo_client):
    cotizada = crear(operativo_client).json()["id"]
    otra = crear(operativo_client).json()["id"]
    editar(operativo_client, otra, estado="perdida")
    filtradas = operativo_client.get("/api/campanias/campanias/?estado=cotizada").json()
    assert [fila["id"] for fila in filtradas] == [cotizada]


@pytest.mark.django_db
def test_filtro_por_marca_y_busqueda(operativo_client):
    marca = crear_marca("Doritos")
    con_marca = crear(operativo_client, nombre="Lanzamiento Doritos", marca=marca.pk).json()["id"]
    crear(operativo_client, nombre="Otra cosa")

    por_marca = operativo_client.get(f"/api/campanias/campanias/?marca={marca.pk}").json()
    por_texto = operativo_client.get("/api/campanias/campanias/?q=doritos").json()

    assert [fila["id"] for fila in por_marca] == [con_marca]
    assert [fila["nombre"] for fila in por_texto] == ["Lanzamiento Doritos"]


@pytest.mark.django_db
def test_filtros_invalidos_se_rechazan(operativo_client):
    estado_malo = operativo_client.get("/api/campanias/campanias/?estado=otro")
    marca_mala = operativo_client.get("/api/campanias/campanias/?marca=abc")
    assert estado_malo.status_code == 400
    assert "estado" in estado_malo.json()
    assert marca_mala.status_code == 400
    assert "marca" in marca_mala.json()


@pytest.mark.django_db
def test_estado_invalido_se_rechaza(operativo_client):
    campania_id = crear(operativo_client).json()["id"]
    respuesta = editar(operativo_client, campania_id, estado="otro")
    assert respuesta.status_code == 400
    assert "estado" in respuesta.json()


@pytest.mark.django_db
def test_delete_no_esta_permitido(operativo_client):
    campania_id = crear(operativo_client).json()["id"]
    assert operativo_client.delete(f"/api/campanias/campanias/{campania_id}/").status_code == 405


@pytest.mark.django_db
def test_anonimo_y_sin_permiso_no_escriben(lector_client):
    anonimo = Client().post("/api/campanias/campanias/", data="{}", content_type="application/json")
    assert anonimo.status_code in (401, 403)

    denegado = lector_client.post(
        "/api/campanias/campanias/", data="{}", content_type="application/json"
    )
    assert denegado.status_code == 403
    assert Campania.objects.count() == 0


@pytest.mark.django_db
def test_operativo_sin_csrf_es_rechazado():
    user = get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    user.groups.add(Group.objects.get(name="Operativo"))
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    respuesta = client.post("/api/campanias/campanias/", data="{}", content_type="application/json")
    assert respuesta.status_code == 403
    assert Campania.objects.count() == 0
