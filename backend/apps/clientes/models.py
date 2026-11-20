from collections.abc import Iterable
from typing import Any

from django.core.exceptions import ValidationError
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
        constraints = [
            models.UniqueConstraint(
                Lower("nombre"),
                name="rubro_nombre_ci",
                violation_error_message="Ya existe un rubro con ese nombre.",
            )
        ]

    def __str__(self) -> str:
        return self.nombre


class GrupoEconomico(models.Model):
    """Grupo de marcas de un mismo dueño, sin importar quién las factura (RN-016)."""

    nombre = models.CharField(max_length=120)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "grupo económico"
        verbose_name_plural = "grupos económicos"
        constraints = [
            models.UniqueConstraint(
                Lower("nombre"),
                name="grupo_economico_nombre_ci",
                violation_error_message="Ya existe un grupo económico con ese nombre.",
            )
        ]

    def __str__(self) -> str:
        return self.nombre


class Cliente(models.Model):
    class Tipo(models.TextChoices):
        DIRECTO = "directo", "Cliente directo"
        INTERMEDIARIO = "intermediario", "Intermediario (bolsero)"
        INTERMEDIARIO_FORMAL = "intermediario_formal", "Central de medios"

    nombre = models.CharField(max_length=160, blank=True)
    razon_social = models.CharField("razón social", max_length=200, blank=True)
    cuit = models.CharField("CUIT", max_length=11, blank=True, validators=[validar_cuit])
    tipo = models.CharField(max_length=24, choices=Tipo.choices, blank=True)
    telefono = models.CharField("teléfono", max_length=60, blank=True)
    correo = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)
    nombre_busqueda = models.CharField(max_length=160, editable=False, db_index=True)
    razon_social_busqueda = models.CharField(max_length=200, editable=False, db_index=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        # Primero los que tienen nombre (alfabético) y al final los sin nombre, por id.
        ordering = [
            models.Case(models.When(nombre="", then=models.Value(1)), default=models.Value(0)),
            "nombre",
            "id",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["cuit"],
                condition=~models.Q(cuit=""),
                name="cliente_cuit_unico",
                violation_error_message="Ya existe un cliente con ese CUIT.",
            ),
        ]

    def __str__(self) -> str:
        return self.nombre_visible

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.nombre_busqueda = normalizar_busqueda(self.nombre)
        self.razon_social_busqueda = normalizar_busqueda(self.razon_social)
        campos = ("nombre_busqueda", "razon_social_busqueda")
        super().save(*args, **_con_campos_de_busqueda(kwargs, campos))

    @property
    def nombre_visible(self) -> str:
        """El nombre, o "Cliente sin nombre #<id>" si no se cargó."""
        return self.nombre or f"Cliente sin nombre #{self.pk}"


class Marca(models.Model):
    nombre = models.CharField(max_length=160)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="marcas")
    rubro = models.ForeignKey(
        Rubro, on_delete=models.PROTECT, related_name="marcas", null=True, blank=True
    )
    grupo = models.ForeignKey(
        GrupoEconomico, on_delete=models.PROTECT, related_name="marcas", null=True, blank=True
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


class Contacto(models.Model):
    """Persona con quien se habla en una central de medios (HU-068, RN-015).

    No lleva datos de facturación, que siguen en el cliente. No se borra: se inactiva (HU-006).
    """

    class Rol(models.TextChoices):
        PLANIFICADOR = "planificador", "Planificador"
        ASISTENTE = "asistente", "Asistente"

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="contactos")
    rol = models.CharField(max_length=16, choices=Rol.choices, default=Rol.PLANIFICADOR)
    planificador = models.ForeignKey(
        "self", on_delete=models.PROTECT, related_name="asistentes", null=True, blank=True
    )
    nombre = models.CharField(max_length=160)
    cargo = models.CharField("cargo o área", max_length=120, blank=True)
    correo = models.EmailField(blank=True)
    telefono = models.CharField("teléfono", max_length=60, blank=True)
    notas = models.TextField(blank=True)
    principal = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rol", "-principal", "nombre", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["cliente"],
                condition=models.Q(principal=True),
                name="contacto_un_principal_por_cliente",
                violation_error_message="El cliente ya tiene un contacto principal.",
            ),
            models.CheckConstraint(
                condition=~models.Q(principal=True, activo=False),
                name="contacto_principal_activo",
                violation_error_message="Un contacto inactivo no puede ser el principal.",
            ),
            models.CheckConstraint(
                condition=models.Q(rol="planificador", planificador__isnull=True)
                | models.Q(rol="asistente", planificador__isnull=False),
                name="contacto_rol_planificador_coherente",
            ),
            models.CheckConstraint(
                condition=~models.Q(rol="asistente", principal=True),
                name="contacto_asistente_no_principal",
            ),
            models.CheckConstraint(
                condition=~models.Q(planificador=models.F("id")),
                name="contacto_no_es_su_planificador",
            ),
        ]

    def __str__(self) -> str:
        return self.nombre

    def clean(self) -> None:
        super().clean()
        planificador = self.planificador
        if (
            self.rol == self.Rol.ASISTENTE
            and planificador is not None
            and (
                planificador.pk == self.pk
                or planificador.cliente_id != self.cliente_id
                or planificador.rol != self.Rol.PLANIFICADOR
                or not planificador.activo
            )
        ):
            raise ValidationError({"planificador": "Elegí un planificador activo de esta central."})
        if (
            self.pk
            and self.asistentes.filter(activo=True).exists()
            and (not self.activo or self.rol != self.Rol.PLANIFICADOR)
        ):
            raise ValidationError({"rol": "Inactivá o reasigná antes sus asistentes activos."})
