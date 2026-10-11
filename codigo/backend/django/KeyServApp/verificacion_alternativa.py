"""
Vía alternativa de verificación de identidad, SIN biometría (más lenta a propósito).

La vía principal es la biometría nativa del teléfono. Quien no puede o no quiere usarla
verifica con tres pasos, que juntos hacen de segundo factor:
  1. Aceptar una advertencia explícita (menos robusta, asume el riesgo asociado).
  2. Código de un solo uso enviado al correo (demuestra control del correo).
  3. Foto/archivo de su documento de identidad, revisado a mano por el staff.
Hasta que el staff aprueba, la identidad NO cuenta como verificada (ver identidad.py).

La advertencia informa y deja constancia, pero no traslada la responsabilidad legal de
KeyServ (ver docs/legal/eipd-reconocimiento-facial.md §5). Textos: borrador, revisar con abogado.
"""
import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone

from .models import VerificacionAlternativa

logger = logging.getLogger(__name__)

ADVERTENCIA = (
    'Estás eligiendo verificar tu identidad sin biometría. Este método es más lento y menos '
    'robusto: es más fácil que alguien se haga pasar por ti, y KeyServ no puede garantizar el '
    'mismo nivel de seguridad que con la biometría de tu teléfono. Entiendo esto y continúo '
    'asumiendo el riesgo asociado.'
)

VIGENCIA_CODIGO = timedelta(minutes=15)
MAX_INTENTOS_CODIGO = 5
ESPERA_REENVIO_SEGUNDOS = 60


class ErrorVerificacion(Exception):
    """Error de negocio con mensaje apto para mostrar al usuario."""

    def __init__(self, mensaje, codigo=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


def _hash_codigo(codigo):
    return hmac.new(settings.SECRET_KEY.encode(), codigo.encode(), hashlib.sha256).hexdigest()


def _enviar_codigo(usuario, codigo):
    send_mail(
        'Tu código de verificación de KeyServ',
        f'Hola {usuario.nombre_usuario},\n\nTu código de verificación es: {codigo}\n'
        'Vence en 15 minutos. Si no lo pediste, ignora este correo.',
        settings.DEFAULT_FROM_EMAIL,
        [usuario.email],
        fail_silently=True,
    )


def iniciar(usuario, acepto_advertencia):
    """Registra la aceptación de la advertencia y envía (o reenvía) el código al correo."""
    if not acepto_advertencia:
        raise ErrorVerificacion('Debes aceptar la advertencia para continuar con esta vía.')

    verificacion, _ = VerificacionAlternativa.objects.get_or_create(usuario=usuario)
    if verificacion.estado == VerificacionAlternativa.APROBADA:
        raise ErrorVerificacion('Tu identidad ya está verificada.', 409)

    clave = f'verif_alt_reenvio:{usuario.pk}'
    if cache.get(clave):
        raise ErrorVerificacion('Espera un minuto antes de pedir otro código.', 429)
    cache.set(clave, 1, ESPERA_REENVIO_SEGUNDOS)

    codigo = f'{secrets.randbelow(10**6):06d}'
    verificacion.advertencia_aceptada_en = verificacion.advertencia_aceptada_en or timezone.now()
    verificacion.codigo_hash = _hash_codigo(codigo)
    verificacion.codigo_expira_en = timezone.now() + VIGENCIA_CODIGO
    verificacion.intentos_codigo = 0
    verificacion.save()
    _enviar_codigo(usuario, codigo)
    logger.info('Código de verificación alternativa enviado: usuario_id=%s', usuario.pk)
    return verificacion


def confirmar_codigo(usuario, codigo):
    verificacion = VerificacionAlternativa.objects.filter(usuario=usuario).first()
    if not verificacion or not verificacion.codigo_hash:
        raise ErrorVerificacion('Primero pide un código.')
    if verificacion.correo_verificado_en:
        return verificacion
    if verificacion.intentos_codigo >= MAX_INTENTOS_CODIGO:
        raise ErrorVerificacion('Demasiados intentos. Pide un código nuevo.', 429)
    if verificacion.codigo_expira_en < timezone.now():
        raise ErrorVerificacion('El código venció. Pide uno nuevo.')

    verificacion.intentos_codigo += 1
    if not hmac.compare_digest(verificacion.codigo_hash, _hash_codigo((codigo or '').strip())):
        verificacion.save(update_fields=['intentos_codigo'])
        raise ErrorVerificacion('Código incorrecto.')

    verificacion.correo_verificado_en = timezone.now()
    verificacion.codigo_hash = ''
    verificacion.save()
    return verificacion


def adjuntar_documento(usuario, archivo, estado_documento):
    """Guarda el documento de identidad (storage privada) y deja la solicitud pendiente de revisión."""
    from .models import Documento

    verificacion = VerificacionAlternativa.objects.filter(usuario=usuario).first()
    if not verificacion or not verificacion.correo_verificado_en:
        raise ErrorVerificacion('Primero confirma el código que enviamos a tu correo.')
    if verificacion.estado == VerificacionAlternativa.APROBADA:
        raise ErrorVerificacion('Tu identidad ya está verificada.', 409)

    documento = Documento(usuario=usuario, nombre_documento='Documento de identidad'[:60], archivo_subido=archivo, estado_documento=estado_documento)
    documento.full_clean()  # extensión, firma real y tamaño (validators.py)
    documento.save()

    verificacion.documento = documento
    verificacion.estado = VerificacionAlternativa.PENDIENTE_REVISION
    verificacion.motivo_rechazo = ''
    verificacion.save()
    logger.info('Documento de identidad recibido para revisión: usuario_id=%s', usuario.pk)
    return verificacion
