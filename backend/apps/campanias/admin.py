from django.contrib import admin

from config.admin_borrado import SoloBorrarAdmin

from .models import Campania


@admin.register(Campania)
class CampaniaAdmin(SoloBorrarAdmin):
    entidad = "campania"
    list_display = ["__str__", "marca", "estado"]
    list_select_related = ["marca"]
    search_fields = ["nombre"]
