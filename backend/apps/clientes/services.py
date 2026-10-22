"""Reglas de negocio de clientes y marcas."""

from typing import Any

from django.db import transaction

from .models import Cliente, Marca


def crear_marca_homonima(cliente: Cliente) -> Marca:
    """Crea la marca con el nombre del cliente directo, que la factura (HU-018)."""
    return Marca.objects.create(nombre=cliente.nombre, cliente=cliente)


@transaction.atomic
def registrar_cliente(cliente: Cliente) -> Cliente:
    """Guarda un cliente nuevo y, si es directo, su marca homónima en la misma transacción (HU-018).

    Un cliente directo sin nombre no crea marca: no hay con qué nombrarla. Si la marca no se puede
    crear, el cliente tampoco queda guardado. La marca se crea solo en el alta: editar el cliente
    después no la duplica ni la renombra (RN-017 sigue pendiente).
    """
    cliente.nombre = cliente.nombre.strip()
    cliente.save()
    if cliente.tipo == Cliente.Tipo.DIRECTO and cliente.nombre:
        crear_marca_homonima(cliente)
    return cliente


def crear_cliente(**datos: Any) -> Cliente:
    """Crea un cliente con los datos validados; ver `registrar_cliente`."""
    return registrar_cliente(Cliente(**datos))
