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
    queryset = Costo.objects.select_related(
        "proveedor", "reserva__cartel__formato", "reserva__campania"
    )
    serializer_class = CostoSerializer

    def get_queryset(self) -> QuerySet[Costo]:
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        params = self.request.query_params
        if params.get("reserva"):
            queryset = queryset.filter(reserva_id=_id_positivo(params["reserva"], "reserva"))
        if params.get("proveedor"):
            queryset = queryset.filter(proveedor_id=_id_positivo(params["proveedor"], "proveedor"))
        if params.get("tipo"):
            if params["tipo"] not in Costo.Tipo.values:
                raise ValidationError({"tipo": "Tipo de costo desconocido."})
            queryset = queryset.filter(tipo=params["tipo"])
        return queryset


class MargenView(APIView):
    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]

    def get(self, request: Request) -> Response:
        valor = request.query_params.get("reserva", "")
        reserva = Reserva.objects.filter(pk=_id_positivo(valor, "reserva")).first()
        if reserva is None:
            raise ValidationError({"reserva": "No existe la reserva."})
        return Response(services.margen_de_reserva(reserva))


class CampaniaMargenView(APIView):
    """Totales y margen de una campaña, desde sus reservas (HU-025, HU-045).

    No importa `campanias` (fuera de la tabla de dependencias de `costos`): recibe el id y agrega
    las reservas por `campania_id`; una campaña sin reservas devuelve ceros.
    """

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]

    def get(self, request: Request) -> Response:
        campania_id = _id_positivo(request.query_params.get("campania", ""), "campania")
        return Response(services.margen_de_campania(campania_id))
