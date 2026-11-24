"""Las reservas Pendientes pasan a Canceladas (HU-035, 2026-11-17).

Toda reserva nace Confirmada y no existe Pendiente. Corre después de cancelar las campañas
Cotizadas y Perdidas. No tiene vuelta atrás: el reverse no hace nada, porque no se sabe cuáles
eran Pendientes.
"""

from typing import Any

from django.db import migrations


def pendientes_a_canceladas(apps: Any, schema_editor: Any) -> None:
    reserva = apps.get_model("reservas", "Reserva")
    reserva.objects.filter(estado="pendiente").update(estado="cancelada")


class Migration(migrations.Migration):
    dependencies = [
        ("reservas", "0005_parametros_fecha_pasada"),
        ("campanias", "0008_campania_siempre_confirmada_datos"),
    ]

    operations = [
        migrations.RunPython(pendientes_a_canceladas, migrations.RunPython.noop),
    ]
