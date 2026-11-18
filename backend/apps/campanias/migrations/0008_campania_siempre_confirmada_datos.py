"""Las campañas Cotizadas y Perdidas pasan a Canceladas (HU-024, 2026-11-17).

La campaña ahora nace Confirmada y solo puede pasar a Cancelada. No tiene vuelta atrás: el reverse
no hace nada, porque no se sabe cuáles eran Cotizadas y cuáles Perdidas.
"""

from typing import Any

from django.db import migrations


def cotizadas_y_perdidas_a_canceladas(apps: Any, schema_editor: Any) -> None:
    campania = apps.get_model("campanias", "Campania")
    campania.objects.filter(estado__in=("cotizada", "perdida")).update(estado="cancelada")


class Migration(migrations.Migration):
    dependencies = [("campanias", "0007_interaccion_asunto_opcional")]

    operations = [
        migrations.RunPython(cotizadas_y_perdidas_a_canceladas, migrations.RunPython.noop),
    ]
