"""Comando de datos de ejemplo para staging (HU — unidad de entornos)."""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.clientes.models import Cliente
from apps.reservas.models import Reserva


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
