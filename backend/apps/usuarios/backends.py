"""Backend de autenticación con bloqueo por intentos fallidos (API y admin)."""

from typing import Any

from asgiref.sync import sync_to_async
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from .services import esta_bloqueado, registrar_exito, registrar_fallo


class BackendConBloqueo(ModelBackend):
    """Rechaza sin mirar la contraseña si el usuario está bloqueado; si no, cuenta el resultado."""

    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        if username is None:
            return super().authenticate(request, username, password, **kwargs)
        if esta_bloqueado(username):
            # PermissionDenied corta la cadena de backends: authenticate() devuelve None.
            raise PermissionDenied
        user = super().authenticate(request, username, password, **kwargs)
        if user is None:
            registrar_fallo(username)
        else:
            registrar_exito(username)
        return user

    async def aauthenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        """ModelBackend tiene su propia versión async: se delega en la sync para no saltear el bloqueo."""
        return await sync_to_async(self.authenticate)(request, username, password, **kwargs)
