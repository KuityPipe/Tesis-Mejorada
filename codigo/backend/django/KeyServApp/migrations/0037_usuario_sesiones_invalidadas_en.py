from django.db import migrations, models


class Migration(migrations.Migration):
    # Escrita a mano a propósito (ver 0036): `makemigrations` volvería a hornear la ruta local del almacenamiento privado.

    dependencies = [
        ('KeyServApp', '0036_usuario_eliminacion_solicitada_en'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='sesiones_invalidadas_en',
            field=models.DateTimeField(blank=True, db_column='SESIONES_INVALIDADAS_EN', null=True),
        ),
    ]
