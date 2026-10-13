"""
Registro de eventos de verificación de identidad y marca de "verificado".

Un único lugar para que las tres vías (biometría nativa, rostro en servidor, vía alternativa) dejen el
mismo rastro de auditoría (`EventoVerificacion`: quién, cuándo, método, resultado) y fijen
`Usuario.verificado_en`, que `identidad.py` usa para exigir una verificación reciente. Nada de lo que se
guarda acá es un dato biométrico: solo el hecho de que ocurrió.
"""
import logging

from django.utils import timezone

from .models import EventoVerificacion

logger = logging.getLogger(__name__)


def registrar_evento(usuario, metodo, accion, resultado, detalle=''):
    try:
        return EventoVerificacion.objects.create(
            usuario=usuario, metodo=metodo, accion=accion, resultado=resultado, detalle=detalle[:120],
        )
    except Exception:  # la auditoría nunca debe tumbar el flujo de verificación
        logger.exception('No se pudo registrar el evento de verificación: usuario_id=%s', getattr(usuario, 'pk', None))
        return None


def marcar_verificado(usuario, metodo, accion='verificacion'):
    """Marca la identidad como verificada ahora y deja el evento."""
    usuario.verificado_biometricamente = True
    usuario.verificado_en = timezone.now()
    usuario.save(update_fields=['verificado_biometricamente', 'verificado_en'])
    registrar_evento(usuario, metodo, accion, EventoVerificacion.EXITOSO)


def registrar_fallo(usuario, metodo, accion='verificacion', detalle=''):
    registrar_evento(usuario, metodo, accion, EventoVerificacion.FALLIDO, detalle)
