import json
from typing import Any

import pytest

from apps.clientes.models import Cliente, Marca, Rubro

URL = "/api/clientes/marcas/"


def _post(client, data) -> Any:
    return client.post(URL, data=json.dumps(data), content_type="application/json")


def _patch(client, pk, data) -> Any:
    return client.patch(f"{URL}{pk}/", data=json.dumps(data), content_type="application/json")


def _cliente(nombre="Agencia Sur", **datos: Any) -> Cliente:
    valores = {"razon_social": f"{nombre} SA", "tipo": "intermediario"} | datos
    return Cliente.objects.create(nombre=nombre, **valores)


@pytest.mark.django_db
def test_alta_marca_con_cliente_y_rubro_devuelve_nombres_legibles(operativo_client):
    cliente = _cliente()
    rubro = Rubro.objects.create(nombre="Bebidas")

    response = _post(
        operativo_client, {"nombre": " Gaseosa Andes ", "cliente": cliente.pk, "rubro": rubro.pk}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["nombre"] == "Gaseosa Andes"
    assert body["cliente"] == cliente.pk
    assert body["cliente_nombre"] == "Agencia Sur"
    assert body["rubro"] == rubro.pk
    assert body["rubro_nombre"] == "Bebidas"
    assert body["activo"] is True
    assert set(body) == {
        "id",
        "nombre",
        "cliente",
        "cliente_nombre",
        "rubro",
        "rubro_nombre",
        "grupo",
        "grupo_nombre",
        "activo",
        "creado_en",
        "actualizado_en",
    }


@pytest.mark.django_db
def test_alta_marca_sin_rubro_se_acepta(operativo_client):
    response = _post(operativo_client, {"nombre": "Sin rubro", "cliente": _cliente().pk})

    assert response.status_code == 201
    assert response.json()["rubro"] is None
    assert response.json()["rubro_nombre"] is None


@pytest.mark.django_db
@pytest.mark.parametrize("cliente", [None, "omitido"])
def test_alta_marca_sin_cliente_se_rechaza(operativo_client, cliente):
    payload = {"nombre": "Huérfana"}
    if cliente != "omitido":
        payload["cliente"] = cliente

    response = _post(operativo_client, payload)

    assert response.status_code == 400
    assert response.json()["cliente"] == ["Seleccioná un cliente."]
    assert Marca.objects.count() == 0


@pytest.mark.django_db
def test_alta_marca_sin_nombre_se_rechaza(operativo_client):
    response = _post(operativo_client, {"nombre": " ", "cliente": _cliente().pk})

    assert response.status_code == 400
    assert response.json()["nombre"] == ["Ingresá un nombre."]


@pytest.mark.django_db
def test_alta_marca_con_cliente_inactivo_se_rechaza(operativo_client):
    cliente = _cliente(activo=False)

    response = _post(operativo_client, {"nombre": "Nueva", "cliente": cliente.pk})

    assert response.status_code == 400
    assert response.json()["cliente"] == ["Seleccioná un cliente activo."]
    assert Marca.objects.count() == 0


@pytest.mark.django_db
def test_alta_marca_con_rubro_inactivo_se_rechaza(operativo_client):
    rubro = Rubro.objects.create(nombre="Viejo", activo=False)

    response = _post(operativo_client, {"nombre": "N", "cliente": _cliente().pk, "rubro": rubro.pk})

    assert response.status_code == 400
    assert response.json()["rubro"] == ["Seleccioná un rubro activo."]


@pytest.mark.django_db
def test_editar_marca_cambiando_a_cliente_inactivo_se_rechaza(operativo_client):
    marca = Marca.objects.create(nombre="M", cliente=_cliente())
    inactivo = _cliente(nombre="Inactivo", activo=False)

    response = _patch(operativo_client, marca.pk, {"cliente": inactivo.pk})

    assert response.status_code == 400
    assert response.json()["cliente"] == ["Seleccioná un cliente activo."]
    marca.refresh_from_db()
    assert marca.cliente.nombre == "Agencia Sur"


@pytest.mark.django_db
def test_editar_marca_de_cliente_y_rubro_ya_inactivos_los_conserva(operativo_client):
    cliente = _cliente()
    rubro = Rubro.objects.create(nombre="Bebidas")
    marca = Marca.objects.create(nombre="M", cliente=cliente, rubro=rubro)
    Cliente.objects.filter(pk=cliente.pk).update(activo=False)
    Rubro.objects.filter(pk=rubro.pk).update(activo=False)

    response = _patch(
        operativo_client, marca.pk, {"nombre": "M2", "cliente": cliente.pk, "rubro": rubro.pk}
    )

    assert response.status_code == 200
    assert response.json()["nombre"] == "M2"


@pytest.mark.django_db
def test_lista_marcas_de_un_cliente_intermediario_muestra_todas_las_suyas(lector_client):
    agencia = _cliente(nombre="Agencia")
    otra = _cliente(nombre="Otra")
    for nombre in ("Uno", "Dos", "Tres"):
        Marca.objects.create(nombre=nombre, cliente=agencia)
    Marca.objects.create(nombre="Ajena", cliente=otra)

    response = lector_client.get(URL, {"cliente": agencia.pk})

    assert response.status_code == 200
    assert [m["nombre"] for m in response.json()] == ["Dos", "Tres", "Uno"]


@pytest.mark.django_db
def test_lista_marcas_filtra_por_rubro_y_busca_por_nombre_sin_tildes(lector_client):
    cliente = _cliente()
    bebidas = Rubro.objects.create(nombre="Bebidas")
    Marca.objects.create(nombre="Jugos Cuyanos", cliente=cliente, rubro=bebidas)
    Marca.objects.create(nombre="Café Mendoza", cliente=cliente, rubro=bebidas)
    Marca.objects.create(nombre="Cafetería", cliente=cliente)

    por_rubro = lector_client.get(URL, {"rubro": bebidas.pk}).json()
    por_texto = lector_client.get(URL, {"q": "CAFE"}).json()
    combinado = lector_client.get(URL, {"q": "cafe", "rubro": bebidas.pk}).json()

    assert [m["nombre"] for m in por_rubro] == ["Café Mendoza", "Jugos Cuyanos"]
    assert {m["nombre"] for m in por_texto} == {"Café Mendoza", "Cafetería"}
    assert [m["nombre"] for m in combinado] == ["Café Mendoza"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("campo", "valor"), [("cliente", "abc"), ("rubro", "0"), ("cliente", "-1")]
)
def test_lista_marcas_con_filtro_no_numerico_devuelve_error_del_campo(lector_client, campo, valor):
    response = lector_client.get(URL, {campo: valor})

    assert response.status_code == 400
    assert campo in response.json()


@pytest.mark.django_db
def test_marca_se_inactiva_y_nunca_se_borra(operativo_client):
    marca = Marca.objects.create(nombre="M", cliente=_cliente())

    assert operativo_client.delete(f"{URL}{marca.pk}/").status_code == 405
    assert _patch(operativo_client, marca.pk, {"activo": False}).status_code == 200
    assert operativo_client.get(URL).json() == []
    assert len(operativo_client.get(URL, {"incluir_inactivos": "1"}).json()) == 1
    assert Marca.objects.filter(pk=marca.pk, activo=False).exists()


@pytest.mark.django_db
def test_marca_de_cliente_sin_nombre_muestra_el_nombre_visible_del_cliente(lector_client):
    cliente = Cliente.objects.create(nombre="")
    Marca.objects.create(nombre="M", cliente=cliente)

    (marca,) = lector_client.get(URL).json()

    assert marca["cliente_nombre"] == f"Cliente sin nombre #{cliente.pk}"
