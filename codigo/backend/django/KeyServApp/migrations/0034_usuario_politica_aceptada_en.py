from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('KeyServApp', '0033_verificacion_vigencia_eventos_solicitudes'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='politica_aceptada_en',
            field=models.DateTimeField(blank=True, db_column='POLITICA_ACEPTADA_EN', null=True),
        ),
    ]
