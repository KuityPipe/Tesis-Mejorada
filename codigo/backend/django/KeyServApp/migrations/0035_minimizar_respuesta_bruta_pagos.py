from django.db import migrations

from KeyServApp.respuestas_pago import respuesta_minima


def minimizar(apps, schema_editor):
    """Deja en los pagos ya guardados solo los campos permitidos (se descartan tarjeta, pagador, banco y enlaces)."""
    Pago = apps.get_model('KeyServApp', 'Pago')
    for pago in Pago.objects.exclude(respuesta_bruta__isnull=True):
        minima = respuesta_minima(pago.respuesta_bruta)
        if minima != pago.respuesta_bruta:
            pago.respuesta_bruta = minima
            pago.save(update_fields=['respuesta_bruta'])


class Migration(migrations.Migration):

    dependencies = [
        ('KeyServApp', '0034_usuario_politica_aceptada_en'),
    ]

    operations = [
        # Irreversible a propósito: lo descartado era dato de terceros que no debe volver a guardarse.
        migrations.RunPython(minimizar, migrations.RunPython.noop),
    ]
