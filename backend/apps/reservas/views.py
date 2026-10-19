from django.db.models import QuerySet
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventario.models import Cartel
from config.permisos import LecturaConSesionEdicionOperativo

from . import services
from .models import Reserva
from .serializers import ReservaSerializer


def _id_positivo(valor: str, campo: str) -> int:
    if not valor.isdecimal() or int(valor) < 1:
        raise ValidationError({campo: "Debe ser un ID numérico positivo."})
    return int(valor)


class ReservaViewSet(viewsets.ModelViewSet[Reserva]):
    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]
    queryset = Reserva.objects.select_related("campania__marca", "cartel")
    serializer_class = ReservaSerializer

    def get_queryset(self) -> QuerySet[Reserva]:
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        params = self.request.query_params
        for campo in ("campania", "cartel"):
            if params.get(campo):
                queryset = queryset.filter(**{f"{campo}_id": _id_positivo(params[campo], campo)})
        if params.get("estado"):
            estados = {value for value, _ in Reserva.Estado.choices}
            if params["estado"] not in estados:
                raise ValidationError({"estado": "Estado desconocido."})
            queryset = queryset.filter(estado=params["estado"])
        return queryset


class OcupacionView(APIView):
    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]

    def get(self, request: Request) -> Response:
        valor = request.query_params.get("cartel", "")
        cartel = Cartel.objects.filter(pk=_id_positivo(valor, "cartel")).first()
        if cartel is None:
            raise ValidationError({"cartel": "No existe el cartel."})
        return Response(services.ocupacion_del_cartel(cartel))
