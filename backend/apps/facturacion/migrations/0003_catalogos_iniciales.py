from django.db import migrations

SECTORES = ["Gobierno", "Privado"]
TIPOS_VENTA = ["F", "V"]


def cargar(apps, schema_editor):
    database = schema_editor.connection.alias
    for modelo, nombres in (("Sector", SECTORES), ("TipoVenta", TIPOS_VENTA)):
        Modelo = apps.get_model("facturacion", modelo)
        for nombre in nombres:
            Modelo.objects.using(database).get_or_create(nombre=nombre)


class Migration(migrations.Migration):
    dependencies = [("facturacion", "0002_items_a_facturar")]
    operations = [migrations.RunPython(cargar, migrations.RunPython.noop)]
