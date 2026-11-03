"""Receptores de señales de otras apps (ADR-0010)."""

from typing import Any

from django.dispatch import receiver

from apps.clientes.models import Cliente, Marca
from apps.clientes.signals import cliente_de_marca_cambiado

from . import services


@receiver(cliente_de_marca_cambiado, sender=Marca)
def conservar_cliente_de_campanias(marca: Marca, cliente_anterior: Cliente, **_kwargs: Any) -> None:
    """Al cambiar el cliente de una marca, sus campañas conservan el anterior (HU-027).

    Django pasa también `sender` y `signal`; quedan en `_kwargs`.
    """
    services.estampar_cliente_anterior(marca, cliente_anterior)
