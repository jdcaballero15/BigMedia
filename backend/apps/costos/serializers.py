from decimal import Decimal
from typing import Any

from django.utils import timezone
from rest_framework import serializers

from .models import Costo


class CostoSerializer(serializers.ModelSerializer[Costo]):
    tipo_nombre = serializers.CharField(source="get_tipo_display", read_only=True)
    proveedor_nombre = serializers.CharField(
        source="proveedor.nombre", read_only=True, default=None
    )
    cartel_nombre = serializers.CharField(source="reserva.cartel.nombre_visible", read_only=True)
    campania = serializers.IntegerField(source="reserva.campania_id", read_only=True)
    campania_nombre = serializers.CharField(source="reserva.campania", read_only=True)

    class Meta:
        model = Costo
        fields = [
            "id",
            "reserva",
            "tipo",
            "tipo_nombre",
            "proveedor",
            "proveedor_nombre",
            "destinatario",
            "cartel_nombre",
            "campania",
            "campania_nombre",
            "porcentaje",
            "monto",
            "fecha",
            "anulado",
            "motivo_anulacion",
            "creado_en",
            "actualizado_en",
        ]
        # Los porcentuales son solo de ítems a facturar (HU-063): acá no se cargan.
        read_only_fields = ["porcentaje", "creado_en", "actualizado_en"]
        extra_kwargs = {
            # La reserva pasó a opcional en el modelo por los costos de ítems; acá sigue exigida.
            "reserva": {"required": True, "allow_null": False},
            "fecha": {"required": False},
            "monto": {"min_value": Decimal("0.01")},
        }

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        proveedor = attrs.get("proveedor")
        sin_cambios = (
            self.instance is not None
            and proveedor is not None
            and self.instance.proveedor_id == proveedor.pk
        )
        if proveedor is not None and not proveedor.activo and not sin_cambios:
            raise serializers.ValidationError({"proveedor": "Seleccioná un proveedor activo."})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Costo:
        validated_data.setdefault("fecha", timezone.localdate())
        return super().create(validated_data)
