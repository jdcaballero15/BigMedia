from django.contrib.auth.models import User
from rest_framework import serializers

from .services import ROLES, rol_de, tiene_gerencia

NOMBRE_OBLIGATORIO = "Ingresá un nombre."
CORREO_OBLIGATORIO = "Ingresá un correo."
ROL_INVALIDO = "Elegí un rol válido."


class UsuarioSerializer(serializers.ModelSerializer[User]):
    """Lectura de un usuario: rol derivado, casilla Gerencia y si ya definió su contraseña."""

    rol = serializers.SerializerMethodField()
    es_gerencia = serializers.SerializerMethodField()
    activo = serializers.BooleanField(source="is_active", read_only=True)
    tiene_clave = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "rol",
            "es_gerencia",
            "activo",
            "tiene_clave",
            "last_login",
        ]
        read_only_fields = fields

    def get_rol(self, user: User) -> str:
        return rol_de(user)

    def get_es_gerencia(self, user: User) -> bool:
        return tiene_gerencia(user)

    def get_tiene_clave(self, user: User) -> bool:
        return user.has_usable_password()


class UsuarioEdicionSerializer(serializers.Serializer[User]):
    """Lo que el administrador puede cambiar. El nombre de usuario no se edita."""

    first_name = serializers.CharField(
        max_length=150, error_messages={"blank": NOMBRE_OBLIGATORIO, "required": NOMBRE_OBLIGATORIO}
    )
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(
        error_messages={
            "blank": CORREO_OBLIGATORIO,
            "required": CORREO_OBLIGATORIO,
            "invalid": "Ingresá un correo válido.",
        }
    )
    rol = serializers.ChoiceField(
        choices=ROLES, error_messages={"invalid_choice": ROL_INVALIDO, "required": ROL_INVALIDO}
    )
    es_gerencia = serializers.BooleanField(required=False)
    activo = serializers.BooleanField(required=False)


class UsuarioAltaSerializer(UsuarioEdicionSerializer):
    username = serializers.RegexField(
        r"^[\w.@+-]+$",
        max_length=150,
        error_messages={
            "blank": "Ingresá un nombre de usuario.",
            "required": "Ingresá un nombre de usuario.",
            "invalid": "Usá solo letras, números y los signos . @ + - _",
        },
    )

    def validate_username(self, value: str) -> str:
        # El bloqueo por intentos no distingue mayúsculas: dos nombres así compartirían el contador.
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese nombre.")
        return value


class DefinirClaveSerializer(serializers.Serializer[None]):
    uid = serializers.CharField()
    token = serializers.CharField()
    clave = serializers.CharField(
        trim_whitespace=False, error_messages={"blank": "Ingresá una contraseña."}
    )
