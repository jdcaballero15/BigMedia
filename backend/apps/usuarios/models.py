"""Modelos de usuarios: seguimiento de intentos de ingreso (HU-003 criterio 3)."""

from django.db import models


class IntentoIngreso(models.Model):
    """Fallidos seguidos de un nombre de usuario (exista o no) y hasta cuándo está bloqueado."""

    username = models.CharField(max_length=150, unique=True)
    fallidos_seguidos = models.PositiveIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "intento de ingreso"
        verbose_name_plural = "intentos de ingreso"

    def __str__(self) -> str:
        return self.username
