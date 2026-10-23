from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DefinirClaveView, UsuarioViewSet

router = DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuario")

urlpatterns = [
    path("definir-clave/", DefinirClaveView.as_view(), name="definir-clave"),
    path("", include(router.urls)),
]
