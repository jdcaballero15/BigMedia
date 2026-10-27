"""Ítems a facturar: carga libre durante el mes (HU-060) y sin borrado (HU-065)."""

import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.test import Client
from django.utils import timezone

from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca
from apps.facturacion.models import ItemFacturacion, Sector, TipoVenta

URL = "/api/facturacion/items/"


def _post(client: Client, data: dict[str, Any]) -> Any:
    return client.post(URL, data=json.dumps(data), content_type="application/json")


def _patch(client: Client, pk: int, data: dict[str, Any]) -> Any:
    return client.patch(f"{URL}{pk}/", data=json.dumps(data), content_type="application/json")


def _cliente() -> Cliente:
    return Cliente.objects.create(nombre="Cliente Prueba", cuit="20123456786")


# --- Criterios 1 y 2: sin datos obligatorios, mes actual por defecto ---


@pytest.mark.django_db
def test_item_sin_datos_se_guarda_en_borrador_con_el_mes_actual(operativo_client):
    respuesta = _post(operativo_client, {})
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    hoy = timezone.localdate()
    assert cuerpo["mes"] == date(hoy.year, hoy.month, 1).isoformat()
    assert cuerpo["estado"] == "borrador"
    assert cuerpo["alicuota_iva"] == "21.00"
    assert (cuerpo["neto"], cuerpo["iva"], cuerpo["total"]) == (None, None, None)
    assert cuerpo["creado_por_nombre"] == "operativo"


@pytest.mark.django_db
def test_el_mes_se_puede_cambiar_y_se_guarda_como_primer_dia(operativo_client):
    respuesta = _post(operativo_client, {"mes": "2026-12-15"})
    assert respuesta.json()["mes"] == "2026-12-01"


@pytest.mark.django_db
def test_un_item_nuevo_no_puede_nacer_en_otro_estado(operativo_client):
    respuesta = _post(operativo_client, {"estado": "facturado", "numero_factura": "A-1"})
    assert respuesta.status_code == 400
    assert "estado" in respuesta.json()


# --- Criterio 3: CUIT del ítem independiente del cliente ---


@pytest.mark.django_db
def test_cuit_del_item_se_edita_sin_tocar_al_cliente(operativo_client):
    cliente = _cliente()
    respuesta = _post(
        operativo_client, {"cliente": cliente.pk, "cuit_facturacion": "30-50001091-2"}
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["cuit_facturacion"] == "30500010912"
    assert respuesta.json()["cliente_nombre"] == "Cliente Prueba"
    cliente.refresh_from_db()
    assert cliente.cuit == "20123456786"


@pytest.mark.django_db
def test_cuit_invalido_se_rechaza(operativo_client):
    respuesta = _post(operativo_client, {"cuit_facturacion": "20123456780"})
    assert respuesta.status_code == 400
    assert "cuit_facturacion" in respuesta.json()


# --- Criterios 4 y 5: con o sin campaña ---


@pytest.mark.django_db
def test_item_vinculado_a_una_campania_con_sus_datos(operativo_client):
    cliente = _cliente()
    marca = Marca.objects.create(nombre="Marca Prueba", cliente=cliente)
    campania = Campania.objects.create(nombre="Verano", marca=marca)
    sector = Sector.objects.get(nombre="Privado")
    tipo_venta = TipoVenta.objects.get(nombre="F")
    datos = {
        "campania": campania.pk,
        "cliente": cliente.pk,
        "marca": marca.pk,
        "tipo_soporte": "Gran Formato, LED",
        "tipo_servicio": "impresion_colocacion",
        "descripcion": "Impresión de lonas",
        "periodo_desde": "2026-11-01",
        "periodo_hasta": "2026-11-30",
        "sector": sector.pk,
        "tipo_venta": tipo_venta.pk,
        "notas": "Facturar junto con la OC anterior.",
    }
    respuesta = _post(operativo_client, datos)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["campania_nombre"] == "Verano"
    assert cuerpo["marca_nombre"] == "Marca Prueba"
    assert cuerpo["sector_nombre"] == "Privado"
    assert cuerpo["tipo_venta_nombre"] == "F"
    assert cuerpo["tipo_servicio"] == "impresion_colocacion"


@pytest.mark.django_db
def test_periodo_invertido_se_rechaza(operativo_client):
    respuesta = _post(
        operativo_client, {"periodo_desde": "2026-11-30", "periodo_hasta": "2026-11-01"}
    )
    assert respuesta.status_code == 400
    assert "periodo_hasta" in respuesta.json()


@pytest.mark.django_db
def test_catalogos_inactivos_no_se_pueden_elegir(operativo_client):
    sector = Sector.objects.create(nombre="Sector viejo", activo=False)
    respuesta = _post(operativo_client, {"sector": sector.pk})
    assert respuesta.status_code == 400
    assert "sector" in respuesta.json()


@pytest.mark.django_db
def test_catalogos_lista_solo_los_activos(lector_client):
    Sector.objects.create(nombre="Sector viejo", activo=False)
    cuerpo = lector_client.get("/api/facturacion/catalogos/").json()
    assert [s["nombre"] for s in cuerpo["sectores"]] == ["Gobierno", "Privado"]
    assert [t["nombre"] for t in cuerpo["tipos_venta"]] == ["F", "V"]


# --- Listado y filtros ---


@pytest.mark.django_db
def test_lista_filtra_por_mes_estado_cliente_y_campania(operativo_client):
    cliente = _cliente()
    campania = Campania.objects.create()
    buscado = ItemFacturacion.objects.create(
        mes=date(2026, 11, 1), cliente=cliente, campania=campania
    )
    ItemFacturacion.objects.create(mes=date(2026, 12, 1), cliente=cliente, campania=campania)
    ItemFacturacion.objects.create(mes=date(2026, 11, 1))
    ItemFacturacion.objects.create(
        mes=date(2026, 11, 1), cliente=cliente, campania=campania, estado="anulado"
    )
    params = f"?mes=2026-11&estado=borrador&cliente={cliente.pk}&campania={campania.pk}"
    lista = operativo_client.get(f"{URL}{params}").json()
    assert [item["id"] for item in lista] == [buscado.pk]


@pytest.mark.django_db
@pytest.mark.parametrize("params", ["?mes=11-2026", "?estado=perdido", "?cliente=x", "?campania=0"])
def test_filtros_invalidos_se_rechazan(operativo_client, params):
    assert operativo_client.get(f"{URL}{params}").status_code == 400


# --- Edición, borrado y permisos ---


@pytest.mark.django_db
def test_item_en_borrador_se_edita(operativo_client):
    item = ItemFacturacion.objects.create()
    respuesta = _patch(operativo_client, item.pk, {"descripcion": "Alquiler noviembre"})
    assert respuesta.status_code == 200
    assert respuesta.json()["descripcion"] == "Alquiler noviembre"


@pytest.mark.django_db
@pytest.mark.parametrize("estado", ["enviado", "facturado", "anulado"])
def test_fuera_de_borrador_no_se_editan_los_datos(operativo_client, estado):
    item = ItemFacturacion.objects.create(
        estado=estado, numero_factura="A-1" if estado == "facturado" else ""
    )
    respuesta = _patch(operativo_client, item.pk, {"neto": "5.00"})
    assert respuesta.status_code == 400
    assert respuesta.json()["estado"] == ["Solo se pueden editar los datos de un ítem en Borrador."]
    item.refresh_from_db()
    assert item.neto is None


@pytest.mark.django_db
def test_items_no_se_borran(operativo_client):
    item = ItemFacturacion.objects.create()
    assert operativo_client.delete(f"{URL}{item.pk}/").status_code == 405
    assert ItemFacturacion.objects.filter(pk=item.pk).exists()


@pytest.mark.django_db
def test_lector_ve_pero_no_crea(lector_client):
    ItemFacturacion.objects.create(neto=Decimal("100.00"))
    assert len(lector_client.get(URL).json()) == 1
    assert _post(lector_client, {}).status_code == 403


@pytest.mark.django_db
def test_str_del_item():
    item = ItemFacturacion(mes=date(2026, 11, 1), descripcion="Alquiler")
    assert str(item) == "2026-11 · Alquiler"
    assert str(ItemFacturacion(mes=None)) == "Sin mes · Sin descripción"
