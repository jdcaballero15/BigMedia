from django.db.models import QuerySet
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reservas.models import Reserva
from config.permisos import LecturaConSesionEdicionOperativo

from . import services
from .models import Costo
from .serializers import CostoSerializer


def _id_positivo(valor: str, campo: str) -> int:
    if not valor.isdecimal() or int(valor) < 1:
        raise ValidationError({campo: "Debe ser un ID numérico positivo."})
    return int(valor)


class CostoViewSet(viewsets.ModelViewSet[Costo]):
    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]
    queryset = Costo.objects.select_related("proveedor")
    serializer_class = CostoSerializer

    def get_queryset(self) -> QuerySet[Costo]:
        queryset = super().get_queryset()
        if self.action == "list" and self.request.query_params.get("reserva"):
            queryset = queryset.filter(
                reserva_id=_id_positivo(self.request.query_params["reserva"], "reserva")
            )
        return queryset


class MargenView(APIView):
    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]

    def get(self, request: Request) -> Response:
        valor = request.query_params.get("reserva", "")
        reserva = Reserva.objects.filter(pk=_id_positivo(valor, "reserva")).first()
        if reserva is None:
            raise ValidationError({"reserva": "No existe la reserva."})
        return Response(services.margen_de_reserva(reserva))
