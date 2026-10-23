"""
Retención de datos de seguridad y sesiones:

- `IntentoAccesoSospechoso` (IP, ciudad, país, user-agent) más viejos que --dias-seguridad (365).
- `EventoVerificacion` (auditoría de verificaciones) más viejos que --dias-eventos (365).
- `TokenSesion` expirados o revocados hace más de --dias-sesiones (30).
- Videos de verificación de identidad sin resolver hace más de `settings.VIDEO_RETENCION_DIAS` (30).
- Cuentas que pidieron eliminarse hace más de --dias-eliminacion (`settings.CUENTA_ELIMINACION_DIAS`, 15): se anonimizan.

Pensado para correr periódicamente (ver `mantenimiento_retencion`, que lo junta con
`limpiar_mensajes_antiguos`). Los plazos son propuestas técnicas, a validar con asesoría legal.

    python manage.py purgar_datos_vencidos --dry-run
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from django.conf import settings

from KeyServApp import derechos_titular, verificacion_alternativa
from KeyServApp.models import CodigoSeguridad, EventoVerificacion, IntentoAccesoSospechoso, TokenSesion, UsoCalculadora, VerificacionAlternativa


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
        videos = VerificacionAlternativa.objects.filter(video_subido_en__lt=ahora - timedelta(days=settings.VIDEO_RETENCION_DIAS))
        n_videos = videos.count()
        if opts['dry_run']:
            n_cuentas = derechos_titular.anonimizar_cuentas_vencidas(opts['dias_eliminacion'], dry_run=True)
            self.stdout.write(f'Se borrarían {n_intentos} intentos sospechosos, {n_tokens} tokens y {n_eventos} eventos de verificación, {n_videos} videos de verificación y se anonimizarían {n_cuentas} cuentas (dry-run).')
            return
        intentos.delete()
        tokens.delete()
        eventos.delete()
        CodigoSeguridad.objects.filter(expira_en__lt=ahora).delete()  # códigos de un solo uso ya vencidos
        UsoCalculadora.objects.filter(actualizado_en__lt=ahora - timedelta(days=400)).delete()  # contador anónimo: 13 meses
        for verificacion in videos:
            verificacion_alternativa.borrar_video(verificacion)  # sin resolver a tiempo: no se conserva
        n_cuentas = derechos_titular.anonimizar_cuentas_vencidas(opts['dias_eliminacion'])
        self.stdout.write(self.style.SUCCESS(f'Borrados {n_intentos} intentos sospechosos, {n_tokens} tokens de sesión y {n_eventos} eventos de verificación; borrados {n_videos} videos de verificación; anonimizadas {n_cuentas} cuentas.'))
