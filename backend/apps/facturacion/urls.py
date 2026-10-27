from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CatalogosFacturacionView, IngresosView, ItemFacturacionViewSet, PorRubroView

router = DefaultRouter()
router.register("items", ItemFacturacionViewSet, basename="item-facturacion")

urlpatterns = [
    path("ingresos/", IngresosView.as_view(), name="ingresos"),
    path("por-rubro/", PorRubroView.as_view(), name="por-rubro"),
    path("catalogos/", CatalogosFacturacionView.as_view(), name="catalogos-facturacion"),
    path("", include(router.urls)),
]
