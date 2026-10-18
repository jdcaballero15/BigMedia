from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CartelViewSet, EstadoCartelViewSet, FormatoViewSet, ProveedorViewSet, ZonaViewSet

router = DefaultRouter()
router.register("proveedores", ProveedorViewSet, basename="proveedor")
router.register("formatos", FormatoViewSet, basename="formato")
router.register("zonas", ZonaViewSet, basename="zona")
router.register("estados", EstadoCartelViewSet, basename="estado-cartel")
router.register("carteles", CartelViewSet, basename="cartel")

urlpatterns = [path("", include(router.urls))]
