import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    # Escrita a mano a propósito (ver 0036): `makemigrations` volvería a hornear la ruta local del almacenamiento privado.

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('KeyServApp', '0039_codigoseguridad'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reembolso',
            fields=[
                ('id_reembolso', models.BigAutoField(db_column='ID_REEMBOLSO', primary_key=True, serialize=False)),
                ('monto', models.PositiveIntegerField(db_column='MONTO')),
                ('motivo', models.CharField(choices=[('PAGO_TARDIO', 'Pago aprobado sobre una contratación ya cancelada'), ('CANCELACION', 'El cliente pidió cancelar un trabajo ya pagado')], db_column='MOTIVO', max_length=12)),
                ('detalle', models.CharField(blank=True, db_column='DETALLE', max_length=300)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('REEMBOLSADO', 'Reembolsado'), ('RECHAZADO', 'Rechazado')], db_column='ESTADO', default='PENDIENTE', max_length=12)),
                ('creado_en', models.DateTimeField(auto_now_add=True, db_column='CREADO_EN')),
                ('resuelto_en', models.DateTimeField(blank=True, db_column='RESUELTO_EN', null=True)),
                ('referencia', models.CharField(blank=True, db_column='REFERENCIA', max_length=120)),
                ('pago', models.ForeignKey(db_column='FK_PAGO', on_delete=django.db.models.deletion.PROTECT, related_name='reembolsos', to='KeyServApp.pago')),
                ('resuelto_por', models.ForeignKey(blank=True, db_column='FK_RESUELTO_POR', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reembolsos_resueltos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Reembolso',
                'verbose_name_plural': 'Reembolsos',
                'db_table': 'REEMBOLSO',
                'ordering': ['-creado_en'],
            },
        ),
    ]
