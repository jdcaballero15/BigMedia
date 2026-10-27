from typing import cast

from django.db import transaction
from django.db.models import Q, QuerySet
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import BaseSerializer

from apps.auditoria import services as auditoria_services
from config.permisos import LecturaConSesionEdicionOperativo
from config.texto import normalizar_busqueda

from .models import Campania, Interaccion
from .serializers import CampaniaSerializer, InteraccionSerializer


def _id_positivo(valor: str, campo: str) -> int:
    if not valor.isdecimal() or int(valor) < 1:
        raise ValidationError({campo: "Debe ser un ID numérico positivo."})
    return int(valor)


class CampaniaViewSet(viewsets.ModelViewSet[Campania]):
    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]
    queryset = Campania.objects.select_related("marca__cliente", "cliente_facturacion")
    serializer_class = CampaniaSerializer

    def perform_update(self, serializer: BaseSerializer[Campania]) -> None:
        instancia = cast(Campania, serializer.instance)
        anterior = instancia.estado
        with transaction.atomic():
            serializer.save()
            nuevo = cast(Campania, serializer.instance).estado
            auditoria_services.registrar_cambios(
                "campania",
                instancia.pk,
                {"estado": anterior},
                {"estado": nuevo},
                self.request.user,
            )

    def get_queryset(self) -> QuerySet[Campania]:
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        params = self.request.query_params
        if params.get("estado"):
            estados = {value for value, _ in Campania.Estado.choices}
            if params["estado"] not in estados:
                raise ValidationError({"estado": "Estado desconocido."})
            queryset = queryset.filter(estado=params["estado"])
        if params.get("marca"):
            queryset = queryset.filter(marca_id=_id_positivo(params["marca"], "marca"))
        if params.get("cliente"):
            # Las que factura el cliente o las de sus marcas (las interacciones las ofrecen así).
            cliente = _id_positivo(params["cliente"], "cliente")
            queryset = queryset.filter(
                Q(cliente_facturacion_id=cliente) | Q(marca__cliente_id=cliente)
            )
        if params.get("q"):
            queryset = queryset.filter(
                nombre_busqueda__icontains=normalizar_busqueda(params["q"].strip())
            )
        return queryset


class InteraccionViewSet(viewsets.ModelViewSet[Interaccion]):
    """Interacciones comerciales (HU-020); sin DELETE (HU-006)."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]
    queryset = Interaccion.objects.select_related(
        "cliente", "contacto", "campania", "registrada_por"
    )
    serializer_class = InteraccionSerializer

    def perform_create(self, serializer: BaseSerializer[Interaccion]) -> None:
        serializer.save(registrada_por=self.request.user)

    def get_queryset(self) -> QuerySet[Interaccion]:
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        params = self.request.query_params
        for campo in ("cliente", "campania"):
            if params.get(campo):
                queryset = queryset.filter(**{f"{campo}_id": _id_positivo(params[campo], campo)})
        return queryset
