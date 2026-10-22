from django.urls import path

from .views import IngresosView, PorRubroView

urlpatterns = [
    path("ingresos/", IngresosView.as_view(), name="ingresos"),
    path("por-rubro/", PorRubroView.as_view(), name="por-rubro"),
]
