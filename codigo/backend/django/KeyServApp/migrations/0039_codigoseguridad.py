import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    # Escrita a mano a propósito (ver 0036): `makemigrations` volvería a hornear la ruta local del almacenamiento privado.

    dependencies = [
        ('KeyServApp', '0038_pago_flow_mercadopago'),
    ]

    operations = [
        migrations.CreateModel(
            name='CodigoSeguridad',
            fields=[
                ('id_codigo', models.BigAutoField(db_column='ID_CODIGO', primary_key=True, serialize=False)),
                ('proposito', models.CharField(choices=[('CERRAR_SESIONES', 'Cerrar sesión en todos los dispositivos')], db_column='PROPOSITO', max_length=20)),
                ('codigo_hash', models.CharField(db_column='CODIGO_HASH', max_length=64)),
                ('expira_en', models.DateTimeField(db_column='EXPIRA_EN')),
                ('intentos', models.PositiveSmallIntegerField(db_column='INTENTOS', default=0)),
                ('creado_en', models.DateTimeField(auto_now_add=True, db_column='CREADO_EN')),
                ('usuario', models.ForeignKey(db_column='FK_USUARIO', on_delete=django.db.models.deletion.CASCADE, related_name='codigos_seguridad', to='KeyServApp.usuario')),
            ],
            options={
                'verbose_name': 'Código de seguridad',
                'verbose_name_plural': 'Códigos de seguridad',
                'db_table': 'CODIGO_SEGURIDAD',
            },
        ),
    ]
