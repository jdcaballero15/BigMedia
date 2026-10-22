from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CampaniaViewSet

router = DefaultRouter()
router.register("campanias", CampaniaViewSet, basename="campania")

urlpatterns = [path("", include(router.urls))]
