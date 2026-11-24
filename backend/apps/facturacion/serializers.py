from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.clientes.validators import normalizar_cuit, validar_cuit
from apps.costos.models import Costo

from . import services
from .models import (
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
    cliente_razon_social = serializers.SerializerMethodField()
    costo_total = serializers.SerializerMethodField()
    neto_final = serializers.SerializerMethodField()
    costos_calculados = serializers.SerializerMethodField()
    costos_elegidos = serializers.SerializerMethodField()
    # Se guardan con el ítem, en la misma transacción (HU-062, HU-063): la lista completa de
    # costos elegidos (JSON, también en multipart) y el PDF de la orden de publicidad.
    costos = serializers.JSONField(write_only=True, required=False)
    orden_publicidad = serializers.FileField(write_only=True, required=False)
    # Se acepta con o sin guiones y se guardan los 11 dígitos (como en clientes).
    cuit_facturacion = serializers.CharField(max_length=13, allow_blank=True, required=False)

    class Meta:
        model = ItemFacturacion
        fields = [
            "id",
            "mes",
            "cliente",
            "cliente_nombre",
            "cliente_razon_social",
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
            "costo_total",
            "neto_final",
            "tipo_servicio",
            "tipo_soporte",
            "sector",
            "sector_nombre",
            "tipo_venta",
            "tipo_venta_nombre",
            "costos_incluidos",
            "detalle_costo",
            "costos_calculados",
            "costos_elegidos",
            "costos",
            "orden_publicidad",
            "notas",
            "orden_compra_numero",
            "orden_compra_fecha",
            "orden_compra_pdf",
            "grupo",
            "grupo_codigo",
            "creado_por_nombre",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["iva", "total", "grupo", "creado_en", "actualizado_en"]

    def to_representation(self, instance: ItemFacturacion) -> dict[str, Any]:
        datos = super().to_representation(instance)
        # Con costos elegidos se muestran los calculados (HU-060).
        incluidos = services.costos_incluidos_del_item(instance)
        datos["costos_incluidos"] = f"{incluidos:.2f}" if incluidos is not None else None
        datos["detalle_costo"] = services.detalle_costo_del_item(instance)
        return datos

    def get_costos_calculados(self, item: ItemFacturacion) -> bool:
        return services.costos_calculados(item)

    def get_costos_elegidos(self, item: ItemFacturacion) -> list[dict[str, Any]]:
        costos = CostoElegibleSerializer(services.costos_elegidos(item), many=True)
        return list(costos.data)

    def validate_costos(self, value: object) -> list[int]:
        if not isinstance(value, list) or not all(
            isinstance(costo, int) and not isinstance(costo, bool) and costo > 0 for costo in value
        ):
            raise serializers.ValidationError("Indicá los costos como una lista de números.")
        return value

    def validate_orden_publicidad(self, value: Any) -> Any:
        try:
            return services.validar_pdf(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict["archivo"]) from error

    def get_orden_compra_pdf(self, item: ItemFacturacion) -> dict[str, Any] | None:
        """Nombre y tamaño del PDF de la OC, sin el contenido (HU-062)."""
        try:
            pdf = item.orden_compra_pdf
        except OrdenCompraPdf.DoesNotExist:
            return None
        return {"nombre": pdf.nombre, "tamanio": pdf.tamanio}

    def get_cliente_razon_social(self, item: ItemFacturacion) -> str | None:
        return services.cliente_razon_social(item)

    def get_costo_total(self, item: ItemFacturacion) -> str:
        return f"{services.costo_total(item):.2f}"

    def get_neto_final(self, item: ItemFacturacion) -> str | None:
        valor = services.neto_final(item)
        return f"{valor:.2f}" if valor is not None else None

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
        self._completar_neto(attrs)
        if self._tendra_costos_elegidos(attrs.get("costos")):
            # Calculados: lo escrito a mano queda guardado para cuando no haya costos (HU-060).
            attrs.pop("costos_incluidos", None)
            attrs.pop("detalle_costo", None)
        return attrs

    def _tendra_costos_elegidos(self, pedidos: list[int] | None) -> bool:
        if pedidos:
            return True
        if self.instance is None:
            return False
        actuales = services.costos_elegidos(self.instance)
        if pedidos is None:
            return any(not costo.anulado for costo in actuales)
        # Los propios del ítem no se quitan al elegir (HU-063).
        return any(not costo.anulado and costo.reserva_id is None for costo in actuales)

    def _separar_extras(self, validated_data: dict[str, Any]) -> None:
        self.costos_pedidos: list[int] | None = validated_data.pop("costos", None)
        self.pdf_orden_publicidad: Any = validated_data.pop("orden_publicidad", None)

    def create(self, validated_data: dict[str, Any]) -> ItemFacturacion:
        self._separar_extras(validated_data)
        return super().create(validated_data)

    def update(self, instance: ItemFacturacion, validated_data: dict[str, Any]) -> ItemFacturacion:
        self._separar_extras(validated_data)
        return super().update(instance, validated_data)

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


class GrupoFacturaSerializer(serializers.ModelSerializer[GrupoFactura]):
    mes = serializers.DateField(format="%Y-%m", read_only=True)
    items = serializers.SerializerMethodField()

    class Meta:
        model = GrupoFactura
        fields = ["id", "codigo", "mes", "items"]

    def get_items(self, grupo: GrupoFactura) -> list[int]:
        return sorted(item.pk for item in grupo.items.all())


class CostoDelItemSerializer(serializers.ModelSerializer[Costo]):
    """Costo de un ítem a facturar (HU-063): propio del ítem o de una reserva vinculada."""

    tipo_nombre = serializers.CharField(source="get_tipo_display", read_only=True)
    proveedor_nombre = serializers.CharField(
        source="proveedor.nombre", read_only=True, default=None
    )
    cartel_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Costo
        fields = [
            "id",
            "tipo",
            "tipo_nombre",
            "proveedor",
            "proveedor_nombre",
            "destinatario",
            "porcentaje",
            "monto",
            "fecha",
            "reserva",
            "cartel_nombre",
            "anulado",
            "motivo_anulacion",
        ]
        read_only_fields = fields

    def get_cartel_nombre(self, costo: Costo) -> str | None:
        return costo.reserva.cartel.nombre_visible if costo.reserva is not None else None


class NuevoCostoSerializer(serializers.Serializer[dict[str, Any]]):
    """Alta de un costo propio del ítem: monto fijo o porcentaje del neto (HU-063)."""

    tipo = serializers.ChoiceField(choices=Costo.Tipo.choices)
    proveedor = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    destinatario = serializers.CharField(max_length=200, required=False, allow_blank=True)
    monto = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0.01"),
        required=False,
        allow_null=True,
    )
    porcentaje = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.01"),
        max_value=Decimal("100"),
        required=False,
        allow_null=True,
    )


class CostoElegibleSerializer(serializers.ModelSerializer[Costo]):
    """Costo para elegir en un ítem o ya elegido (HU-063), con su campaña y su cartel."""

    tipo_nombre = serializers.CharField(source="get_tipo_display", read_only=True)
    a_quien = serializers.SerializerMethodField()
    campania_nombre = serializers.SerializerMethodField()
    cartel_nombre = serializers.SerializerMethodField()
    propio = serializers.SerializerMethodField()

    class Meta:
        model = Costo
        fields = [
            "id",
            "tipo",
            "tipo_nombre",
            "monto",
            "fecha",
            "anulado",
            "a_quien",
            "campania_nombre",
            "cartel_nombre",
            "propio",
        ]
        read_only_fields = fields

    def get_a_quien(self, costo: Costo) -> str:
        return costo.proveedor.nombre if costo.proveedor is not None else costo.destinatario

    def get_campania_nombre(self, costo: Costo) -> str | None:
        return str(costo.reserva.campania) if costo.reserva is not None else None

    def get_cartel_nombre(self, costo: Costo) -> str | None:
        return costo.reserva.cartel.nombre_visible if costo.reserva is not None else None

    def get_propio(self, costo: Costo) -> bool:
        return costo.reserva_id is None
