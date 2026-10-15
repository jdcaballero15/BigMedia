from rest_framework import permissions, viewsets

from .models import EstadoCartel, Formato, Proveedor, Zona
from .serializers import (
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
