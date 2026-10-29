from typing import Any, cast

from rest_framework import serializers

from .models import Cartel, Catalogo, EstadoCartel, Formato, Proveedor, Zona


class CatalogoSerializer(serializers.ModelSerializer[Catalogo]):
    def validate_nombre(self, value: str) -> str:
        nombre = value.strip()
        if not nombre:
            raise serializers.ValidationError("Ingresá un nombre.")
        model = cast(type[Catalogo], self.Meta.model)
        matches = model._default_manager.filter(nombre__iexact=nombre)
        if self.instance:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise serializers.ValidationError("Ya existe un registro con ese nombre.")
        return nombre


class ProveedorSerializer(CatalogoSerializer):
    class Meta:
        model = Proveedor
        fields = ["id", "nombre", "servicio", "activo"]


class FormatoSerializer(CatalogoSerializer):
    class Meta:
        model = Formato
        fields = [
            "id",
            "nombre",
            "modalidad",
            "capacidad_predeterminada",
            "ancho",
            "alto",
            "activo",
        ]

    def validate_capacidad_predeterminada(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("La capacidad debe ser mayor o igual a 1.")
        return value


class ZonaSerializer(CatalogoSerializer):
    class Meta:
        model = Zona
        fields = ["id", "nombre", "activo"]


class EstadoCartelSerializer(CatalogoSerializer):
    class Meta:
        model = EstadoCartel
        fields = ["id", "codigo", "nombre", "operativo", "es_baja", "activo"]
        read_only_fields = ["codigo"]


class CartelSerializer(serializers.ModelSerializer[Cartel]):
    nombre_visible = serializers.CharField(read_only=True)
    formato_nombre = serializers.CharField(source="formato.nombre", read_only=True)
    zona_nombre = serializers.CharField(source="zona.nombre", read_only=True)
    proveedor_nombre = serializers.CharField(source="proveedor.nombre", read_only=True)
    estado_nombre = serializers.CharField(source="estado.nombre", read_only=True)
    es_baja = serializers.BooleanField(source="estado.es_baja", read_only=True)
    operativo = serializers.BooleanField(source="estado.operativo", read_only=True)

    class Meta:
        model = Cartel
        fields = [
            "id",
            "formato",
            "formato_nombre",
            "zona",
            "zona_nombre",
            "proveedor",
            "proveedor_nombre",
            "estado",
            "estado_nombre",
            "operativo",
            "es_baja",
            "direccion",
            "tamano",
            "capacidad",
            "tarifa_lista",
            "foto_url",
            "nombre_visible",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["creado_en", "actualizado_en"]
        extra_kwargs = {
            "capacidad": {"required": False, "min_value": 1},
            "estado": {"required": False},
            "tarifa_lista": {"required": False, "allow_null": True, "min_value": 0},
        }

    def validate_direccion(self, value: str) -> str:
        direccion = value.strip()
        if not direccion:
            raise serializers.ValidationError("Ingresá una dirección.")
        return direccion

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        for field in ("formato", "zona", "proveedor", "estado"):
            value = attrs.get(field)
            unchanged = (
                self.instance is not None
                and value is not None
                and getattr(self.instance, f"{field}_id") == value.pk
            )
            if value is not None and not value.activo and not unchanged:
                raise serializers.ValidationError({field: "Seleccioná una opción activa."})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Cartel:
        if "capacidad" not in validated_data:
            validated_data["capacidad"] = validated_data["formato"].capacidad_predeterminada
        if "estado" not in validated_data:
            estado = EstadoCartel.objects.filter(codigo="activo", activo=True).first()
            if estado is None:
                raise serializers.ValidationError({"estado": "Seleccioná un estado activo."})
            validated_data["estado"] = estado
        return super().create(validated_data)
