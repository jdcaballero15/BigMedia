"""Reglas de negocio de reservas."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db.models import Count
from django.utils import timezone

from apps.inventario.models import Cartel

from .models import Reserva

# Transiciones de estado válidas del ciclo de vida de la reserva (HU-035).
# La revalidación de cupo al confirmar/reactivar es de la unidad del motor (HU-031).
TRANSICIONES: dict[str, set[str]] = {
    Reserva.Estado.PENDIENTE: {Reserva.Estado.CONFIRMADA, Reserva.Estado.CANCELADA},
    Reserva.Estado.CONFIRMADA: {Reserva.Estado.FINALIZADA, Reserva.Estado.CANCELADA},
    Reserva.Estado.CANCELADA: {Reserva.Estado.CONFIRMADA},
    Reserva.Estado.FINALIZADA: set(),
}


def validar_transicion(actual: str, nuevo: str) -> None:
    if nuevo == actual:
        return
    if nuevo not in TRANSICIONES.get(actual, set()):
        raise ValidationError({"estado": f"No se puede pasar de {actual} a {nuevo}."})


def ocupacion_del_cartel(cartel: Cartel, dia: date | None = None) -> dict[str, int]:
    """Cupos ocupados vigentes sobre la capacidad del cartel, al momento (HU-040)."""
    dia = dia or timezone.localdate()
    ocupados = Reserva.objects.filter(
        cartel=cartel,
        estado__in=Reserva.ESTADOS_QUE_OCUPAN,
        fecha_inicio__lte=dia,
        fecha_fin__gte=dia,
    ).aggregate(total=Count("id"))["total"]
    return {"cartel": cartel.pk, "capacidad": cartel.capacidad, "ocupados": ocupados}
