"""
Expira las solicitudes de contratación que el proveedor nunca respondió.

Una contratación SOLICITADA con más de --dias días (por defecto `settings.SOLICITUD_EXPIRA_DIAS`) pasa a CANCELADA,
queda anotada en el historial y en el chat, y se avisa por correo a las dos partes (solo informativo). Sin esto una
solicitud ignorada quedaba abierta para siempre.

Pensado para correr dentro de `mantenimiento_retencion`:

    python manage.py expirar_solicitudes --dry-run
"""
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from KeyServApp import cierres, notificaciones_correo
from KeyServApp.models import Contratacion


class Command(BaseCommand):
    help = 'Cancela las solicitudes sin respuesta del proveedor después de N días y avisa por correo.'

    def add_arguments(self, parser):
        parser.add_argument('--dias', type=int, default=None, help='Por defecto settings.SOLICITUD_EXPIRA_DIAS.')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        dias = opts['dias'] if opts['dias'] is not None else settings.SOLICITUD_EXPIRA_DIAS
        limite = timezone.now() - timedelta(days=dias)
        vencidas = Contratacion.objects.filter(estado=Contratacion.SOLICITADA, fecha_creacion__lt=limite).select_related('cliente', 'proveedor', 'publicacion')
        if opts['dry_run']:
            self.stdout.write(f'Se expirarían {vencidas.count()} solicitudes de más de {dias} días (dry-run).')
            return

        expiradas = 0
        for contratacion in vencidas:
            with transaction.atomic():
                # Se re-lee con bloqueo: el proveedor pudo confirmar justo ahora.
                contratacion = Contratacion.objects.select_for_update().select_related('cliente', 'proveedor', 'publicacion').get(pk=contratacion.pk)
                if contratacion.estado != Contratacion.SOLICITADA:
                    continue
                cierres.cancelar_contratacion(
                    contratacion, contratacion.cliente,
                    f'La solicitud expiró porque el proveedor no respondió en {dias} días.',
                )
            titulo = contratacion.publicacion.titulo
            notificaciones_correo.avisar(
                contratacion.cliente, 'tu solicitud expiró',
                f'Tu solicitud del servicio "{titulo}" expiró porque el proveedor no respondió en {dias} días. Puedes solicitarlo de nuevo o buscar otro proveedor.',
            )
            notificaciones_correo.avisar(
                contratacion.proveedor, 'una solicitud expiró',
                f'Una solicitud de tu servicio "{titulo}" expiró porque no se respondió en {dias} días. Responder a tiempo ayuda a que te elijan.',
            )
            expiradas += 1
        self.stdout.write(self.style.SUCCESS(f'Expiradas {expiradas} solicitudes de más de {dias} días.'))
