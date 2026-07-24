from django.apps import AppConfig


class KeyservappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'KeyServApp'
    verbose_name = 'KeyServApp'

    def ready(self):
        # El User nativo de Django (login de staff a /admin/) y el Usuario de
        # KeyServApp (clientes/proveedores del sitio) son cosas totalmente
        # distintas pero por defecto ambos se ven "Usuario(s)" en el admin —
        # se renombra el nativo para que no se confundan entre sí (ver
        # también Usuario.Meta.verbose_name en models.py).
        from django.contrib.auth.models import User
        User._meta.verbose_name = 'Cuenta de staff (login admin)'
        User._meta.verbose_name_plural = 'Cuentas de staff (login admin)'
