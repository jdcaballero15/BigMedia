"""Cierre de mes: "Enviar a facturar" y el registro del envío (HU-066)."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, Group
from django.db import connection
from django.test import Client

from apps.auditoria.models import RegistroAuditoria
from apps.clientes.models import Cliente
from apps.facturacion.models import EnvioFacturacion, ItemFacturacion

URL = "/api/facturacion/envios/"
NOVIEMBRE = date(2026, 11, 1)


def _enviar(client: Client, mes: Any = "2026-11") -> Any:
    return client.post(URL, data=json.dumps({"mes": mes}), content_type="application/json")


def _cliente(nombre: str = "Cliente Prueba") -> Cliente:
    return Cliente.objects.create(nombre=nombre)


def _item(**extra: Any) -> ItemFacturacion:
    datos: dict[str, Any] = {"mes": NOVIEMBRE, "neto": Decimal("1000.00"), **extra}
    if "cliente" not in datos:
        datos["cliente"] = _cliente()
    return ItemFacturacion.objects.create(**datos)


# --- Criterios 2 y 6: envía los completos y registra el envío ---


@pytest.mark.django_db
def test_envia_los_completos_y_registra_quien_cuando_y_que(operativo_client):
    primero, segundo = _item(), _item(descripcion="Otro")
    respuesta = _enviar(operativo_client)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert sorted(cuerpo["envio"]["items"]) == sorted([primero.pk, segundo.pk])
    assert cuerpo["envio"]["mes"] == "2026-11"
    assert cuerpo["envio"]["enviado_por_nombre"] == "operativo"
    assert cuerpo["envio"]["cantidad"] == 2
    assert cuerpo["incompletos"] == []

    envio = EnvioFacturacion.objects.get()
    assert envio.enviado_por is not None
    assert envio.enviado_por.username == "operativo"
    assert envio.enviado_en is not None
    assert set(envio.items.values_list("pk", flat=True)) == {primero.pk, segundo.pk}
    assert set(ItemFacturacion.objects.values_list("estado", flat=True)) == {"enviado"}


@pytest.mark.django_db
def test_el_cambio_de_estado_queda_auditado(operativo_client):
    item = _item()
    _enviar(operativo_client)
    registro = RegistroAuditoria.objects.get(entidad="item_facturacion", entidad_id=item.pk)
    assert (registro.campo, registro.valor_anterior, registro.valor_nuevo) == (
        "estado",
        "borrador",
        "enviado",
    )


# --- Criterio 4: los incompletos no se envían y dicen qué les falta ---


@pytest.mark.django_db
@pytest.mark.regla("RN-025")
def test_incompletos_no_se_envian_y_listan_lo_que_falta(operativo_client):
    completo = _item()
    sin_cliente = _item(cliente=None, descripcion="Sin cliente")
    sin_neto = _item(neto=None)
    cuerpo = _enviar(operativo_client).json()
    assert cuerpo["envio"]["items"] == [completo.pk]
    faltantes = {i["item"]: i["faltan"] for i in cuerpo["incompletos"]}
    assert faltantes == {sin_cliente.pk: ["cliente"], sin_neto.pk: ["importe neto"]}
    descripciones = {i["item"]: i["descripcion"] for i in cuerpo["incompletos"]}
    assert descripciones[sin_cliente.pk] == "Sin cliente"
    sin_cliente.refresh_from_db()
    assert sin_cliente.estado == "borrador"


@pytest.mark.django_db
def test_mes_sin_completos_no_crea_envio(operativo_client):
    _item(cliente=None)
    respuesta = _enviar(operativo_client)
    assert respuesta.status_code == 200
    assert respuesta.json()["envio"] is None
    assert len(respuesta.json()["incompletos"]) == 1
    assert not EnvioFacturacion.objects.exists()


# --- Criterio 5: anulados, facturados, ya enviados y otros meses no entran ---


@pytest.mark.django_db
def test_solo_entran_los_borradores_del_mes(operativo_client):
    borrador = _item()
    _item(estado="anulado")
    _item(estado="facturado", numero_factura="A-1")
    _item(estado="enviado")
    _item(mes=date(2026, 12, 1))
    cuerpo = _enviar(operativo_client).json()
    assert cuerpo["envio"]["items"] == [borrador.pk]
    assert cuerpo["incompletos"] == []


@pytest.mark.django_db
def test_lista_los_envios_del_mes(operativo_client, lector_client):
    _item()
    _enviar(operativo_client)
    _item(mes=date(2026, 12, 1))
    _enviar(operativo_client, "2026-12")
    envios = lector_client.get(f"{URL}?mes=2026-11").json()
    assert [e["mes"] for e in envios] == ["2026-11"]
    assert envios[0]["cantidad"] == 1


# --- Validaciones y permisos ---


@pytest.mark.django_db
@pytest.mark.parametrize("mes", [None, "", "2026-13", "noviembre"])
def test_mes_invalido_se_rechaza(operativo_client, mes):
    respuesta = _enviar(operativo_client, mes)
    assert respuesta.status_code == 400
    assert "mes" in respuesta.json()


@pytest.mark.django_db
def test_lector_no_puede_enviar(lector_client):
    _item()
    assert _enviar(lector_client).status_code == 403
    assert ItemFacturacion.objects.get().estado == "borrador"


@pytest.mark.django_db
def test_los_envios_no_se_editan_ni_se_borran(operativo_client):
    _item()
    envio_id = _enviar(operativo_client).json()["envio"]["id"]
    # No hay ruta de detalle: ni DELETE ni PATCH llegan a un envío.
    assert operativo_client.delete(f"{URL}{envio_id}/").status_code in {404, 405}
    respuesta = operativo_client.patch(
        f"{URL}{envio_id}/", data=json.dumps({"mes": "2026-12"}), content_type="application/json"
    )
    assert respuesta.status_code in {404, 405}
    envio = EnvioFacturacion.objects.get(pk=envio_id)
    assert envio.mes == NOVIEMBRE


@pytest.mark.django_db
def test_str_del_envio(operativo_client):
    _item()
    _enviar(operativo_client)
    assert str(EnvioFacturacion.objects.get()).startswith("Envío 2026-11 · ")


# --- Concurrencia: dos envíos a la vez no duplican ítems ---


def _operativo() -> AbstractBaseUser:
    user = get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    user.groups.add(Group.objects.get(name="Operativo"))
    return user


def _enviar_en_hilo(user_pk: int) -> Any:
    try:
        client = Client()
        client.force_login(get_user_model().objects.get(pk=user_pk))
        return _enviar(client).json()
    finally:
        connection.close()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_dos_envios_simultaneos_no_duplican_items():
    user = _operativo()
    items = [_item(descripcion=f"Ítem {n}").pk for n in range(5)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(lambda _: _enviar_en_hilo(user.pk), range(2)))
    enviados = [i for r in resultados if r["envio"] for i in r["envio"]["items"]]
    assert sorted(enviados) == sorted(items)
    assert EnvioFacturacion.objects.count() == 1
