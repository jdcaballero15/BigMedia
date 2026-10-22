from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CalendarioView,
    DisponibilidadView,
    OcupacionView,
    PanelView,
    RepartoView,
    ReporteOcupacionView,
    ReservaViewSet,
)

router = DefaultRouter()
router.register("reservas", ReservaViewSet, basename="reserva")

urlpatterns = [
    path("ocupacion/", OcupacionView.as_view(), name="ocupacion"),
    path("disponibilidad/", DisponibilidadView.as_view(), name="disponibilidad"),
    path("calendario/", CalendarioView.as_view(), name="calendario"),
    path("panel/", PanelView.as_view(), name="panel"),
    path("reparto/", RepartoView.as_view(), name="reparto"),
    path("reporte-ocupacion/", ReporteOcupacionView.as_view(), name="reporte-ocupacion"),
    path("", include(router.urls)),
]
