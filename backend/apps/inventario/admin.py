from django.contrib import admin

from config.admin_borrado import SoloBorrarAdmin

from .models import Cartel, EstadoCartel, Formato, Proveedor, Zona


@admin.register(Proveedor)
class ProveedorAdmin(SoloBorrarAdmin):
    entidad = "proveedor"
    list_display = ["nombre", "servicio", "activo"]
    search_fields = ["nombre"]


@admin.register(Formato)
class FormatoAdmin(SoloBorrarAdmin):
    entidad = "formato"
    list_display = ["nombre", "modalidad", "activo"]
    search_fields = ["nombre"]


@admin.register(Zona)
class ZonaAdmin(SoloBorrarAdmin):
    entidad = "zona"
    list_display = ["nombre", "activo"]
    search_fields = ["nombre"]


@admin.register(EstadoCartel)
class EstadoCartelAdmin(SoloBorrarAdmin):
    entidad = "estado_cartel"
    list_display = ["nombre", "codigo", "es_baja", "activo"]
    search_fields = ["nombre"]


@admin.register(Cartel)
class CartelAdmin(SoloBorrarAdmin):
    entidad = "cartel"
    list_display = ["direccion", "formato", "zona", "estado"]
    list_select_related = ["formato", "zona", "estado"]
    search_fields = ["direccion"]
