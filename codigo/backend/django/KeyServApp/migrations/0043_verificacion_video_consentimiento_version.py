from django.db import migrations, models


class Migration(migrations.Migration):
    # Escrita a mano a propósito (ver 0036).

    dependencies = [
        ('KeyServApp', '0042_verificacion_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='verificacionalternativa',
            name='video_consentimiento_version',
            field=models.CharField(blank=True, db_column='VIDEO_CONSENTIMIENTO_VERSION', max_length=20),
        ),
    ]
