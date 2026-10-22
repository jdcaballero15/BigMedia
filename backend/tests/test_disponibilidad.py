"""Matriz de disponibilidad de HU-031 (anexo) y mensaje de conflicto (HU-032)."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, Group
from django.db import connection
from django.test import Client, override_settings

from apps.campanias.models import Campania
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva


def cartel(capacidad: int = 1, baja: bool = False) -> Cartel:
    estado = EstadoCartel.objects.get(codigo="baja" if baja else "activo")
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=estado,
        direccion="Av. San Martín 1234",
        tamano="6x3",
        capacidad=capacidad,
        tarifa_lista="100000.00",
    )


def campania() -> Campania:
    return Campania.objects.create()


def reserva(car: Cartel, inicio: str, fin: str, estado: str = "confirmada") -> Reserva:
    r = Reserva(
        campania=campania(),
        cartel=car,
        fecha_inicio=date.fromisoformat(inicio),
        fecha_fin=date.fromisoformat(fin),
        estado=estado,
    )
    r.save()
    return r


def confirmar(client: Client, car: Cartel, inicio: str, fin: str):
    """Crea una reserva pendiente y la confirma; devuelve la respuesta del confirmar."""
    creada = client.post(
        "/api/reservas/reservas/",
        data=json.dumps(
            {
                "campania": campania().pk,
                "cartel": car.pk,
                "fecha_inicio": inicio,
                "fecha_fin": fin,
                "estado": "pendiente",
            }
        ),
        content_type="application/json",
    )
    assert creada.status_code == 201, creada.content
    return client.patch(
        f"/api/reservas/reservas/{creada.json()['id']}/",
        data=json.dumps({"estado": "confirmada"}),
        content_type="application/json",
    )


@pytest.mark.django_db
@pytest.mark.regla("RN-003")
def test_caso_1_rango_identico_capacidad_1_bloquea(operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-01", "2026-11-15")
    assert confirmar(operativo_client, car, "2026-11-01", "2026-11-15").status_code == 400


@pytest.mark.django_db
def test_caso_2_contenido_bloquea(operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-01", "2026-11-30")
    assert confirmar(operativo_client, car, "2026-11-10", "2026-11-20").status_code == 400


@pytest.mark.django_db
def test_caso_3_contenedor_bloquea(operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-10", "2026-11-20")
    assert confirmar(operativo_client, car, "2026-11-01", "2026-11-30").status_code == 400


@pytest.mark.django_db
def test_caso_4_parcial_izquierda_bloquea(operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-10", "2026-11-20")
    assert confirmar(operativo_client, car, "2026-11-05", "2026-11-15").status_code == 400


@pytest.mark.django_db
def test_caso_5_parcial_derecha_bloquea(operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-10", "2026-11-20")
    assert confirmar(operativo_client, car, "2026-11-15", "2026-11-25").status_code == 400


@pytest.mark.django_db
@pytest.mark.regla("RN-001")
def test_caso_6_adyacente_inclusivo_bloquea(operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-01", "2026-11-15")
    assert confirmar(operativo_client, car, "2026-11-15", "2026-11-30").status_code == 400


@pytest.mark.django_db
@pytest.mark.regla("RN-001")
@override_settings(DISPONIBILIDAD_BORDE_INCLUSIVO=False)
def test_caso_6_adyacente_exclusivo_permite(operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-01", "2026-11-15")
    assert confirmar(operativo_client, car, "2026-11-15", "2026-11-30").status_code == 200


@pytest.mark.django_db
def test_caso_7_separados_por_un_dia_permite(operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-01", "2026-11-14")
    assert confirmar(operativo_client, car, "2026-11-16", "2026-11-30").status_code == 200


@pytest.mark.django_db
def test_caso_8_conflicto_con_cancelada_permite(operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-01", "2026-11-15", estado="cancelada")
    assert confirmar(operativo_client, car, "2026-11-01", "2026-11-15").status_code == 200


@pytest.mark.django_db
@pytest.mark.regla("RN-002")
def test_caso_9_tentativa_no_bloquea_por_defecto(operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-01", "2026-11-15", estado="pendiente")
    assert confirmar(operativo_client, car, "2026-11-01", "2026-11-15").status_code == 200


@pytest.mark.django_db
@pytest.mark.regla("RN-002")
@override_settings(DISPONIBILIDAD_TENTATIVA_BLOQUEA=True)
def test_caso_9_tentativa_bloquea_con_config(operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-01", "2026-11-15", estado="pendiente")
    assert confirmar(operativo_client, car, "2026-11-01", "2026-11-15").status_code == 400


@pytest.mark.django_db
@pytest.mark.regla("RN-003")
def test_caso_10_y_11_digital_cupos(operativo_client):
    car = cartel(capacidad=20)
    for _ in range(12):
        reserva(car, "2026-11-01", "2026-11-30")
    assert confirmar(operativo_client, car, "2026-11-01", "2026-11-30").status_code == 200  # 13/20
    for _ in range(7):
        reserva(car, "2026-11-01", "2026-11-30")
    assert confirmar(operativo_client, car, "2026-11-01", "2026-11-30").status_code == 400  # 20/20


@pytest.mark.django_db
@pytest.mark.regla("RN-003")
def test_pico_diario_permite_reservas_no_simultaneas(operativo_client):
    # LED capacidad 1: dos reservas que no coinciden en el tiempo y una nueva que las abarca.
    car = cartel(capacidad=1)
    reserva(car, "2026-11-01", "2026-11-10")
    reserva(car, "2026-11-20", "2026-11-30")
    # Con pico diario, el 11-19 está libre, pero el rango 1-30 pisa ambos tramos -> bloquea en cap 1.
    assert confirmar(operativo_client, car, "2026-11-01", "2026-11-30").status_code == 400
    # En cambio con capacidad 2 el pico es 2 (nueva + una), nunca 3 -> permite.
    car2 = cartel(capacidad=2)
    reserva(car2, "2026-11-01", "2026-11-10")
    reserva(car2, "2026-11-20", "2026-11-30")
    assert confirmar(operativo_client, car2, "2026-11-01", "2026-11-30").status_code == 200


@pytest.mark.django_db
def test_caso_12_edicion_mueve_fechas_a_ocupado_bloquea(operativo_client):
    car = cartel(capacidad=1)
    reserva(car, "2026-11-01", "2026-11-15")
    confirmada = confirmar(operativo_client, car, "2026-12-01", "2026-12-15")
    assert confirmada.status_code == 200
    movida = operativo_client.patch(
        f"/api/reservas/reservas/{confirmada.json()['id']}/",
        data=json.dumps({"fecha_inicio": "2026-11-01", "fecha_fin": "2026-11-15"}),
        content_type="application/json",
    )
    assert movida.status_code == 400


@pytest.mark.django_db
def test_caso_13_edicion_solo_precio_no_revalida(operativo_client):
    car = cartel(capacidad=1)
    confirmada = confirmar(operativo_client, car, "2026-11-01", "2026-11-15")
    assert confirmada.status_code == 200
    # Otra confirmada idéntica ya no entra; pero editar solo el precio de la primera no revalida.
    reserva(car, "2026-11-01", "2026-11-15")  # ahora el cartel está lleno
    solo_precio = operativo_client.patch(
        f"/api/reservas/reservas/{confirmada.json()['id']}/",
        data=json.dumps({"precio_impresion": "5000.00"}),
        content_type="application/json",
    )
    assert solo_precio.status_code == 200


@pytest.mark.django_db
def test_caso_14_pasar_a_cancelada_siempre_permite(operativo_client):
    car = cartel(capacidad=1)
    confirmada = confirmar(operativo_client, car, "2026-11-01", "2026-11-15")
    cancelada = operativo_client.patch(
        f"/api/reservas/reservas/{confirmada.json()['id']}/",
        data=json.dumps({"estado": "cancelada"}),
        content_type="application/json",
    )
    assert cancelada.status_code == 200


@pytest.mark.django_db
def test_caso_16_cartel_de_baja_se_rechaza(operativo_client):
    car = cartel(capacidad=1, baja=True)
    creada = operativo_client.post(
        "/api/reservas/reservas/",
        data=json.dumps(
            {
                "campania": campania().pk,
                "cartel": car.pk,
                "fecha_inicio": "2026-11-01",
                "fecha_fin": "2026-11-15",
            }
        ),
        content_type="application/json",
    )
    assert creada.status_code == 400
    assert "cartel" in creada.json()


def _operativo() -> AbstractBaseUser:
    user = get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    user.groups.add(Group.objects.get(name="Operativo"))
    return user


def _confirmar_en_hilo(user_pk: int, reserva_pk: int) -> int:
    """Confirma una reserva en su propio hilo/conexión; devuelve el status HTTP."""
    try:
        client = Client()
        client.force_login(get_user_model().objects.get(pk=user_pk))
        respuesta = client.patch(
            f"/api/reservas/reservas/{reserva_pk}/",
            data=json.dumps({"estado": "confirmada"}),
            content_type="application/json",
        )
        return respuesta.status_code
    finally:
        connection.close()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
@pytest.mark.regla("RN-003")
def test_caso_15_confirmaciones_simultaneas_ultimo_cupo():
    car = cartel(capacidad=1)
    user = _operativo()
    pendientes = [reserva(car, "2026-11-01", "2026-11-15", estado="pendiente").pk for _ in range(2)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(lambda pk: _confirmar_en_hilo(user.pk, pk), pendientes))
    assert sorted(resultados) == [200, 400]
    assert Reserva.objects.filter(cartel=car, estado="confirmada").count() == 1


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
@pytest.mark.regla("RN-003")
def test_50_confirmaciones_concurrentes_capacidad_20_nunca_sobrevende():
    car = cartel(capacidad=20)
    user = _operativo()
    pendientes = [
        reserva(car, "2026-11-01", "2026-11-30", estado="pendiente").pk for _ in range(50)
    ]
    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(lambda pk: _confirmar_en_hilo(user.pk, pk), pendientes))
    assert Reserva.objects.filter(cartel=car, estado="confirmada").count() == 20


@pytest.mark.django_db
@pytest.mark.regla("RN-003")
def test_mensaje_de_conflicto_nombra_cartel_cupos_y_reservas(operativo_client):
    car = cartel(capacidad=1)
    existente = reserva(car, "2026-11-01", "2026-11-15")
    bloqueada = confirmar(operativo_client, car, "2026-11-01", "2026-11-15")
    assert bloqueada.status_code == 400
    detalle = json.dumps(bloqueada.json(), ensure_ascii=False)
    assert car.nombre_visible in detalle
    assert "1 de 1" in detalle
    assert existente.nombre in detalle
