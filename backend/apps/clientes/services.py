"""Reglas de negocio de clientes y marcas."""

from collections.abc import Callable
from typing import Any

from django.db import transaction

from config.texto import distancia_edicion, normalizar_comparacion

from .models import Cliente, Contacto, Marca
from .signals import cliente_de_marca_cambiado

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


@transaction.atomic
def actualizar_marca(marca: Marca, guardar: Callable[[], object]) -> None:
    """Guarda una marca editada y, si pasó a otro cliente, lo avisa (HU-027, ADR-0010).

    `guardar` hace el guardado (el serializer o el admin). El cliente anterior se lee de la base con
    la marca bloqueada, y la señal se emite en la misma transacción: si quien la escucha falla, la
    marca tampoco cambia.
    """
    anterior = Marca.objects.select_for_update().select_related("cliente").get(pk=marca.pk)
    guardar()
    if marca.cliente_id != anterior.cliente_id:
        cliente_de_marca_cambiado.send(sender=Marca, marca=marca, cliente_anterior=anterior.cliente)


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


def acepta_contactos(cliente: Cliente) -> bool:
    """Solo el intermediario formal tiene contactos múltiples (RN-015, provisoria)."""
    return cliente.tipo == Cliente.Tipo.INTERMEDIARIO_FORMAL


def tiene_contactos_activos(cliente: Cliente) -> bool:
    return cliente.contactos.filter(activo=True).exists()


@transaction.atomic
def guardar_contacto(contacto: Contacto) -> Contacto:
    """Guarda un contacto dejando un solo principal por cliente (HU-068, criterio 3).

    Bloquea el cliente para que dos contactos marcados a la vez no queden ambos como principales.
    Un contacto inactivo deja de ser el principal.
    """
    Cliente.objects.select_for_update().filter(pk=contacto.cliente_id).first()
    if not contacto.activo:
        contacto.principal = False
    if contacto.principal:
        Contacto.objects.filter(cliente_id=contacto.cliente_id, principal=True).exclude(
            pk=contacto.pk
        ).update(principal=False)
    contacto.save()
    return contacto
