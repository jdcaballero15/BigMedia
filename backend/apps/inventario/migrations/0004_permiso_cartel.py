from django.db import migrations


def asignar_permisos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    database = schema_editor.connection.alias
    group, _ = Group.objects.using(database).get_or_create(name="Operativo")
    content_type, _ = ContentType.objects.using(database).get_or_create(
        app_label="inventario", model="cartel"
    )
    for action in ("view", "add", "change"):
        permission, _ = Permission.objects.using(database).get_or_create(
            content_type=content_type,
            codename=f"{action}_cartel",
            defaults={"name": f"Can {action} cartel"},
        )
        group.permissions.add(permission)


class Migration(migrations.Migration):
    dependencies = [
        ("inventario", "0003_cartel"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    operations = [migrations.RunPython(asignar_permisos, migrations.RunPython.noop)]
