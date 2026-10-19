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

    class Meta:
        model = Costo
        fields = [
            "id",
            "reserva",
            "tipo",
            "tipo_nombre",
            "proveedor",
            "proveedor_nombre",
            "monto",
            "fecha",
            "anulado",
            "motivo_anulacion",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["creado_en", "actualizado_en"]
        extra_kwargs = {
            "fecha": {"required": False},
            "monto": {"min_value": Decimal("0.01")},
        }

    def create(self, validated_data: dict[str, Any]) -> Costo:
        validated_data.setdefault("fecha", timezone.localdate())
        return super().create(validated_data)
