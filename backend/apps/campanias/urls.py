from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CampaniaViewSet, InteraccionViewSet, LineaFormatoViewSet

router = DefaultRouter()
router.register("campanias", CampaniaViewSet, basename="campania")
router.register("interacciones", InteraccionViewSet, basename="interaccion")
router.register("lineas-formato", LineaFormatoViewSet, basename="linea-formato")

urlpatterns = [path("", include(router.urls))]
