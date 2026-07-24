"""
Escaneo antivirus de archivos subidos — integra con un daemon ClamAV
(clamd) si está configurado, vía la librería `clamd` (pura Python, sin
compilación nativa).

Apagado por defecto (`CLAMAV_HABILITADO=False` en .env): este entorno de
desarrollo no tiene ClamAV corriendo — instalarlo como servicio de Windows
de forma no interactiva es el mismo tipo de fricción que ya se documentó
para Postgres en docs/FASE4_LOG.md, así que se deja como integración lista
para prenderse en un servidor real (Linux, con `clamav-daemon` corriendo)
en vez de intentar forzarlo acá. Con la bandera apagada, `escanear_archivo`
no hace nada (deja pasar el archivo) — la defensa real hoy es
`validators.py` (extensión + firma de bytes + verificación real con
Pillow), esto es una capa adicional para cuando haya un servidor con
ClamAV disponible.
"""
import logging

from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

_clamd_disponible = True
try:
    import clamd
except ImportError:
    _clamd_disponible = False


def escanear_archivo(archivo):
    """
    Escanea `archivo` (un UploadedFile ya en el field, seek(0) garantizado
    al volver) contra ClamAV si `CLAMAV_HABILITADO=True`. Levanta
    ValidationError si detecta malware; no hace nada si el escaneo está
    apagado o el daemon no responde (falla "abierto" a propósito: un
    ClamAV caído no debe tumbar la subida de archivos del sitio entero,
    solo se registra en logs para que alguien lo note).
    """
    if not getattr(settings, 'CLAMAV_HABILITADO', False):
        return

    if not _clamd_disponible:
        logger.warning('CLAMAV_HABILITADO=True pero el paquete "clamd" no está instalado (pip install clamd).')
        return

    try:
        cliente = clamd.ClamdNetworkSocket(
            host=getattr(settings, 'CLAMAV_HOST', 'localhost'),
            port=getattr(settings, 'CLAMAV_PORT', 3310),
        )
        archivo.seek(0)
        resultado = cliente.instream(archivo)
        archivo.seek(0)
    except Exception:
        logger.exception('No se pudo contactar al daemon de ClamAV — se deja pasar el archivo sin escanear.')
        return

    estado, detalle = resultado.get('stream', (None, None))
    if estado == 'FOUND':
        raise ValidationError(f'El archivo fue rechazado por el escaneo antivirus ({detalle}).')
