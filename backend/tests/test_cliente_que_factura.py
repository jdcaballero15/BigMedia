import json
from typing import Any
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import Client

from apps.auditoria.models import RegistroAuditoria
from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca

URL = "/api/clientes/marcas/"


def _cliente(nombre: str) -> Cliente:
    return Cliente.objects.create(nombre=nombre, razon_social=f"{nombre} SA", tipo="intermediario")


def _patch(client, marca: Marca, datos: dict[str, Any]) -> Any:
    return client.patch(
        f"{URL}{marca.pk}/", data=json.dumps(datos), content_type="application/json"
    )


@pytest.fixture
def marca(db) -> Marca:
    return Marca.objects.create(nombre="Gaseosa", cliente=_cliente("Agencia Vieja"))


@pytest.mark.django_db
@pytest.mark.regla("RN-014")
@pytest.mark.parametrize("estado", [valor for valor, _ in Campania.Estado.choices])
def test_cambio_de_cliente_de_marca_campania_sin_cliente_propio_conserva_el_anterior(
    operativo_client, marca, estado
):
    anterior = marca.cliente
    campania = Campania.objects.create(nombre="Verano", marca=marca, estado=estado)
    nuevo = _cliente("Agencia Nueva")

    response = _patch(operativo_client, marca, {"cliente": nuevo.pk})

    assert response.status_code == 200
    campania.refresh_from_db()
    assert campania.cliente_facturacion == anterior
    assert campania.cliente_factura == anterior


@pytest.mark.django_db
@pytest.mark.regla("RN-014")
def test_cambio_de_cliente_de_marca_campania_con_cliente_propio_no_cambia(operativo_client, marca):
    propio = _cliente("Facturador Propio")
    campania = Campania.objects.create(marca=marca, cliente_facturacion=propio)

    _patch(operativo_client, marca, {"cliente": _cliente("Agencia Nueva").pk})

    campania.refresh_from_db()
    assert campania.cliente_facturacion == propio
    assert not RegistroAuditoria.objects.filter(entidad="campania").exists()


@pytest.mark.django_db
@pytest.mark.regla("RN-014")
def test_edicion_de_marca_sin_cambio_de_cliente_no_estampa(operativo_client, marca):
    campania = Campania.objects.create(marca=marca)

    response = _patch(operativo_client, marca, {"nombre": "Gaseosa Light"})

    assert response.status_code == 200
    campania.refresh_from_db()
    assert campania.cliente_facturacion is None
    assert campania.cliente_factura == marca.cliente


@pytest.mark.django_db
@pytest.mark.regla("RN-014")
def test_cambio_de_cliente_de_marca_campania_nueva_factura_al_cliente_nuevo(
    operativo_client, marca
):
    nuevo = _cliente("Agencia Nueva")
    _patch(operativo_client, marca, {"cliente": nuevo.pk})

    campania = Campania.objects.create(marca=Marca.objects.get(pk=marca.pk))

    assert campania.cliente_facturacion is None
    assert campania.cliente_factura == nuevo


@pytest.mark.django_db
@pytest.mark.regla("RN-014")
def test_cambio_de_cliente_de_marca_no_toca_campanias_de_otras_marcas(operativo_client, marca):
    otra = Campania.objects.create(marca=Marca.objects.create(nombre="Agua", cliente=marca.cliente))

    _patch(operativo_client, marca, {"cliente": _cliente("Agencia Nueva").pk})

    otra.refresh_from_db()
    assert otra.cliente_facturacion is None


@pytest.mark.django_db
@pytest.mark.regla("RN-014")
def test_estampado_de_cliente_anterior_queda_en_auditoria_como_sistema(operativo_client, marca):
    campania = Campania.objects.create(marca=marca)

    _patch(operativo_client, marca, {"cliente": _cliente("Agencia Nueva").pk})

    registro = RegistroAuditoria.objects.get(entidad="campania", entidad_id=campania.pk)
    assert registro.campo == "cliente_facturacion"
    assert registro.valor_anterior == ""
    assert registro.valor_nuevo == "Agencia Vieja"
    assert registro.origen == RegistroAuditoria.Origen.SISTEMA


@pytest.mark.django_db
@pytest.mark.regla("RN-014")
def test_cambio_de_cliente_de_marca_falla_el_estampado_no_guarda_la_marca(operativo_client, marca):
    anterior = marca.cliente
    campania = Campania.objects.create(marca=marca)
    nuevo = _cliente("Agencia Nueva")

    with (
        patch("apps.auditoria.services.registrar_cambios", side_effect=DatabaseError("falla")),
        pytest.raises(DatabaseError),
    ):
        _patch(operativo_client, marca, {"cliente": nuevo.pk})

    marca.refresh_from_db()
    campania.refresh_from_db()
    assert marca.cliente == anterior
    assert campania.cliente_facturacion is None


@pytest.mark.django_db
@pytest.mark.regla("RN-014")
def test_cambio_de_cliente_de_marca_desde_el_admin_estampa(marca):
    anterior = marca.cliente
    campania = Campania.objects.create(marca=marca)
    nuevo = _cliente("Agencia Nueva")
    user = get_user_model().objects.create_superuser(username="adm", password="clave-segura-123")
    client = Client()
    client.force_login(user)

    response = client.post(
        f"/admin/clientes/marca/{marca.pk}/change/",
        {"nombre": marca.nombre, "cliente": nuevo.pk, "rubro": "", "grupo": "", "activo": "on"},
    )

    assert response.status_code == 302
    marca.refresh_from_db()
    campania.refresh_from_db()
    assert marca.cliente == nuevo
    assert campania.cliente_facturacion == anterior


@pytest.mark.django_db
def test_alta_de_marca_desde_el_admin_la_crea_con_su_cliente(db):
    cliente = _cliente("Agencia")
    user = get_user_model().objects.create_superuser(username="adm", password="clave-segura-123")
    client = Client()
    client.force_login(user)

    response = client.post(
        "/admin/clientes/marca/add/",
        {"nombre": "Agua", "cliente": cliente.pk, "rubro": "", "grupo": "", "activo": "on"},
    )

    assert response.status_code == 302
    assert Marca.objects.get().cliente == cliente
