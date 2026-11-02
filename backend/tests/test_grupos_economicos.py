"""Grupos económicos: catálogo editable y grupo opcional de la marca (RN-016)."""

import json
from typing import Any

import pytest
from django.core.exceptions import ValidationError

from apps.clientes.models import Cliente, GrupoEconomico, Marca

URL = "/api/clientes/grupos/"
URL_MARCAS = "/api/clientes/marcas/"

pytestmark = pytest.mark.regla("RN-016")


def _post(client, url: str, data: dict[str, Any]) -> Any:
    return client.post(url, data=json.dumps(data), content_type="application/json")


def _patch(client, url: str, data: dict[str, Any]) -> Any:
    return client.patch(url, data=json.dumps(data), content_type="application/json")


@pytest.mark.django_db
def test_grupo_nombre_obligatorio_y_unico_sin_distinguir_mayusculas(operativo_client):
    primero = _post(operativo_client, URL, {"nombre": "Grupo Andes"})
    repetido = _post(operativo_client, URL, {"nombre": " grupo andes "})
    vacio = _post(operativo_client, URL, {"nombre": "  "})

    assert primero.status_code == 201
    assert primero.json() == {"id": primero.json()["id"], "nombre": "Grupo Andes", "activo": True}
    assert repetido.status_code == 400
    assert repetido.json()["nombre"] == ["Ya existe un grupo económico con ese nombre."]
    assert vacio.status_code == 400
    assert vacio.json()["nombre"] == ["Ingresá un nombre."]
    assert GrupoEconomico.objects.count() == 1


@pytest.mark.django_db
def test_grupo_se_renombra_e_inactiva_sin_borrarse(operativo_client):
    grupo = GrupoEconomico.objects.create(nombre="Grupo Andes")
    url = f"{URL}{grupo.pk}/"

    renombrado = _patch(operativo_client, url, {"nombre": "Grupo Cuyo"})
    inactivo = _patch(operativo_client, url, {"activo": False})

    assert renombrado.status_code == 200
    assert renombrado.json()["nombre"] == "Grupo Cuyo"
    assert inactivo.status_code == 200
    assert operativo_client.delete(url).status_code == 405
    assert operativo_client.get(URL).json() == []
    assert len(operativo_client.get(URL, {"incluir_inactivos": "1"}).json()) == 1


@pytest.mark.django_db
def test_grupo_lectura_lista_pero_no_escribe(lector_client):
    GrupoEconomico.objects.create(nombre="Grupo Andes")

    assert lector_client.get(URL).status_code == 200
    assert _post(lector_client, URL, {"nombre": "Otro"}).status_code == 403


@pytest.mark.django_db
def test_validar_restricciones_con_grupo_repetido_da_mensaje_en_castellano():
    GrupoEconomico.objects.create(nombre="Grupo Andes")

    with pytest.raises(ValidationError) as error:
        GrupoEconomico(nombre="GRUPO ANDES").validate_constraints()

    assert error.value.messages == ["Ya existe un grupo económico con ese nombre."]


@pytest.mark.django_db
def test_marca_de_clientes_distintos_comparten_grupo(operativo_client):
    grupo = GrupoEconomico.objects.create(nombre="Grupo Andes")
    agencia = Cliente.objects.create(nombre="Agencia Uno")
    directo = Cliente.objects.create(nombre="Directo Dos")

    una = _post(
        operativo_client,
        URL_MARCAS,
        {"nombre": "Gaseosa", "cliente": agencia.pk, "grupo": grupo.pk},
    )
    otra = _post(
        operativo_client,
        URL_MARCAS,
        {"nombre": "Galletitas", "cliente": directo.pk, "grupo": grupo.pk},
    )

    assert una.status_code == 201
    assert otra.status_code == 201
    assert una.json()["grupo"] == grupo.pk
    assert una.json()["grupo_nombre"] == "Grupo Andes"
    assert set(grupo.marcas.values_list("nombre", flat=True)) == {"Gaseosa", "Galletitas"}


@pytest.mark.django_db
def test_marca_sin_grupo_se_acepta_y_el_grupo_se_puede_quitar(operativo_client):
    grupo = GrupoEconomico.objects.create(nombre="Grupo Andes")
    cliente = Cliente.objects.create(nombre="Cliente")

    sin_grupo = _post(operativo_client, URL_MARCAS, {"nombre": "A", "cliente": cliente.pk})
    marca = Marca.objects.create(nombre="B", cliente=cliente, grupo=grupo)
    quitado = _patch(operativo_client, f"{URL_MARCAS}{marca.pk}/", {"grupo": None})

    assert sin_grupo.status_code == 201
    assert sin_grupo.json()["grupo"] is None
    assert sin_grupo.json()["grupo_nombre"] is None
    assert quitado.status_code == 200
    marca.refresh_from_db()
    assert marca.grupo is None


@pytest.mark.django_db
def test_marca_con_grupo_inactivo_o_inexistente_se_rechaza(operativo_client):
    inactivo = GrupoEconomico.objects.create(nombre="Viejo", activo=False)
    cliente = Cliente.objects.create(nombre="Cliente")

    con_inactivo = _post(
        operativo_client, URL_MARCAS, {"nombre": "A", "cliente": cliente.pk, "grupo": inactivo.pk}
    )
    con_inexistente = _post(
        operativo_client, URL_MARCAS, {"nombre": "B", "cliente": cliente.pk, "grupo": 9999}
    )

    assert con_inactivo.status_code == 400
    assert con_inactivo.json()["grupo"] == ["Seleccioná un grupo económico activo."]
    assert con_inexistente.status_code == 400
    assert con_inexistente.json()["grupo"] == ["El grupo económico elegido no existe."]


@pytest.mark.django_db
def test_editar_marca_de_grupo_ya_inactivo_lo_conserva(operativo_client):
    grupo = GrupoEconomico.objects.create(nombre="Grupo Andes")
    marca = Marca.objects.create(
        nombre="A", cliente=Cliente.objects.create(nombre="C"), grupo=grupo
    )
    GrupoEconomico.objects.filter(pk=grupo.pk).update(activo=False)

    response = _patch(
        operativo_client, f"{URL_MARCAS}{marca.pk}/", {"nombre": "A2", "grupo": grupo.pk}
    )

    assert response.status_code == 200
    assert response.json()["grupo"] == grupo.pk


@pytest.mark.django_db
def test_filtro_de_marcas_por_grupo(operativo_client):
    grupo = GrupoEconomico.objects.create(nombre="Grupo Andes")
    cliente = Cliente.objects.create(nombre="Cliente")
    Marca.objects.create(nombre="Del grupo", cliente=cliente, grupo=grupo)
    Marca.objects.create(nombre="Suelta", cliente=cliente)

    filtradas = operativo_client.get(URL_MARCAS, {"grupo": grupo.pk}).json()
    invalido = operativo_client.get(URL_MARCAS, {"grupo": "abc"})

    assert [m["nombre"] for m in filtradas] == ["Del grupo"]
    assert invalido.status_code == 400
