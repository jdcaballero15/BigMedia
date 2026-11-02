from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClienteViewSet,
    ContactoViewSet,
    GrupoEconomicoViewSet,
    MarcaViewSet,
    RubroViewSet,
)

router = DefaultRouter()
router.register("clientes", ClienteViewSet, basename="cliente")
router.register("marcas", MarcaViewSet, basename="marca")
router.register("contactos", ContactoViewSet, basename="contacto")
router.register("rubros", RubroViewSet, basename="rubro")
router.register("grupos", GrupoEconomicoViewSet, basename="grupo-economico")

urlpatterns = [path("", include(router.urls))]
