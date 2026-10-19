from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from . import services
from .models import Cliente, Marca, Rubro
from .validators import normalizar_cuit, validar_cuit

NOMBRE_OBLIGATORIO = "Ingresá un nombre."


def _errores_de_nombre() -> dict[str, str]:
    return {"required": NOMBRE_OBLIGATORIO, "blank": NOMBRE_OBLIGATORIO}


class RubroSerializer(serializers.ModelSerializer[Rubro]):
    class Meta:
        model = Rubro
        fields = ["id", "nombre", "activo"]
        extra_kwargs = {"nombre": {"error_messages": _errores_de_nombre()}}

    def validate_nombre(self, value: str) -> str:
        nombre = value.strip()
        coincidencias = Rubro.objects.filter(nombre__iexact=nombre)
        if self.instance is not None:
            coincidencias = coincidencias.exclude(pk=self.instance.pk)
        if coincidencias.exists():
            raise serializers.ValidationError("Ya existe un rubro con ese nombre.")
        return nombre


class ClienteSerializer(serializers.ModelSerializer[Cliente]):
    cuit = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="11 dígitos, con o sin guiones. Se devuelve sin guiones.",
    )
    tipo_nombre = serializers.CharField(source="get_tipo_display", read_only=True)
    nombre_visible = serializers.CharField(read_only=True)

    class Meta:
        model = Cliente
        fields = [
            "id",
            "nombre",
            "razon_social",
            "cuit",
            "tipo",
            "tipo_nombre",
            "nombre_visible",
            "telefono",
            "correo",
            "activo",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["creado_en", "actualizado_en"]
        extra_kwargs = {
            "tipo": {"error_messages": {"invalid_choice": "Elegí un tipo de cliente válido."}},
            "correo": {"error_messages": {"invalid": "Ingresá un correo válido."}},
        }

    def validate_cuit(self, value: str) -> str:
        if not value.strip():
            return ""
        try:
            cuit = normalizar_cuit(value)
            validar_cuit(cuit)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        repetidos = Cliente.objects.filter(cuit=cuit)
        if self.instance is not None:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise serializers.ValidationError("Ya existe un cliente con ese CUIT.")
        return cuit

    def create(self, validated_data: dict[str, Any]) -> Cliente:
        return services.crear_cliente(**validated_data)


class MarcaSerializer(serializers.ModelSerializer[Marca]):
    cliente_nombre = serializers.CharField(source="cliente.nombre_visible", read_only=True)
    rubro_nombre = serializers.CharField(source="rubro.nombre", read_only=True, default=None)

    class Meta:
        model = Marca
        fields = [
            "id",
            "nombre",
            "cliente",
            "cliente_nombre",
            "rubro",
            "rubro_nombre",
            "activo",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["creado_en", "actualizado_en"]
        extra_kwargs = {
            "nombre": {"error_messages": _errores_de_nombre()},
            "cliente": {
                "error_messages": {
                    "required": "Seleccioná un cliente.",
                    "null": "Seleccioná un cliente.",
                    "does_not_exist": "El cliente elegido no existe.",
                    "incorrect_type": "Seleccioná un cliente.",
                }
            },
            "rubro": {
                "required": False,
                "error_messages": {
                    "does_not_exist": "El rubro elegido no existe.",
                    "incorrect_type": "Seleccioná un rubro.",
                },
            },
        }

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        mensajes = {
            "cliente": "Seleccioná un cliente activo.",
            "rubro": "Seleccioná un rubro activo.",
        }
        for campo, mensaje in mensajes.items():
            valor = attrs.get(campo)
            sin_cambios = (
                self.instance is not None
                and valor is not None
                and getattr(self.instance, f"{campo}_id") == valor.pk
            )
            if valor is not None and not valor.activo and not sin_cambios:
                raise serializers.ValidationError({campo: mensaje})
        return attrs
