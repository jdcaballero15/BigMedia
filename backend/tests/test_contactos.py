"""Contactos del intermediario formal (HU-068)."""

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError, connection
from django.test import Client

from apps.clientes.models import Cliente, Contacto

URL = "/api/clientes/contactos/"
URL_CLIENTES = "/api/clientes/clientes/"


def _post(client: Client, url: str, data: dict[str, Any]) -> Any:
    return client.post(url, data=json.dumps(data), content_type="application/json")


def _patch(client: Client, url: str, data: dict[str, Any]) -> Any:
    return client.patch(url, data=json.dumps(data), content_type="application/json")


def _cliente(tipo: str = Cliente.Tipo.INTERMEDIARIO_FORMAL, **datos: Any) -> Cliente:
    return Cliente.objects.create(nombre="Central de Medios Sur", tipo=tipo, **datos)


def _contacto(cliente: Cliente, nombre: str = "Ana Prueba", **datos: Any) -> Contacto:
    return Contacto.objects.create(cliente=cliente, nombre=nombre, **datos)


def _alta(client: Client, cliente: Cliente, **datos: Any) -> Any:
    return _post(client, URL, {"cliente": cliente.pk, "nombre": "Ana Prueba", **datos})


# --- Criterio 1: varios contactos en un intermediario formal ---


@pytest.mark.django_db
@pytest.mark.regla("RN-015")
def test_contacto_intermediario_formal_acepta_varios(operativo_client):
    cliente = _cliente()
    primero = _alta(
        operativo_client,
        cliente,
        cargo="Planificación",
        correo="ana@ejemplo.test",
        telefono="261 555 0001",
        notas="Prefiere correo.",
    )
    assert primero.status_code == 201
    assert primero.json() | {"id": 0} == {
        "id": 0,
        "cliente": cliente.pk,
        "nombre": "Ana Prueba",
        "cargo": "Planificación",
        "correo": "ana@ejemplo.test",
        "telefono": "261 555 0001",
        "notas": "Prefiere correo.",
        "principal": False,
        "activo": True,
    }
    assert _alta(operativo_client, cliente, nombre="Beto Prueba").status_code == 201
    assert cliente.contactos.count() == 2


# --- Criterio 2: los otros tipos no llevan contactos ---


@pytest.mark.django_db
@pytest.mark.regla("RN-015")
@pytest.mark.parametrize("tipo", ["directo", "intermediario", ""])
def test_contacto_en_cliente_que_no_es_intermediario_formal_se_rechaza(operativo_client, tipo):
    respuesta = _alta(operativo_client, _cliente(tipo=tipo))
    assert respuesta.status_code == 400
    assert respuesta.json()["cliente"] == [
        "Solo un cliente intermediario formal puede tener contactos."
    ]


@pytest.mark.django_db
def test_contacto_en_cliente_inactivo_se_rechaza(operativo_client):
    respuesta = _alta(operativo_client, _cliente(activo=False))
    assert respuesta.status_code == 400
    assert respuesta.json()["cliente"] == ["Seleccioná un cliente activo."]


@pytest.mark.django_db
def test_contacto_no_se_cambia_de_cliente(operativo_client):
    contacto = _contacto(_cliente())
    otro = _cliente()
    respuesta = _patch(operativo_client, f"{URL}{contacto.pk}/", {"cliente": otro.pk})
    assert respuesta.status_code == 400
    assert Contacto.objects.get(pk=contacto.pk).cliente_id != otro.pk


# --- Criterio 3: un solo principal ---


@pytest.mark.django_db
def test_contacto_marcar_principal_desmarca_al_anterior(operativo_client):
    cliente = _cliente()
    anterior = _contacto(cliente, principal=True)
    nuevo = _contacto(cliente, nombre="Beto Prueba")
    otro_cliente = _contacto(_cliente(), principal=True)

    respuesta = _patch(operativo_client, f"{URL}{nuevo.pk}/", {"principal": True})

    assert respuesta.status_code == 200
    assert Contacto.objects.get(pk=nuevo.pk).principal is True
    assert Contacto.objects.get(pk=anterior.pk).principal is False
    assert Contacto.objects.get(pk=otro_cliente.pk).principal is True


@pytest.mark.django_db
def test_contacto_alta_como_principal_desmarca_al_anterior(operativo_client):
    cliente = _cliente()
    anterior = _contacto(cliente, principal=True)
    assert _alta(operativo_client, cliente, nombre="Beto", principal=True).status_code == 201
    assert Contacto.objects.get(pk=anterior.pk).principal is False
    assert cliente.contactos.filter(principal=True).count() == 1


@pytest.mark.django_db
def test_contacto_base_impide_dos_principales():
    cliente = _cliente()
    _contacto(cliente, principal=True)
    with pytest.raises(IntegrityError):
        Contacto.objects.bulk_create([Contacto(cliente=cliente, nombre="Beto", principal=True)])


def _marcar_principal_en_hilo(usuario_pk: int, contacto_pk: int) -> int:
    """Marca un contacto como principal en su propio hilo/conexión; devuelve el status HTTP."""
    try:
        client = Client()
        client.force_login(get_user_model().objects.get(pk=usuario_pk))
        return int(_patch(client, f"{URL}{contacto_pk}/", {"principal": True}).status_code)
    finally:
        connection.close()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_contacto_principal_concurrente_queda_uno_solo():
    usuario = get_user_model().objects.create_user(username="operativo")
    usuario.groups.add(Group.objects.get(name="Operativo"))
    cliente = _cliente()
    uno = _contacto(cliente, nombre="Uno")
    dos = _contacto(cliente, nombre="Dos")
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(
            pool.map(lambda pk: _marcar_principal_en_hilo(usuario.pk, pk), [uno.pk, dos.pk])
        )
    assert resultados == [200, 200]
    assert cliente.contactos.filter(principal=True).count() == 1


# --- Criterio 4: el nombre es obligatorio ---


@pytest.mark.django_db
@pytest.mark.parametrize("nombre", ["", "   "])
def test_contacto_sin_nombre_se_rechaza(operativo_client, nombre):
    respuesta = _alta(operativo_client, _cliente(), nombre=nombre)
    assert respuesta.status_code == 400
    assert respuesta.json()["nombre"] == ["Ingresá un nombre."]


@pytest.mark.django_db
def test_contacto_correo_invalido_se_rechaza(operativo_client):
    respuesta = _alta(operativo_client, _cliente(), correo="no-es-correo")
    assert respuesta.status_code == 400
    assert respuesta.json()["correo"] == ["Ingresá un correo válido."]


# --- Baja lógica (HU-006) ---


@pytest.mark.django_db
def test_contacto_inactivar_saca_el_principal_y_no_se_borra(operativo_client):
    contacto = _contacto(_cliente(), principal=True)
    respuesta = _patch(operativo_client, f"{URL}{contacto.pk}/", {"activo": False})
    assert respuesta.status_code == 200
    guardado = Contacto.objects.get(pk=contacto.pk)
    assert (guardado.activo, guardado.principal) == (False, False)


@pytest.mark.django_db
def test_contacto_inactivo_no_puede_ser_principal(operativo_client):
    contacto = _contacto(_cliente(), activo=False)
    respuesta = _patch(operativo_client, f"{URL}{contacto.pk}/", {"principal": True})
    assert respuesta.status_code == 400
    assert respuesta.json()["principal"] == ["Un contacto inactivo no puede ser el principal."]


@pytest.mark.django_db
def test_contacto_delete_devuelve_405(operativo_client):
    contacto = _contacto(_cliente())
    assert operativo_client.delete(f"{URL}{contacto.pk}/").status_code == 405
    assert Contacto.objects.filter(pk=contacto.pk).exists()


@pytest.mark.django_db
def test_contacto_lista_por_cliente_excluye_inactivos_salvo_pedido(lector_client):
    cliente = _cliente()
    activo = _contacto(cliente, nombre="Activo")
    inactivo = _contacto(cliente, nombre="Inactivo", activo=False)
    _contacto(_cliente(), nombre="De otro cliente")

    lista = lector_client.get(f"{URL}?cliente={cliente.pk}").json()
    assert [c["id"] for c in lista] == [activo.pk]

    todos = lector_client.get(f"{URL}?cliente={cliente.pk}&incluir_inactivos=1").json()
    assert {c["id"] for c in todos} == {activo.pk, inactivo.pk}


@pytest.mark.django_db
def test_contacto_lista_muestra_primero_el_principal(lector_client):
    cliente = _cliente()
    _contacto(cliente, nombre="Ana")
    principal = _contacto(cliente, nombre="Zoe", principal=True)
    lista = lector_client.get(f"{URL}?cliente={cliente.pk}").json()
    assert lista[0]["id"] == principal.pk


@pytest.mark.django_db
def test_contacto_lectura_no_edita(lector_client):
    assert _alta(lector_client, _cliente()).status_code == 403


# --- Criterio 6: cambio de tipo con contactos activos ---


@pytest.mark.django_db
@pytest.mark.regla("RN-015")
def test_cliente_cambio_de_tipo_con_contactos_activos_se_rechaza(operativo_client):
    cliente = _cliente()
    _contacto(cliente)
    respuesta = _patch(operativo_client, f"{URL_CLIENTES}{cliente.pk}/", {"tipo": "intermediario"})
    assert respuesta.status_code == 400
    assert respuesta.json()["tipo"] == ["Inactivá antes sus contactos."]
    assert Cliente.objects.get(pk=cliente.pk).tipo == Cliente.Tipo.INTERMEDIARIO_FORMAL


@pytest.mark.django_db
@pytest.mark.regla("RN-015")
def test_cliente_cambio_de_tipo_con_contactos_inactivos_se_acepta(operativo_client):
    cliente = _cliente()
    _contacto(cliente, activo=False)
    respuesta = _patch(operativo_client, f"{URL_CLIENTES}{cliente.pk}/", {"tipo": "intermediario"})
    assert respuesta.status_code == 200


@pytest.mark.django_db
def test_cliente_edicion_sin_cambio_de_tipo_con_contactos_se_acepta(operativo_client):
    cliente = _cliente()
    _contacto(cliente)
    datos = {"nombre": "Otro nombre", "tipo": "intermediario_formal"}
    assert _patch(operativo_client, f"{URL_CLIENTES}{cliente.pk}/", datos).status_code == 200
