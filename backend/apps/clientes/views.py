from typing import Any

from django.db.models import Q, QuerySet
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from config.permisos import LecturaConSesionEdicionOperativo
from config.texto import normalizar_busqueda

from .models import Cliente, Marca, Rubro
from .serializers import ClienteSerializer, MarcaSerializer, RubroSerializer


def _id_positivo(valor: str, campo: str) -> int:
    if not valor.isdecimal() or int(valor) < 1:
        raise ValidationError({campo: "Debe ser un ID numérico positivo."})
    return int(valor)


class ClientesViewSet(viewsets.ModelViewSet[Any]):
    """Lee cualquiera con sesión, edita Operativo; sin DELETE (baja lógica con `activo`)."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        if self.request.query_params.get("incluir_inactivos") != "1":
            queryset = queryset.filter(activo=True)
        return self.filtrar_lista(queryset)

    def filtrar_lista(self, queryset: QuerySet[Any]) -> QuerySet[Any]:
        return queryset

    def texto_buscado(self) -> str:
        return normalizar_busqueda(self.request.query_params.get("q", "").strip())


class RubroViewSet(ClientesViewSet):
    queryset = Rubro.objects.all()
    serializer_class = RubroSerializer


class ClienteViewSet(ClientesViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    def filtrar_lista(self, queryset: QuerySet[Any]) -> QuerySet[Any]:
        tipo = self.request.query_params.get("tipo")
        if tipo:
            if tipo not in Cliente.Tipo.values:
                raise ValidationError({"tipo": "Elegí un tipo de cliente válido."})
            queryset = queryset.filter(tipo=tipo)
        texto = self.texto_buscado()
        if texto:
            queryset = queryset.filter(
                Q(nombre_busqueda__contains=texto) | Q(razon_social_busqueda__contains=texto)
            )
        return queryset


class MarcaViewSet(ClientesViewSet):
    queryset = Marca.objects.select_related("cliente", "rubro")
    serializer_class = MarcaSerializer

    def filtrar_lista(self, queryset: QuerySet[Any]) -> QuerySet[Any]:
        params = self.request.query_params
        for campo in ("cliente", "rubro"):
            if params.get(campo):
                queryset = queryset.filter(**{f"{campo}_id": _id_positivo(params[campo], campo)})
        texto = self.texto_buscado()
        if texto:
            queryset = queryset.filter(nombre_busqueda__contains=texto)
        return queryset
