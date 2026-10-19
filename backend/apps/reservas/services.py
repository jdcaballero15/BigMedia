"""Reglas de negocio de reservas."""

from datetime import date, timedelta

from django.conf import settings
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


def _estados_que_bloquean() -> set[str]:
    """Estados que ocupan cupo para el bloqueo duro (RN-002)."""
    estados: set[str] = {Reserva.Estado.CONFIRMADA.value, Reserva.Estado.FINALIZADA.value}
    if settings.DISPONIBILIDAD_TENTATIVA_BLOQUEA:
        estados.add(Reserva.Estado.PENDIENTE.value)
    return estados


def _fin_efectivo(fin: date) -> date:
    """Último día que la reserva ocupa el cartel según el día de borde (RN-001)."""
    return fin if settings.DISPONIBILIDAD_BORDE_INCLUSIVO else fin - timedelta(days=1)


def validar_disponibilidad(reserva: Reserva) -> None:
    """Bloquea si el cartel no tiene cupo libre en el rango pedido (HU-031).

    Usa pico diario (RN-003): la ocupación máxima en cualquier tramo del rango, no el conteo de
    reservas que tocan el rango. Debe correr dentro de una transacción que ya bloqueó el cartel
    (`select_for_update`), para que dos confirmaciones del mismo cartel no se pisen (HU-034).
    """
    capacidad = reserva.cartel.capacidad
    fin_nueva = _fin_efectivo(reserva.fecha_fin)
    otras = Reserva.objects.filter(
        cartel=reserva.cartel, estado__in=_estados_que_bloquean()
    ).exclude(pk=reserva.pk)
    # Solo las que se solapan con el rango pedido (intervalos inclusivos con fin efectivo).
    conflictivas = [
        otra
        for otra in otras
        if otra.fecha_inicio <= fin_nueva and reserva.fecha_inicio <= _fin_efectivo(otra.fecha_fin)
    ]
    if not conflictivas:
        return

    # La ocupación solo sube en un inicio de reserva: basta mirar esos días dentro del rango.
    dias_candidatos = {reserva.fecha_inicio} | {
        otra.fecha_inicio
        for otra in conflictivas
        if reserva.fecha_inicio <= otra.fecha_inicio <= fin_nueva
    }
    pico, dia_pico = 0, reserva.fecha_inicio
    for dia in dias_candidatos:
        cubren = sum(
            1 for otra in conflictivas if otra.fecha_inicio <= dia <= _fin_efectivo(otra.fecha_fin)
        )
        if cubren > pico:
            pico, dia_pico = cubren, dia

    # La reserva nueva suma 1: si en el día pico ya hay `capacidad` ocupados, no entra.
    if pico >= capacidad:
        culpables = [
            otra.nombre
            for otra in conflictivas
            if otra.fecha_inicio <= dia_pico <= _fin_efectivo(otra.fecha_fin)
        ]
        raise ValidationError(
            {
                "disponibilidad": (
                    f"{reserva.cartel.nombre_visible}: sin cupo libre "
                    f"({pico} de {capacidad}) entre {reserva.fecha_inicio} y {reserva.fecha_fin}. "
                    f"En conflicto: {', '.join(culpables)}."
                )
            }
        )
