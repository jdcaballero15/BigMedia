"""Permisos de la API compartidos entre apps."""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.usuarios.services import ROL_ADMINISTRADOR, ROL_LECTURA, es_gerencia, rol_de


class LecturaConSesionEdicionOperativo(permissions.BasePermission):
    """Lee cualquier usuario con sesión; edita el rol Operativo o Administrador."""

    def has_permission(self, request: Request, _view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return rol_de(request.user) != ROL_LECTURA


class LecturaSoloGerencia(permissions.BasePermission):
    """Solo lectura, y solo para el grupo Gerencia o un superusuario (datos de facturación)."""

    def has_permission(self, request: Request, _view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return es_gerencia(user)


class SoloAdministrador(permissions.BasePermission):
    """Configuración y gestión de usuarios: solo el rol Administrador (HU-004 criterio 1)."""

    def has_permission(self, request: Request, _view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return rol_de(user) == ROL_ADMINISTRADOR
