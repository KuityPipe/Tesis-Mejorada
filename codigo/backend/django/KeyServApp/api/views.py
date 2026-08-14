"""
Vistas de la API REST (Ionic/Angular) — ver plan de migración. Reutilizan a
propósito la lógica de seguridad ya probada de `KeyServApp/views.py` (límite
de intentos de login, registro de accesos sospechosos) en vez de
reimplementarla: importar los helpers "privados" de ese módulo es preferible
a duplicar el mismo bloqueo por (IP, email) en dos lugares que puedan
divergir con el tiempo.
"""
import logging

from django.core.cache import cache
from django.db.models import Q, Value
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import views as vistas_legacy
from ..forms import RegistroForm
from ..models import Comuna, Publicaciones, Region, Transaccion, TipoCuenta, Usuario
from ..views import Unaccent
from . import jwt_utils
from .serializers import (
    ComunaSerializer, LoginSerializer, PublicacionDetailSerializer, PublicacionListSerializer,
    RegionSerializer, TipoCuentaSerializer, UsuarioMeSerializer,
)

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """
    `POST /api/auth/login/` — equivalente de `sesion_view` (views.py) para
    la API: mismo límite de intentos por (IP, email) vía `cache` y mismo
    registro de `IntentoAccesoSospechoso` en bloqueo, pero devuelve un par
    access+refresh token en JSON en vez de abrir una sesión de Django.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        clave_intentos = vistas_legacy._clave_intentos_login(request, email)
        if cache.get(clave_intentos, 0) >= vistas_legacy.MAX_INTENTOS_LOGIN:
            # usuario=None a propósito, igual que en sesion_view: todavía
            # nadie se autenticó como para saber a quién corresponde.
            vistas_legacy._registrar_intento_sospechoso(
                request, None, 'login_bloqueado', email, 'demasiados intentos fallidos (api)',
            )
            return Response(
                {'detail': 'Demasiados intentos fallidos. Probá de nuevo en unos minutos.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        usuario = Usuario.objects.filter(email=email).first()
        if usuario and usuario.check_password(password):
            cache.delete(clave_intentos)
            access_token, refresh_token, _sesion = jwt_utils.crear_sesion(
                usuario, dispositivo=request.META.get('HTTP_USER_AGENT', ''),
            )
            logger.info('Login exitoso (api): usuario_id=%s', usuario.id_usuario)
            return Response({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'usuario': UsuarioMeSerializer(usuario).data,
            })

        try:
            cache.incr(clave_intentos)
        except ValueError:
            cache.set(clave_intentos, 1, vistas_legacy.VENTANA_INTENTOS_LOGIN)
        logger.warning('Login fallido (api): email=%s', email)
        return Response({'detail': 'Correo o contraseña incorrectos.'}, status=status.HTTP_401_UNAUTHORIZED)


class RegistroView(APIView):
    """
    `POST /api/auth/registro/` — equivalente de `register_view` (views.py).

    Reusa `RegistroForm` (forms.py) directamente en vez de escribir un
    `Serializer` de DRF paralelo con las mismas reglas: es exactamente el
    mismo caso que `LoginView` reusando `_clave_intentos_login` — dos
    validaciones de "las mismas reglas de negocio" que puedan divergir con
    el tiempo son peores que una sola reusada desde los dos lados. Un
    `django.forms.Form` acepta perfectamente un dict plano como `request.data`
    (no necesita ser un `QueryDict` de verdad), así que esto funciona sin
    adaptar nada.

    Costo del atajo: `drf-spectacular` no puede introspectar los campos de
    un `Form` de Django (no es un `Serializer`), así que `/api/schema/` no
    va a documentar el body esperado acá — aceptable mientras nadie genere
    un cliente TypeScript desde ese schema todavía (ver plan de migración).

    A diferencia de `register_view`, no rechaza una sesión ya autenticada:
    ese chequeo existe del lado template para evitar confusión sobre "con
    qué sesión de cookie terminás" — no aplica a un cliente JWT sin estado,
    que decide por su cuenta cuándo llamar a este endpoint.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        form = RegistroForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        tipo_cuenta = form.cleaned_data['tipo_cuenta']
        transaccion = Transaccion.objects.create(tipo_cuenta=tipo_cuenta)
        usuario = form.crear_usuario(transaccion)
        logger.info('Usuario registrado (api): id=%s email=%s', usuario.id_usuario, usuario.email)
        # Sin tokens acá a propósito, mismo criterio que register_view:
        # "cuenta creada, ahora iniciá sesión" — no auto-login.
        return Response(UsuarioMeSerializer(usuario).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """`GET /api/auth/me/` — perfil del usuario autenticado (requiere `Authorization: Bearer <access token>`, ver JWTAuthentication)."""

    def get(self, request):
        return Response(UsuarioMeSerializer(request.user).data)


class RegionListView(generics.ListAPIView):
    """`GET /api/catalogos/regiones/` — catálogo fijo, público, usado por el cascade región→comuna del registro."""
    permission_classes = [AllowAny]
    serializer_class = RegionSerializer
    pagination_class = None
    queryset = Region.objects.all().order_by('nombre_region')


class ComunaListView(generics.ListAPIView):
    """`GET /api/catalogos/comunas/?region=<id>` — equivalente API de `load_comunas` (views.py). Sin `?region`, devuelve las 330 comunas completas (catálogo fijo chico, no hace falta paginar)."""
    permission_classes = [AllowAny]
    serializer_class = ComunaSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Comuna.objects.all().order_by('nombre_comuna')
        region_id = self.request.query_params.get('region', '').strip()
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        return queryset


class TipoCuentaListView(generics.ListAPIView):
    """`GET /api/catalogos/tipos-cuenta/` — los 4 tiers reales (free/individual/pyme/empresa), usados por el selector de tipo de cuenta del registro."""
    permission_classes = [AllowAny]
    serializer_class = TipoCuentaSerializer
    pagination_class = None
    queryset = TipoCuenta.objects.all().order_by('id_tipo_cuenta')


class PaginacionPublicaciones(PageNumberPagination):
    """
    Mismo tamaño de página que el catálogo por templates
    (`views.PUBLICACIONES_POR_PAGINA = 20`) — duplicado a propósito en vez
    de importar la constante: `PageNumberPagination` es una clase de DRF,
    no un valor suelto, así que compartirla de verdad habría significado
    acoplar el catálogo por templates a DRF. Si se cambia uno, cambiar el otro.
    """
    page_size = 20


class PublicacionListView(generics.ListAPIView):
    """
    `GET /api/publicaciones/` — catálogo público, equivalente API de
    `catalogo_view` (views.py): mismos filtros (`q`, `region`,
    `calificacion`, `orden`) y misma búsqueda sin tildes vía `Unaccent`
    (reusada de `views.py`, no reimplementada — mismo criterio que
    `LoginView` reusando el bloqueo de intentos). Público a propósito
    (`AllowAny`, pisa el `IsAuthenticated` por defecto de
    `REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES']`): el catálogo es
    visible sin sesión tanto en el sitio Django como en la futura app.
    """
    permission_classes = [AllowAny]
    serializer_class = PublicacionListSerializer
    pagination_class = PaginacionPublicaciones

    def get_queryset(self):
        query = self.request.query_params.get('q', '').strip()
        region_id = self.request.query_params.get('region', '').strip()
        calificacion_min = self.request.query_params.get('calificacion', '').strip()
        orden = self.request.query_params.get('orden', 'recientes')

        publicaciones = Publicaciones.objects.filter(estado_moderacion=Publicaciones.APROBADA)
        if query:
            query_unaccent = Unaccent(Value(query))
            publicaciones = publicaciones.annotate(
                titulo_unaccent=Unaccent('titulo'),
                sub_titulo_unaccent=Unaccent('sub_titulo'),
                categoria_unaccent=Unaccent('categoria'),
            ).filter(
                Q(titulo_unaccent__icontains=query_unaccent)
                | Q(sub_titulo_unaccent__icontains=query_unaccent)
                | Q(categoria_unaccent__icontains=query_unaccent)
            )
        if region_id:
            publicaciones = publicaciones.filter(usuario_publicador__comuna__region_id=region_id)
        if calificacion_min:
            publicaciones = publicaciones.filter(usuario_publicador__ranking__puntuacion_promedio__gte=calificacion_min)

        publicaciones = publicaciones.select_related(
            'usuario_publicador__ranking', 'usuario_publicador__comuna__region',
        ).prefetch_related('imagenes')

        if orden == 'calificacion':
            return publicaciones.order_by('-usuario_publicador__ranking__puntuacion_promedio', '-fecha_publicacion')
        return publicaciones.order_by('-fecha_publicacion')


class PublicacionDetailView(generics.RetrieveAPIView):
    """
    `GET /api/publicaciones/<pk>/` — equivalente API de
    `publicacion_detalle_view` (views.py). Sin filtrar por
    `estado_moderacion` a propósito, para no divergir del comportamiento
    ya existente ahí: el detalle es visible por URL directa aunque la
    publicación todavía no esté aprobada (no aparece en el listado, pero
    no está 404-protegida). El estado de "ya la contraté" (`puede_contratar`
    en la vista de template) no está acá todavía — llega en la fase de
    contrataciones del plan de migración.
    """
    permission_classes = [AllowAny]
    serializer_class = PublicacionDetailSerializer
    queryset = Publicaciones.objects.select_related(
        'usuario_publicador__ranking', 'usuario_publicador__comuna__region',
    ).prefetch_related('imagenes')
