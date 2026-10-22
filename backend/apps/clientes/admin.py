from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib import admin
from django.http import HttpRequest

from . import services
from .models import Cliente, Marca, Rubro

if TYPE_CHECKING:
    from django.forms import ModelForm

    ModelAdminBase = admin.ModelAdmin[Any]
else:
    ModelAdminBase = admin.ModelAdmin


class SinBorrarAdmin(ModelAdminBase):
    """Baja lógica: se inactiva con `activo`, nunca se borra."""

    def has_delete_permission(self, _request: HttpRequest, _obj: Any = None) -> bool:
        return False


@admin.register(Rubro)
class RubroAdmin(SinBorrarAdmin):
    list_display = ["nombre", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre"]


@admin.register(Cliente)
class ClienteAdmin(SinBorrarAdmin):
    list_display = ["nombre_visible", "razon_social", "cuit", "tipo", "activo"]
    list_filter = ["tipo", "activo"]
    search_fields = ["nombre", "razon_social", "cuit"]

    @admin.display(description="Nombre", ordering="nombre")
    def nombre_visible(self, obj: Cliente) -> str:
        return obj.nombre_visible

    def save_model(
        self, request: HttpRequest, obj: Cliente, form: ModelForm[Cliente], change: bool
    ) -> None:
        if change:
            super().save_model(request, obj, form, change)
        else:
            services.registrar_cliente(obj)


@admin.register(Marca)
class MarcaAdmin(SinBorrarAdmin):
    list_display = ["nombre", "cliente", "rubro", "activo"]
    list_filter = ["activo", "rubro"]
    search_fields = ["nombre", "cliente__nombre"]
    list_select_related = ["cliente", "rubro"]
    autocomplete_fields = ["cliente", "rubro"]
