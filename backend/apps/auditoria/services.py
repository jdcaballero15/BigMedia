"""Servicio de auditoría: escritura de registros de cambios."""

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.db import models

from .models import RegistroAuditoria


def registrar_cambios(
    entidad: str,
    entidad_id: int,
    anteriores: dict[str, str],
    nuevos: dict[str, str],
    usuario: AbstractBaseUser | AnonymousUser | None,
    origen: str = RegistroAuditoria.Origen.USUARIO,
) -> None:
    """Crea un RegistroAuditoria por cada campo cuyo valor cambió.

    Compara `anteriores[campo]` vs `nuevos[campo]` (ambos ya como texto).
    No crea ninguna fila si nada cambió. El usuario puede ser None o AnonymousUser
    (origen sistema/importación o request sin autenticar).
    """
    User = get_user_model()
    usuario_autenticado = usuario if isinstance(usuario, User) else None
    for campo, valor_anterior in anteriores.items():
        valor_nuevo = nuevos.get(campo, valor_anterior)
        if valor_anterior == valor_nuevo:
            continue
        kwargs: dict[str, object] = {
            "entidad": entidad,
            "entidad_id": entidad_id,
            "campo": campo,
            "valor_anterior": valor_anterior,
            "valor_nuevo": valor_nuevo,
            "origen": origen,
        }
        if usuario_autenticado is not None:
            kwargs["usuario"] = usuario_autenticado
        RegistroAuditoria(**kwargs).save()


def registrar_borrado(
    entidad: str,
    instancia: models.Model,
    usuario: AbstractBaseUser | AnonymousUser | None,
) -> None:
    """Audita el borrado de una carga errónea (HU-006, criterio 4).

    Registra cada campo editable con su valor anterior y el nuevo vacío, y una fila `eliminado`
    de "" a "si" para encontrar los borrados sin recorrer todos los campos.
    """
    anteriores: dict[str, str] = {}
    for campo in instancia._meta.concrete_fields:
        if campo.primary_key or not campo.editable:
            continue
        valor = getattr(instancia, campo.attname)
        anteriores[campo.name] = "" if valor is None else str(valor)
    nuevos = dict.fromkeys(anteriores, "")
    anteriores["eliminado"], nuevos["eliminado"] = "", "si"
    registrar_cambios(entidad, int(instancia.pk), anteriores, nuevos, usuario)
