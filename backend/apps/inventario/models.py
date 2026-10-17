import unicodedata

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


def normalizar_busqueda(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )


class Cartel(models.Model):
    formato = models.ForeignKey(Formato, on_delete=models.PROTECT, related_name="carteles")
    zona = models.ForeignKey(Zona, on_delete=models.PROTECT, related_name="carteles")
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.PROTECT, related_name="carteles", null=True, blank=True
    )
    estado = models.ForeignKey(EstadoCartel, on_delete=models.PROTECT, related_name="carteles")
    direccion = models.CharField(max_length=250)
    direccion_busqueda = models.CharField(max_length=250, editable=False, db_index=True)
    tamano = models.CharField(max_length=80, blank=True)
    capacidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    tarifa_lista = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    foto_url = models.URLField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["direccion", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacidad__gte=1), name="cartel_capacidad_positiva"
            ),
            models.CheckConstraint(
                condition=models.Q(tarifa_lista__gte=0) | models.Q(tarifa_lista__isnull=True),
                name="cartel_tarifa_no_negativa",
            ),
        ]

    @property
    def nombre_visible(self):
        if self.formato.nombre == "Séxtuples":
            return f"{self.direccion} · {self.capacidad} slots"
        if self.tamano:
            return f"{self.direccion} · {self.tamano}"
        return self.direccion

    def save(self, *args, **kwargs):
        self.direccion_busqueda = normalizar_busqueda(self.direccion)
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {"direccion_busqueda"}
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre_visible
