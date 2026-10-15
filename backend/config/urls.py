"""Routes for the Big Media API."""

from django.contrib import admin
from django.urls import include, path

from config.auth_views import login_view, logout_view, me
from config.health import health


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/me/", me, name="me"),
    path("api/auth/login/", login_view, name="login"),
    path("api/auth/logout/", logout_view, name="logout"),
    path("api/inventario/", include("apps.inventario.urls")),
]
