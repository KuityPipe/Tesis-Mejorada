from django.db import migrations, models

import KeyServApp.storage
import KeyServApp.validators


class Migration(migrations.Migration):
    # Escrita a mano a propósito (ver 0036). A diferencia de 0023/0025/0028, referencia el almacenamiento privado por su
    # objeto en vez de hornear la ruta local, así no genera diferencias entre máquinas.

    dependencies = [
        ('KeyServApp', '0041_pago_comision'),
    ]

    operations = [
        migrations.AddField(
            model_name='verificacionalternativa',
            name='video',
            field=models.FileField(blank=True, db_column='VIDEO', null=True, storage=KeyServApp.storage.almacenamiento_documentos, upload_to='verificacion/videos/', validators=[KeyServApp.validators.validar_video]),
        ),
        migrations.AddField(
            model_name='verificacionalternativa',
            name='video_subido_en',
            field=models.DateTimeField(blank=True, db_column='VIDEO_SUBIDO_EN', null=True),
        ),
        migrations.AddField(
            model_name='verificacionalternativa',
            name='codigo_video',
            field=models.CharField(blank=True, db_column='CODIGO_VIDEO', max_length=4),
        ),
        migrations.AddField(
            model_name='verificacionalternativa',
            name='video_consentimiento_en',
            field=models.DateTimeField(blank=True, db_column='VIDEO_CONSENTIMIENTO_EN', null=True),
        ),
    ]
