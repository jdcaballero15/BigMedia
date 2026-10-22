from django.db.models import QuerySet
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from config.permisos import LecturaConSesionEdicionOperativo
from config.texto import normalizar_busqueda

from .models import Campania
from .serializers import CampaniaSerializer


class CampaniaViewSet(viewsets.ModelViewSet[Campania]):
    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]
    queryset = Campania.objects.select_related("marca__cliente", "cliente_facturacion")
    serializer_class = CampaniaSerializer

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
            valor = params["marca"]
            if not valor.isdecimal() or int(valor) < 1:
                raise ValidationError({"marca": "Debe ser un ID numérico positivo."})
            queryset = queryset.filter(marca_id=int(valor))
        if params.get("q"):
            queryset = queryset.filter(
                nombre_busqueda__icontains=normalizar_busqueda(params["q"].strip())
            )
        return queryset
