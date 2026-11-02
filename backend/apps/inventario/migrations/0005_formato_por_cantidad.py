from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("inventario", "0004_permiso_cartel")]

    operations = [
        migrations.AddField(
            model_name="formato",
            name="por_cantidad",
            field=models.BooleanField(default=False),
        ),
    ]
