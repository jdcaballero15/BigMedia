"""Session endpoints for the browser application."""

import json

from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_POST

from config.permisos import GRUPO_GERENCIA


def _es_gerencia(request: HttpRequest) -> bool:
    """Un gerente (ve ingresos) es un superusuario o un miembro del grupo Gerencia."""
    user = request.user
    return bool(user.is_superuser or user.groups.filter(name=GRUPO_GERENCIA).exists())


@ensure_csrf_cookie
def me(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Iniciá sesión."}, status=401)
    return JsonResponse(
        {"username": request.user.get_username(), "es_gerencia": _es_gerencia(request)}
    )


@require_POST
@csrf_protect
def login_view(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": "Datos de ingreso inválidos."}, status=400)

    username = payload.get("username", "") if isinstance(payload, dict) else ""
    password = payload.get("password", "") if isinstance(payload, dict) else ""
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"detail": "Usuario o contraseña incorrectos."}, status=401)
    login(request, user)
    return JsonResponse({"username": user.get_username(), "es_gerencia": _es_gerencia(request)})


@require_POST
@csrf_protect
def logout_view(request: HttpRequest) -> JsonResponse:
    logout(request)
    return JsonResponse({"status": "ok"})
