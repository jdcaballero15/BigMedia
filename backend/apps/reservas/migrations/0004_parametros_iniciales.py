from django.db import migrations


def crear_fila(apps, schema_editor):
    # Valores provisorios de RN-001 y RN-002, los mismos que regían por variable de entorno.
    Parametros = apps.get_model("reservas", "ParametrosDisponibilidad")
    Parametros.objects.using(schema_editor.connection.alias).get_or_create(
        pk=1, defaults={"borde_inclusivo": True, "tentativa_bloquea": False}
    )


class Migration(migrations.Migration):
    dependencies = [("reservas", "0003_parametros_disponibilidad")]
    operations = [migrations.RunPython(crear_fila, migrations.RunPython.noop)]
