"""
Códigos de un solo uso enviados al correo para confirmar acciones sensibles (hoy: cerrar la sesión en todos los
dispositivos). Segundo factor por correo: demuestra que quien pide la acción controla el correo de la cuenta, no solo
una sesión que pudo ser robada.

Reglas: 6 dígitos, vence a los 10 minutos, 5 intentos, un solo uso, un código activo por (usuario, propósito) y una
espera entre reenvíos. Solo se guarda el hash (HMAC con `SECRET_KEY`), nunca el código. Vive en la base de datos y no
en la caché: con varios procesos una caché local no compartiría el código entre quien lo pide y quien lo verifica.
"""
import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from . import notificaciones_correo
from .models import CodigoSeguridad

logger = logging.getLogger(__name__)

VIGENCIA = timedelta(minutes=10)
MAX_INTENTOS = 5
ESPERA_REENVIO = timedelta(seconds=60)


class ErrorCodigo(Exception):
    """Error de negocio con mensaje apto para mostrar al usuario y su código HTTP."""

    def __init__(self, mensaje, codigo=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


def _hash(codigo):
    return hmac.new(settings.SECRET_KEY.encode(), codigo.encode(), hashlib.sha256).hexdigest()


def enviar(usuario, proposito, asunto, descripcion):
    """Genera un código nuevo (anula el anterior), lo guarda hasheado y lo manda al correo del usuario."""
    ahora = timezone.now()
    reciente = CodigoSeguridad.objects.filter(usuario=usuario, proposito=proposito, creado_en__gt=ahora - ESPERA_REENVIO).exists()
    if reciente:
        raise ErrorCodigo('Espera un minuto antes de pedir otro código.', 429)

    codigo = f'{secrets.randbelow(10**6):06d}'
    CodigoSeguridad.objects.filter(usuario=usuario, proposito=proposito).delete()
    CodigoSeguridad.objects.create(usuario=usuario, proposito=proposito, codigo_hash=_hash(codigo), expira_en=ahora + VIGENCIA)
    minutos = int(VIGENCIA.total_seconds() // 60)
    notificaciones_correo.avisar(
        usuario, asunto,
        f'{descripcion}\n\nTu código es: {codigo}\nVence en {minutos} minutos y sirve una sola vez. '
        'Si no lo pediste tú, ignora este correo y cambia tu contraseña: alguien con acceso a tu sesión podría estar intentándolo.',
    )
    logger.info('Código de seguridad enviado: usuario_id=%s proposito=%s', usuario.pk, proposito)


def verificar(usuario, proposito, codigo):
    """Valida y consume el código. Lanza `ErrorCodigo` si falta, venció, se agotaron los intentos o es incorrecto."""
    registro = CodigoSeguridad.objects.filter(usuario=usuario, proposito=proposito).first()
    if not registro:
        raise ErrorCodigo('Primero pide un código.')
    if registro.expira_en < timezone.now():
        registro.delete()
        raise ErrorCodigo('El código venció. Pide uno nuevo.')
    if registro.intentos >= MAX_INTENTOS:
        registro.delete()
        raise ErrorCodigo('Demasiados intentos. Pide un código nuevo.', 429)

    registro.intentos += 1
    if not hmac.compare_digest(registro.codigo_hash, _hash((codigo or '').strip())):
        registro.save(update_fields=['intentos'])
        logger.warning('Código de seguridad incorrecto: usuario_id=%s proposito=%s intento=%s', usuario.pk, proposito, registro.intentos)
        raise ErrorCodigo('Código incorrecto.')
    registro.delete()  # un solo uso
