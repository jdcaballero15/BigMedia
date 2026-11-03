from django.apps import AppConfig


class CampaniasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.campanias"
    verbose_name = "Campañas"

    def ready(self) -> None:
        # Conecta los receptores de señales de otras apps (ADR-0010).
        from . import signals  # noqa: F401
