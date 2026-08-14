"""
Vistas de la API REST (Ionic/Angular) — ver plan de migración. Reutilizan a
propósito la lógica de seguridad ya probada de `KeyServApp/views.py` (límite
de intentos de login, registro de accesos sospechosos) en vez de
reimplementarla: importar los helpers "privados" de ese módulo es preferible
a duplicar el mismo bloqueo por (IP, email) en dos lugares que puedan
divergir con el tiempo.
"""
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models import Q, Value
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import views as vistas_legacy
from ..forms import (
    CambiarPasswordForm, CATEGORIAS_PUBLICACION, CrearPerfilForm, EditarPerfilForm,
    NuevaPasswordForm, PreferenciasCuentaForm, RecuperarForm, RegistroForm,
)
from ..models import Comuna, Documento, EstadoDocumento, Publicaciones, Region, Transaccion, TipoCuenta, Usuario
from ..views import Unaccent
from . import jwt_utils
from .serializers import (
    ComunaSerializer, DocumentoPerfilSerializer, LoginSerializer, PublicacionDetailSerializer,
    PublicacionListSerializer, RegionSerializer, TipoCuentaSerializer, UsuarioMeSerializer,
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


class PerfilView(APIView):
    """
    `PUT /api/auth/perfil/` — equivalente API de `editar_perfil_view`, mismo
    criterio de reuso que `RegistroView`: `EditarPerfilForm` (forms.py) se
    usa tal cual, incluida su validación de email duplicado (excluyendo al
    propio usuario) y el manejo de `foto_perfil` (opcional — si el cliente
    no manda un archivo nuevo, `request.FILES` llega vacío y el `ModelForm`
    deja la foto existente sin tocar, mismo comportamiento que ya tenía el
    formulario del template).

    `region` no es un campo real de `Usuario` (solo existe en el Form para
    manejar el cascade región→comuna, igual que en `RegistroForm`) — el
    cliente lo manda igual, pero nunca se guarda por separado; lo que
    persiste es `comuna`, que ya trae su región.
    """
    def put(self, request):
        form = EditarPerfilForm(request.data, request.FILES, instance=request.user)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        form.save()
        logger.info('Perfil actualizado (api): usuario_id=%s', request.user.id_usuario)
        return Response(UsuarioMeSerializer(request.user).data)


class PerfilProveedorView(APIView):
    """
    `PUT /api/auth/perfil-proveedor/` — equivalente API de
    `crear_perfil_view`, mismo criterio de reuso que `PerfilView`:
    `CrearPerfilForm` (forms.py) se usa tal cual, incluida la fusión de
    `areas_servicio` (checkboxes) + `otra_area_servicio` (texto libre) en
    un solo string separado por comas.

    Los certificados/documentos no son un campo del Form (mismo motivo que
    `PublicacionForm`: Django no tiene un FileField multi-archivo) — se
    leen de `request.FILES.getlist('documentos')`, tope
    `MAX_DOCUMENTOS_PUBLICACION` y mismo estado inicial "No firmado"
    (pk=2, ver comentario en `crear_perfil_view`) que el flujo de
    template. Los que no pasan `full_clean()` (formato/tamaño/contenido
    inválido) se listan en `documentos_rechazados` en vez de devolver un
    400 — igual que `crear_perfil_view`, el resto del perfil sí se guarda.
    """
    def put(self, request):
        form = CrearPerfilForm(request.data, request.FILES, instance=request.user)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        form.save()

        rechazados = []
        estado_no_firmado = EstadoDocumento.objects.filter(pk=2).first()  # 2 = No firmado (ver fixture catalogos_iniciales)
        for archivo in request.FILES.getlist('documentos')[:vistas_legacy.MAX_DOCUMENTOS_PUBLICACION]:
            documento = Documento(usuario=request.user, nombre_documento=archivo.name[:60], archivo_subido=archivo, estado_documento=estado_no_firmado)
            try:
                documento.full_clean()
            except ValidationError:
                rechazados.append(archivo.name)
                continue
            documento.save()

        logger.info('Perfil de proveedor actualizado (api): usuario_id=%s', request.user.id_usuario)
        return Response({'usuario': UsuarioMeSerializer(request.user).data, 'documentos_rechazados': rechazados})


class DocumentoPerfilListView(generics.ListAPIView):
    """`GET /api/auth/perfil-proveedor/documentos/` — certificados/documentos del proveedor logueado, equivalente a la lista que muestra `crearperfil.html`."""
    serializer_class = DocumentoPerfilSerializer
    pagination_class = None

    def get_queryset(self):
        return Documento.objects.filter(usuario=self.request.user, publicacion__isnull=True).order_by('-fecha_subida_documento')


class DocumentoPerfilEliminarView(APIView):
    """`DELETE /api/auth/perfil-proveedor/documentos/<id>/` — equivalente API de `documento_perfil_eliminar_view`: solo el dueño, y solo si no quedó ligado a ninguna Publicacion (`get_object_or_404` devuelve 404, no 403, para no confirmar que el documento existe si es de otro usuario)."""
    def delete(self, request, documento_id):
        documento = get_object_or_404(Documento, pk=documento_id, usuario=request.user, publicacion__isnull=True)
        documento.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PreferenciasView(APIView):
    """
    `PUT /api/auth/preferencias/` — equivalente API de la mitad
    "preferencias" de `preferencias_cuenta_view` (el toggle
    `notificaciones_sonido`, el único con efecto real hoy — ver
    CLAUDE.md/Known Issues). El cambio de contraseña es un endpoint
    aparte (`CambiarPasswordView`), igual que en el template son dos
    `<form>` independientes en la misma página.
    """
    def put(self, request):
        form = PreferenciasCuentaForm(request.data, instance=request.user)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        form.save()
        return Response(UsuarioMeSerializer(request.user).data)


class CambiarPasswordView(APIView):
    """`POST /api/auth/cambiar-password/` — equivalente API de la mitad "password" de `preferencias_cuenta_view`: reusa `CambiarPasswordForm`, que exige la contraseña actual además de las reglas de `AUTH_PASSWORD_VALIDATORS` para la nueva."""
    def post(self, request):
        form = CambiarPasswordForm(request.data, usuario=request.user)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(form.cleaned_data['password'])
        request.user.save(update_fields=['password'])
        logger.info('Contraseña cambiada desde preferencias de cuenta (api): usuario_id=%s', request.user.id_usuario)
        return Response({'detail': 'Contraseña actualizada.'})


class CategoriasListView(APIView):
    """`GET /api/catalogos/categorias/` — lista fija de categorías de servicio (`CATEGORIAS_PUBLICACION`, forms.py), usada por el checkbox multi-select de áreas de servicio del perfil de proveedor."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(list(CATEGORIAS_PUBLICACION))


class RecuperarView(APIView):
    """
    `POST /api/auth/recuperar/` — Paso 1, equivalente API de
    `recuperar_view`: mismo rate-limit por (IP, email) (reusa
    `vistas_legacy.MAX_INTENTOS_RECUPERAR`/`VENTANA_INTENTOS_RECUPERAR`) y
    mismo mensaje de éxito "genérico" exista o no la cuenta, para no
    convertir el endpoint en una forma de confirmar qué correos están
    registrados.

    A diferencia de `recuperar_view` (que arma el link con
    `request.build_absolute_uri()`, apuntando al propio Django), el correo
    que manda este endpoint apunta a `settings.IONIC_FRONTEND_URL` — quien
    llama a `/api/auth/recuperar/` es el cliente Ionic, así que el paso 2
    también tiene que resolverse ahí, no en una página de Django.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        form = RecuperarForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        email = form.cleaned_data['email']
        clave_intentos = f'recuperar_intentos:{vistas_legacy._obtener_ip_cliente(request)}:{email.strip().lower()}'
        if cache.get(clave_intentos, 0) >= vistas_legacy.MAX_INTENTOS_RECUPERAR:
            return Response(
                {'detail': 'Demasiadas solicitudes. Probá de nuevo en unos minutos.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        try:
            cache.incr(clave_intentos)
        except ValueError:
            cache.set(clave_intentos, 1, vistas_legacy.VENTANA_INTENTOS_RECUPERAR)

        usuario = Usuario.objects.filter(email=email, telefono=form.cleaned_data['telefono']).first()
        if usuario:
            token = vistas_legacy._generar_token_recuperacion(usuario)
            url_reset = f'{settings.IONIC_FRONTEND_URL}/recuperar/confirmar/{token}'
            send_mail(
                'Recuperar tu contraseña de KeyServ',
                f'Hola {usuario.nombre_usuario},\n\n'
                f'Para elegir una nueva contraseña entrá a este enlace (válido por 1 hora):\n{url_reset}\n\n'
                'Si no pediste esto, podés ignorar este correo — tu contraseña actual sigue siendo válida.',
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=True,
            )
            logger.info('Correo de recuperación de contraseña enviado (api): usuario_id=%s', usuario.id_usuario)

        return Response({
            'detail': 'Si el correo y el teléfono coinciden con una cuenta, te enviamos un enlace para restablecer tu contraseña.',
        })


class RecuperarConfirmarView(APIView):
    """
    `GET`/`POST /api/auth/recuperar/confirmar/<token>/` — Paso 2, equivalente
    API de `recuperar_confirmar_view`. `GET` solo valida el token (para que
    la pantalla de Ionic pueda mostrar "enlace vencido" antes de que la
    persona llene el formulario en vano); `POST` reusa `NuevaPasswordForm`
    para elegir la contraseña nueva. Ninguno de los dos devuelve datos del
    usuario — el token ya es suficientemente sensible, no hace falta
    confirmar de quién es en la respuesta.
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        if not vistas_legacy._usuario_desde_token_recuperacion(token):
            return Response({'detail': 'Este enlace no es válido o ya venció.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'valido': True})

    def post(self, request, token):
        usuario = vistas_legacy._usuario_desde_token_recuperacion(token)
        if not usuario:
            return Response(
                {'detail': 'Este enlace no es válido o ya venció. Pedí uno nuevo.'}, status=status.HTTP_404_NOT_FOUND,
            )

        form = NuevaPasswordForm(request.data, usuario=usuario)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario.set_password(form.cleaned_data['password'])
        usuario.save(update_fields=['password'])
        logger.info('Contraseña restablecida vía recuperación (api): usuario_id=%s', usuario.id_usuario)
        return Response({'detail': 'Contraseña actualizada. Ya podés iniciar sesión.'})


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
