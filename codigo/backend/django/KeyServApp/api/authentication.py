"""
Autenticación DRF por access token JWT — reemplaza a `login_requerido`/
`obtener_usuario_actual` (decorators.py) para la API REST: en vez de
redirigir a `/sesion/` cuando no hay sesión, devuelve 401 (lo que espera un
cliente JSON como Ionic/Angular).
"""
import jwt
from rest_framework import authentication, exceptions

from ..models import Usuario
from . import jwt_utils


class JWTAuthentication(authentication.BaseAuthentication):
    """Espera `Authorization: Bearer <access token>`."""

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode('utf-8')
        if not header.startswith('Bearer '):
            # Sin credenciales: no es un error acá, DRF sigue con
            # AnonymousUser (ver AuthenticationMiddleware) — recién
            # `IsAuthenticated` decide si eso alcanza para la vista pedida.
            return None

        token = header[len('Bearer '):].strip()
        try:
            payload = jwt_utils.decodificar_access_token(token)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('El token expiró, renová la sesión.', code='token_expirado')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Token inválido.', code='token_invalido')

        try:
            usuario_id = int(payload.get('sub', ''))
        except (TypeError, ValueError):
            raise exceptions.AuthenticationFailed('Token inválido.', code='token_invalido')

        usuario = Usuario.objects.filter(pk=usuario_id).first()
        if usuario is None:
            raise exceptions.AuthenticationFailed('El usuario de este token ya no existe.', code='usuario_inexistente')
        return (usuario, token)

    def authenticate_header(self, request):
        # Sin esto, un 401 sin credenciales devuelve 403 (ver docs de DRF:
        # WWW-Authenticate ausente hace que exceptions.NotAuthenticated
        # se recodifique como PermissionDenied).
        return 'Bearer'
