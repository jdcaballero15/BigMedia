"""Orden de publicidad y costos elegidos en el ítem a facturar (HU-060, HU-062, HU-063).

Unidad ajuste-item-op-y-costos: el PDF y los costos se guardan con el ítem, y con costos
elegidos los costos incluidos y su detalle se calculan solos.
"""

import io
import json
import threading
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import Client
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart
from openpyxl import load_workbook

from apps.auditoria.models import RegistroAuditoria
from apps.campanias.models import Campania
from apps.costos.models import Costo
from apps.facturacion import services
from apps.facturacion.models import CostoDeItem, ItemFacturacion, OrdenCompraPdf
from apps.inventario.models import Cartel, EstadoCartel, Formato, Proveedor, Zona
from apps.reservas.models import Reserva

URL = "/api/facturacion/items/"
ELEGIBLES = f"{URL}costos-elegibles/"
PDF = b"%PDF-1.4\n%prueba\n"


def _reserva(campania: Campania, direccion: str | None = None) -> Reserva:
    cartel = Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion=direccion or f"Dir {Cartel.objects.count() + 1}",
        capacidad=1,
        tarifa_lista=Decimal("1000.00"),
    )
    reserva = Reserva(
        campania=campania,
        cartel=cartel,
        fecha_inicio=date(2026, 11, 1),
        fecha_fin=date(2026, 11, 30),
        precio_alquiler=Decimal("1000.00"),
    )
    reserva.save()
    return reserva


def _costo(tipo: str, monto: str, campania: Campania | None = None, **campos: Any) -> Costo:
    return Costo.objects.create(
        reserva=_reserva(campania or Campania.objects.create(nombre="Otra")),
        tipo=tipo,
        monto=Decimal(monto),
        fecha=date(2026, 11, 1),
        **campos,
    )


def _item(**campos: Any) -> ItemFacturacion:
    return ItemFacturacion.objects.create(mes=date(2026, 11, 1), **campos)


def _post(client: Client, data: dict[str, Any]) -> Any:
    return client.post(URL, data=json.dumps(data), content_type="application/json")


def _patch(client: Client, item: ItemFacturacion, data: dict[str, Any]) -> Any:
    return client.patch(f"{URL}{item.pk}/", data=json.dumps(data), content_type="application/json")


def _pdf(contenido: bytes = PDF, nombre: str = "op.pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(nombre, contenido, content_type="application/pdf")


def _patch_multipart(client: Client, item: ItemFacturacion, data: dict[str, Any]) -> Any:
    # El cliente de pruebas no codifica solo un PATCH multipart: se arma como en un POST.
    cuerpo = encode_multipart(BOUNDARY, data)
    return client.patch(f"{URL}{item.pk}/", data=cuerpo, content_type=MULTIPART_CONTENT)


def _excel(client: Client) -> list[tuple[Any, ...]]:
    respuesta = client.get(f"{URL}planilla/?mes=2026-11")
    hoja = load_workbook(io.BytesIO(respuesta.content)).active
    assert hoja is not None
    return [fila for fila in hoja.iter_rows(values_only=True)]


# --- HU-060, criterio 11: impresión + fijación se suman y arman el detalle ---


@pytest.mark.django_db
@pytest.mark.regla("RN-024")
def test_costos_incluidos_con_impresion_y_fijacion_suma_y_arma_detalle(operativo_client):
    impresion = _costo("impresion", "50000.00")
    fijacion = _costo("fijacion", "30000.00")
    respuesta = _post(
        operativo_client,
        {"neto": "200000", "costos_incluidos": "1", "costos": [impresion.pk, fijacion.pk]},
    )
    assert respuesta.status_code == 201, respuesta.json()
    cuerpo = respuesta.json()
    assert cuerpo["costos_incluidos"] == "80000.00"
    assert cuerpo["detalle_costo"] == "Impresión + Fijación"
    assert cuerpo["costos_calculados"] is True
    assert [c["id"] for c in cuerpo["costos_elegidos"]] == [impresion.pk, fijacion.pk]
    listado = operativo_client.get(f"{URL}?mes=2026-11").json()
    assert (listado[0]["costos_incluidos"], listado[0]["detalle_costo"]) == (
        "80000.00",
        "Impresión + Fijación",
    )
    fila = _excel(operativo_client)[3]
    assert (fila[2], fila[3]) == (80000, "Impresión + Fijación")


@pytest.mark.django_db
def test_detalle_costo_no_repite_tipos(operativo_client):
    costos = [_costo("impresion", "10.00"), _costo("impresion", "20.00")]
    respuesta = _post(operativo_client, {"costos": [c.pk for c in costos]})
    assert respuesta.json()["detalle_costo"] == "Impresión"
    assert respuesta.json()["costos_incluidos"] == "30.00"


# --- HU-060, criterios 9 y 12: sin costos elegidos vale lo escrito a mano ---


@pytest.mark.django_db
def test_costos_incluidos_sin_costos_elegidos_usa_lo_escrito(operativo_client):
    respuesta = _post(operativo_client, {"costos_incluidos": "1500", "detalle_costo": "Flete"})
    cuerpo = respuesta.json()
    assert (cuerpo["costos_incluidos"], cuerpo["detalle_costo"]) == ("1500.00", "Flete")
    assert cuerpo["costos_calculados"] is False
    assert cuerpo["costos_elegidos"] == []
    assert not Costo.objects.exists()


@pytest.mark.django_db
def test_al_quitar_todos_los_costos_vuelve_lo_escrito_a_mano(operativo_client):
    item = _item(costos_incluidos=Decimal("1500.00"), detalle_costo="Flete")
    costo = _costo("impresion", "50000.00")
    con_costo = _patch(operativo_client, item, {"costos": [costo.pk]}).json()
    assert con_costo["costos_incluidos"] == "50000.00"
    sin_costos = _patch(operativo_client, item, {"costos": []}).json()
    assert (sin_costos["costos_incluidos"], sin_costos["detalle_costo"]) == ("1500.00", "Flete")
    assert sin_costos["costos_calculados"] is False


@pytest.mark.django_db
def test_con_costos_elegidos_lo_escrito_a_mano_no_se_pisa(operativo_client):
    item = _item(costos_incluidos=Decimal("1500.00"), detalle_costo="Flete")
    costo = _costo("impresion", "50000.00")
    _patch(
        operativo_client,
        item,
        {"costos": [costo.pk], "costos_incluidos": "50000.00", "detalle_costo": "Impresión"},
    )
    item.refresh_from_db()
    assert (item.costos_incluidos, item.detalle_costo) == (Decimal("1500.00"), "Flete")


@pytest.mark.django_db
def test_patch_sin_costos_conserva_los_elegidos(operativo_client):
    item = _item()
    costo = _costo("impresion", "50000.00")
    _patch(operativo_client, item, {"costos": [costo.pk]})
    cuerpo = _patch(operativo_client, item, {"neto": "1000"}).json()
    assert [c["id"] for c in cuerpo["costos_elegidos"]] == [costo.pk]


# --- HU-063, criterios 6 y 7: qué costos se pueden elegir ---


@pytest.mark.django_db
def test_costos_elegibles_de_otra_campania_aparecen(operativo_client):
    campania = Campania.objects.create(nombre="Verano Cuyo")
    costo = _costo(
        "impresion",
        "50000.00",
        campania=campania,
        proveedor=Proveedor.objects.create(nombre="Imprenta Andes"),
    )
    item = _item(campania=Campania.objects.create(nombre="Otra campaña"))
    respuesta = _patch(operativo_client, item, {"costos": [costo.pk]})
    assert respuesta.status_code == 200, respuesta.json()
    elegibles = operativo_client.get(ELEGIBLES).json()
    assert elegibles == []
    _patch(operativo_client, item, {"costos": []})
    fila = operativo_client.get(ELEGIBLES).json()[0]
    assert fila["id"] == costo.pk
    assert fila["campania_nombre"] == "Verano Cuyo"
    assert fila["a_quien"] == "Imprenta Andes"
    assert (fila["tipo_nombre"], fila["monto"], fila["propio"]) == ("Impresión", "50000.00", False)


@pytest.mark.django_db
@pytest.mark.parametrize("busqueda", ["verano", "san martin", "impres", "andes"])
def test_costos_elegibles_se_buscan_por_campania_cartel_tipo_o_destinatario(
    operativo_client, busqueda
):
    campania = Campania.objects.create(nombre="Verano Cuyo")
    buscado = Costo.objects.create(
        reserva=_reserva(campania, direccion="San Martín 100"),
        tipo="impresion",
        monto=Decimal("10.00"),
        fecha=date(2026, 11, 1),
        destinatario="Gráfica Andes",
    )
    _costo("comision", "5.00")
    ids = [c["id"] for c in operativo_client.get(f"{ELEGIBLES}?q={busqueda}").json()]
    assert ids == [buscado.pk]


@pytest.mark.django_db
def test_costos_elegibles_anulado_o_en_otro_item_no_aparece(operativo_client):
    libre = _costo("impresion", "10.00")
    anulado = _costo("fijacion", "20.00", anulado=True, motivo_anulacion="error")
    en_otro = _costo("otro", "30.00")
    _patch(operativo_client, _item(), {"costos": [en_otro.pk]})
    ids = [c["id"] for c in operativo_client.get(ELEGIBLES).json()]
    assert ids == [libre.pk]
    assert anulado.pk not in ids


@pytest.mark.django_db
def test_no_se_elige_un_costo_anulado_ni_uno_de_otro_item(operativo_client):
    anulado = _costo("fijacion", "20.00", anulado=True, motivo_anulacion="error")
    en_otro = _costo("otro", "30.00")
    _patch(operativo_client, _item(), {"costos": [en_otro.pk]})
    item = _item()
    for costo in (anulado, en_otro):
        respuesta = _patch(operativo_client, item, {"costos": [costo.pk]})
        assert respuesta.status_code == 400
        assert "costos" in respuesta.json()
    assert not CostoDeItem.objects.filter(item=item).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("valor", ["1", [0], ["a"], [True], {"id": 1}, [99999]])
def test_costos_invalidos_da_400(operativo_client, valor):
    respuesta = _post(operativo_client, {"costos": valor})
    assert respuesta.status_code == 400
    assert "costos" in respuesta.json()
    assert not ItemFacturacion.objects.exists()


@pytest.mark.django_db
def test_el_lector_ve_los_elegibles_pero_no_elige(lector_client):
    costo = _costo("impresion", "10.00")
    assert lector_client.get(ELEGIBLES).status_code == 200
    item = _item()
    assert _patch(lector_client, item, {"costos": [costo.pk]}).status_code == 403


# --- HU-063, criterio 8: quitar un costo lo libera sin anularlo ---


@pytest.mark.django_db
def test_quitar_costo_lo_libera_sin_anularlo_y_audita(operativo_client):
    costo = _costo("impresion", "50000.00")
    item = _item()
    _patch(operativo_client, item, {"costos": [costo.pk]})
    _patch(operativo_client, item, {"costos": []})
    costo.refresh_from_db()
    assert costo.anulado is False
    vinculo = CostoDeItem.objects.get(costo=costo)
    assert vinculo.quitado_en is not None
    assert vinculo.quitado_por is not None
    cambios = RegistroAuditoria.objects.filter(
        entidad="item_facturacion", entidad_id=item.pk, campo="costos"
    ).values_list("valor_nuevo", flat=True)
    assert any((valor or "").startswith("Vínculo:") for valor in cambios)
    assert any((valor or "").startswith("Quitado:") for valor in cambios)
    otro = _item()
    assert _patch(operativo_client, otro, {"costos": [costo.pk]}).status_code == 200
    assert CostoDeItem.objects.filter(costo=costo).count() == 2


@pytest.mark.django_db
def test_un_costo_propio_del_item_no_se_quita(operativo_client):
    item = _item(neto=Decimal("10000.00"))
    operativo_client.post(
        f"{URL}{item.pk}/costos/",
        data=json.dumps({"tipo": "comision", "porcentaje": "15"}),
        content_type="application/json",
    )
    propio = Costo.objects.get()
    cuerpo = _patch(operativo_client, item, {"costos": []}).json()
    assert [c["id"] for c in cuerpo["costos_elegidos"]] == [propio.pk]
    assert cuerpo["costos_elegidos"][0]["propio"] is True
    assert cuerpo["costos_incluidos"] == "1500.00"


# --- HU-063, criterio 9: un costo anulado en el módulo deja de sumar ---


@pytest.mark.django_db
def test_costo_anulado_en_modulo_deja_de_sumar(operativo_client):
    impresion = _costo("impresion", "50000.00")
    fijacion = _costo("fijacion", "30000.00")
    item = _item()
    _patch(operativo_client, item, {"costos": [impresion.pk, fijacion.pk]})
    fijacion.anulado = True
    fijacion.save()
    cuerpo = operativo_client.get(f"{URL}{item.pk}/").json()
    assert (cuerpo["costos_incluidos"], cuerpo["detalle_costo"]) == ("50000.00", "Impresión")
    assert cuerpo["costo_total"] == "50000.00"


@pytest.mark.django_db
def test_totales_del_mes_no_cuentan_costos_quitados(operativo_client):
    costo = _costo("impresion", "50000.00")
    item = _item(neto=Decimal("100000.00"))
    _patch(operativo_client, item, {"costos": [costo.pk]})
    _patch(operativo_client, item, {"costos": []})
    totales = operativo_client.get(f"{URL}totales/?mes=2026-11").json()
    assert (totales["costos"], totales["neto_final"]) == ("0.00", "100000.00")
    assert operativo_client.get(f"{URL}{item.pk}/").json()["costo_total"] == "0.00"


# --- HU-062, criterio 5, y decisión 4: PDF y costos se guardan con el ítem ---


@pytest.mark.django_db
def test_guardar_item_nuevo_con_pdf_y_costos(operativo_client):
    costo = _costo("impresion", "50000.00")
    datos_multipart = {
        "neto": "200000",
        "cliente": "",
        "costos": json.dumps([costo.pk]),
        "orden_publicidad": _pdf(),
    }
    respuesta = operativo_client.post(URL, data=datos_multipart)
    assert respuesta.status_code == 201, respuesta.json()
    datos = respuesta.json()
    assert datos["orden_compra_pdf"] == {"nombre": "op.pdf", "tamanio": len(PDF)}
    assert datos["costos_incluidos"] == "50000.00"
    assert datos["cliente"] is None
    pdf = operativo_client.get(f"{URL}{datos['id']}/orden-compra-pdf/")
    assert pdf.status_code == 200
    assert pdf.content == PDF


@pytest.mark.django_db
def test_adjuntar_otro_pdf_reemplaza_al_anterior(operativo_client):
    item = _item()
    _patch_multipart(operativo_client, item, {"orden_publicidad": _pdf(nombre="primera.pdf")})
    respuesta = _patch_multipart(
        operativo_client, item, {"orden_publicidad": _pdf(nombre="segunda.pdf")}
    )
    assert respuesta.json()["orden_compra_pdf"]["nombre"] == "segunda.pdf"
    assert OrdenCompraPdf.objects.filter(item=item).count() == 1


@pytest.mark.django_db
def test_guardar_item_con_pdf_invalido_no_guarda_nada(operativo_client):
    costo = _costo("impresion", "50000.00")
    datos_multipart = {
        "neto": "200000",
        "costos": json.dumps([costo.pk]),
        "orden_publicidad": _pdf(b"no es pdf", "op.txt"),
    }
    respuesta = operativo_client.post(URL, data=datos_multipart)
    assert respuesta.status_code == 400
    assert "orden_publicidad" in respuesta.json()
    assert not ItemFacturacion.objects.exists()
    assert not CostoDeItem.objects.exists()


@pytest.mark.django_db
def test_editar_con_costo_invalido_no_cambia_el_item_ni_el_pdf(operativo_client):
    item = _item(neto=Decimal("10.00"))
    anulado = _costo("fijacion", "20.00", anulado=True, motivo_anulacion="error")
    respuesta = _patch_multipart(
        operativo_client,
        item,
        {"neto": "99", "costos": json.dumps([anulado.pk]), "orden_publicidad": _pdf()},
    )
    assert respuesta.status_code == 400
    item.refresh_from_db()
    assert item.neto == Decimal("10.00")
    assert not OrdenCompraPdf.objects.exists()


@pytest.mark.django_db
def test_el_pdf_del_item_queda_auditado(operativo_client):
    item = _item()
    _patch_multipart(operativo_client, item, {"orden_publicidad": _pdf()})
    assert RegistroAuditoria.objects.filter(
        entidad="item_facturacion", entidad_id=item.pk, campo="orden_compra_pdf"
    ).exists()


# --- Concurrencia: dos ítems eligen el mismo costo a la vez ---


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_dos_items_que_eligen_el_mismo_costo_a_la_vez_solo_uno_lo_obtiene(django_user_model):
    usuario = django_user_model.objects.create_user(username="seba", password="x")
    costo = _costo("impresion", "10.00")
    items = [_item(), _item()]
    resultados: list[str] = []
    barrera = threading.Barrier(2)

    def elegir(item: ItemFacturacion) -> None:
        barrera.wait()
        try:
            services.elegir_costos(item.pk, [costo.pk], usuario)
            resultados.append("ok")
        except Exception as error:  # noqa: BLE001  # se cuenta cualquier rechazo del segundo
            resultados.append(type(error).__name__)
        finally:
            connection.close()

    hilos = [threading.Thread(target=elegir, args=(item,)) for item in items]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()
    assert sorted(resultados) == ["ValidationError", "ok"]
    assert CostoDeItem.objects.filter(costo=costo, quitado_en__isnull=True).count() == 1
