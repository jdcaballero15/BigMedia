from django.urls import path

from .views import IngresosView

urlpatterns = [
    path("ingresos/", IngresosView.as_view(), name="ingresos"),
]
