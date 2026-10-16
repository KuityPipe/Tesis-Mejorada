from django.db import migrations, models


class Migration(migrations.Migration):
    # Escrita a mano a propósito (ver 0036): `makemigrations` volvería a hornear la ruta local del almacenamiento privado.

    dependencies = [
        ('KeyServApp', '0040_reembolso'),
    ]

    operations = [
        migrations.AddField(
            model_name='pago',
            name='monto_servicio',
            field=models.PositiveIntegerField(blank=True, db_column='MONTO_SERVICIO', null=True),
        ),
        migrations.AddField(
            model_name='pago',
            name='comision_porcentaje',
            field=models.DecimalField(blank=True, db_column='COMISION_PORCENTAJE', decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='pago',
            name='comision_monto',
            field=models.PositiveIntegerField(db_column='COMISION_MONTO', default=0),
        ),
    ]
