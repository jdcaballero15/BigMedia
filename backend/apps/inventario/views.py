from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from .models import Cartel, EstadoCartel, Formato, Proveedor, Zona, normalizar_busqueda
from .serializers import (
    CartelSerializer,
    EstadoCartelSerializer,
    FormatoSerializer,
    ProveedorSerializer,
    ZonaSerializer,
)


class PuedeOperarInventario(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_superuser or request.user.groups.filter(name="Operativo").exists()


class CatalogoViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, PuedeOperarInventario]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = self.queryset.all()
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


class CartelViewSet(CatalogoViewSet):
    queryset = Cartel.objects.select_related("formato", "zona", "proveedor", "estado")
    serializer_class = CartelSerializer

    def get_queryset(self):
        queryset = self.queryset.all()
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
