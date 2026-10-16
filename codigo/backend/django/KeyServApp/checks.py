"""
Chequeos de configuración que avisan (no frenan el arranque) cuando producción corre con valores por defecto inseguros.
Aparecen en `manage.py check`, en `manage.py check --deploy` y en la salida de `migrate` del build de Render, así que
basta mirar el log del deploy. Con `DEBUG=True` (desarrollo) no se avisa.
"""
from django.conf import settings
from django.core.checks import Tags, Warning, register

_CLAVE_POR_DEFECTO = 'django-insecure-solo-para-desarrollo-local-cambiar-en-produccion'


@register(Tags.security)
def claves_de_produccion(app_configs, **kwargs):
    if settings.DEBUG:
        return []
    avisos = []
    if settings.SECRET_KEY == _CLAVE_POR_DEFECTO:
        avisos.append(Warning(
            'DJANGO_SECRET_KEY usa el valor por defecto, que es público en el repositorio.',
            hint='Define DJANGO_SECRET_KEY con un valor largo y aleatorio en el entorno (en Render: Environment).',
            id='keyserv.W001',
        ))
    if settings.JWT_SECRET == settings.SECRET_KEY:
        avisos.append(Warning(
            'JWT_SECRET no está definido y cae a SECRET_KEY: una filtración de una compromete a la otra.',
            hint='Define JWT_SECRET aparte. Cambiarlo cierra la sesión de todos los usuarios.',
            id='keyserv.W002',
        ))
    if not settings.BIOMETRIC_ENCRYPTION_KEYS:
        avisos.append(Warning(
            'BIOMETRIC_ENCRYPTION_KEYS está vacío: la llave que cifra los vectores faciales se deriva de SECRET_KEY.',
            hint='Genera una con Fernet.generate_key() y guárdala fuera de la base de datos; ver docs/cumplimiento/rotacion-de-llaves.md. '
                 'Si ya hay vectores guardados, rota antes con `manage.py rotar_llaves_biometricas` o quedarán ilegibles.',
            id='keyserv.W003',
        ))
    return avisos
