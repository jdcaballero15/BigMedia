"""Grupos de factura: varios ítems en una misma factura (HU-064)."""

import json
from datetime import date
from typing import Any

import pytest
from django.test import Client

from apps.auditoria.models import RegistroAuditoria
from apps.facturacion.models import GrupoFactura, ItemFacturacion

URL_GRUPOS = "/api/facturacion/grupos/"
URL_ITEMS = "/api/facturacion/items/"
NOVIEMBRE = date(2026, 11, 1)


def _agrupar(client: Client, items: list[Any]) -> Any:
    datos = {"items": [getattr(item, "pk", item) for item in items]}
    return client.post(URL_GRUPOS, data=json.dumps(datos), content_type="application/json")


def _quitar(client: Client, item: ItemFacturacion) -> Any:
    return client.post(f"{URL_ITEMS}{item.pk}/quitar-del-grupo/")


def _items(cantidad: int, **extra: Any) -> list[ItemFacturacion]:
    return [ItemFacturacion.objects.create(mes=NOVIEMBRE, **extra) for _ in range(cantidad)]


# --- Criterio 1: los ítems agrupados comparten un grupo visible en cada uno ---


@pytest.mark.django_db
def test_tres_items_agrupados_comparten_el_grupo(operativo_client):
    items = _items(3)
    respuesta = _agrupar(operativo_client, items)
    assert respuesta.status_code == 201, respuesta.json()
    grupo = GrupoFactura.objects.get()
    assert respuesta.json() == {
        "id": grupo.pk,
        "codigo": f"G-{grupo.pk}",
        "mes": "2026-11",
        "items": sorted(item.pk for item in items),
    }
    assert grupo.mes == NOVIEMBRE
    for item in items:
        detalle = operativo_client.get(f"{URL_ITEMS}{item.pk}/").json()
        assert (detalle["grupo"], detalle["grupo_codigo"]) == (grupo.pk, f"G-{grupo.pk}")


@pytest.mark.django_db
def test_agrupar_con_un_item_ya_agrupado_suma_los_demas_a_ese_grupo(operativo_client):
    primero, segundo, tercero = _items(3)
    _agrupar(operativo_client, [primero, segundo])
    respuesta = _agrupar(operativo_client, [tercero, segundo])
    assert respuesta.status_code == 201
    grupo = GrupoFactura.objects.get()
    assert set(grupo.items.values_list("pk", flat=True)) == {primero.pk, segundo.pk, tercero.pk}


@pytest.mark.django_db
def test_agrupar_queda_auditado(operativo_client):
    item, otro = _items(2)
    _agrupar(operativo_client, [item, otro])
    grupo = GrupoFactura.objects.get()
    registro = RegistroAuditoria.objects.get(entidad_id=item.pk, campo="grupo")
    assert (registro.entidad, registro.valor_anterior, registro.valor_nuevo) == (
        "item_facturacion",
        "",
        f"G-{grupo.pk}",
    )


# --- Criterio 2: quitar del grupo deja el ítem independiente ---


@pytest.mark.django_db
def test_quitar_del_grupo_deja_el_item_independiente(operativo_client):
    item, otro, tercero = _items(3)
    _agrupar(operativo_client, [item, otro, tercero])
    grupo = GrupoFactura.objects.get()
    respuesta = _quitar(operativo_client, item)
    assert respuesta.status_code == 200
    assert (respuesta.json()["grupo"], respuesta.json()["grupo_codigo"]) == (None, None)
    assert set(grupo.items.values_list("pk", flat=True)) == {otro.pk, tercero.pk}
    registro = RegistroAuditoria.objects.filter(entidad_id=item.pk, campo="grupo").latest("id")
    assert (registro.valor_anterior, registro.valor_nuevo) == (f"G-{grupo.pk}", "")


@pytest.mark.django_db
def test_quitar_un_item_sin_grupo_se_rechaza(operativo_client):
    (item,) = _items(1)
    respuesta = _quitar(operativo_client, item)
    assert respuesta.status_code == 400
    assert respuesta.json() == {"grupo": ["El ítem no está en un grupo de factura."]}


@pytest.mark.django_db
def test_fuera_de_borrador_no_se_quita_del_grupo(operativo_client):
    item, otro = _items(2)
    _agrupar(operativo_client, [item, otro])
    ItemFacturacion.objects.filter(pk=item.pk).update(estado="enviado")
    assert _quitar(operativo_client, item).status_code == 400


# --- Validaciones del agrupado ---


@pytest.mark.django_db
def test_hacen_falta_al_menos_dos_items(operativo_client):
    (item,) = _items(1)
    respuesta = _agrupar(operativo_client, [item])
    assert respuesta.status_code == 400
    assert respuesta.json() == {"items": ["Elegí al menos dos ítems para agrupar."]}


@pytest.mark.django_db
def test_items_de_distinto_mes_no_se_agrupan(operativo_client):
    (item,) = _items(1)
    otro = ItemFacturacion.objects.create(mes=date(2026, 12, 1))
    respuesta = _agrupar(operativo_client, [item, otro])
    assert respuesta.status_code == 400
    assert respuesta.json() == {"items": ["Los ítems de un grupo tienen que ser del mismo mes."]}


@pytest.mark.django_db
def test_items_sin_mes_no_se_agrupan(operativo_client):
    (item,) = _items(1)
    otro = ItemFacturacion.objects.create(mes=None)
    assert _agrupar(operativo_client, [item, otro]).status_code == 400


@pytest.mark.django_db
def test_items_fuera_de_borrador_no_se_agrupan(operativo_client):
    (item,) = _items(1)
    (enviado,) = _items(1, estado="enviado")
    respuesta = _agrupar(operativo_client, [item, enviado])
    assert respuesta.status_code == 400
    assert respuesta.json() == {"items": ["Solo se agrupan ítems en Borrador."]}


@pytest.mark.django_db
def test_items_de_dos_grupos_distintos_no_se_agrupan(operativo_client):
    a, b, c, d = _items(4)
    _agrupar(operativo_client, [a, b])
    _agrupar(operativo_client, [c, d])
    respuesta = _agrupar(operativo_client, [a, c])
    assert respuesta.status_code == 400
    assert respuesta.json() == {"items": ["Los ítems ya están en dos grupos distintos."]}


@pytest.mark.django_db
@pytest.mark.parametrize("items", [None, "1,2", [1, "x"], [0, 1]])
def test_pedido_invalido_se_rechaza(operativo_client, items):
    respuesta = operativo_client.post(
        URL_GRUPOS, data=json.dumps({"items": items}), content_type="application/json"
    )
    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_un_item_inexistente_se_rechaza(operativo_client):
    (item,) = _items(1)
    respuesta = _agrupar(operativo_client, [item, 999999])
    assert respuesta.status_code == 400
    assert respuesta.json() == {"items": ["Alguno de los ítems no existe."]}


@pytest.mark.django_db
def test_lectura_no_agrupa_ni_quita(operativo_client, lector_client):
    item, otro = _items(2)
    assert _agrupar(lector_client, [item, otro]).status_code == 403
    _agrupar(operativo_client, [item, otro])
    assert _quitar(lector_client, item).status_code == 403


@pytest.mark.django_db
def test_el_grupo_no_se_edita_desde_el_item(operativo_client):
    item, otro = _items(2)
    _agrupar(operativo_client, [item, otro])
    grupo = GrupoFactura.objects.get()
    respuesta = operativo_client.patch(
        f"{URL_ITEMS}{item.pk}/",
        data=json.dumps({"grupo": None}),
        content_type="application/json",
    )
    assert respuesta.status_code == 200
    item.refresh_from_db()
    assert item.grupo_id == grupo.pk


@pytest.mark.django_db
def test_el_grupo_se_muestra_con_su_codigo():
    grupo = GrupoFactura.objects.create(mes=NOVIEMBRE)
    assert str(grupo) == f"G-{grupo.pk}"
