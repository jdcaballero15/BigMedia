from typing import Any

from django.db import models

from apps.clientes.models import Cliente, Marca
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
