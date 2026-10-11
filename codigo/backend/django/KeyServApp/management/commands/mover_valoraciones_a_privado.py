"""
Mueve las fotos de reseñas que quedaron en MEDIA_ROOT (públicas) al almacenamiento
privado, tras pasar `ValoracionImagen.archivo` a `almacenamiento_documentos`.
Idempotente: ignora lo que ya está en privado o no existe.
"""
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

from KeyServApp.models import ValoracionImagen


class Command(BaseCommand):
    help = 'Mueve fotos de reseñas de MEDIA_ROOT a PRIVATE_MEDIA_ROOT (--dry-run para solo listar).'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        movidos = 0
        for img in ValoracionImagen.objects.exclude(archivo=''):
            origen = settings.MEDIA_ROOT / img.archivo.name
            destino = settings.PRIVATE_MEDIA_ROOT / img.archivo.name
            if not origen.exists() or destino.exists():
                continue
            self.stdout.write(f'{origen} -> {destino}')
            if not opts['dry_run']:
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(origen), str(destino))
            movidos += 1
        self.stdout.write(self.style.SUCCESS(f'{movidos} archivo(s) {"a mover" if opts["dry_run"] else "movidos"}.'))
