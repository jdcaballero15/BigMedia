from django.db import migrations


def asignar_permisos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    database = schema_editor.connection.alias
    group, _ = Group.objects.using(database).get_or_create(name="Operativo")
    content_type, _ = ContentType.objects.using(database).get_or_create(
        app_label="reservas", model="reserva"
    )
    for action in ("view", "add", "change"):
        permission, _ = Permission.objects.using(database).get_or_create(
            content_type=content_type,
            codename=f"{action}_reserva",
            defaults={"name": f"Can {action} reserva"},
        )
        group.permissions.add(permission)


class Migration(migrations.Migration):
    dependencies = [
        ("reservas", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    operations = [migrations.RunPython(asignar_permisos, migrations.RunPython.noop)]
