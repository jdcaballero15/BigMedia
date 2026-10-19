from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OcupacionView, ReservaViewSet

router = DefaultRouter()
router.register("reservas", ReservaViewSet, basename="reserva")

urlpatterns = [
    path("ocupacion/", OcupacionView.as_view(), name="ocupacion"),
    path("", include(router.urls)),
]
