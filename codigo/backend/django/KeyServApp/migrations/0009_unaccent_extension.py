from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('KeyServApp', '0008_alter_areaadministrativa_options_and_more'),
    ]

    operations = [
        UnaccentExtension(),
    ]
