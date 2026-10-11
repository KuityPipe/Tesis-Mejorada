"""
Campo JSON cifrado en reposo (Fernet: AES-128-CBC + HMAC) para datos biométricos.

Se guarda como texto cifrado en la BD; en Python se lee y escribe como un valor JSON
normal (lista, dict...), así el resto del código no cambia. Un volcado de la BD o un
respaldo filtrado no revela el vector facial sin la clave.

Claves: `settings.BIOMETRIC_ENCRYPTION_KEYS` (lista de claves Fernet; la primera cifra,
todas descifran → permite rotar claves sin perder datos). Si no hay ninguna configurada
se deriva una de `SECRET_KEY`: sirve en desarrollo y en la demo, pero en producción real
debe configurarse una clave propia, distinta de SECRET_KEY y guardada fuera de la BD.
Perder la clave equivale a perder los vectores (las personas deben registrar su rostro
de nuevo): descifrar con una clave incorrecta devuelve None y deja un error en el log.

Compatibilidad: un valor que no es un token Fernet se interpreta como JSON en claro
(filas anteriores a este cambio); se cifra la próxima vez que se guarda la fila.
"""
import base64
import hashlib
import json
import logging

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)

_PREFIJO_FERNET = 'gAAAA'


def _fernet():
    claves = list(getattr(settings, 'BIOMETRIC_ENCRYPTION_KEYS', None) or [])
    if not claves:
        derivada = base64.urlsafe_b64encode(hashlib.sha256(('biometria:' + settings.SECRET_KEY).encode()).digest())
        claves = [derivada.decode()]
    return MultiFernet([Fernet(clave.encode() if isinstance(clave, str) else clave) for clave in claves])


def cifrar_json(valor):
    return _fernet().encrypt(json.dumps(valor).encode()).decode()


def descifrar_json(texto):
    """Devuelve el valor original, o None si no se puede descifrar con ninguna clave."""
    if texto is None:
        return None
    if not texto.startswith(_PREFIJO_FERNET):
        return json.loads(texto)  # fila en claro, anterior al cifrado
    try:
        return json.loads(_fernet().decrypt(texto.encode()))
    except InvalidToken:
        logger.error('No se pudo descifrar un dato biométrico: ¿cambió BIOMETRIC_ENCRYPTION_KEYS?')
        return None


class CampoJSONCifrado(models.TextField):
    description = 'JSON cifrado en reposo'

    def from_db_value(self, value, expression, connection):
        return descifrar_json(value)

    def to_python(self, value):
        # Llega ya deserializado desde Python; un str solo se interpreta si es un token/JSON de la BD.
        if isinstance(value, str):
            return descifrar_json(value)
        return value

    def get_prep_value(self, value):
        if value is None:
            return None
        return cifrar_json(value)
