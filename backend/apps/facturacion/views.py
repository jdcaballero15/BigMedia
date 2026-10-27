from datetime import date, timedelta
from typing import cast

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from apps.auditoria import services as auditoria_services
from config.permisos import LecturaConSesionEdicionOperativo, LecturaSoloGerencia

from . import services
from .models import ItemFacturacion, Sector, TipoVenta
from .serializers import ItemFacturacionSerializer

# Cambios del ítem que quedan auditados (HU-007): estado, número e importes.
CAMPOS_AUDITADOS = ("estado", "numero_factura", "neto", "alicuota_iva", "cliente_id")


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


class PorRubroView(APIView):
    """Reporte de ingresos y días-cupo por rubro de la marca (HU-050, criterio 1)."""

    permission_classes = [permissions.IsAuthenticated, LecturaSoloGerencia]

    def get(self, request: Request) -> Response:
        hoy = timezone.localdate()
        params = request.query_params
        desde = _primer_dia(params.get("desde"), date(hoy.year, 1, 1))
        hasta = _ultimo_dia(_primer_dia(params.get("hasta"), date(hoy.year, 12, 1)))
        if hasta < desde:
            raise ValidationError(
                {"hasta": "El período de fin no puede ser anterior al de inicio."}
            )
        return Response(services.reporte_por_rubro(desde, hasta))


class IngresosView(APIView):
    """Reporte de ingresos por cliente y marca, repartidos por mes (HU-049)."""

    permission_classes = [permissions.IsAuthenticated, LecturaSoloGerencia]

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


def _id_positivo(valor: str, campo: str) -> int:
    if not valor.isdecimal() or int(valor) < 1:
        raise ValidationError({campo: "Debe ser un ID numérico positivo."})
    return int(valor)


def _mes(valor: str | None) -> date:
    """Parsea un mes `AAAA-MM` a su primer día."""
    if not valor:
        raise ValidationError({"mes": "Indicá el mes (AAAA-MM)."})
    try:
        return date.fromisoformat(f"{valor}-01")
    except ValueError as error:
        raise ValidationError({"mes": "Formato de mes inválido (AAAA-MM)."}) from error


def _auditables(item: ItemFacturacion) -> dict[str, str]:
    valores = {campo: getattr(item, campo) for campo in CAMPOS_AUDITADOS}
    return {
        campo.removesuffix("_id"): "" if valor is None else str(valor)
        for campo, valor in valores.items()
    }


class ItemFacturacionViewSet(viewsets.ModelViewSet[ItemFacturacion]):
    """Ítems a facturar (HU-060, HU-061, HU-065); sin DELETE: se anulan por estado."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]
    queryset = ItemFacturacion.objects.select_related(
        "cliente", "marca", "campania", "sector", "tipo_venta", "creado_por"
    )
    serializer_class = ItemFacturacionSerializer

    def perform_create(self, serializer: BaseSerializer[ItemFacturacion]) -> None:
        serializer.save(creado_por=self.request.user)

    def perform_update(self, serializer: BaseSerializer[ItemFacturacion]) -> None:
        anteriores = _auditables(cast(ItemFacturacion, serializer.instance))
        # El cambio y su auditoría en la misma transacción: nunca un cambio sin su registro.
        with transaction.atomic():
            item = serializer.save()
            auditoria_services.registrar_cambios(
                "item_facturacion", item.pk, anteriores, _auditables(item), self.request.user
            )

    def get_queryset(self) -> QuerySet[ItemFacturacion]:
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        params = self.request.query_params
        if params.get("mes"):
            queryset = queryset.filter(mes=_mes(params["mes"]))
        if params.get("estado"):
            if params["estado"] not in ItemFacturacion.Estado.values:
                raise ValidationError({"estado": "Estado desconocido."})
            queryset = queryset.filter(estado=params["estado"])
        for campo in ("cliente", "campania"):
            if params.get(campo):
                queryset = queryset.filter(**{f"{campo}_id": _id_positivo(params[campo], campo)})
        return queryset

    @action(detail=False, methods=["get"])
    def totales(self, request: Request) -> Response:
        """Neto, IVA y total del mes, sin los anulados (HU-065, criterio 3)."""
        return Response(services.totales_del_mes(_mes(request.query_params.get("mes"))))


class CatalogosFacturacionView(APIView):
    """Sectores (Gob/Priv) y tipos de venta (F/V) activos (RN-023)."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]

    def get(self, _request: Request) -> Response:
        return Response(
            {
                "sectores": list(Sector.objects.filter(activo=True).values("id", "nombre")),
                "tipos_venta": list(TipoVenta.objects.filter(activo=True).values("id", "nombre")),
            }
        )
