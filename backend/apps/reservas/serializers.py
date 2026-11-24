from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.campanias.models import Campania

from . import services
from .models import ParametrosDisponibilidad, Reserva


class ReservaSerializer(serializers.ModelSerializer[Reserva]):
    nombre = serializers.CharField(read_only=True)
    total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    cartel_nombre = serializers.CharField(source="cartel.nombre_visible", read_only=True)
    campania_nombre = serializers.SerializerMethodField()
    estado_visible = serializers.SerializerMethodField()

    class Meta:
        model = Reserva
        fields = [
            "id",
            "campania",
            "campania_nombre",
            "cartel",
            "cartel_nombre",
            "fecha_inicio",
            "fecha_fin",
            "estado",
            "estado_visible",
            "precio_alquiler",
            "precio_impresion",
            "precio_fijacion",
            "total",
            "nombre",
            "creado_en",
            "actualizado_en",
        ]
        # El estado lo lleva el sistema (HU-035): nace Confirmada y cambia con "Quitar" o al
        # cancelar la campaña.
        read_only_fields = ["estado", "creado_en", "actualizado_en"]
        extra_kwargs = {
            "precio_alquiler": {"required": False, "min_value": Decimal("0")},
            "precio_impresion": {"required": False, "min_value": Decimal("0")},
            "precio_fijacion": {"required": False, "min_value": Decimal("0")},
        }

    def get_campania_nombre(self, reserva: Reserva) -> str:
        return str(reserva.campania)

    def get_estado_visible(self, reserva: Reserva) -> str:
        return services.estado_visible(reserva)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        inicio = attrs.get("fecha_inicio") or getattr(self.instance, "fecha_inicio", None)
        fin = attrs.get("fecha_fin") or getattr(self.instance, "fecha_fin", None)
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError(
                {"fecha_fin": "La fecha de fin no puede ser anterior a la de inicio."}
            )

        cartel = attrs.get("cartel")
        sin_cambios = (
            self.instance is not None
            and cartel is not None
            and self.instance.cartel_id == cartel.pk
        )
        cambia_fin = "fecha_fin" in attrs and (
            self.instance is None or attrs["fecha_fin"] != self.instance.fecha_fin
        )
        try:
            if cambia_fin:
                services.validar_fecha_no_pasada(attrs["fecha_fin"])
            if cartel is not None and not sin_cambios:
                services.validar_cartel_reservable(cartel)
            if self.instance is None and attrs.get("campania") is not None:
                services.validar_campania_admite_reservas(attrs["campania"])
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict) from error
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Reserva:
        if "precio_alquiler" not in validated_data:
            tarifa = validated_data["cartel"].tarifa_lista
            validated_data["precio_alquiler"] = tarifa if tarifa is not None else Decimal("0.00")
        return super().create(validated_data)


class ReservasEnBloqueSerializer(serializers.Serializer[dict[str, Any]]):
    """Pedido de creación en bloque (HU-057): la pantalla lo manda por lotes."""

    MAX_CARTELES = 50

    campania = serializers.PrimaryKeyRelatedField(queryset=Campania.objects.all())
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    carteles = serializers.ListField(
        child=serializers.IntegerField(min_value=1), min_length=1, max_length=MAX_CARTELES
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["fecha_fin"] < attrs["fecha_inicio"]:
            raise serializers.ValidationError(
                {"fecha_fin": "La fecha de fin no puede ser anterior a la de inicio."}
            )
        try:
            services.validar_fecha_no_pasada(attrs["fecha_fin"])
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict) from error
        return attrs


class CampaniaDeReservasSerializer(serializers.Serializer[dict[str, Any]]):
    """Pedido de cancelar una campaña con sus reservas (HU-024)."""

    campania = serializers.PrimaryKeyRelatedField(queryset=Campania.objects.all())


class ParametrosDisponibilidadSerializer(serializers.ModelSerializer[ParametrosDisponibilidad]):
    class Meta:
        model = ParametrosDisponibilidad
        fields = ["borde_inclusivo", "permitir_fecha_pasada"]
