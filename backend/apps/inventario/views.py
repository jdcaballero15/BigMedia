from typing import Any

from django.db.models import QuerySet
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from config.permisos import LecturaConSesionEdicionOperativo
from config.texto import normalizar_busqueda

from .models import Cartel, EstadoCartel, Formato, Proveedor, Zona
from .serializers import (
    CartelSerializer,
    EstadoCartelSerializer,
    FormatoSerializer,
    ProveedorSerializer,
    ZonaSerializer,
)


class InventarioViewSet(viewsets.ModelViewSet[Any]):
    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]


class CatalogoViewSet(InventarioViewSet):
    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        if self.action == "list" and self.request.query_params.get("incluir_inactivos") != "1":
            queryset = queryset.filter(activo=True)
        return queryset


class ProveedorViewSet(CatalogoViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer


class FormatoViewSet(CatalogoViewSet):
    queryset = Formato.objects.all()
    serializer_class = FormatoSerializer


class ZonaViewSet(CatalogoViewSet):
    queryset = Zona.objects.all()
    serializer_class = ZonaSerializer


class EstadoCartelViewSet(CatalogoViewSet):
    queryset = EstadoCartel.objects.all()
    serializer_class = EstadoCartelSerializer


class CartelViewSet(InventarioViewSet):
    queryset = Cartel.objects.select_related("formato", "zona", "proveedor", "estado")
    serializer_class = CartelSerializer

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        params = self.request.query_params
        if params.get("incluir_bajas") != "1":
            queryset = queryset.filter(estado__es_baja=False)
        for field in ("zona", "formato", "estado"):
            if params.get(field):
                value = params[field]
                if not value.isdecimal() or int(value) < 1:
                    raise ValidationError({field: "Debe ser un ID numérico positivo."})
                queryset = queryset.filter(**{field + "_id": int(value)})
        if params.get("modalidad"):
            queryset = queryset.filter(formato__modalidad=params["modalidad"])
        if params.get("q"):
            queryset = queryset.filter(
                direccion_busqueda__icontains=normalizar_busqueda(params["q"].strip())
            )
        return queryset
