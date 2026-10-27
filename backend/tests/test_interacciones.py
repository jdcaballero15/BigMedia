"""Interacciones comerciales (HU-020) y su contacto del intermediario formal (HU-068)."""

import json
from typing import Any

import pytest
from django.test import Client

from apps.campanias.models import Campania, Interaccion
from apps.clientes.models import Cliente, Contacto, Marca

URL = "/api/campanias/interacciones/"


def _post(client: Client, data: dict[str, Any]) -> Any:
    return client.post(URL, data=json.dumps(data), content_type="application/json")


def _patch(client: Client, pk: int, data: dict[str, Any]) -> Any:
    return client.patch(f"{URL}{pk}/", data=json.dumps(data), content_type="application/json")


def _cliente(nombre: str = "Agencia Prueba", tipo: str = Cliente.Tipo.DIRECTO) -> Cliente:
    return Cliente.objects.create(nombre=nombre, tipo=tipo)


def _campania_de(cliente: Cliente) -> Campania:
    marca = Marca.objects.create(nombre=f"Marca de {cliente.nombre}", cliente=cliente)
    return Campania.objects.create(nombre="Campaña de prueba", marca=marca)


def _datos(cliente: Cliente, **extra: Any) -> dict[str, Any]:
    return {
        "tipo": "llamada",
        "asunto": "Renovación de pauta",
        "fecha": "2026-10-20",
        "notas": "Pidió cotizar noviembre.",
        "cliente": cliente.pk,
        **extra,
    }


# --- HU-020 criterio 1: obligatorios ---


@pytest.mark.django_db
@pytest.mark.parametrize("campo", ["asunto", "fecha", "cliente", "tipo"])
def test_interaccion_sin_campo_obligatorio_se_rechaza(operativo_client, campo):
    datos = _datos(_cliente())
    datos.pop(campo)
    respuesta = _post(operativo_client, datos)
    assert respuesta.status_code == 400
    assert campo in respuesta.json()
    assert not Interaccion.objects.exists()


@pytest.mark.django_db
def test_interaccion_con_asunto_en_blanco_se_rechaza(operativo_client):
    respuesta = _post(operativo_client, _datos(_cliente(), asunto="   "))
    assert respuesta.status_code == 400
    assert "asunto" in respuesta.json()


@pytest.mark.django_db
def test_interaccion_minima_se_guarda_y_registra_el_usuario(operativo_client):
    cliente = _cliente()
    respuesta = _post(operativo_client, _datos(cliente))
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["cliente_nombre"] == "Agencia Prueba"
    assert cuerpo["contacto"] is None
    assert cuerpo["campania"] is None
    assert cuerpo["registrada_por_nombre"] == "operativo"
    interaccion = Interaccion.objects.get(pk=cuerpo["id"])
    assert interaccion.registrada_por is not None
    assert interaccion.registrada_por.username == "operativo"


@pytest.mark.django_db
def test_registrada_por_no_se_puede_cambiar(operativo_client, django_user_model):
    otro = django_user_model.objects.create_user(username="otro", password="clave-segura-123")
    creada = _post(operativo_client, _datos(_cliente(), registrada_por=otro.pk)).json()
    assert creada["registrada_por_nombre"] == "operativo"


# --- HU-020 criterio 2: aparece en la ficha del cliente y de la campaña ---


@pytest.mark.django_db
def test_interaccion_con_cliente_y_campania_aparece_en_ambos_filtros(operativo_client):
    cliente = _cliente()
    campania = _campania_de(cliente)
    otro = _cliente("Otro Cliente")
    _post(operativo_client, _datos(otro, asunto="Ajena"))
    creada = _post(operativo_client, _datos(cliente, campania=campania.pk)).json()
    assert creada["campania_nombre"] == "Campaña de prueba"

    por_cliente = operativo_client.get(URL, {"cliente": cliente.pk}).json()
    por_campania = operativo_client.get(URL, {"campania": campania.pk}).json()
    assert [i["id"] for i in por_cliente] == [creada["id"]]
    assert [i["id"] for i in por_campania] == [creada["id"]]


@pytest.mark.django_db
@pytest.mark.parametrize("parametro", ["cliente", "campania"])
def test_filtro_con_id_invalido_se_rechaza(operativo_client, parametro):
    respuesta = operativo_client.get(URL, {parametro: "abc"})
    assert respuesta.status_code == 400


# --- HU-020 criterio 3: orden por fecha descendente ---


@pytest.mark.django_db
def test_lista_ordenada_por_fecha_descendente(operativo_client):
    cliente = _cliente()
    for fecha in ("2026-09-01", "2026-10-15", "2026-10-01"):
        _post(operativo_client, _datos(cliente, fecha=fecha, asunto=f"Charla {fecha}"))
    fechas = [i["fecha"] for i in operativo_client.get(URL).json()]
    assert fechas == ["2026-10-15", "2026-10-01", "2026-09-01"]


# --- Campaña relacionada con el cliente ---


@pytest.mark.django_db
def test_campania_ajena_al_cliente_se_rechaza(operativo_client):
    cliente = _cliente()
    ajena = _campania_de(_cliente("Otro Cliente"))
    respuesta = _post(operativo_client, _datos(cliente, campania=ajena.pk))
    assert respuesta.status_code == 400
    assert "campania" in respuesta.json()


@pytest.mark.django_db
def test_campania_que_el_cliente_factura_se_acepta(operativo_client):
    agencia = _cliente("Agencia", Cliente.Tipo.INTERMEDIARIO)
    campania = _campania_de(_cliente("Anunciante"))
    campania.cliente_facturacion = agencia
    campania.save()
    respuesta = _post(operativo_client, _datos(agencia, campania=campania.pk))
    assert respuesta.status_code == 201


@pytest.mark.django_db
def test_cliente_inactivo_no_se_puede_elegir(operativo_client):
    cliente = _cliente()
    cliente.activo = False
    cliente.save()
    respuesta = _post(operativo_client, _datos(cliente))
    assert respuesta.status_code == 400
    assert "cliente" in respuesta.json()


# --- HU-068 criterio 5: contacto activo del mismo cliente ---


@pytest.mark.django_db
def test_contacto_activo_del_cliente_se_acepta(operativo_client):
    cliente = _cliente(tipo=Cliente.Tipo.INTERMEDIARIO_FORMAL)
    contacto = Contacto.objects.create(cliente=cliente, nombre="Ana Prueba")
    respuesta = _post(operativo_client, _datos(cliente, contacto=contacto.pk))
    assert respuesta.status_code == 201
    assert respuesta.json()["contacto_nombre"] == "Ana Prueba"


@pytest.mark.django_db
def test_contacto_inactivo_no_se_puede_elegir(operativo_client):
    cliente = _cliente(tipo=Cliente.Tipo.INTERMEDIARIO_FORMAL)
    contacto = Contacto.objects.create(cliente=cliente, nombre="Ana Prueba", activo=False)
    respuesta = _post(operativo_client, _datos(cliente, contacto=contacto.pk))
    assert respuesta.status_code == 400
    assert "contacto" in respuesta.json()


@pytest.mark.django_db
def test_contacto_de_otro_cliente_se_rechaza(operativo_client):
    cliente = _cliente(tipo=Cliente.Tipo.INTERMEDIARIO_FORMAL)
    otro = _cliente("Otra Central", Cliente.Tipo.INTERMEDIARIO_FORMAL)
    contacto = Contacto.objects.create(cliente=otro, nombre="Beto Prueba")
    respuesta = _post(operativo_client, _datos(cliente, contacto=contacto.pk))
    assert respuesta.status_code == 400
    assert "contacto" in respuesta.json()


@pytest.mark.django_db
def test_contacto_inactivado_se_conserva_en_la_pasada(operativo_client):
    cliente = _cliente(tipo=Cliente.Tipo.INTERMEDIARIO_FORMAL)
    contacto = Contacto.objects.create(cliente=cliente, nombre="Ana Prueba")
    creada = _post(operativo_client, _datos(cliente, contacto=contacto.pk)).json()
    contacto.activo = False
    contacto.save()

    leida = operativo_client.get(f"{URL}{creada['id']}/").json()
    assert leida["contacto"] == contacto.pk
    assert leida["contacto_nombre"] == "Ana Prueba"
    # Editar otro campo no obliga a cambiar el contacto que ya tenía.
    editada = _patch(operativo_client, creada["id"], {"notas": "Se volvió a llamar."})
    assert editada.status_code == 200
    assert editada.json()["contacto"] == contacto.pk


@pytest.mark.django_db
def test_cambiar_de_cliente_con_contacto_del_anterior_se_rechaza(operativo_client):
    cliente = _cliente(tipo=Cliente.Tipo.INTERMEDIARIO_FORMAL)
    contacto = Contacto.objects.create(cliente=cliente, nombre="Ana Prueba")
    creada = _post(operativo_client, _datos(cliente, contacto=contacto.pk)).json()
    otro = _cliente("Otro Cliente")
    respuesta = _patch(operativo_client, creada["id"], {"cliente": otro.pk})
    assert respuesta.status_code == 400
    assert "contacto" in respuesta.json()


# --- Permisos y baja lógica ---


@pytest.mark.django_db
def test_lectura_puede_listar_pero_no_crear(lector_client):
    assert lector_client.get(URL).status_code == 200
    respuesta = _post(lector_client, _datos(_cliente()))
    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_anonimo_no_accede():
    assert Client().get(URL).status_code in (401, 403)


@pytest.mark.django_db
def test_no_hay_delete(operativo_client):
    creada = _post(operativo_client, _datos(_cliente())).json()
    respuesta = operativo_client.delete(f"{URL}{creada['id']}/")
    assert respuesta.status_code == 405
    assert Interaccion.objects.filter(pk=creada["id"]).exists()


# --- Filtro de campañas por cliente, para ofrecerlas en el formulario ---


@pytest.mark.django_db
def test_campanias_filtradas_por_cliente_incluyen_las_que_factura_y_las_de_sus_marcas(
    operativo_client,
):
    cliente = _cliente()
    propia = _campania_de(cliente)
    facturada = _campania_de(_cliente("Anunciante"))
    facturada.cliente_facturacion = cliente
    facturada.save()
    _campania_de(_cliente("Ajeno"))
    filas = operativo_client.get("/api/campanias/campanias/", {"cliente": cliente.pk}).json()
    assert sorted(f["id"] for f in filas) == sorted([propia.pk, facturada.pk])


@pytest.mark.django_db
def test_campanias_filtro_cliente_invalido_se_rechaza(operativo_client):
    respuesta = operativo_client.get("/api/campanias/campanias/", {"cliente": "0"})
    assert respuesta.status_code == 400
