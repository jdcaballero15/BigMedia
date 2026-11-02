from django.contrib import admin

from config.admin_borrado import BorradoAuditadoAdmin, SoloBorrarAdmin

from .models import Campania, Interaccion


@admin.register(Campania)
class CampaniaAdmin(SoloBorrarAdmin):
    entidad = "campania"
    list_display = ["__str__", "marca", "estado"]
    list_select_related = ["marca"]
    search_fields = ["nombre"]


@admin.register(Interaccion)
class InteraccionAdmin(BorradoAuditadoAdmin):
    entidad = "interaccion"
    list_display = ["fecha", "tipo", "asunto", "cliente", "contacto", "campania"]
    list_filter = ["tipo"]
    list_select_related = ["cliente", "contacto", "campania"]
    search_fields = ["asunto"]
