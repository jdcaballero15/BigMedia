from typing import Any

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.clientes.models import Cliente, Contacto, Marca
from apps.inventario.models import Formato
from config.texto import normalizar_busqueda


class Campania(models.Model):
    class Estado(models.TextChoices):
        COTIZADA = "cotizada", "Cotizada"
        CONFIRMADA = "confirmada", "Confirmada"
        CANCELADA = "cancelada", "Cancelada"
        PERDIDA = "perdida", "Perdida"

    nombre = models.CharField(max_length=200, blank=True)
    marca = models.ForeignKey(
        Marca, on_delete=models.PROTECT, related_name="campanias", null=True, blank=True
    )
    cliente_facturacion = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="campanias_facturadas",
        null=True,
        blank=True,
    )
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.COTIZADA)
    nombre_busqueda = models.CharField(max_length=200, editable=False, db_index=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en", "id"]

    def __str__(self) -> str:
        return self.nombre or f"Campaña #{self.pk}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.nombre_busqueda = normalizar_busqueda(self.nombre)
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {"nombre_busqueda"}
        super().save(*args, **kwargs)

    @property
    def cliente_factura(self) -> Cliente | None:
        """Quién factura: el cliente propio si está; si no, el de la marca (RN-014)."""
        if self.cliente_facturacion is not None:
            return self.cliente_facturacion
        if self.marca is not None:
            return self.marca.cliente
        return None


class LineaFormato(models.Model):
    """Posiciones solicitadas de un formato en la campaña (HU-055).

    Todo es opcional y modificable; cambiarla o quitarla no toca las reservas. Quitar es baja
    lógica (`activa=False`); el formato no se repite entre las líneas activas de una campaña.
    """

    campania = models.ForeignKey(Campania, on_delete=models.PROTECT, related_name="lineas")
    formato = models.ForeignKey(Formato, on_delete=models.PROTECT, related_name="lineas_campania")
    cantidad = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    activa = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["formato__nombre", "id"]
        verbose_name = "línea de formato"
        verbose_name_plural = "líneas de formato"
        constraints = [
            models.UniqueConstraint(
                fields=["campania", "formato"],
                condition=models.Q(activa=True),
                name="linea_formato_unica_activa",
            )
        ]

    def __str__(self) -> str:
        cantidad = self.cantidad if self.cantidad is not None else "sin cantidad"
        return f"{self.formato.nombre}: {cantidad}"


class Interaccion(models.Model):
    """Reunión o llamada comercial con un cliente (HU-020).

    Vive en `campanias` porque puede llevar una campaña y `clientes` no importa de `campanias`.
    No se borra (HU-006).
    """

    class Tipo(models.TextChoices):
        REUNION = "reunion", "Reunión"
        LLAMADA = "llamada", "Llamada"

    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    asunto = models.CharField(max_length=200)
    fecha = models.DateField()
    notas = models.TextField(blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="interacciones")
    contacto = models.ForeignKey(
        Contacto, on_delete=models.PROTECT, related_name="interacciones", null=True, blank=True
    )
    campania = models.ForeignKey(
        Campania, on_delete=models.PROTECT, related_name="interacciones", null=True, blank=True
    )
    registrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="interacciones_registradas",
        null=True,
        editable=False,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "-creado_en", "-id"]
        verbose_name = "interacción"
        verbose_name_plural = "interacciones"

    def __str__(self) -> str:
        return f"{self.fecha} · {self.asunto}"
