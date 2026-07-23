"""
Retención de mensajería: borra los chats de trabajo (Conversacion) que
llevan más de N días cerrados y nunca se exportaron.

Pensado como tarea programada (cron / Programador de tareas de Windows), no
se ejecuta solo — correr manualmente con:

    python manage.py limpiar_mensajes_antiguos              # 90 días por defecto
    python manage.py limpiar_mensajes_antiguos --dias 30
    python manage.py limpiar_mensajes_antiguos --dry-run     # solo mostrar qué borraría

Una conversación se considera "cerrada" cuando su Contratacion está
COMPLETADA o CANCELADA (una en curso nunca se borra, tenga la antigüedad que
tenga). Si el usuario la exportó alguna vez (botón "Exportar chat"),
`exportado_en` queda seteado y esa conversación queda exenta para siempre —
exportar es justamente lo que la protege del borrado automático.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import timezone

from KeyServApp.models import Conversacion


class Command(BaseCommand):
    help = 'Borra chats de trabajos cerrados hace más de N días que nunca se exportaron.'

    def add_arguments(self, parser):
        parser.add_argument('--dias', type=int, default=90, help='Antigüedad mínima en días (default: 90)')
        parser.add_argument('--dry-run', action='store_true', help='No borra nada, solo muestra qué se borraría')

    def handle(self, *args, **options):
        limite = timezone.now() - timedelta(days=options['dias'])

        candidatas = Conversacion.objects.filter(
            exportado_en__isnull=True,
            contratacion__estado__in=['COMPLETADA', 'CANCELADA'],
        ).annotate(ultimo_mensaje=Max('mensaje__fecha_envio')).filter(
            ultimo_mensaje__lt=limite,
        )
        # Conversaciones sin ningún mensaje: usar la fecha de creación en su lugar.
        candidatas_sin_mensajes = Conversacion.objects.filter(
            exportado_en__isnull=True,
            contratacion__estado__in=['COMPLETADA', 'CANCELADA'],
            mensaje__isnull=True,
            fecha_creacion__lt=limite,
        )

        ids = set(candidatas.values_list('id_conversacion', flat=True)) | set(
            candidatas_sin_mensajes.values_list('id_conversacion', flat=True)
        )

        if options['dry_run']:
            self.stdout.write(f'Se borrarían {len(ids)} conversaciones (dry-run, no se modificó nada).')
            return

        total, _ = Conversacion.objects.filter(id_conversacion__in=ids).delete()
        self.stdout.write(self.style.SUCCESS(f'Borradas {len(ids)} conversaciones ({total} filas en total, incluye mensajes).'))
