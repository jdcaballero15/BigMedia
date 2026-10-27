from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CalendarioView,
    DisponibilidadView,
    OcupacionView,
    PanelView,
    ParametrosView,
    RepartoView,
    ReporteOcupacionView,
    ReservaViewSet,
    SeguimientoView,
)

router = DefaultRouter()
router.register("reservas", ReservaViewSet, basename="reserva")

urlpatterns = [
    path("ocupacion/", OcupacionView.as_view(), name="ocupacion"),
    path("disponibilidad/", DisponibilidadView.as_view(), name="disponibilidad"),
    path("calendario/", CalendarioView.as_view(), name="calendario"),
    path("panel/", PanelView.as_view(), name="panel"),
    path("reparto/", RepartoView.as_view(), name="reparto"),
    path("seguimiento/", SeguimientoView.as_view(), name="seguimiento"),
    path("parametros/", ParametrosView.as_view(), name="parametros"),
    path("reporte-ocupacion/", ReporteOcupacionView.as_view(), name="reporte-ocupacion"),
    path("", include(router.urls)),
]
