"""
Decorador de autenticación propio.

Se optó por sesión propia sobre `Usuario` en vez de `AUTH_USER_MODEL` de
Django (decisión tomada con el usuario en el planeamiento de Fase 3, para no
tener que resetear migraciones). Este decorador reemplaza al
`@login_required` de `django.contrib.auth`, que no aplicaría acá porque
`Usuario` no es el modelo de auth oficial de Django.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def login_requerido(vista):
    """Redirige a la pantalla de login si no hay `usuario_id` en la sesión actual."""
    @wraps(vista)
    def envoltorio(request, *args, **kwargs):
        if not request.session.get('usuario_id'):
            messages.error(request, 'Debes iniciar sesión para continuar.')
            return redirect('KeyServApp:sesion')
        return vista(request, *args, **kwargs)
    return envoltorio


def obtener_usuario_actual(request):
    """Devuelve el `Usuario` de la sesión actual, o None si no hay sesión iniciada."""
    from .models import Usuario  # import local para evitar import circular con models.py

    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return None
    return Usuario.objects.filter(pk=usuario_id).first()
