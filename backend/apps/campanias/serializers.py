from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from . import services
from .models import Campania


class CampaniaSerializer(serializers.ModelSerializer[Campania]):
    cliente_factura = serializers.SerializerMethodField()
    cliente_factura_nombre = serializers.SerializerMethodField()
    marca_nombre = serializers.CharField(source="marca.nombre", read_only=True, default=None)

    class Meta:
        model = Campania
        fields = [
            "id",
            "nombre",
            "marca",
            "marca_nombre",
            "cliente_facturacion",
            "cliente_factura",
            "cliente_factura_nombre",
            "fecha_inicio",
            "fecha_fin",
            "estado",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["creado_en", "actualizado_en"]

    def get_cliente_factura(self, campania: Campania) -> int | None:
        cliente = campania.cliente_factura
        return cliente.pk if cliente is not None else None

    def get_cliente_factura_nombre(self, campania: Campania) -> str:
        cliente = campania.cliente_factura
        return cliente.nombre_visible if cliente is not None else ""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        mensajes = {
            "marca": "Seleccioná una marca activa.",
            "cliente_facturacion": "Seleccioná un cliente activo.",
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
        if attrs.get("estado") == Campania.Estado.CONFIRMADA:
            futura = Campania(**{**self._estado_actual(), **attrs})
            try:
                services.validar_confirmacion(futura)
            except DjangoValidationError as error:
                raise serializers.ValidationError(error.message_dict) from error
        return attrs

    def _estado_actual(self) -> dict[str, Any]:
        if self.instance is None:
            return {}
        return {
            "marca": self.instance.marca,
            "cliente_facturacion": self.instance.cliente_facturacion,
            "fecha_inicio": self.instance.fecha_inicio,
            "fecha_fin": self.instance.fecha_fin,
        }
