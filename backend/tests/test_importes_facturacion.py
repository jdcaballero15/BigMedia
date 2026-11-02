"""Cálculo de neto, IVA y total de los ítems a facturar (HU-061)."""

import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.test import Client

from apps.facturacion.models import ItemFacturacion

URL = "/api/facturacion/items/"


def _post(client: Client, data: dict[str, Any]) -> Any:
    respuesta = client.post(URL, data=json.dumps(data), content_type="application/json")
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def _patch(client: Client, pk: int, data: dict[str, Any]) -> Any:
    respuesta = client.patch(f"{URL}{pk}/", data=json.dumps(data), content_type="application/json")
    assert respuesta.status_code == 200, respuesta.json()
    return respuesta.json()


def _importes(cuerpo: dict[str, Any]) -> tuple[str, str, str]:
    return cuerpo["neto"], cuerpo["iva"], cuerpo["total"]


@pytest.mark.django_db
@pytest.mark.regla("RN-023")
def test_cantidad_por_precio_con_iva_21(operativo_client):
    cuerpo = _post(operativo_client, {"cantidad": "10", "precio_unitario": "1000"})
    assert _importes(cuerpo) == ("10000.00", "2100.00", "12100.00")


@pytest.mark.django_db
def test_neto_a_mano_se_respeta_y_recalcula_iva_y_total(operativo_client):
    cuerpo = _post(
        operativo_client, {"cantidad": "10", "precio_unitario": "1000", "neto": "9500.00"}
    )
    assert _importes(cuerpo) == ("9500.00", "1995.00", "11495.00")
    # Editar otra cosa no pisa el neto cargado a mano.
    cuerpo = _patch(operativo_client, cuerpo["id"], {"descripcion": "Con descuento"})
    assert cuerpo["neto"] == "9500.00"


@pytest.mark.django_db
def test_solo_neto_sin_cantidad_ni_precio(operativo_client):
    cuerpo = _post(operativo_client, {"neto": "1234.56"})
    assert _importes(cuerpo) == ("1234.56", "259.26", "1493.82")


@pytest.mark.django_db
@pytest.mark.regla("RN-023")
def test_cambio_de_alicuota_recalcula(operativo_client):
    cuerpo = _post(operativo_client, {"neto": "1000.00"})
    cuerpo = _patch(operativo_client, cuerpo["id"], {"alicuota_iva": "10.5"})
    assert _importes(cuerpo) == ("1000.00", "105.00", "1105.00")
    cuerpo = _patch(operativo_client, cuerpo["id"], {"alicuota_iva": "0"})
    assert _importes(cuerpo) == ("1000.00", "0.00", "1000.00")


@pytest.mark.django_db
def test_cambiar_cantidad_recalcula_el_neto(operativo_client):
    cuerpo = _post(operativo_client, {"cantidad": "10", "precio_unitario": "1000"})
    cuerpo = _patch(operativo_client, cuerpo["id"], {"cantidad": "3"})
    assert _importes(cuerpo) == ("3000.00", "630.00", "3630.00")


@pytest.mark.django_db
def test_redondeo_al_centavo_hacia_arriba_en_la_mitad(operativo_client):
    cuerpo = _post(operativo_client, {"cantidad": "3", "precio_unitario": "0.35"})
    # 1.05 al 21 % = 0.2205, que redondea a 0.22; 0.025 redondea a 0.03.
    assert _importes(cuerpo) == ("1.05", "0.22", "1.27")
    cuerpo = _post(operativo_client, {"neto": "0.50", "alicuota_iva": "5"})
    assert cuerpo["iva"] == "0.03"


@pytest.mark.django_db
def test_iva_y_total_no_se_escriben_desde_la_api(operativo_client):
    cuerpo = _post(operativo_client, {"neto": "100.00", "iva": "999.00", "total": "1.00"})
    assert _importes(cuerpo) == ("100.00", "21.00", "121.00")


@pytest.mark.django_db
def test_importes_negativos_o_alicuota_fuera_de_rango_se_rechazan(operativo_client):
    for datos in ({"neto": "-1"}, {"precio_unitario": "-5"}, {"alicuota_iva": "101"}):
        respuesta = operativo_client.post(
            URL, data=json.dumps(datos), content_type="application/json"
        )
        assert respuesta.status_code == 400, datos


@pytest.mark.django_db
def test_importes_se_guardan_como_decimal():
    item = ItemFacturacion.objects.create(neto=Decimal("10.10"), alicuota_iva=Decimal("21"))
    item.refresh_from_db()
    assert isinstance(item.total, Decimal)
    assert item.total == Decimal("12.22")


# --- Totales del mes (HU-065, criterio 3) ---


@pytest.mark.django_db
def test_totales_del_mes_no_suman_los_anulados(operativo_client):
    ItemFacturacion.objects.create(mes=date(2026, 11, 1), neto=Decimal("1000.00"))
    ItemFacturacion.objects.create(
        mes=date(2026, 11, 1), neto=Decimal("500.00"), estado="facturado", numero_factura="A-1"
    )
    ItemFacturacion.objects.create(mes=date(2026, 11, 1), neto=Decimal("700.00"), estado="anulado")
    ItemFacturacion.objects.create(mes=date(2026, 11, 1))
    ItemFacturacion.objects.create(mes=date(2026, 12, 1), neto=Decimal("9.00"))
    cuerpo = operativo_client.get(f"{URL}totales/?mes=2026-11").json()
    assert cuerpo == {
        "mes": "2026-11",
        "cantidad": 3,
        "neto": "1500.00",
        "iva": "315.00",
        "total": "1815.00",
        "costos": "0.00",
        "neto_final": "1500.00",
    }
    # Los anulados siguen en el listado del mes.
    assert len(operativo_client.get(f"{URL}?mes=2026-11").json()) == 4


@pytest.mark.django_db
@pytest.mark.parametrize("params", ["", "?mes=2026-13"])
def test_totales_exigen_un_mes_valido(operativo_client, params):
    respuesta = operativo_client.get(f"{URL}totales/{params}")
    assert respuesta.status_code == 400
    assert "mes" in respuesta.json()
