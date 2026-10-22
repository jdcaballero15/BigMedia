from django.db import migrations


def crear_grupo(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    database = schema_editor.connection.alias
    Group.objects.using(database).get_or_create(name="Gerencia")


class Migration(migrations.Migration):
    initial = True
    dependencies = [("auth", "0012_alter_user_first_name_max_length")]
    operations = [migrations.RunPython(crear_grupo, migrations.RunPython.noop)]
