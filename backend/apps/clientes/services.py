"""Reglas de negocio de clientes y marcas."""

from typing import Any

from django.db import transaction

from config.texto import distancia_edicion, normalizar_comparacion

from .models import Cliente, Marca

# A partir de este largo se toleran dos errores de tipeo en vez de uno (HU-019).
LARGO_PARA_DOS_ERRORES = 8


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


def _se_parecen(a: str, b: str) -> bool:
    """Iguales normalizados, o a un error de tipeo (dos si ambos son largos) (HU-019)."""
    tope = 2 if min(len(a), len(b)) >= LARGO_PARA_DOS_ERRORES else 1
    return distancia_edicion(a, b, tope) <= tope


def posibles_duplicados(nombre: str, excluir: int | None = None) -> list[Marca]:
    """Marcas, activas o inactivas, con un nombre igual o muy parecido a `nombre` (HU-019)."""
    buscado = normalizar_comparacion(nombre)
    if not buscado:
        return []
    marcas = Marca.objects.select_related("cliente").order_by("nombre", "id")
    if excluir is not None:
        marcas = marcas.exclude(pk=excluir)
    return [m for m in marcas if _se_parecen(buscado, normalizar_comparacion(m.nombre))]


def describir_duplicado(marca: Marca) -> str:
    """Texto del aviso: nombre, cliente que la factura y estado de la marca coincidente."""
    estado = "activa" if marca.activo else "inactiva"
    return f"{marca.nombre} — {marca.cliente.nombre_visible} ({estado})"
