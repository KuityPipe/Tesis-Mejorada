"""
Autenticación DRF por access token JWT — reemplaza a `login_requerido`/
`obtener_usuario_actual` (decorators.py) para la API REST: en vez de
redirigir a `/sesion/` cuando no hay sesión, devuelve 401 (lo que espera un
cliente JSON como Ionic/Angular).
"""
import jwt
from rest_framework import authentication

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
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            # Igual que sin header: se deja pasar como anónimo en vez de
            # cortar la request acá con un 401 duro. Real bug encontrado
            # probando `/api/contacto/` (AllowAny) con una sesión vieja en
            # el navegador: `authInterceptor` (Ionic) adjunta el access
            # token guardado a *toda* request hacia la API, sin importar
            # si el endpoint lo necesita — incluido `/api/auth/login/`.
            # Con `AuthenticationFailed` acá, un token vencido bloqueaba
            # incluso el login mismo (la request nunca llegaba a mirar el
            # email/password del body), dejando a cualquiera con una
            # sesión vencida sin forma de volver a entrar salvo borrando
            # `localStorage` a mano. Devolver `None` le da el mismo trato
            # que "sin credenciales" — `IsAuthenticated` sigue rechazando
            # con 401 normal a los endpoints protegidos, pero `AllowAny`
            # (login, registro, catálogo, contacto) funciona igual que si
            # nunca se hubiera mandado el header.
            return None

        try:
            usuario_id = int(payload.get('sub', ''))
        except (TypeError, ValueError):
            return None

        usuario = Usuario.objects.filter(pk=usuario_id).first()
        if usuario is None:
            return None
        return (usuario, token)

    def authenticate_header(self, request):
        # Sin esto, un 401 sin credenciales devuelve 403 (ver docs de DRF:
        # WWW-Authenticate ausente hace que exceptions.NotAuthenticated
        # se recodifique como PermissionDenied).
        return 'Bearer'
