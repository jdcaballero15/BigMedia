"""Vistas de auditoría: endpoint de solo lectura para Gerencia."""

from datetime import date

from django.db.models import QuerySet
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from config.permisos import LecturaSoloGerencia

from .models import RegistroAuditoria
from .serializers import RegistroAuditoriaSerializer


def _parsear_fecha(valor: str, campo: str) -> date:
    try:
        return date.fromisoformat(valor)
    except ValueError as error:
        raise ValidationError({campo: "Formato de fecha inválido (AAAA-MM-DD)."}) from error


def _id_positivo(valor: str, campo: str) -> int:
    if not valor.isdecimal() or int(valor) < 1:
        raise ValidationError({campo: "Debe ser un ID numérico positivo."})
    return int(valor)


class RegistroAuditoriaViewSet(viewsets.ReadOnlyModelViewSet[RegistroAuditoria]):
    """Registros de auditoría: solo lectura, solo Gerencia o superusuario."""

    permission_classes = [permissions.IsAuthenticated, LecturaSoloGerencia]
    serializer_class = RegistroAuditoriaSerializer
    queryset = RegistroAuditoria.objects.select_related("usuario")

    def get_queryset(self) -> QuerySet[RegistroAuditoria]:
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        params = self.request.query_params
        if params.get("entidad"):
            queryset = queryset.filter(entidad=params["entidad"])
        if params.get("entidad_id"):
            queryset = queryset.filter(entidad_id=_id_positivo(params["entidad_id"], "entidad_id"))
        if params.get("usuario"):
            queryset = queryset.filter(usuario_id=_id_positivo(params["usuario"], "usuario"))
        if params.get("desde"):
            desde = _parsear_fecha(params["desde"], "desde")
            queryset = queryset.filter(momento__date__gte=desde)
        if params.get("hasta"):
            hasta = _parsear_fecha(params["hasta"], "hasta")
            queryset = queryset.filter(momento__date__lte=hasta)
        return queryset
