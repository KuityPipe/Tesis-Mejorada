"""
Configuración del proyecto Django KeyServProject.

Refactor Fase 3: `SECRET_KEY` y las credenciales de base de datos estaban
hardcodeadas en este archivo (issue de seguridad ya documentado en
CODE_ANALYSIS_FINDINGS.md). Ahora se leen desde variables de entorno vía
`django-environ` — ver `.env.example` para la lista completa de variables
esperadas. También se cambió el motor de base de datos de MySQL a
PostgreSQL (decisión tomada con el usuario: la restricción de la tesis de
usar MySQL/AWS era solo para el contexto académico, ya no aplica).

Fase 4: Django se subió de 4.2.1 a 5.2 LTS — la versión original tiene un
bug real de incompatibilidad con Python 3.14 en su test client (revienta
`copy()` del contexto del template en cada request durante `manage.py test`,
incluso en el último parche 4.2.30). 5.2 lo soporta limpio.

Ver codigo/viejo/backup_fase3/KeyServProject/settings.py para la versión
previa (con los secretos hardcodeados).
"""
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# Busca un archivo .env en la raíz del proyecto Django (codigo/backend/django/.env).
# Si no existe (ej. en un entorno donde las variables ya vienen del sistema
# operativo/contenedor), simplemente sigue usando os.environ.
environ.Env.read_env(BASE_DIR / '.env')


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-solo-para-desarrollo-local-cambiar-en-produccion')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DJANGO_DEBUG', default=True)

ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=[])


# Application definition

INSTALLED_APPS = [
    'KeyServApp.apps.KeyservappConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'KeyServProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'KeyServProject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# Postgres en vez de MySQL (ver docstring de arriba). Variables esperadas
# en .env: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT.

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='keyserv'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
# Nota: esto valida el User de django.contrib.auth, que no usamos como
# modelo de login (ver decorators.py) — se deja igual por si en el futuro
# se agregan superusuarios de /admin/.

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
# RNF008 del PDF: idioma español.

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
# Refactor Fase 3: antes STATICFILES_DIRS apuntaba a BASE_DIR / 'static',
# una carpeta que nunca existió (los {% static %} no resolvían a nada). Los
# assets ahora viven en KeyServApp/static/KeyServApp/{css,imagenes}/, que
# Django encuentra solo con el AppDirectoriesFinder por defecto — no hace
# falta declarar STATICFILES_DIRS.

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # destino de `collectstatic` en producción


# Media files (subidas de usuario: documentos, fotos de perfil, etc.)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Logging (nuevo en Fase 3 — antes no había ninguna configuración de logging,
# los errores de las vistas quedaban silenciados o solo como excepción cruda).

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': env('DJANGO_LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        # Sin este override, Django castea los errores 500 al AdminEmailHandler
        # por defecto (activo cuando DEBUG=False, que es lo que fuerza
        # manage.py test) — y ese handler choca con Python 3.14 al intentar
        # generar el traceback HTML (bug de compatibilidad de Django 4.2, no
        # nuestro). Iba camino a un error de infraestructura que tapaba el
        # error real de la vista. Con esto los 500 solo van a la consola.
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
