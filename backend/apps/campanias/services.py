"""Reglas de negocio de campañas."""

from django.core.exceptions import ValidationError

from .models import Campania


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
