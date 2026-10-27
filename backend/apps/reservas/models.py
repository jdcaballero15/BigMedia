from decimal import Decimal
from typing import Any

from django.db import models

from apps.campanias.models import Campania
from apps.inventario.models import Cartel

MESES_ABREV = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
]  # fmt: skip


class Reserva(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        CONFIRMADA = "confirmada", "Confirmada"
        FINALIZADA = "finalizada", "Finalizada"
        CANCELADA = "cancelada", "Cancelada"

    # Un estado ocupa cupo cuando no está cancelada (HU-028, HU-040).
    ESTADOS_QUE_OCUPAN = (Estado.PENDIENTE, Estado.CONFIRMADA, Estado.FINALIZADA)

    campania = models.ForeignKey(Campania, on_delete=models.PROTECT, related_name="reservas")
    cartel = models.ForeignKey(Cartel, on_delete=models.PROTECT, related_name="reservas")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    precio_alquiler = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    precio_impresion = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    precio_fijacion = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    nombre = models.CharField(max_length=250, editable=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_fin__gte=models.F("fecha_inicio")),
                name="reserva_fin_no_antes_de_inicio",
            ),
            models.CheckConstraint(
                condition=models.Q(precio_alquiler__gte=0)
                & models.Q(precio_impresion__gte=0)
                & models.Q(precio_fijacion__gte=0),
                name="reserva_precios_no_negativos",
            ),
        ]

    def __str__(self) -> str:
        return self.nombre

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.total = self.precio_alquiler + self.precio_impresion + self.precio_fijacion
        self.nombre = self.generar_nombre()
        super().save(*args, **kwargs)

    def generar_nombre(self) -> str:
        """Nombre legible "Marca - Cartel - Mes Año" (HU-030)."""
        marca_obj = self.campania.marca
        marca = marca_obj.nombre if marca_obj is not None else "Sin marca"
        periodo = f"{MESES_ABREV[self.fecha_inicio.month - 1]} {self.fecha_inicio.year}"
        return f"{marca} - {self.cartel.nombre_visible} - {periodo}"


class ParametrosDisponibilidad(models.Model):
    """Parámetros del motor de disponibilidad que cambia el administrador (HU-001).

    Una sola fila (`pk=1`), creada por migración y que no se borra.
    """

    # Día de borde (RN-001): si una reserva termina el día en que empieza otra, se pisan.
    borde_inclusivo = models.BooleanField(default=True)
    # Si la reserva pendiente (tentativa) ocupa cupo para el bloqueo duro (RN-002).
    tentativa_bloquea = models.BooleanField(default=False)

    class Meta:
        verbose_name = "parámetros de disponibilidad"
        verbose_name_plural = "parámetros de disponibilidad"

    def __str__(self) -> str:
        return "Parámetros de disponibilidad"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *_args: Any, **_kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValueError("Los parámetros de disponibilidad no se borran.")
