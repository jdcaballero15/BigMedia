from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.inventario.models import Proveedor
from apps.reservas.models import Reserva


class Costo(models.Model):
    """Costo de una reserva (HU-043) o de un ítem a facturar (HU-063).

    Un costo sin reserva es de un ítem: lo crea solo el servicio de `facturacion`, junto con su
    vínculo. Solo esos pueden ir en porcentaje del neto del ítem; el monto se guarda igual.
    """

    class Tipo(models.TextChoices):
        ALQUILER = "alquiler", "Alquiler"
        IMPRESION = "impresion", "Impresión"
        FIJACION = "fijacion", "Fijación"
        COMISION = "comision", "Comisión"
        OTRO = "otro", "Otro"

    reserva = models.ForeignKey(
        Reserva, on_delete=models.PROTECT, related_name="costos", null=True, blank=True
    )
    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.PROTECT, related_name="costos", null=True, blank=True
    )
    destinatario = models.CharField("a quién se le paga", max_length=200, blank=True)
    porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("100"))],
    )
    monto = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    fecha = models.DateField()
    anulado = models.BooleanField(default=False)
    motivo_anulacion = models.CharField(max_length=200, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en", "id"]
        constraints = [
            # Un porcentual puede dar 0 (ítem sin neto); un fijo no.
            models.CheckConstraint(
                condition=models.Q(monto__gt=0) | models.Q(porcentaje__isnull=False, monto__gte=0),
                name="costo_monto_positivo",
            ),
            models.CheckConstraint(
                condition=models.Q(porcentaje__isnull=True)
                | models.Q(porcentaje__gt=0, porcentaje__lte=100, reserva__isnull=True),
                name="costo_porcentaje_solo_de_item",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} {self.monto}"
