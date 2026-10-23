"""Session endpoints for the browser application."""

import json

from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_POST

from apps.usuarios.services import es_gerencia, esta_bloqueado, rol_de

MENSAJE_BLOQUEO = "Demasiados intentos fallidos. Probá de nuevo en unos minutos."


def _sesion(request: HttpRequest) -> dict[str, object]:
    user = request.user
    return {"username": user.get_username(), "es_gerencia": es_gerencia(user), "rol": rol_de(user)}


@ensure_csrf_cookie
def me(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Iniciá sesión."}, status=401)
    return JsonResponse(_sesion(request))


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
        # Mismo mensaje exista o no el usuario: el bloqueo cuenta por nombre (HU-003 criterio 2).
        if isinstance(username, str) and esta_bloqueado(username):
            return JsonResponse({"detail": MENSAJE_BLOQUEO}, status=429)
        return JsonResponse({"detail": "Usuario o contraseña incorrectos."}, status=401)
    login(request, user)
    return JsonResponse(_sesion(request))


@require_POST
@csrf_protect
def logout_view(request: HttpRequest) -> JsonResponse:
    logout(request)
    return JsonResponse({"status": "ok"})
