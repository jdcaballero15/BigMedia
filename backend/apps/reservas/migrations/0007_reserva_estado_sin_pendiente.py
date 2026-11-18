from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reservas", "0006_reserva_sin_pendientes_datos")]

    operations = [
        migrations.RemoveField(model_name="parametrosdisponibilidad", name="tentativa_bloquea"),
        migrations.AlterField(
            model_name="reserva",
            name="estado",
            field=models.CharField(
                choices=[
                    ("confirmada", "Confirmada"),
                    ("finalizada", "Finalizada"),
                    ("cancelada", "Cancelada"),
                ],
                default="confirmada",
                max_length=12,
            ),
        ),
    ]
