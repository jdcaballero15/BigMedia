"""Reglas de negocio de campañas."""

from django.core.exceptions import ValidationError

from apps.clientes.models import Cliente, Contacto
from apps.inventario.models import Formato

from .models import Campania, LineaFormato


def validar_confirmacion(campania: Campania) -> None:
    """Para confirmar se exigen marca, cliente que factura y ambas fechas (RN-011)."""
    faltantes = []
    if campania.marca_id is None:
        faltantes.append("la marca")
    if campania.cliente_factura is None:
        faltantes.append("el cliente que factura")
    if campania.fecha_inicio is None or campania.fecha_fin is None:
        faltantes.append("las fechas")
    if faltantes:
        detalle = ", ".join(faltantes)
        raise ValidationError({"estado": f"Para confirmar falta cargar {detalle}."})


def validar_contacto_de_interaccion(
    cliente: Cliente, contacto: Contacto | None, sin_cambios: bool
) -> None:
    """El contacto es del mismo cliente y está activo (HU-068 criterio 5).

    Un contacto que ya tenía la interacción se conserva aunque después se haya inactivado.
    """
    if contacto is None:
        return
    if contacto.cliente_id != cliente.pk:
        raise ValidationError({"contacto": "El contacto no es de ese cliente."})
    if not contacto.activo and not sin_cambios:
        raise ValidationError({"contacto": "Seleccioná un contacto activo."})


def validar_campania_de_interaccion(cliente: Cliente, campania: Campania | None) -> None:
    """La campaña la factura el cliente o es de una de sus marcas."""
    if campania is None:
        return
    facturador = campania.cliente_factura
    duenio_marca = campania.marca.cliente_id if campania.marca is not None else None
    if cliente.pk not in {getattr(facturador, "pk", None), duenio_marca}:
        raise ValidationError({"campania": "La campaña no es de ese cliente."})


def validar_linea_formato(
    campania: Campania,
    formato: Formato,
    activa: bool,
    actual: LineaFormato | None,
    formato_sin_cambios: bool,
) -> None:
    """Formato activo y sin repetir entre las líneas activas de la campaña (HU-055)."""
    if not formato.activo and not formato_sin_cambios:
        raise ValidationError({"formato": "Seleccioná un formato activo."})
    if not activa:
        return
    repetidas = LineaFormato.objects.filter(campania=campania, formato=formato, activa=True)
    if actual is not None:
        repetidas = repetidas.exclude(pk=actual.pk)
    if repetidas.exists():
        raise ValidationError({"formato": f"La campaña ya tiene una línea de {formato.nombre}."})
