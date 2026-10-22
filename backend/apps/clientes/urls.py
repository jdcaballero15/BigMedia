from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClienteViewSet, MarcaViewSet, RubroViewSet

router = DefaultRouter()
router.register("clientes", ClienteViewSet, basename="cliente")
router.register("marcas", MarcaViewSet, basename="marca")
router.register("rubros", RubroViewSet, basename="rubro")

urlpatterns = [path("", include(router.urls))]
