from django.db import migrations, models


class Migration(migrations.Migration):
    # Escrita a mano a propósito (ver 0036): `makemigrations` volvería a hornear la ruta local del almacenamiento privado.

    dependencies = [
        ('KeyServApp', '0037_usuario_sesiones_invalidadas_en'),
    ]

    operations = [
        migrations.AddField(
            model_name='pago',
            name='referencia_externa',
            field=models.CharField(blank=True, db_column='REFERENCIA_EXTERNA', max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='pago',
            name='metodo',
            field=models.CharField(
                choices=[('WEBPAY', 'Webpay Plus'), ('KHIPU', 'Khipu'), ('FLOW', 'Flow'), ('MERCADOPAGO', 'Mercado Pago')],
                db_column='METODO', max_length=12,
            ),
        ),
    ]
