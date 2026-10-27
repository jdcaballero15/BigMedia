from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca
from apps.clientes.validators import validar_cuit
from apps.costos.models import Costo

ALICUOTA_IVA_POR_DEFECTO = Decimal("21.00")
CENTAVO = Decimal("0.01")


def al_centavo(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def neto_sugerido(cantidad: Decimal | None, precio_unitario: Decimal | None) -> Decimal | None:
    """Cantidad por precio unitario (HU-061), o None si falta alguno de los dos."""
    if cantidad is None or precio_unitario is None:
        return None
    return al_centavo(cantidad * precio_unitario)


def iva_y_total(neto: Decimal | None, alicuota: Decimal) -> tuple[Decimal | None, Decimal | None]:
    """IVA y total desde el neto y la alícuota en porcentaje, redondeados al centavo (HU-061)."""
    if neto is None:
        return None, None
    iva = al_centavo(neto * alicuota / Decimal(100))
    return iva, al_centavo(neto) + iva


def primer_dia_del_mes_actual() -> date:
    hoy = timezone.localdate()
    return hoy.replace(day=1)


class CatalogoFacturacion(models.Model):
    """Lista administrable desde el admin (RN-023): Gob/Priv y tipo de venta F/V."""

    nombre = models.CharField(max_length=80)
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre


class Sector(CatalogoFacturacion):
    class Meta(CatalogoFacturacion.Meta):
        verbose_name_plural = "sectores"
        constraints = [models.UniqueConstraint(Lower("nombre"), name="sector_nombre_ci")]


class TipoVenta(CatalogoFacturacion):
    class Meta(CatalogoFacturacion.Meta):
        verbose_name = "tipo de venta"
        verbose_name_plural = "tipos de venta"
        constraints = [models.UniqueConstraint(Lower("nombre"), name="tipo_venta_nombre_ci")]


class GrupoFactura(models.Model):
    """Ítems que van en una misma factura (HU-064). Todos del mismo mes."""

    mes = models.DateField()
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="grupos_factura",
        null=True,
        editable=False,
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en", "-id"]
        verbose_name = "grupo de factura"
        verbose_name_plural = "grupos de factura"

    def __str__(self) -> str:
        return self.codigo

    @property
    def codigo(self) -> str:
        return f"G-{self.pk}"


class ItemFacturacion(models.Model):
    """Ítem a facturar del mes (HU-060). Nada es obligatorio hasta enviarlo (HU-066).

    El IVA y el total se calculan siempre desde el neto y la alícuota (HU-061). No se borra:
    se anula por estado (HU-065).
    """

    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        ENVIADO = "enviado", "Enviado a facturar"
        FACTURADO = "facturado", "Facturado"
        ANULADO = "anulado", "Anulado"

    class TipoServicio(models.TextChoices):
        ALQUILER = "alquiler", "Alquiler"
        IMPRESION_COLOCACION = "impresion_colocacion", "Impresión y colocación"
        OTRO = "otro", "Otro"

    mes = models.DateField(null=True, blank=True, default=primer_dia_del_mes_actual)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name="items_facturacion", null=True, blank=True
    )
    cuit_facturacion = models.CharField(
        "CUIT de facturación", max_length=11, blank=True, validators=[validar_cuit]
    )
    marca = models.ForeignKey(
        Marca, on_delete=models.PROTECT, related_name="items_facturacion", null=True, blank=True
    )
    campania = models.ForeignKey(
        Campania, on_delete=models.PROTECT, related_name="items_facturacion", null=True, blank=True
    )
    descripcion = models.TextField(blank=True)
    periodo_desde = models.DateField(null=True, blank=True)
    periodo_hasta = models.DateField(null=True, blank=True)
    cantidad = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    precio_unitario = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    neto = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    alicuota_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=ALICUOTA_IVA_POR_DEFECTO,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    iva = models.DecimalField(max_digits=14, decimal_places=2, null=True, editable=False)
    total = models.DecimalField(max_digits=14, decimal_places=2, null=True, editable=False)
    tipo_servicio = models.CharField(max_length=24, choices=TipoServicio.choices, blank=True)
    tipo_soporte = models.CharField(max_length=200, blank=True)
    sector = models.ForeignKey(
        Sector, on_delete=models.PROTECT, related_name="items", null=True, blank=True
    )
    tipo_venta = models.ForeignKey(
        TipoVenta, on_delete=models.PROTECT, related_name="items", null=True, blank=True
    )
    notas = models.TextField(blank=True)
    orden_compra_numero = models.CharField("número de orden de compra", max_length=50, blank=True)
    orden_compra_fecha = models.DateField("fecha de aprobación de la OC", null=True, blank=True)
    grupo = models.ForeignKey(
        GrupoFactura,
        on_delete=models.PROTECT,
        related_name="items",
        null=True,
        blank=True,
        editable=False,
    )
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.BORRADOR)
    numero_factura = models.CharField(max_length=50, blank=True)
    # Reapertura de un ítem enviado (HU-067): quién, cuándo, por qué, y la planilla de ese momento
    # para avisar a Administración qué cambió al reenviarlo.
    reabierto_en = models.DateTimeField(null=True, blank=True, editable=False)
    reabierto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="items_facturacion_reabiertos",
        null=True,
        blank=True,
        editable=False,
    )
    motivo_reapertura = models.CharField(max_length=200, blank=True, editable=False)
    valores_al_reabrir = models.JSONField(default=dict, blank=True, editable=False)
    reenviado = models.BooleanField(default=False, editable=False)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="items_facturacion_creados",
        null=True,
        editable=False,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-mes", "-creado_en", "-id"]
        verbose_name = "ítem a facturar"
        verbose_name_plural = "ítems a facturar"
        constraints = [
            models.CheckConstraint(
                condition=(
                    (models.Q(neto__gte=0) | models.Q(neto__isnull=True))
                    & (models.Q(cantidad__gte=0) | models.Q(cantidad__isnull=True))
                    & (models.Q(precio_unitario__gte=0) | models.Q(precio_unitario__isnull=True))
                ),
                name="item_facturacion_importes_no_negativos",
            ),
            models.CheckConstraint(
                condition=models.Q(alicuota_iva__gte=0) & models.Q(alicuota_iva__lte=100),
                name="item_facturacion_alicuota_valida",
            ),
            models.CheckConstraint(
                condition=models.Q(periodo_hasta__gte=models.F("periodo_desde"))
                | models.Q(periodo_desde__isnull=True)
                | models.Q(periodo_hasta__isnull=True),
                name="item_facturacion_periodo_coherente",
            ),
            models.CheckConstraint(
                condition=~models.Q(estado="facturado", numero_factura=""),
                name="item_facturacion_facturado_con_numero",
            ),
        ]

    def __str__(self) -> str:
        mes = self.mes.strftime("%Y-%m") if self.mes else "Sin mes"
        return f"{mes} · {self.descripcion or 'Sin descripción'}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.mes is not None:
            self.mes = self.mes.replace(day=1)
        self.iva, self.total = iva_y_total(self.neto, self.alicuota_iva)
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {"mes", "iva", "total"}
        super().save(*args, **kwargs)


class OrdenCompraPdf(models.Model):
    """PDF de la orden de compra del ítem (HU-062), guardado en la base (ADR-0009).

    Va aparte del ítem para no traer el archivo cada vez que se listan ítems.
    """

    item = models.OneToOneField(
        ItemFacturacion, on_delete=models.PROTECT, related_name="orden_compra_pdf"
    )
    nombre = models.CharField(max_length=255)
    tamanio = models.PositiveIntegerField()
    contenido = models.BinaryField()
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ordenes_compra_pdf"
    )
    subido_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "PDF de orden de compra"
        verbose_name_plural = "PDF de órdenes de compra"

    def __str__(self) -> str:
        return self.nombre


class CostoDeItem(models.Model):
    """Une un ítem a facturar con sus costos (HU-063). Un costo va en un solo ítem.

    Vive en `facturacion` porque `costos` no puede importar de esta app. El costo es propio del
    ítem (sin reserva) o uno de una reserva de la campaña del ítem, vinculado sin copiarlo.
    """

    item = models.ForeignKey(ItemFacturacion, on_delete=models.PROTECT, related_name="costos")
    costo = models.OneToOneField(Costo, on_delete=models.PROTECT, related_name="item_vinculado")
    vinculado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="costos_de_items",
        null=True,
        editable=False,
    )
    vinculado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "costo del ítem"
        verbose_name_plural = "costos de los ítems"

    def __str__(self) -> str:
        return f"{self.item} · {self.costo}"


class EnvioFacturacion(models.Model):
    """Envío a facturar de un mes (HU-066): quién, cuándo y qué ítems. No se edita ni se borra."""

    mes = models.DateField()
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="envios_facturacion"
    )
    enviado_en = models.DateTimeField(auto_now_add=True)
    items = models.ManyToManyField(ItemFacturacion, related_name="envios")

    class Meta:
        ordering = ["-enviado_en", "-id"]
        verbose_name = "envío a facturar"
        verbose_name_plural = "envíos a facturar"

    def __str__(self) -> str:
        cuando = timezone.localtime(self.enviado_en).strftime("%d/%m/%Y %H:%M")
        return f"Envío {self.mes:%Y-%m} · {cuando}"
