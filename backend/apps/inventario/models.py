from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils.text import slugify


class Catalogo(models.Model):
    nombre = models.CharField(max_length=120)
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.nombre


class Proveedor(Catalogo):
    servicio = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [models.UniqueConstraint(Lower("nombre"), name="proveedor_nombre_ci")]


class Formato(Catalogo):
    class Modalidad(models.TextChoices):
        FIJA = "fija", "Fija"
        DIGITAL = "digital", "Digital"

    modalidad = models.CharField(max_length=10, choices=Modalidad.choices)
    capacidad_predeterminada = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    ancho = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    alto = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(Lower("nombre"), name="formato_nombre_ci"),
            models.CheckConstraint(
                condition=models.Q(capacidad_predeterminada__gte=1),
                name="formato_capacidad_positiva",
            ),
        ]


class Zona(Catalogo):
    class Meta:
        ordering = ["nombre"]
        constraints = [models.UniqueConstraint(Lower("nombre"), name="zona_nombre_ci")]


class EstadoCartel(Catalogo):
    codigo = models.SlugField(unique=True, max_length=80, blank=True)
    operativo = models.BooleanField(default=False)
    es_baja = models.BooleanField(default=False)

    class Meta:
        ordering = ["nombre"]
        constraints = [models.UniqueConstraint(Lower("nombre"), name="estado_nombre_ci")]

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = slugify(self.nombre).replace("-", "_")
        super().save(*args, **kwargs)
