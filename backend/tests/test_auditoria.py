"""Tests de auditoría: registro inmutable de cambios en reservas (HU-007)."""

import json
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import Client
from django.utils import timezone

from apps.auditoria.models import RegistroAuditoria
from apps.auditoria.services import registrar_cambios
from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona

# ---------------------------------------------------------------------------
# Helpers de fixtures
# ---------------------------------------------------------------------------


def crear_cartel() -> Cartel:
    estado = EstadoCartel.objects.get(codigo="activo")
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=estado,
        direccion="Av. Test 100",
        tamano="6x3",
        capacidad=1,
        tarifa_lista="100000.00",
    )


def crear_campania() -> Campania:
    cliente = Cliente.objects.create(nombre="Test SA", razon_social="Test SA", tipo="directo")
    marca = Marca.objects.create(nombre="Test", cliente=cliente)
    return Campania.objects.create(marca=marca)


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


def listar_auditoria(client: Client, **params: object):
    partes = [f"{k}={v}" for k, v in params.items()]
    query = f"?{'&'.join(partes)}" if partes else ""
    return client.get(f"/api/auditoria/registros/{query}")


# ---------------------------------------------------------------------------
# Captura de cambios al editar una reserva
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_editar_reserva_genera_registros_auditoria(operativo_client):
    """Al editar fecha_fin y estado de una reserva, quedan registros de auditoría."""
    cartel = crear_cartel()
    campania = crear_campania()
    creada = crear(
        operativo_client,
        campania=campania.pk,
        cartel=cartel.pk,
        fecha_inicio="2026-08-01",
        fecha_fin="2026-08-31",
    )
    assert creada.status_code == 201
    reserva_id = creada.json()["id"]

    resp = editar(operativo_client, reserva_id, fecha_fin="2026-09-30", estado="confirmada")
    assert resp.status_code == 200

    registros = RegistroAuditoria.objects.filter(entidad="reserva", entidad_id=reserva_id)
    campos_cambiados = {r.campo for r in registros}
    assert "fecha_fin" in campos_cambiados
    assert "estado" in campos_cambiados

    # Verificar valores anteriores y nuevos
    reg_fecha = registros.get(campo="fecha_fin")
    assert reg_fecha.valor_anterior == "2026-08-31"
    assert reg_fecha.valor_nuevo == "2026-09-30"

    reg_estado = registros.get(campo="estado")
    assert reg_estado.valor_anterior == "pendiente"
    assert reg_estado.valor_nuevo == "confirmada"

    # El usuario está registrado (no es None)
    assert reg_fecha.usuario is not None
    # El momento está seteado
    assert reg_fecha.momento is not None


@pytest.mark.django_db
def test_editar_reserva_solo_registra_campos_que_cambiaron(operativo_client):
    """Si se edita solo fecha_fin, no se crea registro para los demás campos."""
    cartel = crear_cartel()
    campania = crear_campania()
    creada = crear(
        operativo_client,
        campania=campania.pk,
        cartel=cartel.pk,
        fecha_inicio="2026-08-01",
        fecha_fin="2026-08-31",
    )
    assert creada.status_code == 201
    reserva_id = creada.json()["id"]

    editar(operativo_client, reserva_id, fecha_fin="2026-09-30")

    registros = RegistroAuditoria.objects.filter(entidad="reserva", entidad_id=reserva_id)
    campos = {r.campo for r in registros}
    assert "fecha_fin" in campos
    assert "estado" not in campos
    assert "cartel" not in campos


@pytest.mark.django_db
def test_crear_reserva_no_genera_registros_auditoria(operativo_client):
    """La creación de una reserva no genera registros de auditoría."""
    cartel = crear_cartel()
    campania = crear_campania()
    creada = crear(
        operativo_client,
        campania=campania.pk,
        cartel=cartel.pk,
        fecha_inicio="2026-08-01",
        fecha_fin="2026-08-31",
    )
    assert creada.status_code == 201
    reserva_id = creada.json()["id"]

    assert not RegistroAuditoria.objects.filter(entidad="reserva", entidad_id=reserva_id).exists()


# ---------------------------------------------------------------------------
# registrar_cambios: no crea filas si nada cambió
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_registrar_cambios_sin_diferencias_no_crea_filas():
    """registrar_cambios no crea ninguna fila si anteriores == nuevos."""
    valores = {"estado": "pendiente", "fecha_fin": "2026-08-31"}
    registrar_cambios("reserva", 1, valores, valores, None)
    assert not RegistroAuditoria.objects.exists()


@pytest.mark.django_db
def test_registrar_cambios_crea_una_fila_por_campo_cambiado():
    """registrar_cambios crea exactamente una fila por campo que cambió."""
    anteriores = {"estado": "pendiente", "fecha_fin": "2026-08-31"}
    nuevos = {"estado": "confirmada", "fecha_fin": "2026-08-31"}
    registrar_cambios("reserva", 42, anteriores, nuevos, None)
    assert RegistroAuditoria.objects.filter(entidad="reserva", entidad_id=42).count() == 1
    reg = RegistroAuditoria.objects.get(entidad="reserva", entidad_id=42)
    assert reg.campo == "estado"
    assert reg.valor_anterior == "pendiente"
    assert reg.valor_nuevo == "confirmada"
    assert reg.usuario is None
    assert reg.origen == RegistroAuditoria.Origen.USUARIO


# ---------------------------------------------------------------------------
# Inmutabilidad del modelo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_modelo_rechaza_update_de_registro_existente():
    """Guardar un RegistroAuditoria ya existente (con pk) levanta ValidationError."""
    reg = RegistroAuditoria(
        entidad="reserva",
        entidad_id=1,
        campo="estado",
        valor_anterior="pendiente",
        valor_nuevo="confirmada",
    )
    reg.save()
    assert reg.pk is not None

    reg.valor_nuevo = "cancelada"  # intento de modificar
    with pytest.raises(DjangoValidationError):
        reg.save()


@pytest.mark.django_db
def test_modelo_rechaza_delete():
    """delete() en un RegistroAuditoria levanta ValidationError."""
    reg = RegistroAuditoria(
        entidad="reserva",
        entidad_id=1,
        campo="estado",
        valor_anterior="pendiente",
        valor_nuevo="confirmada",
    )
    reg.save()
    with pytest.raises(DjangoValidationError):
        reg.delete()


# ---------------------------------------------------------------------------
# API: PATCH y DELETE dan 405
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_api_patch_registro_da_405(gerencia_client):
    """PATCH a /api/auditoria/registros/<id>/ devuelve 405."""
    reg = RegistroAuditoria.objects.create(
        entidad="reserva",
        entidad_id=1,
        campo="estado",
        valor_anterior="pendiente",
        valor_nuevo="confirmada",
    )
    resp = gerencia_client.patch(
        f"/api/auditoria/registros/{reg.pk}/",
        data=json.dumps({"valor_nuevo": "cancelada"}),
        content_type="application/json",
    )
    assert resp.status_code == 405


@pytest.mark.django_db
def test_api_delete_registro_da_405(gerencia_client):
    """DELETE a /api/auditoria/registros/<id>/ devuelve 405."""
    reg = RegistroAuditoria.objects.create(
        entidad="reserva",
        entidad_id=1,
        campo="estado",
        valor_anterior="pendiente",
        valor_nuevo="confirmada",
    )
    resp = gerencia_client.delete(f"/api/auditoria/registros/{reg.pk}/")
    assert resp.status_code == 405


# ---------------------------------------------------------------------------
# Filtros del endpoint
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_endpoint_filtra_por_entidad(gerencia_client):
    """El endpoint filtra correctamente por entidad."""
    RegistroAuditoria.objects.create(
        entidad="reserva",
        entidad_id=1,
        campo="estado",
        valor_anterior="pendiente",
        valor_nuevo="confirmada",
    )
    RegistroAuditoria.objects.create(
        entidad="campania",
        entidad_id=5,
        campo="nombre",
        valor_anterior="Viejo",
        valor_nuevo="Nuevo",
    )
    resp = listar_auditoria(gerencia_client, entidad="reserva")
    assert resp.status_code == 200
    datos = resp.json()
    assert all(r["entidad"] == "reserva" for r in datos)
    assert len(datos) == 1


@pytest.mark.django_db
def test_endpoint_filtra_por_entidad_id(gerencia_client):
    """El endpoint filtra por entidad_id."""
    RegistroAuditoria.objects.create(
        entidad="reserva",
        entidad_id=1,
        campo="estado",
        valor_anterior="pendiente",
        valor_nuevo="confirmada",
    )
    RegistroAuditoria.objects.create(
        entidad="reserva",
        entidad_id=2,
        campo="estado",
        valor_anterior="pendiente",
        valor_nuevo="confirmada",
    )
    resp = listar_auditoria(gerencia_client, entidad_id=1)
    assert resp.status_code == 200
    datos = resp.json()
    assert all(r["entidad_id"] == 1 for r in datos)
    assert len(datos) == 1


@pytest.mark.django_db
def test_endpoint_filtra_por_usuario(gerencia_client, db):
    """El endpoint filtra por usuario (id)."""
    User = get_user_model()
    user = User.objects.create_user(username="auditor_test", password="clave-x-123")
    reg1 = RegistroAuditoria(
        entidad="reserva",
        entidad_id=1,
        campo="estado",
        valor_anterior="pendiente",
        valor_nuevo="confirmada",
        usuario=user,
    )
    reg1.save()
    reg2 = RegistroAuditoria(
        entidad="reserva",
        entidad_id=2,
        campo="estado",
        valor_anterior="pendiente",
        valor_nuevo="cancelada",
    )
    reg2.save()

    resp = listar_auditoria(gerencia_client, usuario=user.pk)
    assert resp.status_code == 200
    datos = resp.json()
    assert len(datos) == 1
    assert datos[0]["usuario"] == user.pk


@pytest.mark.django_db
def test_endpoint_filtra_por_rango_de_fechas(gerencia_client):
    """El endpoint filtra por desde/hasta (fecha de momento)."""
    reg = RegistroAuditoria(
        entidad="reserva",
        entidad_id=1,
        campo="estado",
        valor_anterior="pendiente",
        valor_nuevo="confirmada",
    )
    reg.save()

    hoy = timezone.localdate()
    desde = (hoy - timedelta(days=1)).isoformat()
    hasta = (hoy + timedelta(days=1)).isoformat()

    resp_dentro = listar_auditoria(gerencia_client, desde=desde, hasta=hasta)
    assert resp_dentro.status_code == 200
    assert len(resp_dentro.json()) >= 1

    manana = (hoy + timedelta(days=1)).isoformat()
    pasado = (hoy + timedelta(days=2)).isoformat()
    resp_fuera = listar_auditoria(gerencia_client, desde=manana, hasta=pasado)
    assert resp_fuera.status_code == 200
    assert len(resp_fuera.json()) == 0


@pytest.mark.django_db
def test_endpoint_fecha_invalida_da_400(gerencia_client):
    """Una fecha con formato incorrecto devuelve 400."""
    resp = listar_auditoria(gerencia_client, desde="no-es-fecha")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_endpoint_ordena_del_mas_nuevo_al_mas_viejo(gerencia_client):
    """Los registros se ordenan del más nuevo al más viejo."""
    for i in range(3):
        RegistroAuditoria(
            entidad="reserva",
            entidad_id=i + 1,
            campo="estado",
            valor_anterior="pendiente",
            valor_nuevo="confirmada",
        ).save()

    resp = listar_auditoria(gerencia_client)
    assert resp.status_code == 200
    datos = resp.json()
    momentos = [r["momento"] for r in datos]
    assert momentos == sorted(momentos, reverse=True)


@pytest.mark.django_db
def test_endpoint_usuario_nombre_es_sistema_para_usuario_nulo(gerencia_client):
    """usuario_nombre devuelve 'Sistema' cuando el registro no tiene usuario."""
    RegistroAuditoria(
        entidad="reserva",
        entidad_id=1,
        campo="estado",
        valor_anterior="pendiente",
        valor_nuevo="confirmada",
    ).save()
    resp = listar_auditoria(gerencia_client)
    assert resp.status_code == 200
    assert resp.json()[0]["usuario_nombre"] == "Sistema"


# ---------------------------------------------------------------------------
# Permisos del endpoint
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_gerencia_puede_leer(gerencia_client):
    """El grupo Gerencia puede leer el endpoint de auditoría (200)."""
    resp = listar_auditoria(gerencia_client)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_operativo_no_puede_leer(operativo_client):
    """El grupo Operativo no puede leer el endpoint de auditoría (403)."""
    resp = listar_auditoria(operativo_client)
    assert resp.status_code == 403


@pytest.mark.django_db
def test_anonimo_no_puede_leer(client):
    """Un usuario anónimo no puede leer el endpoint de auditoría (401 o 403)."""
    resp = listar_auditoria(client)
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Endpoint GET /api/auditoria/usuarios/
# ---------------------------------------------------------------------------


def listar_usuarios_auditoria(client: Client):
    return client.get("/api/auditoria/usuarios/")


@pytest.mark.django_db
def test_usuarios_devuelve_usuarios_con_cambios(gerencia_client, operativo_client):
    """GET /api/auditoria/usuarios/ devuelve los usuarios que hicieron cambios."""
    cartel = crear_cartel()
    campania = crear_campania()
    creada = crear(
        operativo_client,
        campania=campania.pk,
        cartel=cartel.pk,
        fecha_inicio="2026-08-01",
        fecha_fin="2026-08-31",
    )
    assert creada.status_code == 201
    reserva_id = creada.json()["id"]
    resp_edit = editar(operativo_client, reserva_id, fecha_fin="2026-09-30")
    assert resp_edit.status_code == 200

    resp = listar_usuarios_auditoria(gerencia_client)
    assert resp.status_code == 200
    datos = resp.json()
    assert isinstance(datos, list)
    assert len(datos) >= 1
    nombres = [u["nombre"] for u in datos]
    assert "operativo" in nombres


@pytest.mark.django_db
def test_usuarios_sin_duplicados(gerencia_client, operativo_client):
    """GET /api/auditoria/usuarios/ no devuelve el mismo usuario dos veces."""
    cartel = crear_cartel()
    campania = crear_campania()
    creada = crear(
        operativo_client,
        campania=campania.pk,
        cartel=cartel.pk,
        fecha_inicio="2026-08-01",
        fecha_fin="2026-08-31",
    )
    assert creada.status_code == 201
    reserva_id = creada.json()["id"]
    # Dos ediciones del mismo usuario generan dos registros de auditoría
    editar(operativo_client, reserva_id, fecha_fin="2026-09-30")
    editar(operativo_client, reserva_id, fecha_fin="2026-10-31")

    resp = listar_usuarios_auditoria(gerencia_client)
    assert resp.status_code == 200
    datos = resp.json()
    ids = [u["id"] for u in datos]
    assert len(ids) == len(set(ids))


@pytest.mark.django_db
def test_usuarios_gerencia_200(gerencia_client):
    """GET /api/auditoria/usuarios/ con Gerencia devuelve 200."""
    resp = listar_usuarios_auditoria(gerencia_client)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_usuarios_operativo_403(operativo_client):
    """GET /api/auditoria/usuarios/ con Operativo devuelve 403."""
    resp = listar_usuarios_auditoria(operativo_client)
    assert resp.status_code == 403


@pytest.mark.django_db
def test_usuarios_anonimo_401_o_403(client):
    """GET /api/auditoria/usuarios/ anónimo devuelve 401 o 403."""
    resp = listar_usuarios_auditoria(client)
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Auditoría de campaña: cambio de estado
# ---------------------------------------------------------------------------


def editar_campania(client: Client, campania_id: int, **campos: object):
    return client.patch(
        f"/api/campanias/campanias/{campania_id}/",
        data=json.dumps(campos),
        content_type="application/json",
    )


def editar_cartel(client: Client, cartel_id: int, **campos: object):
    return client.patch(
        f"/api/inventario/carteles/{cartel_id}/",
        data=json.dumps(campos),
        content_type="application/json",
    )


@pytest.mark.django_db
def test_cambiar_estado_campania_genera_registro_auditoria(operativo_client):
    """Al cambiar el estado de una campaña por PATCH, queda un RegistroAuditoria."""
    campania = crear_campania()
    assert campania.estado == "cotizada"

    # Se usa "cancelada" (no requiere marca ni fechas, a diferencia de "confirmada").
    resp = editar_campania(operativo_client, campania.pk, estado="cancelada")
    assert resp.status_code == 200

    registros = RegistroAuditoria.objects.filter(entidad="campania", entidad_id=campania.pk)
    assert registros.count() == 1
    reg = registros.get()
    assert reg.campo == "estado"
    assert reg.valor_anterior == "cotizada"
    assert reg.valor_nuevo == "cancelada"
    assert reg.usuario is not None


@pytest.mark.django_db
def test_patch_campania_sin_cambiar_estado_no_genera_registro(operativo_client):
    """Editar otro campo de campaña sin cambiar estado no genera registros de auditoría."""
    campania = crear_campania()

    resp = editar_campania(operativo_client, campania.pk, nombre="Nuevo Nombre")
    assert resp.status_code == 200

    assert not RegistroAuditoria.objects.filter(entidad="campania", entidad_id=campania.pk).exists()


# ---------------------------------------------------------------------------
# Auditoría de cartel: cambio de tarifa_lista
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cambiar_tarifa_cartel_genera_registro_auditoria(operativo_client):
    """Al cambiar tarifa_lista de un cartel por PATCH, queda un RegistroAuditoria."""
    cartel = crear_cartel()  # tarifa_lista="100000.00"

    resp = editar_cartel(operativo_client, cartel.pk, tarifa_lista="200000.00")
    assert resp.status_code == 200

    registros = RegistroAuditoria.objects.filter(entidad="cartel", entidad_id=cartel.pk)
    assert registros.count() == 1
    reg = registros.get()
    assert reg.campo == "tarifa_lista"
    assert reg.valor_anterior == "100000.00"
    assert reg.valor_nuevo == "200000.00"
    assert reg.usuario is not None


@pytest.mark.django_db
def test_patch_cartel_sin_cambiar_tarifa_no_genera_registro(operativo_client):
    """Editar otro campo de cartel sin cambiar tarifa_lista no genera registros de auditoría."""
    cartel = crear_cartel()

    resp = editar_cartel(operativo_client, cartel.pk, tamano="8x4")
    assert resp.status_code == 200

    assert not RegistroAuditoria.objects.filter(entidad="cartel", entidad_id=cartel.pk).exists()
