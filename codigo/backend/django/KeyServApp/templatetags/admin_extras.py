"""Tag de inclusión para el dashboard de /admin/ — panel de aprobaciones pendientes, incidencias abiertas e intentos de acceso sospechoso (ver templates/admin/index.html)."""
from django import template
from django.utils import timezone

from KeyServApp.models import Consulta, IntentoAccesoSospechoso, Publicaciones

register = template.Library()

# Ventana de "reciente" para el panel de alertas — más allá de esto ya no es
# una alerta activa, es historial (se sigue viendo completo en el listado).
_VENTANA_INTENTOS_SOSPECHOSOS_HORAS = 48


@register.inclusion_tag('admin/_panel_aprobaciones.html', takes_context=True)
def panel_aprobaciones(context):
    request = context['request']
    usuario = request.user

    contexto = {'es_superuser': usuario.is_superuser}

    if usuario.has_perm('KeyServApp.view_publicaciones'):
        pendientes = Publicaciones.objects.filter(estado_moderacion=Publicaciones.PENDIENTE).select_related('usuario_publicador').order_by('-fecha_publicacion')
        contexto['total_pendientes'] = pendientes.count()
        contexto['publicaciones_pendientes'] = pendientes[:8]

    if usuario.has_perm('KeyServApp.view_consulta'):
        abiertas = Consulta.objects.filter(estado_consulta__nombre_estado_consulta='Abierta').order_by('-fecha_consulta')
        contexto['total_abiertas'] = abiertas.count()
        contexto['consultas_abiertas'] = abiertas[:8]

    if usuario.has_perm('KeyServApp.view_intentoaccesosospechoso'):
        desde = timezone.now() - timezone.timedelta(hours=_VENTANA_INTENTOS_SOSPECHOSOS_HORAS)
        recientes = IntentoAccesoSospechoso.objects.filter(fecha__gte=desde).select_related('usuario')
        contexto['total_sospechosos'] = recientes.count()
        contexto['intentos_sospechosos'] = recientes[:8]

    return contexto
