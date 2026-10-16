from django.db import migrations, models


class Migration(migrations.Migration):
    # Escrita a mano a propósito: `makemigrations` volvería a hornear la ruta local del almacenamiento privado
    # (ver CLAUDE.md, migraciones 0023/0025/0028).

    dependencies = [
        ('KeyServApp', '0035_minimizar_respuesta_bruta_pagos'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='eliminacion_solicitada_en',
            field=models.DateTimeField(blank=True, db_column='ELIMINACION_SOLICITADA_EN', null=True),
        ),
    ]
