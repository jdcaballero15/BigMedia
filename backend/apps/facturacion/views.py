from datetime import date, timedelta

from django.utils import timezone
from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.permisos import LecturaConSesionEdicionOperativo

from . import services


def _primer_dia(valor: str | None, por_defecto: date) -> date:
    """Parsea un período `AAAA-MM` al primer día del mes; vacío usa el valor por defecto."""
    if not valor:
        return por_defecto
    try:
        return date.fromisoformat(f"{valor}-01")
    except ValueError as error:
        raise ValidationError({"periodo": "Formato de período inválido (AAAA-MM)."}) from error


def _ultimo_dia(primero: date) -> date:
    """Último día del mes del `primero` dado."""
    if primero.month == 12:
        return date(primero.year, 12, 31)
    return date(primero.year, primero.month + 1, 1) - timedelta(days=1)


class IngresosView(APIView):
    """Reporte de ingresos por cliente y marca, repartidos por mes (HU-049)."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]

    def get(self, request: Request) -> Response:
        hoy = timezone.localdate()
        params = request.query_params
        desde = _primer_dia(params.get("desde"), date(hoy.year, 1, 1))
        hasta = _ultimo_dia(_primer_dia(params.get("hasta"), date(hoy.year, 12, 1)))
        if hasta < desde:
            raise ValidationError(
                {"hasta": "El período de fin no puede ser anterior al de inicio."}
            )
        return Response(services.reporte_ingresos(desde, hasta))
