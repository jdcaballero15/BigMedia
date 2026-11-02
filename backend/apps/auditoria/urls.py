from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RegistroAuditoriaViewSet, UsuariosView

router = DefaultRouter()
router.register("registros", RegistroAuditoriaViewSet, basename="registro-auditoria")

urlpatterns = [
    path("usuarios/", UsuariosView.as_view(), name="auditoria-usuarios"),
    path("", include(router.urls)),
]
