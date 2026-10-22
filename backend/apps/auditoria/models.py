"""Modelo de auditoría: registro inmutable de cambios en entidades del sistema."""

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class RegistroAuditoria(models.Model):
    """Una fila por campo cambiado. Inmutable: no se permite update ni delete."""

    class Origen(models.TextChoices):
        USUARIO = "usuario", "Usuario"
        SISTEMA = "sistema", "Sistema"
        IMPORTACION = "importacion", "Importación"

    entidad = models.CharField(max_length=100)
    entidad_id = models.PositiveIntegerField()
    campo = models.CharField(max_length=100)
    # null=True intencional: un campo puede ir de None a un valor (o al revés) en la primera captura.
    valor_anterior = models.TextField(blank=True, null=True)  # noqa: DJ001
    valor_nuevo = models.TextField(blank=True, null=True)  # noqa: DJ001
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="registros_auditoria",
    )
    origen = models.CharField(max_length=12, choices=Origen.choices, default=Origen.USUARIO)
    momento = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-momento", "-id"]

    def __str__(self) -> str:
        return f"{self.entidad}#{self.entidad_id} {self.campo} @ {self.momento}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ValidationError("Los registros de auditoría son inmutables.")
        super().save(*args, **kwargs)

    def delete(self, using: Any = None, keep_parents: bool = False) -> tuple[int, dict[str, int]]:  # noqa: ARG002
        raise ValidationError("Los registros de auditoría no pueden eliminarse.")
