from datetime import date, timedelta
from typing import cast

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from apps.auditoria import services as auditoria_services
from apps.inventario.models import Cartel
from config.permisos import LecturaConSesionEdicionOperativo, SoloAdministrador

from . import services
from .models import ParametrosDisponibilidad, Reserva
from .serializers import ParametrosDisponibilidadSerializer, ReservaSerializer


def _id_positivo(valor: str, campo: str) -> int:
    if not valor.isdecimal() or int(valor) < 1:
        raise ValidationError({campo: "Debe ser un ID numérico positivo."})
    return int(valor)


def _campos_auditados(reserva: Reserva) -> dict[str, str]:
    """Devuelve los campos auditables de una reserva como texto, para comparar cambios."""
    return {
        "fecha_inicio": reserva.fecha_inicio.isoformat(),
        "fecha_fin": reserva.fecha_fin.isoformat(),
        "estado": reserva.estado,
        "cartel": str(reserva.cartel_id),
        "precio_alquiler": str(reserva.precio_alquiler),
        "precio_impresion": str(reserva.precio_impresion),
        "precio_fijacion": str(reserva.precio_fijacion),
    }


class ReservaViewSet(viewsets.ModelViewSet[Reserva]):
    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]
    queryset = Reserva.objects.select_related("campania__marca", "cartel")
    serializer_class = ReservaSerializer

    def perform_create(self, serializer: BaseSerializer[Reserva]) -> None:
        estado = serializer.validated_data.get("estado", Reserva.Estado.PENDIENTE)
        necesita = services.necesita_validar_cupo(None, estado, cambia_ocupacion=True)
        self._guardar_con_disponibilidad(serializer, necesita)

    def perform_update(self, serializer: BaseSerializer[Reserva]) -> None:
        datos = serializer.validated_data
        instancia = cast(Reserva, serializer.instance)
        nuevo_estado = datos.get("estado", instancia.estado)
        cambia_ocupacion = any(c in datos for c in ("fecha_inicio", "fecha_fin", "cartel"))
        # No se revalida si solo cambia un precio (matriz caso 13).
        necesita = services.necesita_validar_cupo(instancia.estado, nuevo_estado, cambia_ocupacion)
        # El cambio y su auditoría en la misma transacción: nunca un cambio sin su registro.
        anteriores = _campos_auditados(instancia)
        with transaction.atomic():
            self._guardar_con_disponibilidad(serializer, necesita)
            nuevos = _campos_auditados(cast(Reserva, serializer.instance))
            auditoria_services.registrar_cambios(
                "reserva", instancia.pk, anteriores, nuevos, self.request.user
            )

    def _guardar_con_disponibilidad(
        self, serializer: BaseSerializer[Reserva], necesita: bool
    ) -> None:
        with transaction.atomic():
            if "cartel" in serializer.validated_data:
                cartel = serializer.validated_data["cartel"]
            else:
                cartel = cast(Reserva, serializer.instance).cartel
            # Bloquea el cartel: serializa confirmaciones del mismo cartel (HU-034).
            Cartel.objects.select_for_update().get(pk=cartel.pk)
            reserva = serializer.save()
            if necesita:
                try:
                    services.validar_disponibilidad(reserva)
                except DjangoValidationError as error:
                    raise ValidationError(error.message_dict) from error

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


class DisponibilidadView(APIView):
    """Ocupación actual de los carteles, con accesos rápidos y filtros de inventario (HU-041)."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]

    def get(self, request: Request) -> Response:
        queryset = services.carteles_con_ocupacion_hoy()
        params = request.query_params
        for campo in ("zona", "formato"):
            if params.get(campo):
                queryset = queryset.filter(**{f"{campo}_id": _id_positivo(params[campo], campo)})
        if params.get("modalidad"):
            queryset = queryset.filter(formato__modalidad=params["modalidad"])
        # `cupos_libres` es una anotación; se filtra con kwargs dinámicos.
        if params.get("ocupacion") == "libres":
            queryset = queryset.filter(**{"cupos_libres__gt": 0})
        elif params.get("ocupacion") == "ocupados":
            queryset = queryset.filter(**{"cupos_libres__lte": 0})
        filas = [
            services.fila_disponibilidad(fila)
            for fila in queryset.values(*services.CAMPOS_DISPONIBILIDAD)
        ]
        return Response(filas)


class CalendarioView(APIView):
    """Calendario de disponibilidad a futuro: carteles por mes (HU-042)."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]

    def get(self, request: Request) -> Response:
        params = request.query_params
        hoy = timezone.localdate()
        desde = self._fecha(params.get("desde"), hoy)
        # Por defecto, 3 columnas: el mes actual y los dos siguientes.
        hasta = self._fecha(params.get("hasta"), services.sumar_meses(desde, 2))
        if hasta < desde:
            raise ValidationError(
                {"hasta": "La fecha de fin no puede ser anterior a la de inicio."}
            )
        if services.sumar_meses(desde, services.MESES_CALENDARIO_MAX) < hasta:
            raise ValidationError(
                {"hasta": f"El rango no puede superar los {services.MESES_CALENDARIO_MAX} meses."}
            )
        zona = _id_positivo(params["zona"], "zona") if params.get("zona") else None
        formato = _id_positivo(params["formato"], "formato") if params.get("formato") else None
        return Response(
            services.calendario_disponibilidad(
                desde, hasta, zona=zona, formato=formato, modalidad=params.get("modalidad")
            )
        )

    @staticmethod
    def _fecha(valor: str | None, por_defecto: date) -> date:
        if not valor:
            return por_defecto
        try:
            return date.fromisoformat(valor)
        except ValueError as error:
            raise ValidationError({"fecha": "Formato de fecha inválido (AAAA-MM-DD)."}) from error


class PanelView(APIView):
    """Resumen del panel de inicio (HU-047)."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]

    def get(self, _request: Request) -> Response:
        return Response(services.panel_principal())


class ReporteOcupacionView(APIView):
    """Ocupación en días-cupo por cartel y mes: mapa de calor, ranking y evolución (HU-048)."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]

    def get(self, request: Request) -> Response:
        params = request.query_params
        hoy = timezone.localdate()
        desde = self._mes(params.get("desde"), date(hoy.year, 1, 1))
        hasta = self._fin_de_mes(self._mes(params.get("hasta"), date(hoy.year, 12, 1)))
        if hasta < desde:
            raise ValidationError(
                {"hasta": "El período de fin no puede ser anterior al de inicio."}
            )
        if services.sumar_meses(desde, services.MESES_CALENDARIO_MAX) < hasta:
            raise ValidationError(
                {"hasta": f"El rango no puede superar los {services.MESES_CALENDARIO_MAX} meses."}
            )
        zona = _id_positivo(params["zona"], "zona") if params.get("zona") else None
        return Response(
            services.reporte_ocupacion(
                desde, hasta, zona=zona, modalidad=params.get("modalidad") or None
            )
        )

    @staticmethod
    def _mes(valor: str | None, por_defecto: date) -> date:
        if not valor:
            return por_defecto
        try:
            return date.fromisoformat(f"{valor}-01")
        except ValueError as error:
            raise ValidationError({"periodo": "Formato de período inválido (AAAA-MM)."}) from error

    @staticmethod
    def _fin_de_mes(primero: date) -> date:
        if primero.month == 12:
            return date(primero.year, 12, 31)
        return date(primero.year, primero.month + 1, 1) - timedelta(days=1)


class RepartoView(APIView):
    """Reparto del ingreso de una reserva por mes (HU-051)."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]

    def get(self, request: Request) -> Response:
        valor = request.query_params.get("reserva", "")
        reserva = Reserva.objects.filter(pk=_id_positivo(valor, "reserva")).first()
        if reserva is None:
            raise ValidationError({"reserva": "No existe la reserva."})
        return Response(services.reparto_por_mes(reserva))


def _parametros_auditados(parametros: ParametrosDisponibilidad) -> dict[str, str]:
    return {
        "borde_inclusivo": str(parametros.borde_inclusivo),
        "tentativa_bloquea": str(parametros.tentativa_bloquea),
    }


class ParametrosView(APIView):
    """Parámetros del motor de disponibilidad (HU-001): solo el rol Administrador."""

    permission_classes = [permissions.IsAuthenticated, SoloAdministrador]
    http_method_names = ["get", "patch", "head", "options"]

    def get(self, _request: Request) -> Response:
        return Response(
            ParametrosDisponibilidadSerializer(services.parametros_disponibilidad()).data
        )

    def patch(self, request: Request) -> Response:
        # El cambio y su auditoría en la misma transacción, con la fila bloqueada.
        with transaction.atomic():
            services.parametros_disponibilidad()
            parametros = ParametrosDisponibilidad.objects.select_for_update().get(pk=1)
            anteriores = _parametros_auditados(parametros)
            serializer = ParametrosDisponibilidadSerializer(
                parametros, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            auditoria_services.registrar_cambios(
                "parametros",
                parametros.pk,
                anteriores,
                _parametros_auditados(parametros),
                request.user,
            )
        return Response(serializer.data)
