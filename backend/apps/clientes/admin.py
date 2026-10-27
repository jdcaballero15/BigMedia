from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin
from django.http import HttpRequest

from config.admin_borrado import BorradoAuditadoAdmin

from . import services
from .models import Cliente, Contacto, Marca, Rubro

if TYPE_CHECKING:
    from django.forms import ModelForm


@admin.register(Rubro)
class RubroAdmin(BorradoAuditadoAdmin):
    entidad = "rubro"
    list_display = ["nombre", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre"]


@admin.register(Cliente)
class ClienteAdmin(BorradoAuditadoAdmin):
    entidad = "cliente"
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
class MarcaAdmin(BorradoAuditadoAdmin):
    entidad = "marca"
    list_display = ["nombre", "cliente", "rubro", "activo"]
    list_filter = ["activo", "rubro"]
    search_fields = ["nombre", "cliente__nombre"]
    list_select_related = ["cliente", "rubro"]
    autocomplete_fields = ["cliente", "rubro"]


@admin.register(Contacto)
class ContactoAdmin(BorradoAuditadoAdmin):
    entidad = "contacto"
    list_display = ["nombre", "cliente", "cargo", "principal", "activo"]
    list_filter = ["activo", "principal"]
    search_fields = ["nombre", "cliente__nombre"]
    list_select_related = ["cliente"]
    autocomplete_fields = ["cliente"]
