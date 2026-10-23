"""Carga datos de ejemplo para staging: un primer lote chico y el lote demo (`_datos_demo`).

Nunca corre en producción (guarda explícita) y nunca usa datos reales: todo es inventado. Es
idempotente, así que puede correr en cada arranque del servicio de staging sin duplicar.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca
from apps.inventario.models import Cartel, EstadoCartel, Formato, Zona
from apps.reservas.models import Reserva

from . import _datos_demo

# Cliente que marca que los datos de ejemplo ya se cargaron (idempotencia).
SENTINELA = "Agencia Norte"


class Command(BaseCommand):
    help = "Crea datos de ejemplo para staging. No corre en producción."

    def handle(self, *_args: object, **_options: object) -> None:
        if settings.PRODUCTION:
            raise CommandError("No se cargan datos de ejemplo en producción.")
        if Cliente.objects.filter(nombre=SENTINELA).exists():
            self.stdout.write("Los datos de ejemplo ya existen.")
        else:
            self._crear()
            self.stdout.write("Datos de ejemplo creados.")
        if _datos_demo.cargar():
            self.stdout.write("Datos de demo creados.")
        else:
            self.stdout.write("Los datos de demo ya existen.")

    def _crear(self) -> None:
        led = Formato.objects.filter(modalidad="digital").first()
        fija = Formato.objects.filter(modalidad="fija").first()
        if led is None or fija is None:
            raise CommandError("Faltan los catálogos base (formatos).")
        activo = EstadoCartel.objects.get(codigo="activo")
        ciudad = Zona.objects.get(nombre="Ciudad")
        maipu = Zona.objects.get(nombre="Maipú")
        carteles = [
            Cartel.objects.create(
                formato=formato,
                zona=zona,
                estado=activo,
                direccion=direccion,
                capacidad=capacidad,
                tarifa_lista="100000.00",
            )
            for formato, zona, direccion, capacidad in (
                (led, ciudad, "Av. San Martín 1000", 6),
                (fija, ciudad, "Acceso Este 2500", 1),
                (led, maipu, "Ruta 60 km 5", 4),
                (fija, maipu, "Carril Rodríguez Peña 800", 1),
            )
        ]

        norte = Cliente.objects.create(nombre=SENTINELA, tipo=Cliente.Tipo.INTERMEDIARIO)
        directo = Cliente.objects.create(nombre="Comercio Directo", tipo=Cliente.Tipo.DIRECTO)
        bebida = Marca.objects.create(nombre="Bebida Fresca", cliente=norte)
        moda = Marca.objects.create(nombre="Moda Urbana", cliente=norte)
        pan = Marca.objects.create(nombre="Panadería del Barrio", cliente=directo)

        primero = timezone.localdate().replace(day=1)
        self._reservar(carteles[0], bebida, primero - timedelta(days=40), primero + timedelta(days=50), "900000.00")  # fmt: skip
        self._reservar(carteles[1], moda, primero, primero + timedelta(days=27), "250000.00")
        self._reservar(carteles[2], pan, primero - timedelta(days=5), primero + timedelta(days=9), "80000.00")  # fmt: skip
        self._reservar(carteles[3], bebida, primero + timedelta(days=5), primero + timedelta(days=35), "150000.00")  # fmt: skip

    @staticmethod
    def _reservar(cartel: Cartel, marca: Marca, inicio: date, fin: date, total: str) -> None:
        reserva = Reserva(
            campania=Campania.objects.create(marca=marca),
            cartel=cartel,
            fecha_inicio=inicio,
            fecha_fin=fin,
            precio_alquiler=Decimal(total),
            estado=Reserva.Estado.CONFIRMADA,
        )
        reserva.save()
