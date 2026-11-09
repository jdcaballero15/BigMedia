from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CampaniaViewSet,
    InteraccionViewSet,
    LineaFormatoViewSet,
    OrdenPublicidadViewSet,
)

router = DefaultRouter()
router.register("campanias", CampaniaViewSet, basename="campania")
router.register("interacciones", InteraccionViewSet, basename="interaccion")
router.register("lineas-formato", LineaFormatoViewSet, basename="linea-formato")
router.register("ordenes-publicidad", OrdenPublicidadViewSet, basename="orden-publicidad")

urlpatterns = [path("", include(router.urls))]
