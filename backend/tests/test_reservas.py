import json
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.utils import timezone

from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva


def crear_cartel(tarifa="150000.00", capacidad=1, baja=False, formato="LED") -> Cartel:
    estado = EstadoCartel.objects.get(codigo="baja" if baja else "activo")
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre=formato),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=estado,
        direccion="Av. San Martín 1234",
        tamano="6x3",
        capacidad=capacidad,
        tarifa_lista=Decimal(tarifa),
    )


def crear_campania(marca_nombre: str | None = "McDonald's") -> Campania:
    if marca_nombre is None:
        return Campania.objects.create()
    cliente = Cliente.objects.create(
        nombre=marca_nombre, razon_social=f"{marca_nombre} S.A.", tipo="directo"
    )
    marca = Marca.objects.create(nombre=marca_nombre, cliente=cliente)
    return Campania.objects.create(marca=marca)


def payload(cartel: Cartel, campania: Campania, **extra: object) -> dict[str, object]:
    base: dict[str, object] = {
        "campania": campania.pk,
        "cartel": cartel.pk,
        "fecha_inicio": "2026-08-01",
        "fecha_fin": "2026-08-31",
    }
    base.update(extra)
    return base


def crear(client: Client, **campos: object):
    return client.post(
        "/api/reservas/reservas/", data=json.dumps(campos), content_type="application/json"
    )


def editar(client: Client, reserva_id: int, **campos: object):
    return client.patch(
        f"/api/reservas/reservas/{reserva_id}/",
        data=json.dumps(campos),
        content_type="application/json",
    )


@pytest.mark.django_db
def test_crear_reserva_minima(operativo_client):
    cartel = crear_cartel()
    campania = crear_campania()
    creada = crear(operativo_client, **payload(cartel, campania))
    assert creada.status_code == 201
    cuerpo = creada.json()
    assert cuerpo["estado"] == "pendiente"
    assert Reserva.objects.filter(pk=cuerpo["id"]).exists()


@pytest.mark.django_db
def test_cartel_y_fechas_son_obligatorios(operativo_client):
    cartel = crear_cartel()
    campania = crear_campania()
    sin_cartel = crear(
        operativo_client, campania=campania.pk, fecha_inicio="2026-08-01", fecha_fin="2026-08-31"
    )
    sin_fecha = crear(
        operativo_client, campania=campania.pk, cartel=cartel.pk, fecha_inicio="2026-08-01"
    )
    assert sin_cartel.status_code == 400
    assert "cartel" in sin_cartel.json()
    assert sin_fecha.status_code == 400
    assert "fecha_fin" in sin_fecha.json()


@pytest.mark.django_db
def test_fecha_fin_anterior_se_rechaza(operativo_client):
    cartel = crear_cartel()
    campania = crear_campania()
    respuesta = crear(
        operativo_client,
        **payload(cartel, campania, fecha_inicio="2026-08-31", fecha_fin="2026-08-01"),
    )
    assert respuesta.status_code == 400
    assert "fecha_fin" in respuesta.json()


@pytest.mark.django_db
def test_cartel_de_baja_se_rechaza(operativo_client):
    cartel = crear_cartel(baja=True)
    campania = crear_campania()
    respuesta = crear(operativo_client, **payload(cartel, campania))
    assert respuesta.status_code == 400
    assert "cartel" in respuesta.json()


@pytest.mark.django_db
def test_precio_alquiler_se_precarga_y_queda_estampado(operativo_client):
    cartel = crear_cartel(tarifa="150000.00")
    campania = crear_campania()
    creada = crear(operativo_client, **payload(cartel, campania))
    assert creada.status_code == 201
    assert Decimal(creada.json()["precio_alquiler"]) == Decimal("150000.00")

    cartel.tarifa_lista = Decimal("200000.00")
    cartel.save()
    reserva = Reserva.objects.get(pk=creada.json()["id"])
    assert reserva.precio_alquiler == Decimal("150000.00")


@pytest.mark.django_db
def test_total_es_la_suma_y_rechaza_negativos(operativo_client):
    cartel = crear_cartel(tarifa="100000.00")
    campania = crear_campania()
    creada = crear(
        operativo_client,
        **payload(cartel, campania, precio_impresion="20000.00", precio_fijacion="5000.00"),
    )
    assert creada.status_code == 201
    assert Decimal(creada.json()["total"]) == Decimal("125000.00")

    negativo = crear(operativo_client, **payload(cartel, campania, precio_impresion="-1.00"))
    assert negativo.status_code == 400
    assert "precio_impresion" in negativo.json()


@pytest.mark.django_db
def test_nombre_se_genera_y_se_regenera(operativo_client):
    cartel = crear_cartel()
    campania = crear_campania("McDonald's")
    creada = crear(operativo_client, **payload(cartel, campania))
    nombre = creada.json()["nombre"]
    assert nombre.startswith("McDonald's - ")
    assert "Ago 2026" in nombre

    cambiada = editar(
        operativo_client, creada.json()["id"], fecha_inicio="2026-09-01", fecha_fin="2026-09-30"
    )
    assert "Sep 2026" in cambiada.json()["nombre"]


@pytest.mark.django_db
def test_nombre_sin_marca(operativo_client):
    cartel = crear_cartel()
    campania = crear_campania(marca_nombre=None)
    creada = crear(operativo_client, **payload(cartel, campania))
    assert creada.json()["nombre"].startswith("Sin marca - ")


@pytest.mark.django_db
def test_transiciones_de_estado(operativo_client):
    cartel = crear_cartel()
    campania = crear_campania()
    reserva_id = crear(operativo_client, **payload(cartel, campania)).json()["id"]

    assert editar(operativo_client, reserva_id, estado="confirmada").status_code == 200
    assert editar(operativo_client, reserva_id, estado="finalizada").status_code == 200
    # finalizada no vuelve a un estado activo
    invalida = editar(operativo_client, reserva_id, estado="confirmada")
    assert invalida.status_code == 400
    assert "estado" in invalida.json()


@pytest.mark.django_db
def test_transicion_invalida_desde_pendiente(operativo_client):
    cartel = crear_cartel()
    campania = crear_campania()
    reserva_id = crear(operativo_client, **payload(cartel, campania)).json()["id"]
    invalida = editar(operativo_client, reserva_id, estado="finalizada")
    assert invalida.status_code == 400
    assert "estado" in invalida.json()


@pytest.mark.django_db
@pytest.mark.regla("RN-006")
def test_cancelar_conserva_el_registro_y_no_hay_delete(operativo_client):
    cartel = crear_cartel()
    campania = crear_campania()
    reserva_id = crear(operativo_client, **payload(cartel, campania)).json()["id"]
    editar(operativo_client, reserva_id, estado="confirmada")

    cancelada = editar(operativo_client, reserva_id, estado="cancelada")
    assert cancelada.status_code == 200
    assert Reserva.objects.get(pk=reserva_id).estado == "cancelada"
    assert operativo_client.delete(f"/api/reservas/reservas/{reserva_id}/").status_code == 405


@pytest.mark.django_db
def test_ocupacion_del_cartel_al_momento(operativo_client):
    cartel = crear_cartel(capacidad=1)
    campania = crear_campania()
    hoy = timezone.localdate()
    crear(
        operativo_client,
        **payload(
            cartel,
            campania,
            fecha_inicio=str(hoy - timedelta(days=1)),
            fecha_fin=str(hoy + timedelta(days=1)),
            estado="confirmada",
        ),
    )
    respuesta = operativo_client.get(f"/api/reservas/ocupacion/?cartel={cartel.pk}")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["capacidad"] == 1
    assert cuerpo["ocupados"] == 1


@pytest.mark.django_db
def test_filtros_de_lista(operativo_client):
    cartel = crear_cartel()
    campania = crear_campania()
    reserva_id = crear(operativo_client, **payload(cartel, campania)).json()["id"]
    editar(operativo_client, reserva_id, estado="confirmada")

    por_campania = operativo_client.get(f"/api/reservas/reservas/?campania={campania.pk}").json()
    por_estado = operativo_client.get("/api/reservas/reservas/?estado=pendiente").json()
    assert [fila["id"] for fila in por_campania] == [reserva_id]
    assert por_estado == []


@pytest.mark.django_db
def test_filtros_invalidos_se_rechazan(operativo_client):
    estado_malo = operativo_client.get("/api/reservas/reservas/?estado=otro")
    cartel_malo = operativo_client.get("/api/reservas/reservas/?cartel=abc")
    assert estado_malo.status_code == 400
    assert "estado" in estado_malo.json()
    assert cartel_malo.status_code == 400
    assert "cartel" in cartel_malo.json()


@pytest.mark.django_db
def test_ocupacion_cartel_invalido_o_inexistente(operativo_client):
    sin_valor = operativo_client.get("/api/reservas/ocupacion/?cartel=abc")
    inexistente = operativo_client.get("/api/reservas/ocupacion/?cartel=99999")
    assert sin_valor.status_code == 400
    assert inexistente.status_code == 400
    assert "cartel" in inexistente.json()


@pytest.mark.django_db
def test_anonimo_y_sin_permiso_no_escriben(lector_client):
    cartel = crear_cartel()
    campania = crear_campania()
    cuerpo = json.dumps(payload(cartel, campania))
    anonimo = Client().post("/api/reservas/reservas/", data=cuerpo, content_type="application/json")
    assert anonimo.status_code in (401, 403)
    denegado = lector_client.post(
        "/api/reservas/reservas/", data=cuerpo, content_type="application/json"
    )
    assert denegado.status_code == 403
    assert Reserva.objects.count() == 0


@pytest.mark.django_db
def test_operativo_sin_csrf_es_rechazado():
    cartel = crear_cartel()
    campania = crear_campania()
    user = get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    user.groups.add(Group.objects.get(name="Operativo"))
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    respuesta = client.post(
        "/api/reservas/reservas/",
        data=json.dumps(payload(cartel, campania)),
        content_type="application/json",
    )
    assert respuesta.status_code == 403
