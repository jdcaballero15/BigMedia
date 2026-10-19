from collections.abc import Iterable
from typing import Any

from django.db import models
from django.db.models.functions import Lower

from config.texto import normalizar_busqueda

from .validators import validar_cuit


def _con_campos_de_busqueda(kwargs: dict[str, Any], campos: Iterable[str]) -> dict[str, Any]:
    """Suma los campos de búsqueda a `update_fields` cuando el guardado es parcial."""
    update_fields = kwargs.get("update_fields")
    if update_fields is not None:
        kwargs["update_fields"] = set(update_fields) | set(campos)
    return kwargs


class Rubro(models.Model):
    nombre = models.CharField(max_length=120)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        constraints = [models.UniqueConstraint(Lower("nombre"), name="rubro_nombre_ci")]

    def __str__(self) -> str:
        return self.nombre


class Cliente(models.Model):
    class Tipo(models.TextChoices):
        DIRECTO = "directo", "Directo"
        INTERMEDIARIO = "intermediario", "Intermediario"
        INTERMEDIARIO_FORMAL = "intermediario_formal", "Intermediario formal"

    nombre = models.CharField("nombre de fantasía", max_length=160)
    razon_social = models.CharField("razón social", max_length=200)
    cuit = models.CharField("CUIT", max_length=11, blank=True, validators=[validar_cuit])
    tipo = models.CharField(max_length=24, choices=Tipo.choices)
    telefono = models.CharField("teléfono", max_length=60, blank=True)
    correo = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)
    nombre_busqueda = models.CharField(max_length=160, editable=False, db_index=True)
    razon_social_busqueda = models.CharField(max_length=200, editable=False, db_index=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["cuit"], condition=~models.Q(cuit=""), name="cliente_cuit_unico"
            ),
        ]

    def __str__(self) -> str:
        return self.nombre

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.nombre_busqueda = normalizar_busqueda(self.nombre)
        self.razon_social_busqueda = normalizar_busqueda(self.razon_social)
        campos = ("nombre_busqueda", "razon_social_busqueda")
        super().save(*args, **_con_campos_de_busqueda(kwargs, campos))


class Marca(models.Model):
    nombre = models.CharField(max_length=160)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="marcas")
    rubro = models.ForeignKey(
        Rubro, on_delete=models.PROTECT, related_name="marcas", null=True, blank=True
    )
    activo = models.BooleanField(default=True)
    nombre_busqueda = models.CharField(max_length=160, editable=False, db_index=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre", "id"]

    def __str__(self) -> str:
        return self.nombre

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.nombre_busqueda = normalizar_busqueda(self.nombre)
        super().save(*args, **_con_campos_de_busqueda(kwargs, ("nombre_busqueda",)))
