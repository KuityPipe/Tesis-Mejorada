import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    # Escrita a mano a propósito (ver 0036).

    dependencies = [
        ('KeyServApp', '0045_calculadora'),
    ]

    operations = [
        migrations.CreateModel(
            name='BoletaHonorarios',
            fields=[
                ('id_boleta', models.BigAutoField(db_column='ID_BOLETA', primary_key=True, serialize=False)),
                ('folio', models.CharField(db_column='FOLIO', max_length=12)),
                ('fecha_emision', models.DateField(blank=True, db_column='FECHA_EMISION', null=True)),
                ('es_primera_boleta', models.BooleanField(db_column='ES_PRIMERA_BOLETA', default=False)),
                ('registrada_en', models.DateTimeField(auto_now_add=True, db_column='REGISTRADA_EN')),
                ('actualizada_en', models.DateTimeField(auto_now=True, db_column='ACTUALIZADA_EN')),
                ('contratacion', models.OneToOneField(db_column='FK_CONTRATACION', on_delete=django.db.models.deletion.CASCADE, related_name='boleta', to='KeyServApp.contratacion')),
                ('proveedor', models.ForeignKey(db_column='FK_PROVEEDOR', on_delete=django.db.models.deletion.CASCADE, related_name='boletas_registradas', to='KeyServApp.usuario')),
            ],
            options={
                'verbose_name': 'Boleta de honorarios (folio)',
                'verbose_name_plural': 'Boletas de honorarios (folios)',
                'db_table': 'BOLETA_HONORARIOS',
                'constraints': [models.UniqueConstraint(fields=('proveedor', 'folio'), name='boleta_folio_unico_por_proveedor')],
            },
        ),
    ]
