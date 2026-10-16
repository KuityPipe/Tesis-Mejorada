"""
Retención de datos de seguridad y sesiones:

- `IntentoAccesoSospechoso` (IP, ciudad, país, user-agent) más viejos que --dias-seguridad (365).
- `EventoVerificacion` (auditoría de verificaciones) más viejos que --dias-eventos (365).
- `TokenSesion` expirados o revocados hace más de --dias-sesiones (30).
- Cuentas que pidieron eliminarse hace más de --dias-eliminacion (`settings.CUENTA_ELIMINACION_DIAS`, 15): se anonimizan.

Pensado para correr periódicamente (ver `mantenimiento_retencion`, que lo junta con
`limpiar_mensajes_antiguos`). Los plazos son propuestas técnicas, a validar con asesoría legal.

    python manage.py purgar_datos_vencidos --dry-run
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from KeyServApp import derechos_titular
from KeyServApp.models import EventoVerificacion, IntentoAccesoSospechoso, TokenSesion


class Command(BaseCommand):
    help = 'Borra intentos sospechosos y tokens de sesión vencidos.'

    def add_arguments(self, parser):
        parser.add_argument('--dias-seguridad', type=int, default=365)
        parser.add_argument('--dias-sesiones', type=int, default=30)
        parser.add_argument('--dias-eventos', type=int, default=365)
        parser.add_argument('--dias-eliminacion', type=int, default=None, help='Por defecto settings.CUENTA_ELIMINACION_DIAS.')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        ahora = timezone.now()
        intentos = IntentoAccesoSospechoso.objects.filter(fecha__lt=ahora - timedelta(days=opts['dias_seguridad']))
        limite_sesion = ahora - timedelta(days=opts['dias_sesiones'])
        tokens = TokenSesion.objects.filter(Q(expira_en__lt=limite_sesion) | Q(revocado_en__lt=limite_sesion))

        eventos = EventoVerificacion.objects.filter(fecha__lt=ahora - timedelta(days=opts['dias_eventos']))
        n_intentos, n_tokens, n_eventos = intentos.count(), tokens.count(), eventos.count()
        if opts['dry_run']:
            n_cuentas = derechos_titular.anonimizar_cuentas_vencidas(opts['dias_eliminacion'], dry_run=True)
            self.stdout.write(f'Se borrarían {n_intentos} intentos sospechosos, {n_tokens} tokens y {n_eventos} eventos de verificación, y se anonimizarían {n_cuentas} cuentas (dry-run).')
            return
        intentos.delete()
        tokens.delete()
        eventos.delete()
        n_cuentas = derechos_titular.anonimizar_cuentas_vencidas(opts['dias_eliminacion'])
        self.stdout.write(self.style.SUCCESS(f'Borrados {n_intentos} intentos sospechosos, {n_tokens} tokens de sesión y {n_eventos} eventos de verificación; anonimizadas {n_cuentas} cuentas.'))
