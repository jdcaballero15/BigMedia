"""Señales de clientes para las apps que no pueden ser importadas desde acá (ADR-0010)."""

from django.dispatch import Signal

# Una marca pasó a otro cliente. Argumentos: `marca` (ya guardada) y `cliente_anterior`.
# Se emite dentro de la transacción que guarda la marca; la escucha `campanias` (HU-027).
cliente_de_marca_cambiado = Signal()
