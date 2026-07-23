"""Tag de inclusión para el dashboard de /admin/ — panel de aprobaciones pendientes e incidencias abiertas (ver templates/admin/index.html)."""
from django import template

from KeyServApp.models import Consulta, Publicaciones

register = template.Library()


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

    return contexto
