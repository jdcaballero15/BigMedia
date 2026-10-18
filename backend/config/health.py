"""Availability of the API and its primary database."""

from django.db import OperationalError, connection
from django.http import HttpRequest, JsonResponse


def health(_request: HttpRequest) -> JsonResponse:
    try:
        connection.ensure_connection()
    except OperationalError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
