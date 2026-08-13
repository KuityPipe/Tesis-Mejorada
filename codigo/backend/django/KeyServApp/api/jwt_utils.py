"""
JWT hecho a mano (PyJWT), no `djangorestframework-simplejwt` — ver el
comentario de `JWT_SECRET` en `KeyServProject/settings.py` sobre por qué
(resumen: `Usuario` no es `AUTH_USER_MODEL` y simplejwt asume
`get_user_model()` en varios puntos).

Esquema: access token = JWT stateless de vida corta (`sub` = `Usuario.id_usuario`).
Refresh token = secreto opaco de alta entropía, solo su hash se guarda en
`TokenSesion` (ver models.py) — permite revocar sesiones (logout real,
"cerrar sesión en todos los dispositivos", Fase 7 de dispositivo de
confianza), algo que un JWT puramente stateless no permite.
"""
import hashlib
import secrets
from datetime import timedelta

import jwt
from django.conf import settings
from django.utils import timezone

from ..models import TokenSesion


def generar_access_token(usuario):
    """JWT de vida corta (`settings.JWT_ACCESS_TOKEN_MINUTOS`) para autenticar requests a la API."""
    ahora = timezone.now()
    payload = {
        # PyJWT exige que 'sub' sea string (RFC 7519) — id_usuario es un
        # BigAutoField numérico, se castea acá y se vuelve a castear a int
        # del lado del decode (ver authentication.py).
        'sub': str(usuario.id_usuario),
        'iat': ahora,
        'exp': ahora + timedelta(minutes=settings.JWT_ACCESS_TOKEN_MINUTOS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decodificar_access_token(token):
    """Devuelve el payload, o levanta `jwt.ExpiredSignatureError`/`jwt.InvalidTokenError` — el caller decide cómo responder."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def _hash_refresh_token(token_plano):
    """
    SHA-256 alcanza acá: el refresh token ya es un secreto de alta entropía
    (`secrets.token_urlsafe`), no una contraseña elegida por una persona —
    no hace falta un hash lento tipo PBKDF2/Argon2 (eso es para resistir
    fuerza bruta sobre baja entropía, que acá no aplica).
    """
    return hashlib.sha256(token_plano.encode('utf-8')).hexdigest()


def crear_sesion(usuario, dispositivo=''):
    """
    Emite un par access+refresh nuevo y crea la fila `TokenSesion` que
    respalda al refresh token. Devuelve `(access_token, refresh_token_plano, TokenSesion)`.
    """
    refresh_token_plano = secrets.token_urlsafe(48)
    sesion = TokenSesion.objects.create(
        usuario=usuario,
        refresh_token_hash=_hash_refresh_token(refresh_token_plano),
        dispositivo=(dispositivo or '')[:255],
        expira_en=timezone.now() + timedelta(days=settings.JWT_REFRESH_TOKEN_DIAS),
    )
    return generar_access_token(usuario), refresh_token_plano, sesion


def obtener_sesion_vigente(refresh_token_plano):
    """`TokenSesion` activa (no revocada, no expirada) para este refresh token, o `None`."""
    return TokenSesion.objects.filter(
        refresh_token_hash=_hash_refresh_token(refresh_token_plano),
        revocado_en__isnull=True,
        expira_en__gt=timezone.now(),
    ).select_related('usuario').first()


def revocar_sesion(sesion):
    sesion.revocado_en = timezone.now()
    sesion.save(update_fields=['revocado_en'])
