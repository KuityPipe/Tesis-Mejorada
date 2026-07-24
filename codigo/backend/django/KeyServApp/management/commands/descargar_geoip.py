"""
Descarga (o actualiza) la base de datos GeoIP local — DB-IP City Lite,
gratuita y sin necesidad de crear cuenta (a diferencia de MaxMind GeoLite2,
que desde 2020 exige registrarse y generar una license key para descargarla).
Licencia CC-BY 4.0: hay que atribuir a DB-IP.com donde se muestren
resultados (ver el pie del panel de IntentoAccesoSospechoso en /admin/).

La fuente se actualiza mensualmente sola — no hace falta correr esto muy
seguido, pero conviene tenerlo como comando en vez de depender de que
alguien la haya bajado a mano una vez y se quede desactualizada para siempre.

Correr con: python manage.py descargar_geoip
"""
import gzip
import os
import shutil
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand

URL_DESCARGA = 'https://cdn.jsdelivr.net/npm/dbip-city-lite/dbip-city-lite.mmdb.gz'


class Command(BaseCommand):
    help = 'Descarga/actualiza la base de datos GeoIP local (DB-IP City Lite, gratuita, sin cuenta).'

    def handle(self, *args, **options):
        destino = str(settings.GEOIP_DB_PATH)
        destino_gz = destino + '.gz'
        os.makedirs(os.path.dirname(destino), exist_ok=True)

        self.stdout.write(f'Descargando {URL_DESCARGA} ...')
        urllib.request.urlretrieve(URL_DESCARGA, destino_gz)

        self.stdout.write('Descomprimiendo...')
        with gzip.open(destino_gz, 'rb') as f_in, open(destino, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove(destino_gz)

        self.stdout.write(self.style.SUCCESS(f'Base GeoIP actualizada en {destino}'))
