from django.contrib import admin

from config.admin_borrado import ModelAdminBase, SoloBorrarAdmin

from .models import ItemFacturacion, Sector, TipoVenta


@admin.register(Sector, TipoVenta)
class CatalogoFacturacionAdmin(ModelAdminBase):
    """Listas administrables de Gob/Priv y tipo de venta (RN-023)."""

    list_display = ["nombre", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre"]


@admin.register(ItemFacturacion)
class ItemFacturacionAdmin(SoloBorrarAdmin):
    entidad = "item_facturacion"
    list_display = ["__str__", "cliente", "neto", "total", "estado"]
    list_filter = ["estado"]
    list_select_related = ["cliente"]
    search_fields = ["descripcion", "numero_factura"]
