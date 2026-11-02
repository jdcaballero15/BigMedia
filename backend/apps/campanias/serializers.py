from typing import Any, cast

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.clientes.models import Cliente
from apps.inventario.models import Formato

from . import services
from .models import Campania, Interaccion, LineaFormato


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


class LineaFormatoSerializer(serializers.ModelSerializer[LineaFormato]):
    formato_nombre = serializers.CharField(source="formato.nombre", read_only=True)

    class Meta:
        model = LineaFormato
        fields = [
            "id",
            "campania",
            "formato",
            "formato_nombre",
            "cantidad",
            "activa",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["creado_en", "actualizado_en"]
        # El formato repetido lo valida el servicio, con un mensaje claro (HU-055, criterio 3).
        validators: list[object] = []

    def update(self, instance: LineaFormato, validated_data: dict[str, Any]) -> LineaFormato:
        # La línea pertenece a su campaña: no se mueve a otra.
        validated_data.pop("campania", None)
        return super().update(instance, validated_data)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        actual = self.instance
        # En un alta, campaña y formato vienen en attrs; en una edición, de la instancia.
        campania: Campania = actual.campania if actual is not None else attrs["campania"]
        formato: Formato = (
            attrs["formato"] if "formato" in attrs else cast(LineaFormato, actual).formato
        )
        activa = attrs.get("activa", getattr(actual, "activa", True))
        formato_sin_cambios = actual is not None and actual.formato_id == formato.pk
        try:
            services.validar_linea_formato(campania, formato, activa, actual, formato_sin_cambios)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict) from error
        return attrs


class InteraccionSerializer(serializers.ModelSerializer[Interaccion]):
    cliente_nombre = serializers.CharField(source="cliente.nombre_visible", read_only=True)
    contacto_nombre = serializers.CharField(source="contacto.nombre", read_only=True, default=None)
    campania_nombre = serializers.SerializerMethodField()
    marca_nombre = serializers.CharField(source="marca.nombre", read_only=True, default=None)
    registrada_por_nombre = serializers.CharField(
        source="registrada_por.username", read_only=True, default=None
    )

    class Meta:
        model = Interaccion
        fields = [
            "id",
            "tipo",
            "asunto",
            "fecha",
            "notas",
            "cliente",
            "cliente_nombre",
            "contacto",
            "contacto_nombre",
            "campania",
            "campania_nombre",
            "marca",
            "marca_nombre",
            "registrada_por_nombre",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["creado_en", "actualizado_en"]

    def get_campania_nombre(self, interaccion: Interaccion) -> str | None:
        return str(interaccion.campania) if interaccion.campania is not None else None

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        actual = self.instance
        # El cliente es obligatorio: en un alta viene en attrs; en una edición, de la instancia.
        cliente: Cliente = (
            attrs["cliente"] if "cliente" in attrs else cast(Interaccion, actual).cliente
        )
        contacto = attrs.get("contacto", getattr(actual, "contacto", None))
        campania = attrs.get("campania", getattr(actual, "campania", None))
        marca = attrs.get("marca", getattr(actual, "marca", None))
        if (actual is None or actual.cliente_id != cliente.pk) and not cliente.activo:
            raise serializers.ValidationError({"cliente": "Seleccioná un cliente activo."})
        contacto_sin_cambios = (
            self.instance is not None
            and contacto is not None
            and self.instance.contacto_id == contacto.pk
        )
        try:
            services.validar_contacto_de_interaccion(cliente, contacto, contacto_sin_cambios)
            services.validar_campania_de_interaccion(cliente, campania)
            services.validar_marca_de_interaccion(
                cliente, marca, campania, actual is not None and actual.marca == marca
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict) from error
        return attrs
