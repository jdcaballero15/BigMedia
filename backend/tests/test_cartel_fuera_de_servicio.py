"""Cartel fuera de servicio con reservas activas (HU-039, RN-010)."""

import json
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import pytest
from django.test import Client
from django.utils import timezone

from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas import services
from apps.reservas.models import Reserva
from apps.reservas.serializers import ReservaSerializer

RESERVAS = "/api/reservas/reservas/"


@pytest.fixture
def formato() -> Formato:
    return Formato.objects.create(nombre="Gran Formato Prueba", modalidad="fija")


def _cartel(formato: Formato, direccion: str = "Av. Rota 1", estado: str = "activo") -> Cartel:
    return Cartel.objects.create(
        formato=formato,
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo=estado),
        direccion=direccion,
        tamano="8x3",
        capacidad=2,
        tarifa_lista=Decimal("1000.00"),
    )


def _campania() -> Campania:
    cliente = Cliente.objects.create(nombre="Cliente Prueba")
    marca = Marca.objects.create(nombre="Marca Prueba", cliente=cliente)
    return Campania.objects.create(nombre="Verano", marca=marca)


def _reserva(cartel: Cartel, inicio: date, fin: date, estado: str = "confirmada") -> Reserva:
    reserva = Reserva(
        campania=_campania(), cartel=cartel, fecha_inicio=inicio, fecha_fin=fin, estado=estado
    )
    reserva.save()
    return reserva


def _apagar(cartel: Cartel, codigo: str = "apagado") -> None:
    cartel.estado = EstadoCartel.objects.get(codigo=codigo)
    cartel.save()


def _json(client: Client, metodo: str, url: str, datos: dict[str, Any]) -> Any:
    enviar = getattr(client, metodo)
    return enviar(url, data=json.dumps(datos), content_type="application/json")


def _alta(client: Client, cartel: Cartel, campania: Campania) -> Any:
    datos = {
        "campania": campania.pk,
        "cartel": cartel.pk,
        "fecha_inicio": "2026-12-01",
        "fecha_fin": "2026-12-31",
    }
    return _json(client, "post", RESERVAS, datos)


# --- Criterio 2: un cartel no operativo no se reserva ---


@pytest.mark.django_db
@pytest.mark.regla("RN-010")
@pytest.mark.parametrize("codigo", ["mantenimiento", "apagado", "vidrio_destruido"])
def test_crear_reserva_cartel_no_operativo_rechaza(operativo_client, formato, codigo):
    cartel = _cartel(formato, estado=codigo)
    respuesta = _alta(operativo_client, cartel, _campania())
    assert respuesta.status_code == 400
    nombre = EstadoCartel.objects.get(codigo=codigo).nombre
    assert respuesta.json()["cartel"] == [
        f"El cartel está fuera de servicio ({nombre}): no se puede reservar hasta que vuelva "
        "a un estado operativo."
    ]


@pytest.mark.django_db
@pytest.mark.regla("RN-010")
def test_crear_reserva_cartel_de_baja_conserva_mensaje(operativo_client, formato):
    cartel = _cartel(formato, estado="baja")
    respuesta = _alta(operativo_client, cartel, _campania())
    assert respuesta.status_code == 400
    assert respuesta.json()["cartel"] == ["El cartel está de baja: no se puede reservar."]


# --- Criterio 3: vuelve a Activo y se puede reservar ---


@pytest.mark.django_db
@pytest.mark.regla("RN-010")
def test_crear_reserva_cartel_vuelve_a_activo_permite(operativo_client, formato):
    cartel = _cartel(formato, estado="mantenimiento")
    campania = _campania()
    assert _alta(operativo_client, cartel, campania).status_code == 400
    _apagar(cartel, "activo")
    assert _alta(operativo_client, cartel, campania).status_code == 201


# --- Las reservas que ya estaban no se modifican ni se traban ---


@pytest.mark.django_db
@pytest.mark.regla("RN-010")
def test_mover_reserva_a_cartel_no_operativo_rechaza(operativo_client, formato):
    sano = _cartel(formato, "Av. Sana 1")
    roto = _cartel(formato, "Av. Rota 2", estado="vidrio_destruido")
    reserva = _reserva(sano, date(2026, 12, 1), date(2026, 12, 31), estado="pendiente")
    respuesta = _json(operativo_client, "patch", f"{RESERVAS}{reserva.pk}/", {"cartel": roto.pk})
    assert respuesta.status_code == 400
    assert "cartel" in respuesta.json()


@pytest.mark.django_db
@pytest.mark.regla("RN-010")
def test_editar_reserva_en_cartel_no_operativo_permite(operativo_client, formato):
    cartel = _cartel(formato)
    reserva = _reserva(cartel, date(2026, 12, 1), date(2026, 12, 31), estado="pendiente")
    _apagar(cartel)
    respuesta = _json(
        operativo_client,
        "patch",
        f"{RESERVAS}{reserva.pk}/",
        {"cartel": cartel.pk, "fecha_fin": "2026-12-20", "estado": "confirmada"},
    )
    assert respuesta.status_code == 200, respuesta.json()
    reserva.refresh_from_db()
    assert (reserva.fecha_fin, reserva.estado) == (date(2026, 12, 20), "confirmada")


# --- Reserva masiva ---


@pytest.mark.django_db
@pytest.mark.regla("RN-010")
def test_reserva_en_bloque_cartel_no_operativo_queda_fallida(operativo_client, formato):
    roto = _cartel(formato, "Av. Rota 3", estado="apagado")
    sano = _cartel(formato, "Av. Sana 3")
    datos = {
        "campania": _campania().pk,
        "fecha_inicio": "2026-12-01",
        "fecha_fin": "2026-12-31",
        "carteles": [roto.pk, sano.pk],
    }
    cuerpo = _json(operativo_client, "post", f"{RESERVAS}en-bloque/", datos).json()
    assert [item["cartel"] for item in cuerpo["creadas"]] == [sano.pk]
    assert cuerpo["fallidas"] == [
        {
            "cartel": roto.pk,
            "motivo": "El cartel está fuera de servicio (Apagado): no se puede reservar hasta "
            "que vuelva a un estado operativo.",
        }
    ]
    assert not Reserva.objects.filter(cartel=roto).exists()


@pytest.mark.django_db
@pytest.mark.regla("RN-010")
def test_carteles_para_tanda_cartel_no_operativo_no_aparece(operativo_client, formato):
    _cartel(formato, "Av. Rota 4", estado="mantenimiento")
    sano = _cartel(formato, "Av. Sana 4")
    params = {
        "campania": _campania().pk,
        "formato": formato.pk,
        "desde": "2026-12-01",
        "hasta": "2026-12-31",
    }
    respuesta = operativo_client.get("/api/reservas/carteles-para-tanda/", params)
    assert respuesta.status_code == 200
    assert [fila["id"] for fila in respuesta.json()] == [sano.pk]


# --- Criterio 1: reservas activas del cartel ---


@pytest.mark.django_db
@pytest.mark.regla("RN-010")
def test_reservas_vigentes_del_cartel_devuelve_activas(formato):
    hoy = date(2026, 11, 10)
    cartel = _cartel(formato)
    termina_hoy = _reserva(cartel, hoy - timedelta(days=9), hoy)
    futura = _reserva(cartel, hoy + timedelta(days=5), hoy + timedelta(days=20), "pendiente")
    _reserva(cartel, hoy - timedelta(days=30), hoy - timedelta(days=1))
    _reserva(cartel, hoy, hoy + timedelta(days=3), "cancelada")
    _reserva(_cartel(formato, "Av. Otra 9"), hoy, hoy + timedelta(days=3))

    vigentes = services.filtrar_vigentes(Reserva.objects.filter(cartel=cartel), dia=hoy)
    assert [reserva.pk for reserva in vigentes] == [termina_hoy.pk, futura.pk]


@pytest.mark.django_db
@pytest.mark.regla("RN-010")
def test_listar_reservas_vigentes_del_cartel_devuelve_activas(operativo_client, formato):
    hoy = timezone.localdate()
    cartel = _cartel(formato)
    vigente = _reserva(cartel, hoy, hoy + timedelta(days=10))
    _reserva(cartel, hoy - timedelta(days=20), hoy - timedelta(days=1))
    _apagar(cartel)

    respuesta = operativo_client.get(RESERVAS, {"cartel": cartel.pk, "vigentes": "1"})
    assert respuesta.status_code == 200
    assert [fila["id"] for fila in respuesta.json()] == [vigente.pk]


@pytest.mark.django_db
def test_listar_reservas_vigentes_sin_cartel_rechaza(operativo_client):
    respuesta = operativo_client.get(RESERVAS, {"vigentes": "1"})
    assert respuesta.status_code == 400
    assert "cartel" in respuesta.json()


@pytest.mark.django_db
def test_listar_reservas_vigentes_cartel_inexistente_devuelve_vacio(operativo_client):
    respuesta = operativo_client.get(RESERVAS, {"cartel": 999999, "vigentes": "1"})
    assert respuesta.status_code == 200
    assert respuesta.json() == []


# --- Otro pedido pasa el cartel a no operativo entre la validación y el guardado ---


def _apagar_despues_de_validar(monkeypatch: pytest.MonkeyPatch, cartel: Cartel) -> None:
    validar = ReservaSerializer.validate

    def validar_y_apagar(self: ReservaSerializer, attrs: dict[str, Any]) -> dict[str, Any]:
        resultado = validar(self, attrs)
        _apagar(Cartel.objects.get(pk=cartel.pk))
        return resultado

    monkeypatch.setattr(ReservaSerializer, "validate", validar_y_apagar)


@pytest.mark.django_db
@pytest.mark.regla("RN-010")
def test_crear_reserva_cartel_pasa_a_no_operativo_antes_de_guardar_rechaza(
    operativo_client, formato, monkeypatch
):
    cartel = _cartel(formato)
    _apagar_despues_de_validar(monkeypatch, cartel)

    respuesta = _alta(operativo_client, cartel, _campania())
    assert respuesta.status_code == 400
    assert "fuera de servicio" in respuesta.json()["cartel"][0]
    assert not Reserva.objects.filter(cartel=cartel).exists()


@pytest.mark.django_db
@pytest.mark.regla("RN-010")
def test_mover_reserva_cartel_pasa_a_no_operativo_antes_de_guardar_rechaza(
    operativo_client, formato, monkeypatch
):
    origen = _cartel(formato, "Av. Origen 1")
    destino = _cartel(formato, "Av. Destino 2")
    reserva = _reserva(origen, date(2026, 12, 1), date(2026, 12, 31), "pendiente")
    _apagar_despues_de_validar(monkeypatch, destino)

    respuesta = _json(operativo_client, "patch", f"{RESERVAS}{reserva.pk}/", {"cartel": destino.pk})
    assert respuesta.status_code == 400
    reserva.refresh_from_db()
    assert reserva.cartel_id == origen.pk


# --- El cartel informa si es operativo ---


@pytest.mark.django_db
def test_cartel_expone_operativo(operativo_client, formato):
    sano = _cartel(formato, "Av. Sana 5")
    roto = _cartel(formato, "Av. Rota 5", estado="apagado")
    filas = operativo_client.get("/api/inventario/carteles/").json()
    operativo = {fila["id"]: fila["operativo"] for fila in filas}
    assert operativo[sano.pk] is True
    assert operativo[roto.pk] is False
