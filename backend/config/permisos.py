"""Permisos de la API compartidos entre apps."""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

GRUPO_OPERATIVO = "Operativo"
GRUPO_GERENCIA = "Gerencia"


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


class LecturaSoloGerencia(permissions.BasePermission):
    """Solo lectura, y solo para el grupo Gerencia o un superusuario (datos de facturación)."""

    def has_permission(self, request: Request, _view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return bool(user.is_superuser or user.groups.filter(name=GRUPO_GERENCIA).exists())
