from django.db import migrations


FORMATOS = (
    ("PPL/Gran Formato", "fija"),
    ("Banderolas", "fija"),
    ("Séxtuples", "fija"),
    ("LED", "digital"),
    ("Mediano Formato", "fija"),
    ("Monocolumnas", "fija"),
    ("Carteleras", "fija"),
)
ZONAS = (
    "Ciudad", "Godoy Cruz", "Maipú", "Luján de Cuyo", "Guaymallén",
    "Las Heras", "San Martín", "Rivadavia", "San Carlos",
)
ESTADOS = (
    ("activo", "Activo", True, False),
    ("mantenimiento", "En mantenimiento", False, False),
    ("baja", "De baja", False, True),
    ("apagado", "Apagado", False, False),
    ("vidrio_destruido", "Vidrio destruido", False, False),
)


def sembrar_catalogos(apps, schema_editor):
    Formato = apps.get_model("inventario", "Formato")
    Zona = apps.get_model("inventario", "Zona")
    EstadoCartel = apps.get_model("inventario", "EstadoCartel")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    database = schema_editor.connection.alias

    for nombre, modalidad in FORMATOS:
        Formato.objects.using(database).get_or_create(
            nombre=nombre,
            defaults={"modalidad": modalidad, "capacidad_predeterminada": 1},
        )
    for nombre in ZONAS:
        Zona.objects.using(database).get_or_create(nombre=nombre)
    for codigo, nombre, operativo, es_baja in ESTADOS:
        EstadoCartel.objects.using(database).get_or_create(
            codigo=codigo,
            defaults={"nombre": nombre, "operativo": operativo, "es_baja": es_baja},
        )

    grupo, _ = Group.objects.using(database).get_or_create(name="Operativo")
    for model_name in ("proveedor", "formato", "zona", "estadocartel"):
        content_type, _ = ContentType.objects.using(database).get_or_create(
            app_label="inventario", model=model_name
        )
        for action in ("view", "add", "change"):
            permission, _ = Permission.objects.using(database).get_or_create(
                content_type=content_type,
                codename=f"{action}_{model_name}",
                defaults={"name": f"Can {action} {model_name}"},
            )
            grupo.permissions.add(permission)


class Migration(migrations.Migration):
    dependencies = [
        ("inventario", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    operations = [migrations.RunPython(sembrar_catalogos, migrations.RunPython.noop)]
