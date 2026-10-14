"""
Envía un correo de prueba y muestra el resultado real.

Recuperar contraseña, el código de la vía "sin biometría" y el aviso a soporte mandan correo con `fail_silently=True`: si el SMTP
está mal configurado, la persona simplemente no recibe nada y nadie se entera. Este comando manda UN correo sin silenciar errores,
para comprobar la configuración (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `DJANGO_DEFAULT_FROM_EMAIL`).

    python manage.py probar_correo tu.correo@ejemplo.cl
"""
import smtplib

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Envía un correo de prueba a la dirección indicada y muestra el error real si falla.'

    def add_arguments(self, parser):
        parser.add_argument('destino', help='Dirección que recibirá el correo de prueba.')

    def handle(self, *args, **opciones):
        destino = opciones['destino']
        backend = settings.EMAIL_BACKEND
        es_consola = backend.endswith('console.EmailBackend')
        self.stdout.write(f'Backend de correo: {backend}')
        if es_consola:
            self.stdout.write(self.style.WARNING(
                'Sin SMTP_PASSWORD el correo solo se imprime en la terminal; no sale a ninguna bandeja. '
                'Define SMTP_HOST, SMTP_PORT, SMTP_USER y SMTP_PASSWORD para enviar de verdad.'
            ))
        else:
            self.stdout.write(f'Servidor: {settings.EMAIL_HOST}:{settings.EMAIL_PORT} (usuario: {settings.EMAIL_HOST_USER or "—"})')
        self.stdout.write(f'Remitente: {settings.DEFAULT_FROM_EMAIL}')

        try:
            enviados = send_mail(
                'Prueba de correo de KeyServ',
                'Si estás leyendo esto, el envío de correo de KeyServ funciona.\n\n'
                'Con esta misma configuración salen la recuperación de contraseña y el código de verificación.',
                settings.DEFAULT_FROM_EMAIL, [destino], fail_silently=False,
            )
        except smtplib.SMTPAuthenticationError as error:
            raise CommandError(
                f'El servidor rechazó el usuario o la clave ({error.smtp_code}). Revisa SMTP_USER/SMTP_PASSWORD; '
                'en Gmail y Outlook con verificación en dos pasos hace falta una "contraseña de aplicación".'
            )
        except smtplib.SMTPSenderRefused as error:
            raise CommandError(
                f'El servidor no acepta el remitente "{settings.DEFAULT_FROM_EMAIL}" ({error.smtp_code}). '
                'DJANGO_DEFAULT_FROM_EMAIL debe ser la misma dirección de la cuenta SMTP (o un dominio verificado en el proveedor).'
            )
        except (smtplib.SMTPException, OSError) as error:
            raise CommandError(f'No se pudo enviar: {error.__class__.__name__}: {error}')

        if enviados and es_consola:
            self.stdout.write(self.style.WARNING('El correo quedó impreso arriba, pero NO salió de este equipo: falta configurar el SMTP.'))
        elif enviados:
            self.stdout.write(self.style.SUCCESS(f'Correo enviado a {destino}. Revisa la bandeja de entrada (y el spam).'))
        else:
            raise CommandError('El servidor no reportó ningún envío.')
