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

from . import verificaciones
from .models import EventoVerificacion, VerificacionAlternativa

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


# Subir al cambiar CONSENTIMIENTO_VIDEO: queda guardada con cada aceptación como constancia de qué texto se aceptó.
VERSION_CONSENTIMIENTO_VIDEO = '2026-10-v1'

CONSENTIMIENTO_VIDEO = (
    'Acepto grabar un video corto mostrando mi cédula junto a mi cara, y que una persona del equipo de KeyServ lo vea '
    'para comparar mi rostro con la foto de mi cédula. El video no se usa para otra cosa, solo lo ve el equipo que '
    'revisa mi verificación y se elimina apenas la revisión termina (o a los 30 días si nadie la resuelve).'
)


def _codigo_de_video():
    return f'{secrets.randbelow(10**4):04d}'


def borrar_video(verificacion):
    """Elimina el archivo del video y deja un código nuevo (así un video anterior no se puede reusar). Idempotente."""
    if verificacion.video:
        verificacion.video.delete(save=False)
    verificacion.video = None
    verificacion.video_subido_en = None
    verificacion.codigo_video = _codigo_de_video()
    verificacion.save(update_fields=['video', 'video_subido_en', 'codigo_video'])


def _actualizar_revision(verificacion):
    """Pasa la solicitud a revisión del staff solo cuando están todos los respaldos (documento y, si se exige, el video)."""
    completa = bool(verificacion.documento_id) and (bool(verificacion.video) or not settings.VERIFICACION_REQUIERE_VIDEO)
    verificacion.estado = VerificacionAlternativa.PENDIENTE_REVISION if completa else VerificacionAlternativa.INICIADA
    verificacion.motivo_rechazo = ''
    verificacion.save()


def iniciar(usuario, acepto_advertencia, acepto_video=False):
    """Registra la aceptación de la advertencia (y del video, si se exige) y envía (o reenvía) el código al correo."""
    if not acepto_advertencia:
        raise ErrorVerificacion('Debes aceptar la advertencia para continuar con esta vía.')

    verificacion, _ = VerificacionAlternativa.objects.get_or_create(usuario=usuario)
    if verificacion.estado == VerificacionAlternativa.APROBADA:
        raise ErrorVerificacion('Tu identidad ya está verificada.', 409)
    if settings.VERIFICACION_REQUIERE_VIDEO and not (acepto_video or verificacion.video_consentimiento_en):
        raise ErrorVerificacion('Debes aceptar que se grabe y se revise el video para continuar con esta vía.')

    clave = f'verif_alt_reenvio:{usuario.pk}'
    if cache.get(clave):
        raise ErrorVerificacion('Espera un minuto antes de pedir otro código.', 429)
    cache.set(clave, 1, ESPERA_REENVIO_SEGUNDOS)

    codigo = f'{secrets.randbelow(10**6):06d}'
    verificacion.advertencia_aceptada_en = verificacion.advertencia_aceptada_en or timezone.now()
    if settings.VERIFICACION_REQUIERE_VIDEO:
        if not verificacion.video_consentimiento_en:
            verificacion.video_consentimiento_en = timezone.now()
            verificacion.video_consentimiento_version = VERSION_CONSENTIMIENTO_VIDEO
        verificacion.codigo_video = verificacion.codigo_video or _codigo_de_video()
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
        verificaciones.registrar_fallo(usuario, EventoVerificacion.ALTERNATIVA, 'codigo_correo', 'código incorrecto')
        raise ErrorVerificacion('Código incorrecto.')

    verificacion.correo_verificado_en = timezone.now()
    verificacion.codigo_hash = ''
    verificacion.save()
    verificaciones.registrar_evento(usuario, EventoVerificacion.ALTERNATIVA, 'codigo_correo', EventoVerificacion.EXITOSO)
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
    _actualizar_revision(verificacion)
    verificaciones.registrar_evento(usuario, EventoVerificacion.ALTERNATIVA, 'documento_enviado', EventoVerificacion.EXITOSO)
    logger.info('Documento de identidad recibido para revisión: usuario_id=%s', usuario.pk)
    return verificacion


def adjuntar_video(usuario, archivo):
    """Guarda el video de verificación (almacenamiento privado). Exige correo verificado y haber aceptado la grabación."""
    from .validators import validar_video

    verificacion = VerificacionAlternativa.objects.filter(usuario=usuario).first()
    if not verificacion or not verificacion.correo_verificado_en:
        raise ErrorVerificacion('Primero confirma el código que enviamos a tu correo.')
    if verificacion.estado == VerificacionAlternativa.APROBADA:
        raise ErrorVerificacion('Tu identidad ya está verificada.', 409)
    if not verificacion.video_consentimiento_en:
        raise ErrorVerificacion('Debes aceptar que se grabe y se revise el video para enviarlo.')

    validar_video(archivo)  # extensión, firma real y tamaño; levanta ValidationError
    if verificacion.video:
        verificacion.video.delete(save=False)  # reemplaza uno anterior
    verificacion.video.save(archivo.name, archivo, save=False)
    verificacion.video_subido_en = timezone.now()
    _actualizar_revision(verificacion)
    verificaciones.registrar_evento(usuario, EventoVerificacion.ALTERNATIVA, 'video_enviado', EventoVerificacion.EXITOSO)
    logger.info('Video de verificación recibido para revisión: usuario_id=%s', usuario.pk)
    return verificacion
