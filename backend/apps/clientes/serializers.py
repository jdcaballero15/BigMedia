from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from . import services
from .models import Cliente, Marca, Rubro
from .validators import normalizar_cuit, validar_cuit

NOMBRE_OBLIGATORIO = "Ingresá un nombre."


def _errores_de_nombre() -> dict[str, str]:
    return {"required": NOMBRE_OBLIGATORIO, "blank": NOMBRE_OBLIGATORIO}


def _campo_confirmar_distinta() -> serializers.BooleanField:
    return serializers.BooleanField(
        write_only=True,
        required=False,
        default=False,
        help_text="Confirma que no es la marca del aviso `posible_duplicado` (HU-019).",
    )


def _avisar_duplicados(nombre: str, excluir: int | None = None) -> None:
    """Rechaza con `posible_duplicado` si hay marcas con un nombre igual o parecido (HU-019)."""
    coincidentes = services.posibles_duplicados(nombre, excluir)
    if coincidentes:
        raise serializers.ValidationError(
            {"posible_duplicado": [services.describir_duplicado(m) for m in coincidentes]}
        )


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
    confirmar_distinta = _campo_confirmar_distinta()

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
            "confirmar_distinta",
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

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        confirmada = attrs.pop("confirmar_distinta", False)
        # Solo el alta de un cliente directo crea su marca homónima (HU-018).
        crea_marca = self.instance is None and attrs.get("tipo") == Cliente.Tipo.DIRECTO
        if crea_marca and not confirmada:
            _avisar_duplicados(attrs.get("nombre", ""))
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Cliente:
        return services.crear_cliente(**validated_data)


class MarcaSerializer(serializers.ModelSerializer[Marca]):
    cliente_nombre = serializers.CharField(source="cliente.nombre_visible", read_only=True)
    rubro_nombre = serializers.CharField(source="rubro.nombre", read_only=True, default=None)
    confirmar_distinta = _campo_confirmar_distinta()

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
            "confirmar_distinta",
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
        confirmada = attrs.pop("confirmar_distinta", False)
        nombre = attrs.get("nombre")
        if nombre is None or confirmada:
            return attrs
        # Se avisa en el alta y al cambiar el nombre, sin comparar la marca consigo misma.
        if self.instance is None:
            _avisar_duplicados(nombre)
        elif nombre != self.instance.nombre:
            _avisar_duplicados(nombre, self.instance.pk)
        return attrs
