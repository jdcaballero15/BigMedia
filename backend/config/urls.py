"""Routes for the Big Media API."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from config.auth_views import login_view, logout_view, me
from config.health import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/me/", me, name="me"),
    path("api/auth/login/", login_view, name="login"),
    path("api/auth/logout/", logout_view, name="logout"),
    path("api/inventario/", include("apps.inventario.urls")),
    path("api/clientes/", include("apps.clientes.urls")),
    path("api/campanias/", include("apps.campanias.urls")),
    path("", TemplateView.as_view(template_name="index.html"), name="spa"),
]
