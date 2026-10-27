"""Costos del ítem a facturar y neto final (HU-063; HU-066, criterio 1)."""

import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.test import Client

from apps.auditoria.models import RegistroAuditoria
from apps.campanias.models import Campania
from apps.costos.models import Costo
from apps.facturacion.models import CostoDeItem, ItemFacturacion
from apps.inventario.models import Cartel, EstadoCartel, Formato, Proveedor, Zona
from apps.reservas.models import Reserva

URL = "/api/facturacion/items/"


def _url(item: ItemFacturacion, resto: str = "") -> str:
    return f"{URL}{item.pk}/costos/{resto}"


def _post(client: Client, url: str, data: dict[str, Any]) -> Any:
    return client.post(url, data=json.dumps(data), content_type="application/json")


def _item(neto: str | None = "10000.00", **campos: Any) -> ItemFacturacion:
    return ItemFacturacion.objects.create(
        mes=date(2026, 11, 1), neto=Decimal(neto) if neto is not None else None, **campos
    )


def _reserva(campania: Campania, precio: str = "1000.00") -> Reserva:
    cartel = Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion=f"Dir {Cartel.objects.count() + 1}",
        capacidad=1,
        tarifa_lista=Decimal(precio),
    )
    reserva = Reserva(
        campania=campania,
        cartel=cartel,
        fecha_inicio=date(2026, 11, 1),
        fecha_fin=date(2026, 11, 30),
        precio_alquiler=Decimal(precio),
    )
    reserva.save()
    return reserva


def _detalle(client: Client, item: ItemFacturacion) -> dict[str, Any]:
    cuerpo: dict[str, Any] = client.get(f"{URL}{item.pk}/").json()
    return cuerpo


# --- Criterio 1: un costo en porcentaje del neto ---


@pytest.mark.django_db
def test_costo_en_porcentaje_del_neto_da_1500_y_neto_final_8500(operativo_client):
    item = _item()
    respuesta = _post(
        operativo_client,
        _url(item),
        {"tipo": "comision", "destinatario": "Agencia Sur", "porcentaje": "15"},
    )
    assert respuesta.status_code == 201, respuesta.json()
    costo = respuesta.json()
    assert (costo["monto"], costo["porcentaje"], costo["tipo_nombre"]) == (
        "1500.00",
        "15.00",
        "Comisión",
    )
    assert costo["destinatario"] == "Agencia Sur"
    detalle = _detalle(operativo_client, item)
    assert (detalle["costo_total"], detalle["neto_final"]) == ("1500.00", "8500.00")


@pytest.mark.django_db
def test_el_costo_del_item_es_un_costo_sin_reserva_vinculado_al_item(operativo_client):
    item = _item()
    _post(operativo_client, _url(item), {"tipo": "comision", "porcentaje": "15"})
    costo = Costo.objects.get()
    assert costo.reserva is None
    assert CostoDeItem.objects.get(costo=costo).item == item
    assert RegistroAuditoria.objects.filter(
        entidad="item_facturacion", entidad_id=item.pk, campo="costos"
    ).exists()


@pytest.mark.django_db
def test_porcentaje_sin_neto_da_monto_cero(operativo_client):
    item = _item(neto=None)
    respuesta = _post(operativo_client, _url(item), {"tipo": "comision", "porcentaje": "15"})
    assert respuesta.status_code == 201
    assert respuesta.json()["monto"] == "0.00"
    detalle = _detalle(operativo_client, item)
    assert (detalle["costo_total"], detalle["neto_final"]) == ("0.00", None)


# --- Criterio 2: un costo fijo se resta tal cual ---


@pytest.mark.django_db
def test_costo_fijo_se_resta_tal_cual_del_neto(operativo_client):
    item = _item()
    proveedor = Proveedor.objects.create(nombre="Imprenta Cuyo")
    respuesta = _post(
        operativo_client,
        _url(item),
        {"tipo": "impresion", "proveedor": proveedor.pk, "monto": "1234.56"},
    )
    assert respuesta.status_code == 201, respuesta.json()
    assert respuesta.json()["proveedor_nombre"] == "Imprenta Cuyo"
    assert respuesta.json()["porcentaje"] is None
    detalle = _detalle(operativo_client, item)
    assert (detalle["costo_total"], detalle["neto_final"]) == ("1234.56", "8765.44")


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("datos", "campo"),
    [
        ({"tipo": "comision"}, "monto"),
        ({"tipo": "comision", "monto": "10", "porcentaje": "5"}, "monto"),
        ({"tipo": "comision", "monto": "0"}, "monto"),
        ({"tipo": "comision", "porcentaje": "0"}, "porcentaje"),
        ({"tipo": "comision", "porcentaje": "100.01"}, "porcentaje"),
        ({"monto": "10"}, "tipo"),
        ({"tipo": "inventado", "monto": "10"}, "tipo"),
        ({"tipo": "otro", "monto": "10", "proveedor": 999999}, "proveedor"),
    ],
)
def test_alta_de_costo_invalida_da_400(operativo_client, datos, campo):
    respuesta = _post(operativo_client, _url(_item()), datos)
    assert respuesta.status_code == 400
    assert campo in respuesta.json()
    assert not Costo.objects.exists()


@pytest.mark.django_db
def test_alta_de_costo_con_proveedor_inactivo_da_400(operativo_client):
    proveedor = Proveedor.objects.create(nombre="Viejo", activo=False)
    respuesta = _post(
        operativo_client, _url(_item()), {"tipo": "otro", "monto": "10", "proveedor": proveedor.pk}
    )
    assert respuesta.status_code == 400
    assert "proveedor" in respuesta.json()


@pytest.mark.django_db
def test_no_se_cargan_costos_en_un_item_fuera_de_borrador(operativo_client):
    item = _item(estado="enviado")
    respuesta = _post(operativo_client, _url(item), {"tipo": "otro", "monto": "10"})
    assert respuesta.status_code == 400
    assert "estado" in respuesta.json()


@pytest.mark.django_db
def test_el_lector_no_carga_costos(lector_client):
    respuesta = _post(lector_client, _url(_item()), {"tipo": "otro", "monto": "10"})
    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_costos_de_un_item_inexistente_da_404(operativo_client):
    assert operativo_client.get(f"{URL}999999/costos/").status_code == 404


# --- Criterio 3: cambiar el neto recalcula los porcentuales ---


@pytest.mark.django_db
def test_cambiar_el_neto_recalcula_los_costos_porcentuales(operativo_client):
    item = _item()
    _post(operativo_client, _url(item), {"tipo": "comision", "porcentaje": "15"})
    _post(operativo_client, _url(item), {"tipo": "otro", "monto": "100.00"})
    respuesta = operativo_client.patch(
        f"{URL}{item.pk}/", data=json.dumps({"neto": "20000.00"}), content_type="application/json"
    )
    assert respuesta.status_code == 200
    assert (respuesta.json()["costo_total"], respuesta.json()["neto_final"]) == (
        "3100.00",
        "16900.00",
    )
    montos = sorted(Costo.objects.values_list("monto", flat=True))
    assert montos == [Decimal("100.00"), Decimal("3000.00")]


@pytest.mark.django_db
def test_el_porcentaje_se_redondea_al_centavo(operativo_client):
    item = _item(neto="333.33")
    respuesta = _post(operativo_client, _url(item), {"tipo": "comision", "porcentaje": "15"})
    assert respuesta.json()["monto"] == "50.00"


# --- Criterio 4: un costo de reserva vinculado cuenta una sola vez ---


@pytest.mark.django_db
def test_costo_de_reserva_vinculado_cuenta_una_vez_en_la_campania(operativo_client):
    campania = Campania.objects.create()
    reserva = _reserva(campania)
    de_reserva = Costo.objects.create(
        reserva=reserva, tipo="impresion", monto=Decimal("300.00"), fecha=date(2026, 11, 1)
    )
    item = _item(campania=campania)
    vinculado = _post(operativo_client, _url(item, "vincular/"), {"costo": de_reserva.pk})
    assert vinculado.status_code == 201, vinculado.json()
    assert vinculado.json()["reserva"] == reserva.pk
    _post(operativo_client, _url(item), {"tipo": "comision", "porcentaje": "10"})

    detalle = _detalle(operativo_client, item)
    assert (detalle["costo_total"], detalle["neto_final"]) == ("1300.00", "8700.00")
    assert Costo.objects.count() == 2
    margen = operativo_client.get(f"/api/costos/campania/?campania={campania.pk}").json()
    assert margen["costo"] == "300.00"


@pytest.mark.django_db
def test_los_costos_vinculables_son_los_de_las_reservas_de_la_campania(operativo_client):
    campania = Campania.objects.create()
    reserva = _reserva(campania)
    libre = Costo.objects.create(
        reserva=reserva, tipo="impresion", monto=Decimal("1.00"), fecha=date(2026, 11, 1)
    )
    Costo.objects.create(
        reserva=reserva, tipo="otro", monto=Decimal("1.00"), fecha=date(2026, 11, 1), anulado=True
    )
    Costo.objects.create(
        reserva=_reserva(Campania.objects.create()),
        tipo="otro",
        monto=Decimal("1.00"),
        fecha=date(2026, 11, 1),
    )
    item = _item(campania=campania)
    respuesta = operativo_client.get(_url(item, "vinculables/"))
    assert respuesta.status_code == 200
    assert [c["id"] for c in respuesta.json()] == [libre.pk]
    _post(operativo_client, _url(item, "vincular/"), {"costo": libre.pk})
    assert operativo_client.get(_url(item, "vinculables/")).json() == []


@pytest.mark.django_db
def test_no_se_vincula_un_costo_de_otra_campania_ni_dos_veces(operativo_client):
    campania = Campania.objects.create()
    ajeno = Costo.objects.create(
        reserva=_reserva(Campania.objects.create()),
        tipo="otro",
        monto=Decimal("1.00"),
        fecha=date(2026, 11, 1),
    )
    propio = Costo.objects.create(
        reserva=_reserva(campania), tipo="otro", monto=Decimal("1.00"), fecha=date(2026, 11, 1)
    )
    item = _item(campania=campania)
    otro_item = _item(campania=campania)
    assert _post(operativo_client, _url(item, "vincular/"), {"costo": ajeno.pk}).status_code == 400
    assert _post(operativo_client, _url(item, "vincular/"), {"costo": propio.pk}).status_code == 201
    repetido = _post(operativo_client, _url(otro_item, "vincular/"), {"costo": propio.pk})
    assert repetido.status_code == 400
    assert "costo" in repetido.json()


@pytest.mark.django_db
@pytest.mark.parametrize("valor", [None, "x", 0, True])
def test_vincular_exige_un_costo_valido(operativo_client, valor):
    item = _item(campania=Campania.objects.create())
    respuesta = _post(operativo_client, _url(item, "vincular/"), {"costo": valor})
    assert respuesta.status_code == 400
    assert "costo" in respuesta.json()


@pytest.mark.django_db
def test_no_se_vincula_un_costo_anulado_ni_en_un_item_sin_campania(operativo_client):
    campania = Campania.objects.create()
    anulado = Costo.objects.create(
        reserva=_reserva(campania),
        tipo="otro",
        monto=Decimal("1.00"),
        fecha=date(2026, 11, 1),
        anulado=True,
    )
    con_campania = _item(campania=campania)
    respuesta = _post(operativo_client, _url(con_campania, "vincular/"), {"costo": anulado.pk})
    assert respuesta.status_code == 400
    sin_campania = _post(operativo_client, _url(_item(), "vincular/"), {"costo": anulado.pk})
    assert sin_campania.status_code == 400
    assert "campania" in sin_campania.json()
    assert operativo_client.get(_url(_item(), "vinculables/")).json() == []


# --- Anulación ---


@pytest.mark.django_db
def test_anular_un_costo_del_item_deja_de_sumar(operativo_client):
    item = _item()
    creado = _post(operativo_client, _url(item), {"tipo": "otro", "monto": "100.00"}).json()
    sin_motivo = _post(operativo_client, _url(item, f"{creado['id']}/anular/"), {"motivo": " "})
    assert sin_motivo.status_code == 400
    anulado = _post(
        operativo_client, _url(item, f"{creado['id']}/anular/"), {"motivo": "Carga duplicada"}
    )
    assert anulado.status_code == 200, anulado.json()
    assert (anulado.json()["anulado"], anulado.json()["motivo_anulacion"]) == (
        True,
        "Carga duplicada",
    )
    assert _detalle(operativo_client, item)["costo_total"] == "0.00"
    listado = operativo_client.get(_url(item)).json()
    assert [c["anulado"] for c in listado] == [True]
    repetido = _post(operativo_client, _url(item, f"{creado['id']}/anular/"), {"motivo": "Otra"})
    assert repetido.status_code == 400


@pytest.mark.django_db
def test_un_costo_de_reserva_vinculado_se_anula_desde_costos(operativo_client):
    campania = Campania.objects.create()
    costo = Costo.objects.create(
        reserva=_reserva(campania), tipo="otro", monto=Decimal("1.00"), fecha=date(2026, 11, 1)
    )
    item = _item(campania=campania)
    _post(operativo_client, _url(item, "vincular/"), {"costo": costo.pk})
    respuesta = _post(operativo_client, _url(item, f"{costo.pk}/anular/"), {"motivo": "No va"})
    assert respuesta.status_code == 400
    costo.refresh_from_db()
    assert costo.anulado is False


@pytest.mark.django_db
def test_no_se_anula_un_costo_de_otro_item(operativo_client):
    item = _item()
    ajeno = _post(operativo_client, _url(_item()), {"tipo": "otro", "monto": "1.00"}).json()
    respuesta = _post(operativo_client, _url(item, f"{ajeno['id']}/anular/"), {"motivo": "x"})
    assert respuesta.status_code == 404


# --- Criterio 5: totales del mes ---


@pytest.mark.django_db
def test_totales_del_mes_suman_costos_y_neto_final_sin_anulados(operativo_client):
    uno = _item(neto="10000.00")
    dos = _item(neto="5000.00")
    anulado = _item(neto="700.00")
    _post(operativo_client, _url(uno), {"tipo": "comision", "porcentaje": "15"})
    _post(operativo_client, _url(dos), {"tipo": "otro", "monto": "200.00"})
    descartado = _post(operativo_client, _url(dos), {"tipo": "otro", "monto": "999.00"}).json()
    _post(operativo_client, _url(dos, f"{descartado['id']}/anular/"), {"motivo": "Error"})
    _post(operativo_client, _url(anulado), {"tipo": "otro", "monto": "50.00"})
    ItemFacturacion.objects.filter(pk=anulado.pk).update(estado="anulado")

    totales = operativo_client.get(f"{URL}totales/?mes=2026-11").json()
    assert (totales["neto"], totales["costos"], totales["neto_final"]) == (
        "15000.00",
        "1700.00",
        "13300.00",
    )
    listado = operativo_client.get(f"{URL}?mes=2026-11").json()
    no_anulados = [i for i in listado if i["estado"] != "anulado"]
    assert sum(Decimal(i["costo_total"]) for i in no_anulados) == Decimal(totales["costos"])
    assert sum(Decimal(i["neto_final"]) for i in no_anulados) == Decimal(totales["neto_final"])


# --- El módulo de costos sigue siendo de reservas ---


@pytest.mark.django_db
def test_el_listado_de_costos_no_muestra_los_costos_del_item(operativo_client):
    _post(operativo_client, _url(_item()), {"tipo": "otro", "monto": "1.00"})
    assert operativo_client.get("/api/costos/costos/").json() == []


@pytest.mark.django_db
def test_el_modulo_de_costos_exige_la_reserva(operativo_client):
    respuesta = _post(operativo_client, "/api/costos/costos/", {"tipo": "otro", "monto": "1.00"})
    assert respuesta.status_code == 400
    assert "reserva" in respuesta.json()
