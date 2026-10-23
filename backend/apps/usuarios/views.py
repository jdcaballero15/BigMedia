from typing import cast

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import QuerySet
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from config.permisos import SoloAdministrador

from . import services
from .serializers import (
    DefinirClaveSerializer,
    UsuarioAltaSerializer,
    UsuarioEdicionSerializer,
    UsuarioSerializer,
)


def _respuesta_de_error(error: DjangoValidationError) -> Response:
    """Un error de campo va por campo; uno general (último administrador), como `detail`."""
    if hasattr(error, "error_dict"):
        raise ValidationError(error.message_dict) from error
    return Response({"detail": " ".join(error.messages)}, status=status.HTTP_400_BAD_REQUEST)


class UsuarioViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet[User],
):
    """Gestión de usuarios (HU-005): solo el administrador, y sin DELETE (se inactiva)."""

    permission_classes = [permissions.IsAuthenticated, SoloAdministrador]
    http_method_names = ["get", "post", "patch", "head", "options"]
    serializer_class = UsuarioSerializer

    def get_queryset(self) -> QuerySet[User]:
        return User.objects.prefetch_related("groups").order_by("username")

    def create(self, request: Request) -> Response:
        entrada = UsuarioAltaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        validos = dict(entrada.validated_data)
        username = str(validos.pop("username"))
        user = services.crear_usuario(username, cast(services.DatosUsuario, validos), request.user)
        return Response(UsuarioSerializer(user).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request: Request, **_kwargs: object) -> Response:
        user = self.get_object()
        entrada = UsuarioEdicionSerializer(data=request.data, partial=True)
        entrada.is_valid(raise_exception=True)
        datos = cast(services.DatosUsuario, entrada.validated_data)
        try:
            user = services.actualizar_usuario(user.pk, datos, request.user)
        except DjangoValidationError as error:
            return _respuesta_de_error(error)
        return Response(UsuarioSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="link-clave")
    def link_clave(self, request: Request, **_kwargs: object) -> Response:
        """Link de un solo uso para definir o restablecer la contraseña; se manda a mano."""
        user = self.get_object()
        codigo = services.generar_codigo_clave(user.pk)
        link = request.build_absolute_uri(f"/?definir-clave={codigo}")
        return Response({"link": link})


class DefinirClaveView(APIView):
    """Público: lo usa quien recibió el link, que todavía no tiene sesión."""

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        entrada = DefinirClaveSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        try:
            services.definir_clave(datos["uid"], datos["token"], datos["clave"])
        except DjangoValidationError as error:
            return _respuesta_de_error(error)
        return Response({"status": "ok"})
