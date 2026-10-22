import json
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.test import Client

from apps.clientes.models import Cliente

URL = "/api/clientes/clientes/"


def _post(client, data) -> Any:
    return client.post(URL, data=json.dumps(data), content_type="application/json")


def _patch(client, pk, data) -> Any:
    return client.patch(f"{URL}{pk}/", data=json.dumps(data), content_type="application/json")


def _cliente(**datos: Any) -> Cliente:
    valores = {"nombre": "Agencia Sur", "razon_social": "Agencia Sur SRL", "tipo": "intermediario"}
    valores.update(datos)
    return Cliente.objects.create(**valores)


@pytest.mark.django_db
def test_alta_cliente_con_nombre_razon_social_y_tipo_queda_disponible(operativo_client):
    response = _post(
        operativo_client,
        {
            "nombre": "  Agencia Andina ",
            "razon_social": "Andina Medios SA",
            "tipo": "intermediario_formal",
            "telefono": "261 400-0000",
            "correo": "contacto@ejemplo.com",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["nombre"] == "Agencia Andina"
    assert body["tipo"] == "intermediario_formal"
    assert body["tipo_nombre"] == "Intermediario formal"
    assert body["cuit"] == ""
    assert body["activo"] is True
    assert set(body) == {
        "id",
        "nombre",
        "razon_social",
        "cuit",
        "tipo",
        "tipo_nombre",
        "nombre_visible",
        "telefono",
        "correo",
        "activo",
        "creado_en",
        "actualizado_en",
    }
    assert Cliente.objects.get(pk=body["id"]).razon_social == "Andina Medios SA"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("datos", "campo"),
    [
        ({"tipo": "otro"}, "tipo"),
        ({"correo": "no-es-correo"}, "correo"),
    ],
)
def test_alta_cliente_con_dato_invalido_devuelve_error_del_campo(operativo_client, datos, campo):
    payload = {"nombre": "Agencia", "razon_social": "Agencia SA", "tipo": "directo"} | datos

    response = _post(operativo_client, payload)

    assert response.status_code == 400
    assert campo in response.json()
    assert Cliente.objects.count() == 0


@pytest.mark.django_db
def test_alta_cliente_sin_ningun_dato_se_acepta_y_se_muestra_sin_nombre(operativo_client):
    response = _post(operativo_client, {})

    assert response.status_code == 201
    body = response.json()
    assert body["nombre"] == ""
    assert body["razon_social"] == ""
    assert body["cuit"] == ""
    assert body["tipo"] == ""
    assert body["tipo_nombre"] == ""
    assert body["telefono"] == ""
    assert body["correo"] == ""
    assert body["nombre_visible"] == f"Cliente sin nombre #{body['id']}"


@pytest.mark.django_db
def test_alta_cliente_con_campos_en_blanco_se_acepta(operativo_client):
    response = _post(
        operativo_client,
        {
            "nombre": "  ",
            "razon_social": "",
            "cuit": "",
            "tipo": "",
            "telefono": "",
            "correo": "",
        },
    )

    assert response.status_code == 201
    assert response.json()["nombre"] == ""
    assert response.json()["tipo"] == ""


@pytest.mark.django_db
def test_cliente_con_nombre_se_muestra_por_su_nombre():
    cliente = _cliente(nombre="Agencia Sur")
    sin_nombre = _cliente(nombre="")

    assert cliente.nombre_visible == "Agencia Sur"
    assert str(cliente) == "Agencia Sur"
    assert str(sin_nombre) == f"Cliente sin nombre #{sin_nombre.pk}"


@pytest.mark.django_db
def test_lista_clientes_ordena_por_nombre_y_deja_los_sin_nombre_al_final_por_id(lector_client):
    segundo_sin_nombre = _cliente(nombre="")
    zeta = _cliente(nombre="Zeta")
    primero_sin_nombre = _cliente(nombre="")
    alfa = _cliente(nombre="Alfa")
    ids_sin_nombre = sorted([segundo_sin_nombre.pk, primero_sin_nombre.pk])

    ids = [c["id"] for c in lector_client.get(URL).json()]

    assert ids == [alfa.pk, zeta.pk, *ids_sin_nombre]


@pytest.mark.django_db
def test_alta_cliente_con_cuit_con_guiones_lo_guarda_sin_guiones(operativo_client):
    response = _post(
        operativo_client,
        {
            "nombre": "Lácteos",
            "razon_social": "Lácteos SA",
            "tipo": "directo",
            "cuit": "20-12345678-6",
        },
    )

    assert response.status_code == 201
    assert response.json()["cuit"] == "20123456786"
    assert Cliente.objects.get().cuit == "20123456786"


@pytest.mark.django_db
@pytest.mark.parametrize("cuit", ["20-12345678-9", "2012345678", "20.12345678.6"])
def test_alta_cliente_con_cuit_invalido_se_rechaza(operativo_client, cuit):
    response = _post(
        operativo_client,
        {"nombre": "Lácteos", "razon_social": "Lácteos SA", "tipo": "directo", "cuit": cuit},
    )

    assert response.status_code == 400
    assert "cuit" in response.json()
    assert Cliente.objects.count() == 0


@pytest.mark.django_db
def test_alta_cliente_con_cuit_repetido_se_rechaza(operativo_client):
    _cliente(cuit="20123456786")

    response = _post(
        operativo_client,
        {
            "nombre": "Otra",
            "razon_social": "Otra SA",
            "tipo": "intermediario",
            "cuit": "20-12345678-6",
        },
    )

    assert response.status_code == 400
    assert response.json()["cuit"] == ["Ya existe un cliente con ese CUIT."]
    assert Cliente.objects.count() == 1


@pytest.mark.django_db
def test_editar_cliente_conservando_su_cuit_no_lo_toma_como_repetido(operativo_client):
    cliente = _cliente(cuit="20123456786")

    response = _patch(operativo_client, cliente.pk, {"cuit": "20-12345678-6", "telefono": "123"})

    assert response.status_code == 200
    assert response.json()["telefono"] == "123"


@pytest.mark.django_db
def test_editar_cliente_puede_borrar_su_cuit(operativo_client):
    cliente = _cliente(cuit="20123456786")

    response = _patch(operativo_client, cliente.pk, {"cuit": "  "})

    assert response.status_code == 200
    assert response.json()["cuit"] == ""


@pytest.mark.django_db
def test_varios_clientes_sin_cuit_se_permiten(operativo_client):
    _cliente(nombre="Uno")
    response = _post(
        operativo_client, {"nombre": "Dos", "razon_social": "Dos SA", "tipo": "intermediario"}
    )

    assert response.status_code == 201
    assert Cliente.objects.filter(cuit="").count() == 2


@pytest.mark.django_db
def test_busqueda_por_parte_del_nombre_o_razon_social_ignora_tildes_y_mayusculas(lector_client):
    _cliente(nombre="Panadería Güemes", razon_social="Harinas del Oeste SRL")
    _cliente(nombre="Óptica Lumière", razon_social="Visión Cuyana SA")
    _cliente(nombre="Ferretería", razon_social="Tornillos SA")

    def nombres(q) -> list[str]:
        response = lector_client.get(URL, {"q": q})
        assert response.status_code == 200
        return sorted(item["nombre"] for item in response.json())

    assert nombres("panaderia") == ["Panadería Güemes"]
    assert nombres("GUEMES") == ["Panadería Güemes"]
    assert nombres("vision cuy") == ["Óptica Lumière"]
    assert nombres("Visión") == ["Óptica Lumière"]
    assert nombres(" sa ") == ["Ferretería", "Óptica Lumière"]


@pytest.mark.django_db
def test_editar_nombre_de_cliente_actualiza_la_busqueda(lector_client):
    cliente = _cliente(nombre="Viejo")
    cliente.nombre = "Señal Nueva"
    cliente.save(update_fields=["nombre"])

    assert [c["id"] for c in lector_client.get(URL, {"q": "senal"}).json()] == [cliente.pk]


@pytest.mark.django_db
def test_lista_clientes_oculta_inactivos_salvo_que_se_pidan(operativo_client):
    activo = _cliente(nombre="Activo")
    inactivo = _cliente(nombre="Inactivo")

    response = _patch(operativo_client, inactivo.pk, {"activo": False})

    assert response.status_code == 200
    assert [c["id"] for c in operativo_client.get(URL).json()] == [activo.pk]
    todos = operativo_client.get(URL, {"incluir_inactivos": "1"}).json()
    assert {c["id"] for c in todos} == {activo.pk, inactivo.pk}
    assert operativo_client.get(f"{URL}{inactivo.pk}/").status_code == 200


@pytest.mark.django_db
def test_lista_clientes_filtra_por_tipo(lector_client):
    _cliente(nombre="Directo", tipo="directo")
    _cliente(nombre="Agencia", tipo="intermediario")

    response = lector_client.get(URL, {"tipo": "directo"})
    invalido = lector_client.get(URL, {"tipo": "otro"})

    assert [c["nombre"] for c in response.json()] == ["Directo"]
    assert invalido.status_code == 400
    assert "tipo" in invalido.json()


@pytest.mark.django_db
def test_cliente_nunca_se_borra_desde_la_api(operativo_client):
    cliente = _cliente()

    assert operativo_client.delete(f"{URL}{cliente.pk}/").status_code == 405
    assert Cliente.objects.filter(pk=cliente.pk).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("url", [URL, "/api/clientes/marcas/", "/api/clientes/rubros/"])
def test_api_clientes_sin_sesion_devuelve_403(url):
    assert Client().get(url).status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url", "datos"),
    [
        (URL, {"nombre": "X", "razon_social": "X SA", "tipo": "directo"}),
        ("/api/clientes/rubros/", {"nombre": "Bebidas"}),
        ("/api/clientes/marcas/", {"nombre": "Marca"}),
    ],
)
def test_usuario_sin_grupo_operativo_lee_y_no_edita(lector_client, url, datos):
    assert lector_client.get(url).status_code == 200
    response = lector_client.post(url, data=json.dumps(datos), content_type="application/json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_alta_cliente_con_cuit_en_digitos_no_ascii_se_rechaza(operativo_client):
    response = _post(
        operativo_client,
        {"nombre": "Ar", "razon_social": "Ar SA", "tipo": "directo", "cuit": "٢٠١٢٣٤٥٦٧٨٦"},
    )

    assert response.status_code == 400
    assert "cuit" in response.json()
    assert Cliente.objects.count() == 0


@pytest.mark.django_db
def test_validar_restricciones_con_cuit_repetido_da_mensaje_en_castellano():
    _cliente(cuit="20123456786")
    repetido = Cliente(nombre="Otra", razon_social="Otra SA", tipo="directo", cuit="20123456786")

    with pytest.raises(ValidationError) as error:
        repetido.validate_constraints()

    assert error.value.messages == ["Ya existe un cliente con ese CUIT."]


@pytest.mark.django_db
def test_patch_de_tipo_no_crea_ni_borra_la_marca_homonima(operativo_client):
    agencia = _cliente(nombre="Agencia", tipo="intermediario")
    directo_id = _post(
        operativo_client, {"nombre": "Bodega", "razon_social": "Bodega SA", "tipo": "directo"}
    ).json()["id"]

    a_directo = _patch(operativo_client, agencia.pk, {"tipo": "directo"})
    desde_directo = _patch(operativo_client, directo_id, {"tipo": "intermediario"})

    assert a_directo.status_code == 200
    assert desde_directo.status_code == 200
    assert not agencia.marcas.exists()
    assert list(Cliente.objects.get(pk=directo_id).marcas.values_list("nombre", "activo")) == [
        ("Bodega", True)
    ]
