"""
Retención de datos de seguridad y sesiones:

- `IntentoAccesoSospechoso` (IP, ciudad, país, user-agent) más viejos que --dias-seguridad (365).
- `TokenSesion` expirados o revocados hace más de --dias-sesiones (30).

Pensado para correr periódicamente (ver `mantenimiento_retencion`, que lo junta con
`limpiar_mensajes_antiguos`). Los plazos son propuestas técnicas, a validar con asesoría legal.

    python manage.py purgar_datos_vencidos --dry-run
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from KeyServApp.models import IntentoAccesoSospechoso, TokenSesion


class Command(BaseCommand):
    help = 'Borra intentos sospechosos y tokens de sesión vencidos.'

    def add_arguments(self, parser):
        parser.add_argument('--dias-seguridad', type=int, default=365)
        parser.add_argument('--dias-sesiones', type=int, default=30)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        ahora = timezone.now()
        intentos = IntentoAccesoSospechoso.objects.filter(fecha__lt=ahora - timedelta(days=opts['dias_seguridad']))
        limite_sesion = ahora - timedelta(days=opts['dias_sesiones'])
        tokens = TokenSesion.objects.filter(Q(expira_en__lt=limite_sesion) | Q(revocado_en__lt=limite_sesion))

        n_intentos, n_tokens = intentos.count(), tokens.count()
        if opts['dry_run']:
            self.stdout.write(f'Se borrarían {n_intentos} intentos sospechosos y {n_tokens} tokens (dry-run).')
            return
        intentos.delete()
        tokens.delete()
        self.stdout.write(self.style.SUCCESS(f'Borrados {n_intentos} intentos sospechosos y {n_tokens} tokens de sesión.'))
