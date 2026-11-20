from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("campanias", "0006_orden_publicidad")]

    operations = [
        migrations.AlterField(
            model_name="interaccion",
            name="asunto",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
