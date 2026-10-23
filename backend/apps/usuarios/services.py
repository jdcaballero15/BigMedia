"""Roles (HU-004), bloqueo por intentos fallidos (HU-003) y gestión de usuarios (HU-005)."""

import logging
from datetime import timedelta
from typing import Literal, TypedDict

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group, User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.auditoria import services as auditoria_services

from .models import IntentoIngreso

logger = logging.getLogger(__name__)

Rol = Literal["administrador", "operativo", "lectura"]
ROL_ADMINISTRADOR: Rol = "administrador"
ROL_OPERATIVO: Rol = "operativo"
ROL_LECTURA: Rol = "lectura"
ROLES: tuple[Rol, ...] = (ROL_ADMINISTRADOR, ROL_OPERATIVO, ROL_LECTURA)

GRUPO_OPERATIVO = "Operativo"
GRUPO_GERENCIA = "Gerencia"
GRUPO_LECTURA = "Lectura"

ENTIDAD_AUDITORIA = "usuario"
SIN_ADMINISTRADOR = "Tiene que quedar al menos un administrador activo."
LINK_INVALIDO = "El link no es válido o ya venció. Pedile uno nuevo al administrador."


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


class DatosUsuario(TypedDict, total=False):
    """Lo que el administrador puede cambiar de un usuario. El nombre de usuario no se edita."""

    first_name: str
    last_name: str
    email: str
    rol: Rol
    es_gerencia: bool
    activo: bool


def _en_grupo(user: User, grupo: str) -> bool:
    return user.groups.filter(name=grupo).exists()


def tiene_gerencia(user: User) -> bool:
    """La casilla Gerencia: solo el grupo, sin contar que un superusuario ya ve todo."""
    return _en_grupo(user, GRUPO_GERENCIA)


def _foto(user: User) -> dict[str, str]:
    """Los campos auditados, como texto. Ni la contraseña ni el token."""
    return {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "rol": rol_de(user),
        "gerencia": "sí" if tiene_gerencia(user) else "no",
        "activo": "sí" if user.is_active else "no",
    }


def _asignar_rol(user: User, rol: Rol) -> None:
    """Lo mismo que se hacía en el admin de Django: superusuario o grupo de rol."""
    user.is_superuser = user.is_staff = rol == ROL_ADMINISTRADOR
    operativo = Group.objects.get(name=GRUPO_OPERATIVO)
    lectura = Group.objects.get(name=GRUPO_LECTURA)
    user.groups.remove(operativo, lectura)
    if rol == ROL_OPERATIVO:
        user.groups.add(operativo)
    elif rol == ROL_LECTURA:
        user.groups.add(lectura)


def _asignar_gerencia(user: User, es_gerencia: bool) -> None:
    gerencia = Group.objects.get(name=GRUPO_GERENCIA)
    if es_gerencia:
        user.groups.add(gerencia)
    else:
        user.groups.remove(gerencia)


def crear_usuario(username: str, datos: DatosUsuario, autor: User | AnonymousUser) -> User:
    """Alta sin contraseña usable: la define el usuario con el link (HU-005 criterio 1)."""
    with transaction.atomic():
        user = User(
            username=username,
            first_name=datos.get("first_name", ""),
            last_name=datos.get("last_name", ""),
            email=datos.get("email", ""),
        )
        user.set_unusable_password()
        user.save()
        _asignar_rol(user, datos.get("rol", ROL_LECTURA))
        _asignar_gerencia(user, datos.get("es_gerencia", False))
        user.save()
        despues = _foto(user)
        antes = dict.fromkeys(despues, "")
        auditoria_services.registrar_cambios(ENTIDAD_AUDITORIA, user.pk, antes, despues, autor)
    return user


def _pierde_administrador(datos: DatosUsuario) -> bool:
    return datos.get("activo") is False or datos.get("rol", ROL_ADMINISTRADOR) != ROL_ADMINISTRADOR


def _validar_queda_administrador(usuario_id: int) -> None:
    """Bloquea a los administradores activos, así dos bajas simultáneas no dejan ninguno."""
    activos = list(
        User.objects.select_for_update()
        .filter(is_superuser=True, is_active=True)
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    if activos == [usuario_id]:
        raise ValidationError(SIN_ADMINISTRADOR)


def _aplicar(user: User, datos: DatosUsuario) -> None:
    if "first_name" in datos:
        user.first_name = datos["first_name"]
    if "last_name" in datos:
        user.last_name = datos["last_name"]
    if "email" in datos:
        user.email = datos["email"]
    if "activo" in datos:
        user.is_active = datos["activo"]
    if "rol" in datos:
        _asignar_rol(user, datos["rol"])
    if "es_gerencia" in datos:
        _asignar_gerencia(user, datos["es_gerencia"])


def actualizar_usuario(usuario_id: int, datos: DatosUsuario, autor: User | AnonymousUser) -> User:
    """Edita datos, rol, Gerencia y activo; nunca deja el sistema sin administrador (criterio 3)."""
    with transaction.atomic():
        if _pierde_administrador(datos):
            _validar_queda_administrador(usuario_id)
        user = User.objects.select_for_update().get(pk=usuario_id)
        antes = _foto(user)
        _aplicar(user, datos)
        user.save()
        auditoria_services.registrar_cambios(ENTIDAD_AUDITORIA, user.pk, antes, _foto(user), autor)
    return user


def generar_codigo_clave(usuario_id: int) -> str:
    """Código `<uid>.<token>` del link de un solo uso para definir o restablecer la contraseña.

    Deja la contraseña anterior inutilizable: el token depende de ella, así que también invalida
    cualquier link generado antes y cierra las sesiones abiertas del usuario.
    """
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=usuario_id)
        user.set_unusable_password()
        user.save(update_fields=["password"])
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{uid}.{default_token_generator.make_token(user)}"


def _usuario_del_link(uid: str, token: str) -> User:
    try:
        pk = int(force_str(urlsafe_base64_decode(uid)))
    except (ValueError, TypeError, OverflowError) as error:
        raise ValidationError({"token": LINK_INVALIDO}) from error
    user = User.objects.select_for_update().filter(pk=pk).first()
    if user is None or not default_token_generator.check_token(user, token):
        raise ValidationError({"token": LINK_INVALIDO})
    return user


def definir_clave(uid: str, token: str, clave: str) -> None:
    """Define la contraseña con el link; al cambiarla, el link deja de servir."""
    with transaction.atomic():
        user = _usuario_del_link(uid, token)
        try:
            validate_password(clave, user)
        except ValidationError as error:
            raise ValidationError({"clave": error.messages}) from error
        user.set_password(clave)
        user.save(update_fields=["password"])
