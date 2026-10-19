from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CostoViewSet, MargenView

router = DefaultRouter()
router.register("costos", CostoViewSet, basename="costo")

urlpatterns = [
    path("margen/", MargenView.as_view(), name="margen"),
    path("", include(router.urls)),
]
