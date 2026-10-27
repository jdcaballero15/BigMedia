from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.clientes.validators import normalizar_cuit, validar_cuit

from . import services
from .models import (
    EnvioFacturacion,
    GrupoFactura,
    ItemFacturacion,
    OrdenCompraPdf,
    Sector,
    TipoVenta,
    neto_sugerido,
)


class ItemFacturacionSerializer(serializers.ModelSerializer[ItemFacturacion]):
    cliente_nombre = serializers.CharField(
        source="cliente.nombre_visible", read_only=True, default=None
    )
    marca_nombre = serializers.CharField(source="marca.nombre", read_only=True, default=None)
    campania_nombre = serializers.SerializerMethodField()
    sector_nombre = serializers.CharField(source="sector.nombre", read_only=True, default=None)
    tipo_venta_nombre = serializers.CharField(
        source="tipo_venta.nombre", read_only=True, default=None
    )
    creado_por_nombre = serializers.CharField(
        source="creado_por.username", read_only=True, default=None
    )
    grupo_codigo = serializers.CharField(source="grupo.codigo", read_only=True, default=None)
    orden_compra_pdf = serializers.SerializerMethodField()
    # Se acepta con o sin guiones y se guardan los 11 dígitos (como en clientes).
    cuit_facturacion = serializers.CharField(max_length=13, allow_blank=True, required=False)

    class Meta:
        model = ItemFacturacion
        fields = [
            "id",
            "mes",
            "cliente",
            "cliente_nombre",
            "cuit_facturacion",
            "marca",
            "marca_nombre",
            "campania",
            "campania_nombre",
            "descripcion",
            "periodo_desde",
            "periodo_hasta",
            "cantidad",
            "precio_unitario",
            "neto",
            "alicuota_iva",
            "iva",
            "total",
            "tipo_servicio",
            "tipo_soporte",
            "sector",
            "sector_nombre",
            "tipo_venta",
            "tipo_venta_nombre",
            "notas",
            "orden_compra_numero",
            "orden_compra_fecha",
            "orden_compra_pdf",
            "grupo",
            "grupo_codigo",
            "estado",
            "numero_factura",
            "creado_por_nombre",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["iva", "total", "grupo", "creado_en", "actualizado_en"]

    def get_orden_compra_pdf(self, item: ItemFacturacion) -> dict[str, Any] | None:
        """Nombre y tamaño del PDF de la OC, sin el contenido (HU-062)."""
        try:
            pdf = item.orden_compra_pdf
        except OrdenCompraPdf.DoesNotExist:
            return None
        return {"nombre": pdf.nombre, "tamanio": pdf.tamanio}

    def get_campania_nombre(self, item: ItemFacturacion) -> str | None:
        return str(item.campania) if item.campania is not None else None

    def validate_cuit_facturacion(self, value: str) -> str:
        if not value.strip():
            return ""
        try:
            cuit = normalizar_cuit(value)
            validar_cuit(cuit)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return cuit

    def validate_numero_factura(self, value: str) -> str:
        return value.strip()

    def validate_orden_compra_numero(self, value: str) -> str:
        return value.strip()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        self._validar_catalogos_activos(attrs)
        desde = attrs.get("periodo_desde", getattr(self.instance, "periodo_desde", None))
        hasta = attrs.get("periodo_hasta", getattr(self.instance, "periodo_hasta", None))
        if desde and hasta and hasta < desde:
            raise serializers.ValidationError(
                {"periodo_hasta": "El fin del período no puede ser anterior al inicio."}
            )
        try:
            services.validar_cambio_de_item(self.instance, attrs)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict) from error
        self._completar_neto(attrs)
        return attrs

    def _validar_catalogos_activos(self, attrs: dict[str, Any]) -> None:
        for campo in ("sector", "tipo_venta"):
            valor: Sector | TipoVenta | None = attrs.get(campo)
            sin_cambios = valor is not None and getattr(self.instance, f"{campo}_id", None) == (
                valor.pk
            )
            if valor is not None and not valor.activo and not sin_cambios:
                raise serializers.ValidationError({campo: "Elegí una opción activa."})

    def _completar_neto(self, attrs: dict[str, Any]) -> None:
        """Neto = cantidad por precio si no viene a mano y cambió alguno de los dos (HU-061)."""
        if attrs.get("neto") is not None:
            return
        cambia_base = "cantidad" in attrs or "precio_unitario" in attrs
        if not cambia_base and self.instance is not None:
            return
        cantidad = attrs.get("cantidad", getattr(self.instance, "cantidad", None))
        precio = attrs.get("precio_unitario", getattr(self.instance, "precio_unitario", None))
        sugerido = neto_sugerido(cantidad, precio)
        if sugerido is not None or "neto" in attrs:
            attrs["neto"] = sugerido


class EnvioFacturacionSerializer(serializers.ModelSerializer[EnvioFacturacion]):
    mes = serializers.DateField(format="%Y-%m", read_only=True)
    enviado_por_nombre = serializers.CharField(source="enviado_por.username", read_only=True)
    items = serializers.SerializerMethodField()
    cantidad = serializers.SerializerMethodField()

    class Meta:
        model = EnvioFacturacion
        fields = ["id", "mes", "enviado_por_nombre", "enviado_en", "items", "cantidad"]

    def get_items(self, envio: EnvioFacturacion) -> list[int]:
        return sorted(item.pk for item in envio.items.all())

    def get_cantidad(self, envio: EnvioFacturacion) -> int:
        return len(envio.items.all())


class GrupoFacturaSerializer(serializers.ModelSerializer[GrupoFactura]):
    mes = serializers.DateField(format="%Y-%m", read_only=True)
    items = serializers.SerializerMethodField()

    class Meta:
        model = GrupoFactura
        fields = ["id", "codigo", "mes", "items"]

    def get_items(self, grupo: GrupoFactura) -> list[int]:
        return sorted(item.pk for item in grupo.items.all())
