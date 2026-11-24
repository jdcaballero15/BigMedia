from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("campanias", "0008_campania_siempre_confirmada_datos")]

    operations = [
        migrations.AlterField(
            model_name="campania",
            name="estado",
            field=models.CharField(
                choices=[("confirmada", "Confirmada"), ("cancelada", "Cancelada")],
                default="confirmada",
                max_length=12,
            ),
        ),
    ]
