"""
Avisos por correo de lo que le pasa a la cuenta o a un servicio (solicitud expirada, eliminación programada, ...).

Un solo punto de envío para que los avisos nuevos (intento de acceso a la cuenta, servicio contratado o confirmado,
pago aprobado) se agreguen llamando a `avisar` y no con un `send_mail` suelto en cada vista. Solo informativos: nunca
llevan datos sensibles, solo qué pasó y dónde verlo.

Como el resto de los correos de la app usan `fail_silently=True`, una configuración SMTP mala no se ve acá; para
diagnosticarla está `manage.py probar_correo`.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def avisar(usuario, asunto, texto):
    """Envía un correo informativo a `usuario`. No hace nada con cuentas anonimizadas (correo `.invalid`). Devuelve si lo intentó."""
    if not usuario or not usuario.email or usuario.email.endswith('.invalid'):
        return False
    cuerpo = f'Hola {usuario.nombre_usuario},\n\n{texto}\n\nEste es un aviso automático de KeyServ.'
    send_mail(f'KeyServ: {asunto}', cuerpo, settings.DEFAULT_FROM_EMAIL, [usuario.email], fail_silently=True)
    logger.info('Aviso por correo enviado: usuario_id=%s asunto=%s', usuario.pk, asunto)
    return True
