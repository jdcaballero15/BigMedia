from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CatalogosFacturacionView,
    EnvioFacturacionViewSet,
    GrupoFacturaViewSet,
    IngresosView,
    ItemFacturacionViewSet,
    OrdenCompraPdfView,
    PorGrupoView,
    PorRubroView,
)

router = DefaultRouter()
router.register("items", ItemFacturacionViewSet, basename="item-facturacion")
router.register("envios", EnvioFacturacionViewSet, basename="envio-facturacion")
router.register("grupos", GrupoFacturaViewSet, basename="grupo-factura")

urlpatterns = [
    path("ingresos/", IngresosView.as_view(), name="ingresos"),
    path("por-rubro/", PorRubroView.as_view(), name="por-rubro"),
    path("por-grupo/", PorGrupoView.as_view(), name="por-grupo"),
    path(
        "items/<int:pk>/orden-compra-pdf/",
        OrdenCompraPdfView.as_view(),
        name="orden-compra-pdf",
    ),
    path("catalogos/", CatalogosFacturacionView.as_view(), name="catalogos-facturacion"),
    path("", include(router.urls)),
]
