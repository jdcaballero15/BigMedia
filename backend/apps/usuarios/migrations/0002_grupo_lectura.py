from django.db import migrations


def crear_grupo(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    database = schema_editor.connection.alias
    Group.objects.using(database).get_or_create(name="Lectura")


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0001_intentoingreso"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    operations = [migrations.RunPython(crear_grupo, migrations.RunPython.noop)]
