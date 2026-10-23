from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin

from .models import IntentoIngreso

if TYPE_CHECKING:
    ModelAdminBase = admin.ModelAdmin[IntentoIngreso]
else:
    ModelAdminBase = admin.ModelAdmin


@admin.register(IntentoIngreso)
class IntentoIngresoAdmin(ModelAdminBase):
    """Solo para que un administrador pueda desbloquear a mano."""

    list_display = ("username", "fallidos_seguidos", "bloqueado_hasta")
    search_fields = ("username",)
