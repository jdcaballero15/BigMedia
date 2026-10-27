"""Comando de datos de ejemplo para staging (HU — unidad de entornos)."""

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.auditoria.models import RegistroAuditoria
from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca, Rubro
from apps.costos.models import Costo
from apps.inventario.models import Cartel, Proveedor
from apps.reservas.models import Reserva
from apps.usuarios.management.commands.cargar_datos_ejemplo import Command
from apps.usuarios.services import ROL_LECTURA, ROL_OPERATIVO, es_gerencia, rol_de


@pytest.mark.django_db
def test_carga_crea_datos_de_ejemplo():
    call_command("cargar_datos_ejemplo")
    assert Cliente.objects.filter(nombre="Agencia Norte").exists()
    assert Reserva.objects.count() > 0


@pytest.mark.django_db
def test_carga_es_idempotente():
    call_command("cargar_datos_ejemplo")
    clientes = Cliente.objects.count()
    reservas = Reserva.objects.count()
    call_command("cargar_datos_ejemplo")
    assert Cliente.objects.count() == clientes
    assert Reserva.objects.count() == reservas


@pytest.mark.django_db
def test_no_corre_en_produccion(settings):
    settings.PRODUCTION = True
    with pytest.raises(CommandError):
        call_command("cargar_datos_ejemplo")
    assert not Cliente.objects.filter(nombre="Agencia Norte").exists()


DEMO = "Distribuidora Andina"
USUARIOS_DEMO = {"demo-operativo", "demo-gerencia", "demo-lectura"}


def _contar() -> dict[str, int]:
    return {
        "carteles": Cartel.objects.count(),
        "clientes": Cliente.objects.count(),
        "marcas": Marca.objects.count(),
        "campanias": Campania.objects.count(),
        "reservas": Reserva.objects.count(),
        "costos": Costo.objects.count(),
        "auditoria": RegistroAuditoria.objects.count(),
    }


@pytest.mark.django_db
def test_carga_demo_llena_todas_las_pantallas():
    call_command("cargar_datos_ejemplo")

    assert Cliente.objects.filter(nombre=DEMO).exists()
    assert Cartel.objects.count() >= 20
    assert Proveedor.objects.count() >= 4
    assert Rubro.objects.count() >= 6
    assert not Marca.objects.filter(rubro__isnull=True).exists()
    assert Cliente.objects.count() >= 8
    assert Campania.objects.exclude(nombre="").count() >= 10
    assert set(Campania.objects.values_list("estado", flat=True)) == set(Campania.Estado.values)
    assert set(Reserva.objects.values_list("estado", flat=True)) == set(Reserva.Estado.values)
    assert Reserva.objects.count() >= 25
    assert Costo.objects.count() >= 15
    assert RegistroAuditoria.objects.count() >= 8
    assert Cartel.objects.filter(proveedor__isnull=False).exists()


@pytest.mark.django_db
def test_carga_demo_respeta_la_capacidad_de_cada_cartel():
    call_command("cargar_datos_ejemplo")

    bloquean = [Reserva.Estado.CONFIRMADA, Reserva.Estado.FINALIZADA]
    for cartel in Cartel.objects.all():
        reservas = list(cartel.reservas.filter(estado__in=bloquean))
        dias = {r.fecha_inicio for r in reservas}
        for dia in dias:
            ocupados = sum(1 for r in reservas if r.fecha_inicio <= dia <= r.fecha_fin)
            assert ocupados <= cartel.capacidad, (cartel.direccion, dia)


@pytest.mark.django_db
def test_carga_demo_sobre_primer_lote_existente_agrega_sin_duplicar():
    # Así está staging hoy: solo el primer lote, cargado antes de que existiera el lote demo.
    Command()._crear()
    carteles = Cartel.objects.count()

    call_command("cargar_datos_ejemplo")

    assert Cliente.objects.filter(nombre="Agencia Norte").count() == 1
    assert Cliente.objects.filter(nombre=DEMO).count() == 1
    assert Cartel.objects.count() == carteles + 16
    assert not Marca.objects.filter(rubro__isnull=True).exists()


@pytest.mark.django_db
def test_carga_demo_es_idempotente():
    call_command("cargar_datos_ejemplo")
    antes = _contar()

    call_command("cargar_datos_ejemplo")

    assert _contar() == antes


@pytest.mark.django_db
def test_carga_demo_con_clave_crea_usuarios_con_su_rol(monkeypatch):
    monkeypatch.setenv("DJANGO_DEMO_PASSWORD", "clave-demo-de-prueba")

    call_command("cargar_datos_ejemplo")

    usuarios = {u.username: u for u in User.objects.filter(username__in=USUARIOS_DEMO)}
    assert set(usuarios) == USUARIOS_DEMO
    assert rol_de(usuarios["demo-operativo"]) == ROL_OPERATIVO
    assert rol_de(usuarios["demo-gerencia"]) == ROL_OPERATIVO
    assert es_gerencia(usuarios["demo-gerencia"])
    assert rol_de(usuarios["demo-lectura"]) == ROL_LECTURA
    assert usuarios["demo-lectura"].check_password("clave-demo-de-prueba")
    assert RegistroAuditoria.objects.filter(usuario__username__in=USUARIOS_DEMO).exists()


@pytest.mark.django_db
def test_carga_demo_sin_clave_no_crea_usuarios(monkeypatch):
    monkeypatch.delenv("DJANGO_DEMO_PASSWORD", raising=False)

    call_command("cargar_datos_ejemplo")

    assert not User.objects.filter(username__in=USUARIOS_DEMO).exists()
    assert RegistroAuditoria.objects.filter(origen=RegistroAuditoria.Origen.SISTEMA).exists()


@pytest.mark.django_db
def test_carga_campanias_con_reservas_confirmadas_quedan_confirmadas():
    call_command("cargar_datos_ejemplo")
    confirmadas = Reserva.objects.filter(
        estado__in=[Reserva.Estado.CONFIRMADA, Reserva.Estado.FINALIZADA]
    )
    estados = set(
        Campania.objects.filter(reservas__in=confirmadas).values_list("estado", flat=True)
    )
    assert estados == {Campania.Estado.CONFIRMADA}
