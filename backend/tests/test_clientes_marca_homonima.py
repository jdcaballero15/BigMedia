import json
from typing import Any
from unittest.mock import patch

import pytest
from django.db import DatabaseError

from apps.clientes import services
from apps.clientes.models import Cliente, Marca

URL = "/api/clientes/clientes/"


def _post(client, data) -> Any:
    return client.post(URL, data=json.dumps(data), content_type="application/json")


@pytest.mark.django_db
def test_alta_cliente_directo_crea_su_marca_homonima(operativo_client):
    response = _post(
        operativo_client,
        {"nombre": "Bodega Lunlunta", "razon_social": "Lunlunta SA", "tipo": "directo"},
    )

    assert response.status_code == 201
    marca = Marca.objects.get()
    assert marca.nombre == "Bodega Lunlunta"
    assert marca.cliente_id == response.json()["id"]
    assert marca.rubro is None
    assert marca.activo is True


@pytest.mark.django_db
@pytest.mark.parametrize("tipo", ["intermediario", "intermediario_formal"])
def test_alta_cliente_intermediario_no_crea_marca(operativo_client, tipo):
    response = _post(operativo_client, {"nombre": "Agencia", "razon_social": "Ag SA", "tipo": tipo})

    assert response.status_code == 201
    assert Marca.objects.count() == 0


@pytest.mark.django_db
def test_editar_cliente_directo_no_duplica_su_marca(operativo_client):
    cliente_id = _post(
        operativo_client, {"nombre": "Bodega", "razon_social": "Bodega SA", "tipo": "directo"}
    ).json()["id"]

    for datos in ({"nombre": "Bodega Nueva"}, {"telefono": "261"}, {"tipo": "directo"}):
        response = operativo_client.patch(
            f"{URL}{cliente_id}/", data=json.dumps(datos), content_type="application/json"
        )
        assert response.status_code == 200

    assert list(Marca.objects.values_list("nombre", flat=True)) == ["Bodega"]


@pytest.mark.django_db
def test_crear_cliente_directo_si_falla_la_marca_no_crea_el_cliente():
    with (
        patch.object(services, "crear_marca_homonima", side_effect=DatabaseError("falla")),
        pytest.raises(DatabaseError),
    ):
        services.crear_cliente(nombre="Bodega", razon_social="Bodega SA", tipo="directo")

    assert Cliente.objects.count() == 0
    assert Marca.objects.count() == 0


@pytest.mark.django_db
def test_crear_cliente_directo_si_la_base_rechaza_la_marca_no_crea_el_cliente():
    with (
        patch.object(Marca, "save", side_effect=DatabaseError("falla")),
        pytest.raises(DatabaseError),
    ):
        services.crear_cliente(nombre="Bodega", razon_social="Bodega SA", tipo="directo")

    assert Cliente.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("nombre", ["", "   "])
def test_alta_cliente_directo_sin_nombre_no_crea_marca(operativo_client, nombre):
    response = _post(operativo_client, {"nombre": nombre, "tipo": "directo"})

    assert response.status_code == 201
    assert Marca.objects.count() == 0


@pytest.mark.django_db
def test_alta_cliente_directo_solo_con_nombre_crea_su_marca(operativo_client):
    response = _post(operativo_client, {"nombre": "Bodega", "tipo": "directo"})

    assert response.status_code == 201
    assert list(Marca.objects.values_list("nombre", flat=True)) == ["Bodega"]
