"""Reglas de negocio de costos."""

from decimal import Decimal

from django.db.models import Sum

from apps.reservas.models import Reserva

from .models import Costo


def margen_de_reserva(reserva: Reserva) -> dict[str, object]:
    """Ingreso, costo, margen y porcentaje de una reserva (HU-044); los anulados no suman."""
    ingreso = reserva.total
    costo = Costo.objects.filter(reserva=reserva, anulado=False).aggregate(total=Sum("monto"))[
        "total"
    ] or Decimal("0.00")
    margen = ingreso - costo
    porcentaje = round(float(margen / ingreso * 100), 2) if ingreso else None
    return {
        "ingreso": f"{ingreso:.2f}",
        "costo": f"{costo:.2f}",
        "margen": f"{margen:.2f}",
        "porcentaje": porcentaje,
    }
