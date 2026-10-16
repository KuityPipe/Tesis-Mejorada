"""
Corre todas las tareas de retención de datos en una sola llamada, pensada para un único
cron/tarea programada:

    python manage.py mantenimiento_retencion

Hoy NO está programada en ningún entorno (la demo de Render es gratuita y sus cron jobs son
de pago): programarla es una acción operativa pendiente, ver docs/cumplimiento/.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Ejecuta expirar_solicitudes, limpiar_mensajes_antiguos y purgar_datos_vencidos.'

    def handle(self, *args, **opts):
        call_command('expirar_solicitudes', stdout=self.stdout)
        call_command('limpiar_mensajes_antiguos', stdout=self.stdout)
        call_command('purgar_datos_vencidos', stdout=self.stdout)
