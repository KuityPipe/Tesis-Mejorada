# encoding_facial pasa de jsonb en claro a texto cifrado (KeyServApp/campos.py).
# El AlterField convierte la columna a texto conservando el JSON; luego RunPython
# re-guarda cada fila con valor para que quede cifrada.
import KeyServApp.campos
from django.db import migrations


def cifrar_existentes(apps, schema_editor):
    Usuario = apps.get_model('KeyServApp', 'Usuario')
    for usuario in Usuario.objects.exclude(encoding_facial__isnull=True):
        # from_db_value leyó el JSON en claro; save() lo vuelve a escribir cifrado.
        Usuario.objects.filter(pk=usuario.pk).update(encoding_facial=usuario.encoding_facial)


class Migration(migrations.Migration):

    dependencies = [
        ('KeyServApp', '0030_consentimiento_biometrico'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='encoding_facial',
            field=KeyServApp.campos.CampoJSONCifrado(blank=True, db_column='ENCODING_FACIAL', null=True),
        ),
        migrations.RunPython(cifrar_existentes, migrations.RunPython.noop),
    ]
