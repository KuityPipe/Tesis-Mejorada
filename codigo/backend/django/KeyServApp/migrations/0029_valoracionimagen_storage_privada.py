# Fotos de reseñas pasan a almacenamiento privado. Referencia el objeto de storage real
# (no una ruta absoluta de la máquina que generó la migración). Archivos existentes:
# `manage.py mover_valoraciones_a_privado`.
import KeyServApp.storage
import KeyServApp.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('KeyServApp', '0028_mensaje_imagen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='valoracionimagen',
            name='archivo',
            field=models.ImageField(db_column='ARCHIVO', storage=KeyServApp.storage.almacenamiento_documentos, upload_to='valoraciones/imagenes/', validators=[KeyServApp.validators.validar_imagen]),
        ),
    ]
