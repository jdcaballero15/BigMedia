from __future__ import annotations

from typing import cast

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import Q, QuerySet
from django.http import FileResponse, HttpResponseBase, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from apps.auditoria import services as auditoria_services
from config.permisos import LecturaConSesionEdicionOperativo
from config.texto import normalizar_busqueda

from . import services
from .models import Campania, Interaccion, LineaFormato, OrdenPublicidad
from .serializers import (
    CampaniaSerializer,
    InteraccionSerializer,
    LineaFormatoSerializer,
    OrdenPublicidadSerializer,
)


def _id_positivo(valor: str, campo: str) -> int:
    if not valor.isdecimal() or int(valor) < 1:
        raise ValidationError({campo: "Debe ser un ID numérico positivo."})
    return int(valor)


class CampaniaViewSet(viewsets.ModelViewSet[Campania]):
    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]
    queryset = Campania.objects.select_related(
        "marca__cliente", "cliente_facturacion"
    ).prefetch_related("ordenes_publicidad__subida_por")
    serializer_class = CampaniaSerializer

    def _ordenes_publicidad(self) -> list[UploadedFile[bytes]]:
        """PDF adjuntos en el mismo pedido, validados antes de guardar nada (HU-069)."""
        archivos: list[UploadedFile[bytes]] = self.request.FILES.getlist("ordenes_publicidad")
        try:
            services.validar_ordenes_publicidad(archivos)
        except DjangoValidationError as error:
            raise ValidationError(error.message_dict) from error
        return archivos

    def _usuario(self) -> AbstractBaseUser:
        return cast(AbstractBaseUser, self.request.user)

    def perform_create(self, serializer: BaseSerializer[Campania]) -> None:
        archivos = self._ordenes_publicidad()
        with transaction.atomic():
            campania = serializer.save()
            services.adjuntar_ordenes_publicidad(campania, archivos, self._usuario())

    def perform_update(self, serializer: BaseSerializer[Campania]) -> None:
        archivos = self._ordenes_publicidad()
        instancia = cast(Campania, serializer.instance)
        anterior = instancia.estado
        with transaction.atomic():
            serializer.save()
            services.adjuntar_ordenes_publicidad(instancia, archivos, self._usuario())
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


class LineaFormatoViewSet(viewsets.ModelViewSet[LineaFormato]):
    """Posiciones solicitadas por formato (HU-055); quitar es `activa=false`, sin DELETE."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]
    queryset = LineaFormato.objects.select_related("formato")
    serializer_class = LineaFormatoSerializer

    def get_queryset(self) -> QuerySet[LineaFormato]:
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        queryset = queryset.filter(activa=True)
        campania = self.request.query_params.get("campania")
        if campania:
            queryset = queryset.filter(campania_id=_id_positivo(campania, "campania"))
        return queryset


class InteraccionViewSet(viewsets.ModelViewSet[Interaccion]):
    """Interacciones comerciales (HU-020); sin DELETE (HU-006)."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]
    queryset = Interaccion.objects.select_related(
        "cliente", "contacto", "campania", "marca", "registrada_por"
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
        if params.get("marca"):
            # Las que llevan la marca y las de sus campañas, aunque no la tengan cargada (RN-018).
            marca = _id_positivo(params["marca"], "marca")
            queryset = queryset.filter(Q(marca_id=marca) | Q(campania__marca_id=marca))
        return queryset


class OrdenPublicidadViewSet(viewsets.GenericViewSet[OrdenPublicidad]):
    """Abrir y dar de baja una orden de publicidad (HU-069). Se adjunta desde la campaña."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    queryset = OrdenPublicidad.objects.select_related("subida_por")
    serializer_class = OrdenPublicidadSerializer

    @action(detail=True, methods=["get"])
    def archivo(self, _request: Request, pk: str) -> HttpResponseBase:
        """Con R2, redirige a una URL firmada de pocos minutos; sin R2, sirve el archivo."""
        orden = get_object_or_404(self.get_queryset(), pk=pk)
        if settings.R2_BUCKET:
            return HttpResponseRedirect(orden.archivo.url)
        return FileResponse(
            orden.archivo.open("rb"), content_type="application/pdf", filename=orden.nombre
        )

    @action(detail=True, methods=["post"], url_path="dar-de-baja")
    def dar_de_baja(self, request: Request, pk: str) -> Response:
        """Baja lógica de la orden: el archivo queda en el bucket (HU-069, criterio 5)."""
        orden = get_object_or_404(self.get_queryset(), pk=pk)
        orden = services.dar_de_baja_orden_publicidad(
            orden.pk, cast(AbstractBaseUser, request.user)
        )
        return Response(self.get_serializer(orden).data)
