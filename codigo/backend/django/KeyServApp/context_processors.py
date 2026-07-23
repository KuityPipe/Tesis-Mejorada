"""Context processor: expone el usuario logueado (sesión propia, no auth de Django) y sus mensajes no leídos a todos los templates."""
from .decorators import obtener_usuario_actual


def usuario_actual(request):
    usuario = obtener_usuario_actual(request)
    mensajes_no_leidos = 0
    if usuario:
        from .views import contar_mensajes_no_leidos  # import local para evitar import circular con views.py
        mensajes_no_leidos = contar_mensajes_no_leidos(usuario)
    return {'usuario_actual': usuario, 'mensajes_no_leidos': mensajes_no_leidos}
