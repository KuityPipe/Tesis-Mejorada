from django.db import migrations, models


class Migration(migrations.Migration):
    # Escrita a mano a propósito (ver 0036): makemigrations volvería a hornear la ruta local del almacenamiento privado.

    dependencies = [
        ('KeyServApp', '0043_verificacion_video_consentimiento_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='situacion_laboral_previa',
            field=models.CharField(blank=True, choices=[('SIN_TRABAJO', 'Sin trabajo'), ('INFORMAL', 'Trabajo informal (sin contrato ni boleta)'), ('FORMAL', 'Trabajo formal (con contrato o boletas)'), ('ESTUDIANTE', 'Estudiante'), ('NO_DICE', 'Prefiero no decir')], db_column='SITUACION_LABORAL_PREVIA', default='', max_length=12),
        ),
        migrations.AddField(
            model_name='usuario',
            name='genero',
            field=models.CharField(blank=True, choices=[('MUJER', 'Mujer'), ('HOMBRE', 'Hombre'), ('OTRO', 'Otro'), ('NO_DICE', 'Prefiero no decir')], db_column='GENERO', default='', max_length=8),
        ),
        migrations.AddField(
            model_name='publicaciones',
            name='tipo_servicio',
            field=models.CharField(choices=[('REPARACION', 'Reparación'), ('MANTENCION', 'Mantención'), ('INSTALACION_NUEVA', 'Instalación nueva'), ('OTRO', 'Otro')], db_column='TIPO_SERVICIO', default='OTRO', max_length=18),
        ),
        migrations.AddField(
            model_name='valoracion',
            name='evito_reemplazo',
            field=models.CharField(blank=True, choices=[('SI', 'Sí'), ('NO', 'No'), ('NO_APLICA', 'No aplica')], db_column='EVITO_REEMPLAZO', default='', max_length=10),
        ),
    ]
