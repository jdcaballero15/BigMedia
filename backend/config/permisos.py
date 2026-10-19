"""Permisos de la API compartidos entre apps."""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

GRUPO_OPERATIVO = "Operativo"


class LecturaConSesionEdicionOperativo(permissions.BasePermission):
    """Lee cualquier usuario con sesión; edita el grupo Operativo o un superusuario."""

    def has_permission(self, request: Request, _view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_superuser or request.user.groups.filter(name=GRUPO_OPERATIVO).exists()
        )
