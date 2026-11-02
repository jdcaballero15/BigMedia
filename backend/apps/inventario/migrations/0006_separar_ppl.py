from django.db import migrations

CIRCUITOS = ("Séxtuples", "Banderolas")


def separar_ppl(apps, schema_editor):
    """Marca los circuitos, renombra «PPL/Gran Formato» y crea PPL (HU-009, RN-005)."""
    Formato = apps.get_model("inventario", "Formato")
    database = schema_editor.connection.alias
    formatos = Formato.objects.using(database)
    formatos.filter(nombre__in=CIRCUITOS).update(por_cantidad=True)
    if not formatos.filter(nombre__iexact="Gran Formato").exists():
        formatos.filter(nombre="PPL/Gran Formato").update(nombre="Gran Formato")
    ppl, _ = formatos.get_or_create(
        nombre__iexact="PPL",
        defaults={
            "nombre": "PPL",
            "modalidad": "fija",
            "capacidad_predeterminada": 1,
            "por_cantidad": True,
        },
    )
    if not ppl.por_cantidad:
        ppl.por_cantidad = True
        ppl.save(update_fields=["por_cantidad"])


def juntar_ppl(apps, schema_editor):
    Formato = apps.get_model("inventario", "Formato")
    database = schema_editor.connection.alias
    formatos = Formato.objects.using(database)
    formatos.filter(nombre="PPL", carteles__isnull=True).delete()
    if not formatos.filter(nombre="PPL/Gran Formato").exists():
        formatos.filter(nombre="Gran Formato").update(nombre="PPL/Gran Formato")


class Migration(migrations.Migration):
    dependencies = [("inventario", "0005_formato_por_cantidad")]

    operations = [migrations.RunPython(separar_ppl, juntar_ppl)]
