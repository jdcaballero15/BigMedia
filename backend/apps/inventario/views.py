from typing import Any, cast

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import QuerySet
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from apps.auditoria import services as auditoria_services
from config.permisos import LecturaConSesionEdicionOperativo, SoloAdministrador
from config.texto import normalizar_busqueda

from . import services
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

    def perform_update(self, serializer: BaseSerializer[Cartel]) -> None:
        instancia = cast(Cartel, serializer.instance)
        tarifa_anterior = instancia.tarifa_lista
        anterior = "" if tarifa_anterior is None else str(tarifa_anterior)
        with transaction.atomic():
            serializer.save()
            tarifa_nueva = cast(Cartel, serializer.instance).tarifa_lista
            nuevo = "" if tarifa_nueva is None else str(tarifa_nueva)
            auditoria_services.registrar_cambios(
                "cartel",
                instancia.pk,
                {"tarifa_lista": anterior},
                {"tarifa_lista": nuevo},
                self.request.user,
            )

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


class ImportacionCartelesView(APIView):
    """Importa carteles desde un CSV, o lo simula sin guardar (HU-015). Solo Administrador."""

    permission_classes = [permissions.IsAuthenticated, SoloAdministrador]
    parser_classes = [MultiPartParser]

    def post(self, request: Request) -> Response:
        archivo = request.FILES.get("archivo")
        if archivo is None:
            raise ValidationError({"archivo": "Elegí el archivo CSV a importar."})
        datos = cast(dict[str, Any], request.data)
        formato_id = str(datos.get("formato", ""))
        formato = (
            Formato.objects.filter(pk=int(formato_id)).first() if formato_id.isdecimal() else None
        )
        if formato is None:
            raise ValidationError({"formato": "Elegí un formato que exista."})
        simular = str(datos.get("simular", "")).casefold() in ("1", "true", "si")
        try:
            resultado = services.importar_carteles(
                archivo, formato, cast(AbstractBaseUser, request.user), simular=simular
            )
        except DjangoValidationError as error:
            raise ValidationError(error.message_dict) from error
        return Response(resultado.como_dict())
