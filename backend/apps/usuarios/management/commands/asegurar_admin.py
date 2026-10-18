"""Crea el primer superusuario a partir de variables de entorno, si todavía no existe.

Pensado para entornos sin consola (Render gratis): corre en cada arranque y no hace nada
si el usuario ya existe, así una contraseña cambiada desde el admin no se pisa.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crea el superusuario de DJANGO_SUPERUSER_USERNAME si no existe."

    def handle(self, *_args: object, **_options: object) -> None:
        usuario = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        if not usuario:
            self.stdout.write("Sin DJANGO_SUPERUSER_USERNAME: no se crea administrador.")
            return

        modelo = get_user_model()
        if modelo.objects.filter(username=usuario).exists():
            self.stdout.write(f"El administrador {usuario} ya existe.")
            return

        clave = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        if not clave:
            raise CommandError("Falta DJANGO_SUPERUSER_PASSWORD para crear el administrador.")

        modelo.objects.create_superuser(
            username=usuario,
            email=os.environ.get("DJANGO_SUPERUSER_EMAIL", ""),
            password=clave,
        )
        self.stdout.write(f"Administrador {usuario} creado.")
