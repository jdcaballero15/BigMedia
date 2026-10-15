from rest_framework import serializers

from .models import EstadoCartel, Formato, Proveedor, Zona


class CatalogoSerializer(serializers.ModelSerializer):
    def validate_nombre(self, value):
        nombre = value.strip()
        if not nombre:
            raise serializers.ValidationError("Ingresá un nombre.")
        matches = self.Meta.model.objects.filter(nombre__iexact=nombre)
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
        fields = ["id", "nombre", "modalidad", "capacidad_predeterminada", "ancho", "alto", "activo"]

    def validate_capacidad_predeterminada(self, value):
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
