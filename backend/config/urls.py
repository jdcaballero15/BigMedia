"""Routes for the Big Media API."""

from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from config.health import health


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("", TemplateView.as_view(template_name="index.html"), name="spa"),
]
