"""Session endpoints for the browser application."""

import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_POST


@ensure_csrf_cookie
def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Iniciá sesión."}, status=401)
    return JsonResponse({"username": request.user.username})


@require_POST
@csrf_protect
def login_view(request):
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
    return JsonResponse({"username": user.username})


@require_POST
@csrf_protect
def logout_view(request):
    logout(request)
    return JsonResponse({"status": "ok"})
