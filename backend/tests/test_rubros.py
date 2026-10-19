import json
from typing import Any

import pytest

from apps.clientes.models import Rubro

URL = "/api/clientes/rubros/"


def _post(client, data) -> Any:
    return client.post(URL, data=json.dumps(data), content_type="application/json")


@pytest.mark.django_db
def test_rubro_sin_cargas_no_tiene_valores_iniciales():
    assert Rubro.objects.count() == 0


@pytest.mark.django_db
def test_rubro_nombre_obligatorio_y_unico_sin_distinguir_mayusculas(operativo_client):
    primero = _post(operativo_client, {"nombre": "Bebidas"})
    repetido = _post(operativo_client, {"nombre": " bebidas "})
    vacio = _post(operativo_client, {"nombre": "  "})

    assert primero.status_code == 201
    assert primero.json() == {"id": primero.json()["id"], "nombre": "Bebidas", "activo": True}
    assert repetido.status_code == 400
    assert repetido.json()["nombre"] == ["Ya existe un rubro con ese nombre."]
    assert vacio.status_code == 400
    assert vacio.json()["nombre"] == ["Ingresá un nombre."]
    assert Rubro.objects.count() == 1


@pytest.mark.django_db
def test_rubro_se_renombra_e_inactiva_sin_borrarse(operativo_client):
    rubro = Rubro.objects.create(nombre="Bebidas")
    url = f"{URL}{rubro.pk}/"

    mismo = operativo_client.patch(
        url, data=json.dumps({"nombre": "BEBIDAS"}), content_type="application/json"
    )
    inactivo = operativo_client.patch(
        url, data=json.dumps({"activo": False}), content_type="application/json"
    )

    assert mismo.status_code == 200
    assert mismo.json()["nombre"] == "BEBIDAS"
    assert inactivo.status_code == 200
    assert operativo_client.delete(url).status_code == 405
    assert operativo_client.get(URL).json() == []
    assert len(operativo_client.get(URL, {"incluir_inactivos": "1"}).json()) == 1
