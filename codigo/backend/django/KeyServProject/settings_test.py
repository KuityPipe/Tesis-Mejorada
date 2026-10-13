"""
Settings solo para correr la suite de tests (`manage.py test --settings=KeyServProject.settings_test`).

Importa todo de settings.py y cambia únicamente el hasher de contraseñas: PBKDF2 con
~1M de iteraciones (el default de Django 5.2) tarda ~0,3 s por hash/verificación, y
la suite crea y valida cientos de usuarios. MD5 es inseguro y por eso NUNCA debe
usarse fuera de tests; settings.py (producción/desarrollo) no se toca.
"""
import sys

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F401,F403

# Protección: este módulo solo puede cargarse corriendo `manage.py test`. Si por error
# queda como DJANGO_SETTINGS_MODULE en Render/.env (gunicorn, runserver, shell...), el
# proceso se niega a arrancar en vez de hashear contraseñas reales con MD5.
if 'test' not in sys.argv[1:2]:
    raise ImproperlyConfigured(
        'settings_test.py solo se puede usar con `manage.py test` (usa MD5 para contraseñas).'
    )

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
