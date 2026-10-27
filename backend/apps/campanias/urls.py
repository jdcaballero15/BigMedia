from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CampaniaViewSet, InteraccionViewSet

router = DefaultRouter()
router.register("campanias", CampaniaViewSet, basename="campania")
router.register("interacciones", InteraccionViewSet, basename="interaccion")

urlpatterns = [path("", include(router.urls))]
