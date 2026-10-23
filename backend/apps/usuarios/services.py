"""Roles de usuario (HU-004) y bloqueo temporal por intentos fallidos (HU-003 criterio 3)."""

import logging
from datetime import timedelta
from typing import Literal

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.db import transaction
from django.utils import timezone

from .models import IntentoIngreso

logger = logging.getLogger(__name__)

Rol = Literal["administrador", "operativo", "lectura"]
ROL_ADMINISTRADOR: Rol = "administrador"
ROL_OPERATIVO: Rol = "operativo"
ROL_LECTURA: Rol = "lectura"

GRUPO_OPERATIVO = "Operativo"
GRUPO_GERENCIA = "Gerencia"


def rol_de(user: User | AnonymousUser) -> Rol:
    """El rol se deriva en cada petición: superusuario, grupo Operativo o, si no, Lectura.

    Gerencia no es un rol: es un permiso aparte (ingresos y auditoría) que se suma a cualquiera.
    """
    if user.is_superuser:
        return ROL_ADMINISTRADOR
    if user.groups.filter(name=GRUPO_OPERATIVO).exists():
        return ROL_OPERATIVO
    return ROL_LECTURA


def es_gerencia(user: User | AnonymousUser) -> bool:
    """Ve ingresos y auditoría: un superusuario o un miembro del grupo Gerencia."""
    return bool(user.is_superuser or user.groups.filter(name=GRUPO_GERENCIA).exists())


def _clave(username: str) -> str:
    """El contador no distingue mayúsculas ni espacios alrededor del nombre."""
    return username.strip().lower()


def esta_bloqueado(username: str) -> bool:
    return IntentoIngreso.objects.filter(
        username=_clave(username), bloqueado_hasta__gt=timezone.now()
    ).exists()


def registrar_fallo(username: str) -> None:
    """Suma un fallo; al llegar al máximo bloquea. Un bloqueo vencido arranca de cero."""
    clave = _clave(username)
    if not clave:
        return
    with transaction.atomic():
        intento, _ = IntentoIngreso.objects.select_for_update().get_or_create(username=clave)
        ahora = timezone.now()
        if intento.bloqueado_hasta is not None and intento.bloqueado_hasta <= ahora:
            intento.fallidos_seguidos = 0
            intento.bloqueado_hasta = None
        intento.fallidos_seguidos += 1
        if intento.fallidos_seguidos >= settings.LOGIN_MAX_INTENTOS:
            intento.bloqueado_hasta = ahora + timedelta(minutes=settings.LOGIN_BLOQUEO_MINUTOS)
            # Solo el id: el nombre de usuario puede ser un dato personal (regla 6).
            logger.warning(
                "Ingreso bloqueado por intentos fallidos (IntentoIngreso %s)", intento.pk
            )
        intento.save()


def registrar_exito(username: str) -> None:
    IntentoIngreso.objects.filter(username=_clave(username)).update(
        fallidos_seguidos=0, bloqueado_hasta=None
    )
