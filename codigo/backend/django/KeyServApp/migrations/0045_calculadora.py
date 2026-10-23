import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    # Escrita a mano a propósito (ver 0036).

    dependencies = [
        ('KeyServApp', '0044_medicion_impacto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itempresupuesto',
            name='categoria',
            field=models.CharField(choices=[('MATERIAL', 'Materiales'), ('MANO_DE_OBRA', 'Tiempo y esfuerzo'), ('VIAJE', 'Gasto de viaje'), ('HERRAMIENTAS', 'Herramientas'), ('IMPREVISTOS', 'Imprevistos'), ('OTRO', 'Otro')], db_column='CATEGORIA', default='OTRO', max_length=12),
        ),
        migrations.AddField(
            model_name='itempresupuesto',
            name='cantidad',
            field=models.DecimalField(blank=True, db_column='CANTIDAD', decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='itempresupuesto',
            name='unidad',
            field=models.CharField(blank=True, db_column='UNIDAD', default='', max_length=20),
        ),
        migrations.AddField(
            model_name='itempresupuesto',
            name='precio_unitario',
            field=models.PositiveIntegerField(blank=True, db_column='PRECIO_UNITARIO', null=True),
        ),
        migrations.AddField(
            model_name='itempresupuesto',
            name='reutilizado',
            field=models.BooleanField(db_column='REUTILIZADO', default=False),
        ),
        migrations.CreateModel(
            name='PlantillaValorizacion',
            fields=[
                ('id_plantilla', models.BigAutoField(db_column='ID_PLANTILLA', primary_key=True, serialize=False)),
                ('nombre', models.CharField(db_column='NOMBRE', max_length=60)),
                ('tipo_trabajo', models.CharField(blank=True, db_column='TIPO_TRABAJO', default='', max_length=60)),
                ('datos', models.JSONField(db_column='DATOS')),
                ('creada_en', models.DateTimeField(auto_now_add=True, db_column='CREADA_EN')),
                ('actualizada_en', models.DateTimeField(auto_now=True, db_column='ACTUALIZADA_EN')),
                ('usuario', models.ForeignKey(db_column='FK_USUARIO', on_delete=django.db.models.deletion.CASCADE, related_name='plantillas_valorizacion', to='KeyServApp.usuario')),
            ],
            options={
                'verbose_name': 'Plantilla de valorización',
                'verbose_name_plural': 'Plantillas de valorización',
                'db_table': 'PLANTILLA_VALORIZACION',
                'ordering': ['nombre'],
                'constraints': [models.UniqueConstraint(fields=('usuario', 'nombre'), name='plantilla_nombre_unico_por_usuario')],
            },
        ),
        migrations.CreateModel(
            name='UsoCalculadora',
            fields=[
                ('id_uso', models.BigAutoField(db_column='ID_USO', primary_key=True, serialize=False)),
                ('periodo', models.CharField(db_column='PERIODO', max_length=7)),
                ('visitante', models.CharField(db_column='VISITANTE', max_length=64)),
                ('valorizaciones', models.PositiveIntegerField(db_column='VALORIZACIONES', default=0)),
                ('con_boleta', models.PositiveIntegerField(db_column='CON_BOLETA', default=0)),
                ('con_reutilizado', models.PositiveIntegerField(db_column='CON_REUTILIZADO', default=0)),
                ('actualizado_en', models.DateTimeField(auto_now=True, db_column='ACTUALIZADO_EN')),
            ],
            options={
                'verbose_name': 'Uso de la calculadora',
                'verbose_name_plural': 'Usos de la calculadora',
                'db_table': 'USO_CALCULADORA',
                'constraints': [models.UniqueConstraint(fields=('periodo', 'visitante'), name='uso_calculadora_unico_por_mes')],
            },
        ),
    ]
