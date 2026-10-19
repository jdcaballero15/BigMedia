from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.inventario.models import Proveedor
from apps.reservas.models import Reserva


class Costo(models.Model):
    class Tipo(models.TextChoices):
        ALQUILER = "alquiler", "Alquiler"
        IMPRESION = "impresion", "Impresión"
        FIJACION = "fijacion", "Fijación"
        OTRO = "otro", "Otro"

    reserva = models.ForeignKey(Reserva, on_delete=models.PROTECT, related_name="costos")
    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.PROTECT, related_name="costos", null=True, blank=True
    )
    monto = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    fecha = models.DateField()
    anulado = models.BooleanField(default=False)
    motivo_anulacion = models.CharField(max_length=200, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en", "id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(monto__gt=0), name="costo_monto_positivo")
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} {self.monto}"
