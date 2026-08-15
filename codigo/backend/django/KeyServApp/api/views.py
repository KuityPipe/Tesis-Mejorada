"""
Vistas de la API REST (Ionic/Angular) — ver plan de migración. Reutilizan a
propósito la lógica de seguridad ya probada de `KeyServApp/views.py` (límite
de intentos de login, registro de accesos sospechosos) en vez de
reimplementarla: importar los helpers "privados" de ese módulo es preferible
a duplicar el mismo bloqueo por (IP, email) en dos lugares que puedan
divergir con el tiempo.
"""
import logging
import os

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models import Q, Value
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import biometria
from .. import pagos
from .. import views as vistas_legacy
from ..forms import (
    CambiarPasswordForm, CATEGORIAS_PUBLICACION, ContactoForm, CrearPerfilForm, EditarPerfilForm, MensajeForm,
    MontoAcordadoForm, NuevaPasswordForm, PreferenciasCuentaForm, PublicacionForm, ReautenticacionForm,
    RecuperarForm, RegistroForm, ValoracionForm,
)
from ..models import (
    Comuna, Contratacion, Conversacion, Documento, EstadoConsulta, EstadoDocumento,
    HistorialEstadoContratacion, Imagenes, ItemPresupuesto, Mensaje, Pago, Publicaciones, Region,
    Transaccion, TipoCuenta, Usuario, UsuarioConversacion, Valoracion, ValoracionImagen,
)
from ..views import Unaccent
from . import jwt_utils
from .serializers import (
    ComunaSerializer, ContratacionDetailSerializer, ContratacionListSerializer, ConversacionResumenSerializer,
    DocumentoPerfilSerializer, LoginSerializer, MensajeSerializer, PagoHistorialSerializer,
    PublicacionDetailSerializer, PublicacionListSerializer, PublicacionPropiaSerializer, RegionSerializer,
    ResenaRecibidaSerializer, TipoCuentaSerializer, UsuarioMeSerializer, ValoracionSerializer,
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


class ContactoView(APIView):
    """
    `POST /api/contacto/` — equivalente de `contacto_view` (views.py),
    reusa `ContactoForm` igual que `RegistroView` reusa `RegistroForm`
    (mismo motivo: una sola validación de las reglas de negocio en vez de
    dos que puedan divergir). Público (`AllowAny`) — cualquiera puede
    escribir a soporte sin sesión iniciada; si el caller sí manda un JWT
    válido (`request.user.is_authenticated`), se usan sus propios datos
    para `nombre_contacto`/`email_contacto`, igual que `contacto_view` hace
    con la sesión de Django.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        usuario = request.user if request.user.is_authenticated else None
        form = ContactoForm(request.data, requiere_datos_contacto=not bool(usuario))
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        consulta = form.save(commit=False)
        consulta.usuario_consulta = usuario
        consulta.estado_consulta = EstadoConsulta.objects.filter(pk=1).first()  # 1 = Abierta (ver migración 0006)
        if usuario:
            consulta.nombre_contacto = str(usuario)
            consulta.email_contacto = usuario.email
        consulta.save()
        logger.info('Consulta creada (api): id=%s usuario=%s', consulta.id_consulta, usuario.id_usuario if usuario else None)
        return Response({'detalle': 'Recibimos tu mensaje — te contactaremos pronto.'}, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """`GET /api/auth/me/` — perfil del usuario autenticado (requiere `Authorization: Bearer <access token>`, ver JWTAuthentication)."""

    def get(self, request):
        return Response(UsuarioMeSerializer(request.user).data)


class VerificarBiometriaNativaView(APIView):
    """
    `POST /api/auth/verificar-biometria-nativa/` — marca
    `Usuario.verificado_biometricamente = True` tras un desbloqueo
    biométrico nativo exitoso en el dispositivo (Face ID / huella del
    teléfono, vía `@capgo/capacitor-native-biometric` del lado Ionic,
    ver Fase 5 del plan de migración), en vez del reconocimiento facial
    pesado del servidor (`/rostro/`) o la huella dactilar por imagen
    (`/huella/`).

    Sin verificación adicional más allá del JWT a propósito — decisión
    tomada con el usuario: a diferencia de esos dos flujos, acá el
    servidor nunca ve ni puede ver el dato biométrico en sí (Face ID/
    huella nativos se validan enteramente dentro del enclave seguro del
    dispositivo; el plugin solo le informa a la app "sí" o "no"). La
    única garantía real que el servidor puede pedir es que quien llama
    ya tiene una sesión JWT válida — exactamente lo que hace, mismo
    criterio que confiar en el device en apps bancarias/de producción.
    """

    def post(self, request):
        usuario = request.user
        usuario.verificado_biometricamente = True
        usuario.save(update_fields=['verificado_biometricamente'])
        logger.info('Verificación biométrica nativa exitosa (api): usuario_id=%s', usuario.id_usuario)
        return Response(UsuarioMeSerializer(usuario).data)


class RostroEstadoView(APIView):
    """
    `GET /api/auth/rostro/estado/` — equivalente API de la variable
    `tiene_referencia` que `rostro_view` le pasa a la plantilla: si el
    usuario ya registró un rostro de referencia, sin exponer el encoding
    en sí — `UsuarioMeSerializer` nunca lo incluye a propósito (dato
    biométrico crudo), así que Ionic necesita este endpoint aparte para
    decidir si mostrar "registrar" o "verificar".
    """

    def get(self, request):
        return Response({'tiene_referencia': bool(request.user.encoding_facial)})


class RostroRegistrarView(APIView):
    """
    `POST /api/auth/rostro/registrar/` — equivalente API de
    `registro_rostro_view`. Sube una ráfaga de referencia (`rostro_frames`,
    multi-archivo, mismo campo y mismo helper —
    `vistas_legacy._obtener_frames_captura` — que usa el template),
    calcula su encoding facial (prueba de vida por parpadeo) y lo guarda
    en `Usuario.encoding_facial`. No marca al usuario como verificado
    todavía — eso requiere una verificación aparte (`RostroVerificarView`),
    igual que el flujo de template. Reemplaza cualquier encoding anterior
    si el usuario vuelve a registrar su rostro.
    """

    def post(self, request):
        try:
            rutas = vistas_legacy._obtener_frames_captura(request)
        except ValidationError as error:
            detail = ' '.join(error.messages) if hasattr(error, 'messages') else str(error)
            return Response({'detail': detail}, status=status.HTTP_400_BAD_REQUEST)

        try:
            encoding = biometria.calcular_encoding_facial(rutas)
        finally:
            for ruta in rutas:
                os.remove(ruta)

        if encoding is None:
            return Response(
                {'detail': 'No se pudo validar la prueba de vida — mirá a la cámara, parpadeá una vez durante la captura, y asegurate de tener buena luz.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.encoding_facial = encoding
        request.user.save()
        logger.info('Rostro de referencia registrado (api): usuario_id=%s', request.user.id_usuario)
        return Response({'detail': 'Rostro registrado. Ahora podés verificarlo.'})


class RostroVerificarView(APIView):
    """`POST /api/auth/rostro/verificar/` — equivalente API de `verificacion_facial_view`: compara una ráfaga nueva contra `Usuario.encoding_facial` y, si coincide, marca `verificado_biometricamente = True`."""

    def post(self, request):
        usuario = request.user
        if not usuario.encoding_facial:
            return Response({'detail': 'Todavía no registraste un rostro de referencia.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rutas = vistas_legacy._obtener_frames_captura(request)
        except ValidationError as error:
            detail = ' '.join(error.messages) if hasattr(error, 'messages') else str(error)
            return Response({'detail': detail}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resultado = biometria.verificar_rostro_usuario(usuario.encoding_facial, rutas)
        finally:
            for ruta in rutas:
                os.remove(ruta)

        if resultado is True:
            usuario.verificado_biometricamente = True
            usuario.save()
            logger.info('Rostro verificado (api): usuario_id=%s', usuario.id_usuario)
            return Response(UsuarioMeSerializer(usuario).data)
        if resultado is False:
            return Response({'detail': 'El rostro no coincide con el registrado. Intentá nuevamente.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'No se pudo procesar la foto. Intentá nuevamente.'}, status=status.HTTP_400_BAD_REQUEST)


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


class AlternarProveedorView(APIView):
    """
    `POST /api/auth/alternar-proveedor/` — equivalente API de
    `alternar_proveedor_view`: única forma real de cambiar `es_proveedor`
    después del registro. Sin body ni Form que reusar acá (el original es
    un botón que solo invierte el booleano) — simple `not` + `save`,
    devuelve el perfil actualizado para que el cliente Ionic refresque su
    estado local sin una segunda llamada a `GET /api/auth/me/`.
    """
    def post(self, request):
        usuario = request.user
        usuario.es_proveedor = not usuario.es_proveedor
        usuario.save(update_fields=['es_proveedor'])
        logger.info('Proveedor alternado (api): usuario_id=%s es_proveedor=%s', usuario.id_usuario, usuario.es_proveedor)
        return Response(UsuarioMeSerializer(usuario).data)


class ResenasRecibidasView(generics.ListAPIView):
    """`GET /api/perfil/resenas-recibidas/` — equivalente API de la parte de `perfil_view` que lista `resenas_recibidas`. Sin filtrar por `estado_moderacion` a propósito, igual que el template — el propio receptor ve sus reseñas pendientes/rechazadas también, no solo las aprobadas (a diferencia del catálogo público, que sí filtra)."""
    serializer_class = ResenaRecibidaSerializer
    pagination_class = None

    def get_queryset(self):
        return Valoracion.objects.filter(usuario_receptor=self.request.user).select_related('usuario_emisor').order_by('-fecha_valoracion')


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


class PublicacionCrearView(APIView):
    """
    `POST /api/publicaciones/crear/` — equivalente API de
    `publicacion_crear_view` (views.py), mismo criterio de reuso que
    `PerfilProveedorView`: `PublicacionForm` (forms.py) tal cual, incluida
    la resolución de categoría "Otra" en `form.clean()`. Imágenes y
    documentos no son campos del Form (Django no tiene un FileField
    multi-archivo) — se leen de `request.FILES.getlist('imagenes'/
    'documentos')`, mismos topes `MAX_IMAGENES_PUBLICACION`/
    `MAX_DOCUMENTOS_PUBLICACION` y mismo estado inicial "No firmado"
    (pk=2) para los documentos. Los archivos que no pasan `full_clean()`
    (formato/tamaño/contenido inválido) no tiran un 400 — se listan en
    `imagenes_rechazadas`/`documentos_rechazados`, la publicación se crea
    igual con el resto, mismo trade-off que `ValoracionCrearView`/
    `PerfilProveedorView`.
    """
    def post(self, request):
        if not request.user.es_proveedor:
            return Response({'detail': 'Solo los proveedores pueden publicar servicios.'}, status=status.HTTP_403_FORBIDDEN)

        form = PublicacionForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        publicacion = form.save(commit=False)
        publicacion.usuario_publicador = request.user
        publicacion.save()

        imagenes_rechazadas = []
        for archivo in request.FILES.getlist('imagenes')[:vistas_legacy.MAX_IMAGENES_PUBLICACION]:
            imagen = Imagenes(publicacion=publicacion, archivo=archivo)
            try:
                imagen.full_clean()
            except ValidationError:
                imagenes_rechazadas.append(archivo.name)
                continue
            imagen.save()

        documentos_rechazados = []
        estado_no_firmado = EstadoDocumento.objects.filter(pk=2).first()  # 2 = No firmado (ver fixture catalogos_iniciales)
        for archivo in request.FILES.getlist('documentos')[:vistas_legacy.MAX_DOCUMENTOS_PUBLICACION]:
            documento = Documento(publicacion=publicacion, usuario=request.user, nombre_documento=archivo.name[:60], archivo_subido=archivo, estado_documento=estado_no_firmado)
            try:
                documento.full_clean()
            except ValidationError:
                documentos_rechazados.append(archivo.name)
                continue
            documento.save()

        logger.info('Publicación creada (api): id=%s usuario=%s', publicacion.id_publicacion, request.user.id_usuario)
        return Response({
            'publicacion': PublicacionDetailSerializer(publicacion).data,
            'imagenes_rechazadas': imagenes_rechazadas,
            'documentos_rechazados': documentos_rechazados,
        }, status=status.HTTP_201_CREATED)


class MisPublicacionesView(generics.ListAPIView):
    """`GET /api/publicaciones/mias/` — equivalente API de la sección "Mis publicaciones" de `perfil.html`: publicaciones propias con cualquier `estado_moderacion` (no solo `APROBADA`, a diferencia de `PublicacionListView`), para que el proveedor vea si están pendientes/rechazadas."""
    serializer_class = PublicacionPropiaSerializer
    pagination_class = None

    def get_queryset(self):
        return Publicaciones.objects.filter(usuario_publicador=self.request.user).prefetch_related('imagenes').order_by('-fecha_publicacion')


def _parsear_items_presupuesto_api(data):
    """
    Equivalente API de `vistas_legacy._parsear_items_presupuesto` — misma
    validación fila por fila (descripción no vacía, monto entero positivo,
    categoría dentro de las válidas o `OTRO`), pero sobre `data.get('items')`
    (una lista de objetos JSON, `[{descripcion, categoria, monto}, ...]`) en
    vez de `request.POST.getlist('item_descripcion')`/... — el original está
    atado a listas paralelas de un `<form>` HTML, que no es la forma en que
    un cliente JSON manda esto, así que no se pudo reusar tal cual.
    """
    items = []
    categorias_validas = dict(ItemPresupuesto.CATEGORIAS_ITEM)
    for fila in (data.get('items') or []):
        descripcion = (fila.get('descripcion') or '').strip()[:200]
        if not descripcion:
            continue
        try:
            monto = int(fila.get('monto'))
        except (TypeError, ValueError):
            continue
        if monto <= 0:
            continue
        categoria = fila.get('categoria')
        if categoria not in categorias_validas:
            categoria = ItemPresupuesto.OTRO
        items.append((descripcion, categoria, monto))
    return items


class ContratacionListCreateView(APIView):
    """`GET`/`POST /api/contrataciones/` — equivalente API de `reservas_view` (listado) + `contratacion_crear_view` (creación, "solicitar")."""

    def get(self, request):
        contrataciones = Contratacion.objects.filter(
            Q(cliente=request.user) | Q(proveedor=request.user),
        ).distinct().select_related('publicacion', 'cliente', 'proveedor').prefetch_related('publicacion__imagenes').order_by('-fecha_creacion')
        return Response(ContratacionListSerializer(contrataciones, many=True).data)

    def post(self, request):
        publicacion = get_object_or_404(Publicaciones, pk=request.data.get('publicacion'))
        cliente = request.user
        proveedor = publicacion.usuario_publicador

        if cliente == proveedor:
            return Response({'detail': 'No podés contratar tu propia publicación.'}, status=status.HTTP_400_BAD_REQUEST)

        ya_activa = Contratacion.objects.filter(
            publicacion=publicacion, cliente=cliente,
            estado__in=[Contratacion.SOLICITADA, Contratacion.CONFIRMADA, Contratacion.EN_CURSO],
        ).exists()
        if ya_activa:
            return Response(
                {'detail': 'Ya tenés una solicitud en curso para este servicio — esperá a que se complete antes de volver a pedirlo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contratacion = Contratacion.objects.create(publicacion=publicacion, cliente=cliente, proveedor=proveedor)
        HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=Contratacion.SOLICITADA)
        conversacion = vistas_legacy._obtener_o_crear_conversacion_de_contratacion(contratacion)
        Mensaje.objects.create(
            conversacion=conversacion, usuario=cliente,
            contenido=f'[Sistema] {cliente} solicitó contratar "{publicacion.titulo}". Contratación #{contratacion.id_contratacion}.',
        )
        logger.info('Contratación solicitada (api): id=%s cliente=%s proveedor=%s', contratacion.id_contratacion, cliente.id_usuario, proveedor.id_usuario)
        return Response(ContratacionDetailSerializer(contratacion).data, status=status.HTTP_201_CREATED)


class ContratacionDetailView(APIView):
    """`GET /api/contrataciones/<id>/` — equivalente API de la mitad "detalle" de `contratacion_detalle_view` (todo menos el chat, ver `ContratacionMensajesView`). 404 (no 403) para una contratación ajena, mismo criterio que `documento_descargar_view` — no confirmarle a quien pregunta que el recurso existe."""

    def get(self, request, contratacion_id):
        contratacion = get_object_or_404(
            Contratacion.objects.select_related('publicacion', 'cliente', 'proveedor').prefetch_related(
                'publicacion__imagenes', 'historial_estados', 'items_presupuesto', 'valoracion__imagenes',
            ),
            pk=contratacion_id,
        )
        if request.user not in (contratacion.cliente, contratacion.proveedor):
            vistas_legacy._registrar_intento_sospechoso(request, request.user, 'contratacion', contratacion_id, 'contratación ajena (api)')
            raise Http404()
        return Response(ContratacionDetailSerializer(contratacion).data)


class ContratacionMensajesView(APIView):
    """`GET`/`POST /api/contrataciones/<id>/mensajes/` — equivalente API de la parte de chat embebida en `contratacion_detalle_view`. `GET` también marca `ultimo_leido`, igual que el template."""

    def _obtener_contratacion(self, request, contratacion_id):
        contratacion = get_object_or_404(Contratacion, pk=contratacion_id)
        if request.user not in (contratacion.cliente, contratacion.proveedor):
            vistas_legacy._registrar_intento_sospechoso(request, request.user, 'contratacion', contratacion_id, 'contratación ajena (api, mensajes)')
            raise Http404()
        return contratacion

    def get(self, request, contratacion_id):
        contratacion = self._obtener_contratacion(request, contratacion_id)
        conversacion = vistas_legacy._obtener_o_crear_conversacion_de_contratacion(contratacion)
        participacion = UsuarioConversacion.objects.filter(usuario=request.user, conversacion=conversacion).first()
        if participacion:
            participacion.ultimo_leido = timezone.now()
            participacion.save(update_fields=['ultimo_leido'])
        mensajes = Mensaje.objects.filter(conversacion=conversacion).select_related('usuario').order_by('fecha_envio')
        return Response(MensajeSerializer(mensajes, many=True).data)

    def post(self, request, contratacion_id):
        contratacion = self._obtener_contratacion(request, contratacion_id)
        form = MensajeForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        conversacion = vistas_legacy._obtener_o_crear_conversacion_de_contratacion(contratacion)
        mensaje = form.save(commit=False)
        mensaje.conversacion = conversacion
        mensaje.usuario = request.user
        mensaje.save()
        return Response(MensajeSerializer(mensaje).data, status=status.HTTP_201_CREATED)


class ConversacionListView(APIView):
    """
    `GET /api/conversaciones/` — equivalente API de `chat_view` (bandeja de
    entrada): un chat por trabajo, con badge de no leídos, contraparte y
    una vista previa del último mensaje. Arma la lista a mano igual que el
    template en vez de un `ModelSerializer` (ver `ConversacionResumenSerializer`)
    porque `no_leidos`/`ultimo_mensaje`/`contraparte` no son campos reales
    de `Conversacion` — se calculan por conversación, mismo criterio que
    `chat_view` ya hacía del lado template.
    """
    def get(self, request):
        usuario = request.user
        conversacion_ids = UsuarioConversacion.objects.filter(usuario=usuario).values_list('conversacion_id', flat=True)
        conversaciones = Conversacion.objects.filter(id_conversacion__in=conversacion_ids).select_related(
            'contratacion__publicacion', 'contratacion__cliente', 'contratacion__proveedor',
        ).order_by('-fecha_creacion')
        no_leidos_map = vistas_legacy._mensajes_no_leidos_por_conversacion(usuario)

        datos = []
        for conv in conversaciones:
            ultimo = Mensaje.objects.filter(conversacion=conv).select_related('usuario').order_by('-fecha_envio').first()
            contraparte = None
            if conv.contratacion_id:
                contraparte = conv.contratacion.proveedor if usuario == conv.contratacion.cliente else conv.contratacion.cliente
            datos.append({
                'id_conversacion': conv.id_conversacion,
                'contratacion_id': conv.contratacion_id,
                'publicacion_titulo': conv.contratacion.publicacion.titulo if conv.contratacion_id else None,
                'contratacion_estado': conv.contratacion.estado if conv.contratacion_id else None,
                'contraparte_nombre': str(contraparte) if contraparte else conv.nombre_conversacion,
                'no_leidos': no_leidos_map.get(conv.id_conversacion, 0),
                'ultimo_mensaje_contenido': ultimo.contenido if ultimo else None,
                'ultimo_mensaje_fecha': ultimo.fecha_envio if ultimo else None,
                'ultimo_mensaje_es_propio': bool(ultimo and ultimo.usuario_id == usuario.id_usuario),
            })
        return Response(ConversacionResumenSerializer(datos, many=True).data)


class MensajesNoLeidosView(APIView):
    """
    `GET /api/mensajes/no-leidos/` — equivalente API de `mensajes_no_leidos_ajax`:
    endpoint liviano (solo el total, no la lista completa de conversaciones)
    para el polling del badge de notificaciones del header en Ionic (ver
    `mensajes/conversaciones.ts` y `core/notificaciones.ts`), cada ~15s —
    mismo motivo que el original: evitar traer `ConversacionListView`
    entera (con preview de último mensaje por chat) solo para un contador.
    """
    def get(self, request):
        return Response({'no_leidos': vistas_legacy.contar_mensajes_no_leidos(request.user)})


class ContratacionConfirmarView(APIView):
    """
    `POST /api/contrataciones/<id>/confirmar/` — equivalente API de
    `contratacion_confirmar_view` (el PROVEEDOR acepta, SOLICITADA ->
    CONFIRMADA). Reusa `ReautenticacionForm`/`MontoAcordadoForm` igual que
    el resto de la migración, y el mismo rate-limit por (usuario,
    contratación) (`vistas_legacy._reautenticacion_bloqueada`/
    `_registrar_intento_reautenticacion`) — importado, no reimplementado,
    para que un límite no pueda divergir del otro.

    Body esperado: `password` (re-auth), y opcionalmente `monto` (entero) o
    `items` (lista de `{descripcion, categoria, monto}` — ver
    `_parsear_items_presupuesto_api`); si se manda `items` con al menos una
    fila válida, el monto acordado es la suma de esos ítems y `monto` se
    ignora, mismo criterio que la hoja de presupuesto del template.
    """

    def post(self, request, contratacion_id):
        contratacion = get_object_or_404(
            Contratacion.objects.select_related('publicacion'), pk=contratacion_id, estado=Contratacion.SOLICITADA,
        )
        usuario = request.user
        if usuario != contratacion.proveedor:
            vistas_legacy._registrar_intento_sospechoso(request, usuario, 'contratacion_confirmar', contratacion_id, 'no es el proveedor (api)')
            return Response({'detail': 'Solo el proveedor puede confirmar esta contratación.'}, status=status.HTTP_403_FORBIDDEN)

        if vistas_legacy._reautenticacion_bloqueada(usuario, contratacion_id):
            vistas_legacy._registrar_intento_sospechoso(request, usuario, 'reauth_bloqueado_confirmar', contratacion_id, 'demasiados intentos fallidos (api)')
            return Response({'detail': 'Demasiados intentos fallidos. Probá de nuevo en unos minutos.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        form = ReautenticacionForm(request.data)
        if not (form.is_valid() and usuario.check_password(form.cleaned_data['password'])):
            vistas_legacy._registrar_intento_reautenticacion(usuario, contratacion_id, exito=False)
            return Response({'detail': 'Contraseña incorrecta — no se pudo confirmar.'}, status=status.HTTP_400_BAD_REQUEST)

        vistas_legacy._registrar_intento_reautenticacion(usuario, contratacion_id, exito=True)
        items_presupuesto = _parsear_items_presupuesto_api(request.data)
        monto_acordado = contratacion.publicacion.precio
        if items_presupuesto:
            monto_acordado = sum(monto for _, _, monto in items_presupuesto)
        else:
            monto_form = MontoAcordadoForm({'monto': request.data.get('monto')})
            if monto_form.is_valid() and monto_form.cleaned_data.get('monto'):
                monto_acordado = monto_form.cleaned_data['monto']

        contratacion.monto_acordado = monto_acordado
        contratacion.estado = Contratacion.CONFIRMADA
        contratacion.save()
        HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=Contratacion.CONFIRMADA)
        if items_presupuesto:
            ItemPresupuesto.objects.bulk_create([
                ItemPresupuesto(contratacion=contratacion, descripcion=descripcion, categoria=categoria, monto=monto, orden=indice)
                for indice, (descripcion, categoria, monto) in enumerate(items_presupuesto)
            ])
        logger.info('Contratación confirmada por el proveedor (api): id=%s monto_acordado=%s items_presupuesto=%s', contratacion.id_contratacion, monto_acordado, len(items_presupuesto))
        return Response(ContratacionDetailSerializer(contratacion).data)


class ContratacionCompletarView(APIView):
    """`POST /api/contrataciones/<id>/completar/` — equivalente API de `contratacion_completar_view` (el CLIENTE confirma que el servicio se completó, EN_CURSO -> COMPLETADA). Mismo criterio de reuso que `ContratacionConfirmarView`."""

    def post(self, request, contratacion_id):
        contratacion = get_object_or_404(Contratacion, pk=contratacion_id, estado=Contratacion.EN_CURSO)
        usuario = request.user
        if usuario != contratacion.cliente:
            vistas_legacy._registrar_intento_sospechoso(request, usuario, 'contratacion_completar', contratacion_id, 'no es el cliente (api)')
            return Response({'detail': 'Solo el cliente puede marcar la contratación como completada.'}, status=status.HTTP_403_FORBIDDEN)

        if vistas_legacy._reautenticacion_bloqueada(usuario, contratacion_id):
            vistas_legacy._registrar_intento_sospechoso(request, usuario, 'reauth_bloqueado_completar', contratacion_id, 'demasiados intentos fallidos (api)')
            return Response({'detail': 'Demasiados intentos fallidos. Probá de nuevo en unos minutos.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        form = ReautenticacionForm(request.data)
        if not (form.is_valid() and usuario.check_password(form.cleaned_data['password'])):
            vistas_legacy._registrar_intento_reautenticacion(usuario, contratacion_id, exito=False)
            return Response({'detail': 'Contraseña incorrecta — no se pudo completar.'}, status=status.HTTP_400_BAD_REQUEST)

        vistas_legacy._registrar_intento_reautenticacion(usuario, contratacion_id, exito=True)
        contratacion.estado = Contratacion.COMPLETADA
        contratacion.save()
        HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=Contratacion.COMPLETADA)
        logger.info('Contratación completada (api): id=%s', contratacion.id_contratacion)
        return Response(ContratacionDetailSerializer(contratacion).data)


class ValoracionCrearView(APIView):
    """
    `POST /api/contrataciones/<id>/valoracion/` — equivalente API de
    `valoracion_crear_view`: reusa `ValoracionForm`, sube fotos adjuntas con
    el mismo `validators.py` (byte-signature + Pillow) que el resto del
    sitio y recalcula el `Ranking` del proveedor. Las fotos rechazadas no
    tiran un 400 (la reseña ya se guardó) — se listan en
    `imagenes_rechazadas`, mismo criterio que `documentos_rechazados` en
    `PerfilProveedorView`.
    """

    def post(self, request, contratacion_id):
        contratacion = get_object_or_404(Contratacion, pk=contratacion_id, estado=Contratacion.COMPLETADA)
        emisor = request.user
        if emisor != contratacion.cliente:
            vistas_legacy._registrar_intento_sospechoso(request, emisor, 'valoracion_crear', contratacion_id, 'no es el cliente (api)')
            return Response({'detail': 'Solo el cliente puede calificar este trabajo.'}, status=status.HTTP_403_FORBIDDEN)
        if getattr(contratacion, 'valoracion', None) is not None:
            return Response({'detail': 'Ya calificaste este trabajo.'}, status=status.HTTP_400_BAD_REQUEST)

        form = ValoracionForm(request.data)
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

        valoracion = form.save(commit=False)
        valoracion.usuario_emisor = emisor
        valoracion.usuario_receptor = contratacion.proveedor
        valoracion.publicacion = contratacion.publicacion
        valoracion.contratacion = contratacion
        valoracion.save()

        rechazadas = []
        for archivo in request.FILES.getlist('imagenes')[:vistas_legacy.MAX_IMAGENES_VALORACION]:
            imagen = ValoracionImagen(valoracion=valoracion, archivo=archivo)
            try:
                imagen.full_clean()
            except ValidationError:
                rechazadas.append(archivo.name)
                continue
            imagen.save()

        vistas_legacy._recalcular_ranking(contratacion.proveedor)
        logger.info('Valoración creada (api): contratacion_id=%s emisor=%s', contratacion_id, emisor.id_usuario)
        return Response(
            {'valoracion': ValoracionSerializer(valoracion).data, 'imagenes_rechazadas': rechazadas},
            status=status.HTTP_201_CREATED,
        )


def _validar_pago_posible_api(request, contratacion_id):
    """
    Espejo de `vistas_legacy._validar_pago_posible`, pero devolviendo
    `(contratacion, Response|None)` en vez de `(contratacion,
    HttpResponseRedirect|None)` — acá no hay una página de reservas a la
    que mandar de vuelta, solo una respuesta de error para que el cliente
    Ionic la muestre. Mismos chequeos: dueño correcto (el cliente), estado
    CONFIRMADA, monto acordado real.
    """
    contratacion = get_object_or_404(
        Contratacion.objects.select_related('publicacion'), pk=contratacion_id, estado=Contratacion.CONFIRMADA,
    )
    usuario = request.user
    if usuario != contratacion.cliente:
        vistas_legacy._registrar_intento_sospechoso(request, usuario, 'pago_iniciar', contratacion_id, 'no es el cliente (api)')
        return None, Response({'detail': 'Solo el cliente puede pagar esta contratación.'}, status=status.HTTP_403_FORBIDDEN)
    if not contratacion.monto_acordado:
        return None, Response(
            {'detail': 'Esta contratación no tiene un monto acordado — no se puede cobrar.'}, status=status.HTTP_400_BAD_REQUEST,
        )
    return contratacion, None


class PagoWebpayIniciarView(APIView):
    """
    `POST /api/contrataciones/<id>/pagos/webpay/iniciar/` — equivalente
    API de `pago_webpay_iniciar_view`. En vez de renderizar la página con
    el `<form>` de auto-submit, devuelve `{token, url_pago}`: ese POST
    real a Transbank lo arma el propio cliente Ionic
    (`pago/webpay/webpay.page`), mismo truco que la plantilla pero del
    lado del navegador — Transbank exige un POST de `token_ws` a su URL,
    no una navegación GET común.

    `url_retorno` apunta a `settings.IONIC_FRONTEND_URL` en vez de una
    URL de Django, mismo criterio que `RecuperarView`: quien tiene que
    resolver el regreso es la app Ionic (`pago/webpay/retorno.page`), no
    una página de este sitio.
    """

    def post(self, request, contratacion_id):
        contratacion, error = _validar_pago_posible_api(request, contratacion_id)
        if error:
            return error

        pago, _creado = Pago.objects.get_or_create(
            contratacion=contratacion, defaults={'monto': contratacion.monto_acordado, 'metodo': Pago.WEBPAY},
        )
        if pago.estado == Pago.PAGADO:
            return Response({'detail': 'Esta contratación ya está pagada.'}, status=status.HTTP_400_BAD_REQUEST)
        pago.metodo = Pago.WEBPAY
        pago.monto = contratacion.monto_acordado
        pago.estado = Pago.PENDIENTE

        orden_compra = vistas_legacy._generar_orden_compra(contratacion)
        url_retorno = f'{settings.IONIC_FRONTEND_URL}/pago/webpay/retorno'
        try:
            token, url_pago = pagos.TransbankService().iniciar_transaccion(
                monto=pago.monto, orden_compra=orden_compra,
                session_id=f'usuario-{contratacion.cliente_id}', url_retorno=url_retorno,
            )
        except Exception:
            logger.exception('Error iniciando transacción Webpay (api): contratacion=%s', contratacion_id)
            return Response(
                {'detail': 'No pudimos conectar con Webpay en este momento. Probá de nuevo en unos minutos.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        pago.orden_compra = orden_compra
        pago.token_webpay = token
        pago.save()
        logger.info('Transacción Webpay iniciada (api): contratacion=%s pago=%s', contratacion_id, pago.id_pago)
        return Response({'token': token, 'url_pago': url_pago})


class PagoWebpayConfirmarView(APIView):
    """
    `POST /api/pagos/webpay/confirmar/` — equivalente API de
    `pago_webpay_retorno_view`. La pantalla de Ionic que recibe el
    retorno de Transbank (`pago/webpay/retorno.page`) manda acá lo que
    haya llegado en la query string (`token_ws` o `TBK_TOKEN`).

    Sin autenticación a propósito, igual que la vista de template (que
    solo tiene `@csrf_exempt`, no `@login_requerido`): quien redirige acá
    es el propio Transbank devolviendo al navegador del usuario, no una
    request nuestra — y el JWT de la sesión Ionic pudo haber quedado
    obsoleto durante el rato que el usuario estuvo en Transbank. La
    "credencial" real acá es el `token_ws` en sí (lo emitió Transbank,
    solo alguien que pasó por el flujo real lo tiene).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token_ws = request.data.get('token_ws')
        tbk_token = request.data.get('TBK_TOKEN')

        if not token_ws:
            pago = Pago.objects.filter(token_webpay=tbk_token).first() if tbk_token else None
            if pago and pago.estado == Pago.PENDIENTE:
                pago.estado = Pago.ANULADO
                pago.save()
            return Response({
                'aprobado': False,
                'mensaje': 'Cancelaste el pago en Webpay.' if tbk_token else 'El pago no se completó a tiempo.',
                'contratacion_id': pago.contratacion_id if pago else None,
            })

        pago = get_object_or_404(Pago, token_webpay=token_ws)
        try:
            respuesta = pagos.TransbankService().confirmar_transaccion(token_ws)
        except Exception:
            logger.exception('Error confirmando transacción Webpay (api): pago=%s', pago.id_pago)
            pago.estado = Pago.RECHAZADO
            pago.save()
            return Response({
                'aprobado': False, 'mensaje': 'No pudimos confirmar el pago con Webpay.', 'contratacion_id': pago.contratacion_id,
            })

        aprobado = respuesta.get('response_code') == 0 and respuesta.get('status') == 'AUTHORIZED'
        if aprobado:
            vistas_legacy._procesar_pago_aprobado(pago, respuesta)
            mensaje = f'Pago aprobado — código de autorización {respuesta.get("authorization_code")}.'
        else:
            pago.estado = Pago.RECHAZADO
            pago.respuesta_bruta = respuesta
            pago.save()
            logger.warning('Pago Webpay rechazado (api): pago=%s respuesta=%s', pago.id_pago, respuesta)
            mensaje = 'El pago fue rechazado por el banco emisor de la tarjeta.'

        return Response({'aprobado': aprobado, 'mensaje': mensaje, 'contratacion_id': pago.contratacion_id})


class PagoKhipuIniciarView(APIView):
    """
    `POST /api/contrataciones/<id>/pagos/khipu/iniciar/` — equivalente
    API de `pago_khipu_iniciar_view`. Devuelve `{payment_url}` para que
    Ionic navegue ahí directo (`window.location.href`) — a diferencia de
    Webpay, Khipu sí acepta una navegación GET común, no hace falta armar
    ningún `<form>` de auto-submit del lado del cliente.

    `url_notificacion` (el webhook) sigue apuntando a la URL de Django
    existente sin cambios (`pago_khipu_notificacion_view`) — lo llama
    Khipu servidor-a-servidor, nunca pasa por el navegador del usuario,
    así que no tiene sentido moverlo a Ionic como `url_retorno`.
    """

    def post(self, request, contratacion_id):
        contratacion, error = _validar_pago_posible_api(request, contratacion_id)
        if error:
            return error

        pago, _creado = Pago.objects.get_or_create(
            contratacion=contratacion, defaults={'monto': contratacion.monto_acordado, 'metodo': Pago.KHIPU},
        )
        if pago.estado == Pago.PAGADO:
            return Response({'detail': 'Esta contratación ya está pagada.'}, status=status.HTTP_400_BAD_REQUEST)
        pago.metodo = Pago.KHIPU
        pago.monto = contratacion.monto_acordado
        pago.estado = Pago.PENDIENTE
        pago.save()

        url_retorno = f'{settings.IONIC_FRONTEND_URL}/pago/khipu/retorno/{contratacion_id}'
        url_notificacion = request.build_absolute_uri(reverse('KeyServApp:pago_khipu_notificacion'))
        try:
            respuesta = pagos.KhipuService().crear_pago(
                monto=pago.monto,
                asunto=f'KeyServ — {contratacion.publicacion.titulo}'[:250],
                transaction_id=str(pago.id_pago),
                url_retorno=url_retorno, url_cancelacion=url_retorno, url_notificacion=url_notificacion,
            )
        except RuntimeError as error:
            # KHIPU_API_KEY no configurado — mensaje claro en vez de un 500 críptico.
            return Response({'detail': str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            logger.exception('Error iniciando pago Khipu (api): contratacion=%s', contratacion_id)
            return Response(
                {'detail': 'No pudimos conectar con Khipu en este momento. Probá de nuevo en unos minutos.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        pago.khipu_payment_id = respuesta.get('payment_id')
        pago.save()
        logger.info('Pago Khipu iniciado (api): contratacion=%s pago=%s', contratacion_id, pago.id_pago)
        return Response({'payment_url': respuesta.get('payment_url') or respuesta.get('simplified_transfer_url')})


class PagoKhipuEstadoView(APIView):
    """
    `GET /api/contrataciones/<id>/pagos/khipu/estado/` — equivalente API
    de `pago_khipu_retorno_view`: reconsulta contra Khipu si el pago
    sigue `PENDIENTE` (mejor UX al volver del banco — evita mostrar
    "pendiente" si el webhook todavía no llegó pero el pago ya está
    aprobado). La fuente de verdad real sigue siendo el webhook
    (`pago_khipu_notificacion_view`, sin cambios) — esto es solo para no
    hacer esperar al usuario mientras el webhook llega.
    """

    def get(self, request, contratacion_id):
        contratacion = get_object_or_404(Contratacion, pk=contratacion_id)
        if request.user not in (contratacion.cliente, contratacion.proveedor):
            vistas_legacy._registrar_intento_sospechoso(request, request.user, 'contratacion', contratacion_id, 'contratación ajena (api, pago khipu)')
            raise Http404()

        pago = getattr(contratacion, 'pago', None)
        if pago and pago.estado == Pago.PENDIENTE and pago.khipu_payment_id:
            try:
                respuesta = pagos.KhipuService().consultar_pago(pago.khipu_payment_id)
                if respuesta.get('status') == 'done':
                    vistas_legacy._procesar_pago_aprobado(pago, respuesta)
            except Exception:
                logger.exception('Error reconsultando pago Khipu al volver (api): pago=%s', pago.id_pago)

        if pago:
            pago.refresh_from_db()
        aprobado = bool(pago and pago.estado == Pago.PAGADO)
        if aprobado:
            mensaje = 'Pago confirmado por transferencia bancaria.'
        elif pago and pago.estado == Pago.PENDIENTE:
            mensaje = 'Todavía estamos esperando la confirmación de tu banco — puede tardar unos minutos.'
        else:
            mensaje = 'El pago no se completó.'
        return Response({'aprobado': aprobado, 'mensaje': mensaje})


class PagoHistorialView(generics.ListAPIView):
    """`GET /api/pagos/historial/` — equivalente API de `historial_pagos_view`: pagos del cliente logueado, más recientes primero. Nunca los del proveedor (`contratacion__cliente`, no `contratacion__proveedor`) — el proveedor ve el estado del pago de una contratación puntual dentro de esa contratación, no un historial propio (mismo criterio que el template)."""
    serializer_class = PagoHistorialSerializer
    pagination_class = None

    def get_queryset(self):
        return Pago.objects.filter(contratacion__cliente=self.request.user).select_related(
            'contratacion', 'contratacion__publicacion',
        ).order_by('-fecha_creacion')
