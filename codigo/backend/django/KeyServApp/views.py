"""
Vistas de KeyServ.

Refactor Fase 3 completo: la versión anterior tenía una función `register_view`
duplicada (una muerta, sobrescrita por la otra), nombres de campo que no
coincidían con `models.py` (rompía todo POST a /registro/ con TypeError),
y `sesion_view` que solo renderizaba el template sin loguear a nadie de
verdad. Ver codigo/viejo/backup_fase3/KeyServApp/views.py para la versión
previa completa.

Convención de esta fase: cada vista lleva un comentario corto explicando
qué hace (pedido explícito del usuario, para poder tocar el código a mano
más adelante sin tener que releer todo).
"""
import hashlib
import logging
import os
import secrets
import tempfile

from django.conf import settings
from django.contrib import messages
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Func, Q, Value
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .decorators import login_requerido, obtener_usuario_actual
from .forms import (
    RegistroForm, LoginForm, PublicacionForm, ValoracionForm, MensajeForm,
    ReautenticacionForm, ContactoForm, EditarPerfilForm, RecuperarForm,
    NuevaPasswordForm, MontoAcordadoForm, CambiarPasswordForm,
    PreferenciasCuentaForm, CrearPerfilForm,
)
from .models import (
    Comuna, Contratacion, Conversacion, Documento, EstadoConsulta,
    HistorialEstadoContratacion, Imagenes, IntentoAccesoSospechoso,
    ItemPresupuesto, Mensaje, Pago, Publicaciones, Ranking, Region,
    TipoCuenta, Transaccion, Usuario, UsuarioConversacion, Valoracion,
    ValoracionImagen,
)
from . import biometria, geolocalizacion, pagos
from . import validators

logger = logging.getLogger(__name__)


def _obtener_ip_cliente(request):
    """
    IP real del visitante. Si hay un proxy/balanceador delante (despliegue
    real detrás de nginx/similar), `REMOTE_ADDR` es la IP del proxy, no la
    del cliente — `X-Forwarded-For` trae la cadena real, y el primer valor
    es el cliente original. En este entorno de desarrollo (sin proxy) da lo
    mismo, siempre termina cayendo a `REMOTE_ADDR`.
    """
    adelante = request.META.get('HTTP_X_FORWARDED_FOR')
    if adelante:
        return adelante.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'sin-ip')


def _registrar_intento_sospechoso(request, usuario, recurso, recurso_id, detalle=''):
    """
    Deja constancia de un intento de acceder a algo de lo que `usuario` no es
    parte — una conversación, contratación o documento ajenos — o de un
    login/re-autenticación agotado a fuerza bruta (ahí `usuario` puede ser
    None: esto también cubre a quien todavía no tiene sesión iniciada). Se
    llama SOLO desde los puntos donde una vista deniega acceso por
    pertenencia o bloquea por demasiados intentos, nunca en un 404 común de
    "esto no existe": pedir el ID de otra persona no es un error de tipeo,
    es como mínimo curiosidad y en el peor caso reconocimiento manual antes
    de un ataque (probar /chat/1/, /chat/2/, ... a ver cuál abre).

    Queda en IntentoAccesoSospechoso (visible en /admin/, incluido el panel
    de alertas del dashboard) con IP, país/ciudad aproximados (geolocalizacion.py
    — base local, no se manda la IP a ningún servicio externo) y user-agent,
    y también en el logger de la consola/archivo de logs del servidor.
    """
    ip = _obtener_ip_cliente(request)
    pais, ciudad = geolocalizacion.geolocalizar_ip(ip)
    IntentoAccesoSospechoso.objects.create(
        usuario=usuario, ip=ip, pais=pais, ciudad=ciudad,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        ruta=request.path, recurso=recurso, recurso_id=str(recurso_id), detalle=detalle,
    )
    logger.warning(
        'ACCESO SOSPECHOSO: usuario=%s ip=%s (%s, %s) ruta=%s recurso=%s#%s %s',
        usuario.id_usuario if usuario else 'anónimo', ip, ciudad or '?', pais or '?', request.path, recurso, recurso_id, detalle,
    )


class Unaccent(Func):
    """Envuelve la función `unaccent` de Postgres (ver migración 0009_unaccent_extension)."""
    function = 'unaccent'


# ---------------------------------------------------------------------------
# Páginas simples (solo renderizan un template, sin lógica de negocio propia)
# ---------------------------------------------------------------------------

def paginicio_view(request):
    """
    Página de inicio: presentación de la marca + búsqueda rápida (RF004) que
    lleva al catálogo completo (`catalogo_view`). Muestra solo un puñado de
    publicaciones destacadas como teaser, no el listado completo.
    """
    destacadas = Publicaciones.objects.filter(estado_moderacion=Publicaciones.APROBADA).select_related(
        'usuario_publicador__ranking',
    ).prefetch_related('imagenes').order_by('-fecha_publicacion')[:4]
    return render(request, 'KeyServApp/paginicio.html', {'destacadas': destacadas})


PUBLICACIONES_POR_PAGINA = 20


def catalogo_view(request):
    """
    Catálogo completo de servicios (ventana aparte del home): búsqueda de
    texto + filtros reales por región del proveedor, calificación mínima y
    orden — pensada para una búsqueda más amplia que la barra rápida del home.

    Antes tenía un tope fijo de 40 resultados sin forma de ver el resto —
    ahora es un `Paginator` real (RF? "sin errores de enlace entre botones"
    empieza a importar de verdad apenas hay más publicaciones aprobadas que
    las que entran en una pantalla).
    """
    query = request.GET.get('q', '').strip()
    region_id = request.GET.get('region', '').strip()
    calificacion_min = request.GET.get('calificacion', '').strip()
    orden = request.GET.get('orden', 'recientes')

    publicaciones = Publicaciones.objects.filter(estado_moderacion=Publicaciones.APROBADA)
    if query:
        # Búsqueda sin distinción de tildes (RUT/dolor real reportado: nadie
        # escribe "gasfitería" con tilde en un buscador) vía la extensión
        # `unaccent` de Postgres — ver migración 0009_unaccent_extension.
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
        publicaciones = publicaciones.order_by('-usuario_publicador__ranking__puntuacion_promedio', '-fecha_publicacion')
    else:
        publicaciones = publicaciones.order_by('-fecha_publicacion')

    paginador = Paginator(publicaciones, PUBLICACIONES_POR_PAGINA)
    pagina = paginador.get_page(request.GET.get('page'))

    return render(request, 'KeyServApp/catalogo.html', {
        'publicaciones': pagina,
        'pagina': pagina,
        'total_publicaciones': paginador.count,
        'query': query,
        'regiones': Region.objects.all(),
        'region_seleccionada': region_id,
        'calificacion_seleccionada': calificacion_min,
        'orden_seleccionado': orden,
    })


def acerca_de_nosotros_view(request):
    """Página institucional estática 'Acerca de nosotros'."""
    return render(request, 'KeyServApp/Acercadeenosotros.html')


def contacto_view(request):
    """
    Página de contacto — crea una Consulta real (incidencia/ticket de
    soporte) que el equipo de moderación/admin atiende desde /admin/. Antes
    era 100% estática y no enviaba el formulario a ningún lado.
    """
    usuario = obtener_usuario_actual(request)
    if request.method == 'POST':
        form = ContactoForm(request.POST, requiere_datos_contacto=not bool(usuario))
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.usuario_consulta = usuario
            consulta.estado_consulta = EstadoConsulta.objects.filter(pk=1).first()  # 1 = Abierta (ver migración 0006)
            if usuario:
                consulta.nombre_contacto = str(usuario)
                consulta.email_contacto = usuario.email
            consulta.save()
            logger.info('Consulta creada: id=%s usuario=%s', consulta.id_consulta, usuario.id_usuario if usuario else None)
            messages.success(request, 'Recibimos tu mensaje — te contactaremos pronto.')
            return redirect('KeyServApp:contacto')
    else:
        form = ContactoForm(requiere_datos_contacto=not bool(usuario))

    return render(request, 'KeyServApp/contacto.html', {'form': form})


ESTADOS_TRABAJO_ACTUAL = ('SOLICITADA', 'CONFIRMADA', 'EN_CURSO')
ESTADOS_TRABAJO_PASADO = ('COMPLETADA', 'CANCELADA')


@login_requerido
def sesion_iniciada_view(request):
    """
    Home alternativo para un usuario ya logueado (Sesioniniciadainicio.html):
    trabajos actuales y pasados (como cliente o proveedor) + alertas de
    mensajes nuevos sin leer.
    """
    usuario = obtener_usuario_actual(request)
    contrataciones_usuario = (
        Contratacion.objects.filter(cliente=usuario) | Contratacion.objects.filter(proveedor=usuario)
    ).distinct().select_related('publicacion', 'cliente', 'proveedor').order_by('-fecha_actualizacion')

    trabajos_actuales = [c for c in contrataciones_usuario if c.estado in ESTADOS_TRABAJO_ACTUAL]
    trabajos_pasados = [c for c in contrataciones_usuario if c.estado in ESTADOS_TRABAJO_PASADO]

    no_leidos_por_conversacion = _mensajes_no_leidos_por_conversacion(usuario)
    alertas_mensajes = []
    if no_leidos_por_conversacion:
        conversaciones = Conversacion.objects.filter(id_conversacion__in=no_leidos_por_conversacion.keys())
        for conv in conversaciones:
            conv.no_leidos = no_leidos_por_conversacion[conv.id_conversacion]
            conv.ultimo_mensaje = Mensaje.objects.filter(conversacion=conv).order_by('-fecha_envio').first()
            alertas_mensajes.append(conv)

    return render(request, 'KeyServApp/Sesioniniciadainicio.html', {
        'usuario': usuario,
        'trabajos_actuales': trabajos_actuales,
        'trabajos_pasados': trabajos_pasados,
        'alertas_mensajes': alertas_mensajes,
    })


@login_requerido
def preferencias_cuenta_view(request):
    """
    Preferencias de la cuenta + cambio de contraseña + términos y
    condiciones — antes ninguno de los tres formularios de esta página
    guardaba nada. Dos forms independientes en la misma página (se
    distinguen por el campo oculto `form`), cada uno se procesa aparte.
    """
    usuario = obtener_usuario_actual(request)
    prefs_form = PreferenciasCuentaForm(instance=usuario)
    password_form = CambiarPasswordForm(usuario=usuario)

    if request.method == 'POST' and request.POST.get('form') == 'preferencias':
        prefs_form = PreferenciasCuentaForm(request.POST, instance=usuario)
        if prefs_form.is_valid():
            prefs_form.save()
            messages.success(request, 'Preferencias actualizadas.')
            return redirect('KeyServApp:preferencias_cuenta')
    elif request.method == 'POST' and request.POST.get('form') == 'password':
        password_form = CambiarPasswordForm(request.POST, usuario=usuario)
        if password_form.is_valid():
            usuario.set_password(password_form.cleaned_data['password'])
            usuario.save(update_fields=['password'])
            logger.info('Contraseña cambiada desde preferencias de cuenta: usuario_id=%s', usuario.id_usuario)
            messages.success(request, 'Contraseña actualizada.')
            return redirect('KeyServApp:preferencias_cuenta')

    return render(request, 'KeyServApp/preferencias_cuenta.html', {
        'usuario': usuario,
        'prefs_form': prefs_form,
        'password_form': password_form,
    })


TOKEN_SALT_RECUPERAR = 'keyserv-recuperar-password'
TOKEN_MAX_AGE_RECUPERAR = 3600  # 1 hora
MAX_INTENTOS_RECUPERAR = 3
VENTANA_INTENTOS_RECUPERAR = 600  # 10 minutos


def _huella_password(usuario):
    """
    Hash corto y determinístico del hash de contraseña completo — NO un
    slice de `usuario.password` directo, porque todos los hashes PBKDF2 con
    la misma config comparten el mismo prefijo `pbkdf2_sha256$<iteraciones>$`
    (los primeros ~20 caracteres son idénticos para cualquier contraseña, sin
    importar el salt). Este hash sí cambia apenas cambia la contraseña real.
    """
    return hashlib.sha256(usuario.password.encode()).hexdigest()[:20]


def _generar_token_recuperacion(usuario):
    """
    Token firmado con expiración (django.core.signing, sin necesidad de
    guardar nada en la base de datos). Incluye una huella de la contraseña
    actual: apenas se usa el link (o se pide uno nuevo tras cambiar la
    contraseña), el hash cambia y el token viejo deja de ser válido solo,
    sin tener que llevar una lista de tokens usados.
    """
    return signing.dumps({'uid': usuario.id_usuario, 'h': _huella_password(usuario)}, salt=TOKEN_SALT_RECUPERAR)


def _usuario_desde_token_recuperacion(token):
    try:
        datos = signing.loads(token, salt=TOKEN_SALT_RECUPERAR, max_age=TOKEN_MAX_AGE_RECUPERAR)
    except signing.BadSignature:
        return None
    usuario = Usuario.objects.filter(pk=datos.get('uid')).first()
    if not usuario or _huella_password(usuario) != datos.get('h'):
        return None
    return usuario


def recuperar_view(request):
    """
    Paso 1 de recuperación de contraseña (BPMN 'Login' del PDF menciona
    'validación de contacto'). Pide correo + teléfono — no alcanza con
    adivinar solo el correo — y, si coinciden con una cuenta real, manda un
    enlace firmado y con expiración de 1 hora a ese correo. El mensaje que
    ve el usuario es siempre el mismo exista o no la cuenta, para no
    convertir este formulario en una forma de confirmar qué correos están
    registrados (mismo criterio que login_bloqueado en sesion_view).
    """
    if obtener_usuario_actual(request):
        messages.info(request, 'Ya tenés una sesión iniciada.')
        return redirect('KeyServApp:sesion_iniciada')

    if request.method == 'POST':
        form = RecuperarForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            clave_intentos = f'recuperar_intentos:{_obtener_ip_cliente(request)}:{email.strip().lower()}'
            if cache.get(clave_intentos, 0) >= MAX_INTENTOS_RECUPERAR:
                messages.error(request, 'Demasiadas solicitudes. Probá de nuevo en unos minutos.')
                return render(request, 'KeyServApp/recuperar.html', {'form': form})
            try:
                cache.incr(clave_intentos)
            except ValueError:
                cache.set(clave_intentos, 1, VENTANA_INTENTOS_RECUPERAR)

            usuario = Usuario.objects.filter(email=email, telefono=form.cleaned_data['telefono']).first()
            if usuario:
                token = _generar_token_recuperacion(usuario)
                url_reset = request.build_absolute_uri(reverse('KeyServApp:recuperar_confirmar', args=[token]))
                send_mail(
                    'Recuperar tu contraseña de KeyServ',
                    f'Hola {usuario.nombre_usuario},\n\n'
                    f'Para elegir una nueva contraseña entrá a este enlace (válido por 1 hora):\n{url_reset}\n\n'
                    'Si no pediste esto, podés ignorar este correo — tu contraseña actual sigue siendo válida.',
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario.email],
                    fail_silently=True,
                )
                logger.info('Correo de recuperación de contraseña enviado: usuario_id=%s', usuario.id_usuario)
            messages.success(request, 'Si el correo y el teléfono coinciden con una cuenta, te enviamos un enlace para restablecer tu contraseña.')
            return redirect('KeyServApp:recuperar')
    else:
        form = RecuperarForm()
    return render(request, 'KeyServApp/recuperar.html', {'form': form})


def recuperar_confirmar_view(request, token):
    """Paso 2: valida el enlace firmado y, si es válido y no venció, deja elegir una contraseña nueva."""
    usuario = _usuario_desde_token_recuperacion(token)
    if not usuario:
        messages.error(request, 'Este enlace no es válido o ya venció. Pedí uno nuevo.')
        return redirect('KeyServApp:recuperar')

    if request.method == 'POST':
        form = NuevaPasswordForm(request.POST, usuario=usuario)
        if form.is_valid():
            usuario.set_password(form.cleaned_data['password'])
            usuario.save(update_fields=['password'])
            logger.info('Contraseña restablecida vía recuperación: usuario_id=%s', usuario.id_usuario)
            messages.success(request, 'Contraseña actualizada. Ya podés iniciar sesión.')
            return redirect('KeyServApp:sesion')
    else:
        form = NuevaPasswordForm(usuario=usuario)
    return render(request, 'KeyServApp/recuperar_confirmar.html', {'form': form})


@login_requerido
def historial_pagos_view(request):
    """
    Reemplaza lo que antes era "Mis tarjetas" (un formulario de número de
    tarjeta/CVV que no guardaba nada — guardar eso tal cual habría sido un
    problema serio de PCI-DSS). Con Webpay Plus/Khipu ya funcionando de
    verdad, lo útil de verdad acá es el historial de Pago del cliente — la
    tarjeta en sí nunca la ve ni la guarda este sitio, la ingresa en la
    página del banco. Tokenización real (Transbank Oneclick) queda pendiente
    aparte, ver Known Issues.
    """
    usuario = obtener_usuario_actual(request)
    pagos = Pago.objects.filter(contratacion__cliente=usuario).select_related(
        'contratacion', 'contratacion__publicacion',
    ).order_by('-fecha_creacion')
    return render(request, 'KeyServApp/historial_pagos.html', {
        'usuario': usuario,
        'pagos': pagos,
    })


# ---------------------------------------------------------------------------
# Autenticación (real en esta fase, no esqueleto)
# ---------------------------------------------------------------------------

def register_view(request):
    """
    Registro de un nuevo Usuario (RF001/RF002/RF008). GET muestra el
    formulario, POST lo procesa.

    Si ya hay una sesión abierta, redirige al dashboard en vez de mostrar el
    formulario — antes se podía llegar a /registro/ con una cuenta ya
    logueada y crear una cuenta nueva sin que quedara claro con cuál sesión
    terminabas (ver también sesion_view, mismo criterio).
    """
    if obtener_usuario_actual(request):
        messages.info(request, 'Ya tenés una sesión iniciada.')
        return redirect('KeyServApp:sesion_iniciada')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            tipo_cuenta = form.cleaned_data['tipo_cuenta']
            # Toda alta de cuenta genera una Transaccion de referencia (mismo patrón que la versión anterior).
            transaccion = Transaccion.objects.create(tipo_cuenta=tipo_cuenta)
            usuario = form.crear_usuario(transaccion)
            logger.info('Usuario registrado: id=%s email=%s', usuario.id_usuario, usuario.email)
            messages.success(request, 'Usuario creado exitosamente. Ahora inicia sesión.')
            return redirect('KeyServApp:sesion')
        # Formulario inválido: se vuelve a mostrar con los errores (form.errors se ve en el template si se agregan {{ form.errors }}).
        messages.error(request, 'Revisa los datos del formulario.')
    else:
        form = RegistroForm()

    return render(request, 'KeyServApp/registroinicio.html', {
        'regiones': Region.objects.all(),
        'tipos_cuenta': TipoCuenta.objects.all(),
        'form': form,
    })


MAX_INTENTOS_LOGIN = 5
VENTANA_INTENTOS_LOGIN = 300  # 5 minutos


def _clave_intentos_login(request, email):
    """Por (IP, email) y no solo por email: así nadie puede bloquearle la cuenta a otra persona a propósito fallando su login desde una IP distinta."""
    return f'login_intentos:{_obtener_ip_cliente(request)}:{email.strip().lower()}'


def sesion_view(request):
    """
    Login real (RF003): valida el email/password contra `Usuario.check_password()`
    y abre sesión.

    SEGURIDAD:
    - `request.session.cycle_key()` antes de loguear: sin esto, un atacante
      que le "planta" a la víctima un ID de sesión conocido (ej. por un link)
      podía loguearse él mismo después con ESA sesión ya autenticada (fijación
      de sesión) — Django no lo hace solo salvo que se use `contrib.auth.login`,
      que acá no aplica porque el modelo de sesión es propio (ver decorators.py).
    - Límite de intentos fallidos por (IP, email) — antes no había ningún
      freno para probar contraseñas a fuerza bruta.
    - Si ya hay una sesión abierta, redirige al dashboard en vez de mostrar
      el formulario de login — se podía llegar acá con una cuenta ya
      logueada (ej. Javiera en el header) y loguearte con otra encima, sin
      que quedara claro qué sesión terminaba activa.
    """
    if obtener_usuario_actual(request):
        messages.info(request, 'Ya tenés una sesión iniciada.')
        return redirect('KeyServApp:sesion_iniciada')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            clave_intentos = _clave_intentos_login(request, email)
            if cache.get(clave_intentos, 0) >= MAX_INTENTOS_LOGIN:
                # A propósito con usuario=None: todavía nadie se autenticó
                # como para saber a quién corresponde de verdad — esto es
                # justo el caso "alguien sin usuario" que también hay que
                # poder ver en el panel de alertas, no solo a los que ya
                # tienen sesión.
                _registrar_intento_sospechoso(request, None, 'login_bloqueado', email, 'demasiados intentos fallidos')
                messages.error(request, 'Demasiados intentos fallidos. Probá de nuevo en unos minutos.')
                return render(request, 'KeyServApp/sesion.html')

            usuario = Usuario.objects.filter(email=email).first()
            if usuario and usuario.check_password(form.cleaned_data['password']):
                cache.delete(clave_intentos)
                request.session.cycle_key()
                request.session['usuario_id'] = usuario.id_usuario
                logger.info('Login exitoso: usuario_id=%s', usuario.id_usuario)
                return redirect('KeyServApp:sesion_iniciada')

            try:
                cache.incr(clave_intentos)
            except ValueError:
                cache.set(clave_intentos, 1, VENTANA_INTENTOS_LOGIN)
            logger.warning('Login fallido: email=%s ip=%s', email, request.META.get('REMOTE_ADDR', 'sin-ip'))
            messages.error(request, 'Correo o contraseña incorrectos.')
    return render(request, 'KeyServApp/sesion.html')


def logout_view(request):
    """Cierra la sesión actual (RF005). `flush()` y no solo sacar `usuario_id`: invalida el ID de sesión entero, no solo el dato de quién estaba logueado."""
    request.session.flush()
    messages.success(request, 'Sesión cerrada.')
    return redirect('KeyServApp:paginicio')


def load_comunas(request):
    """Endpoint AJAX: devuelve las comunas de una región (usado por el <select> de registroinicio.html)."""
    region_id = request.GET.get('region_id')
    comunas = Comuna.objects.filter(region_id=region_id).order_by('nombre_comuna')
    comunas_list = list(comunas.values('id_comuna', 'nombre_comuna'))
    # Se normaliza la clave a "id" porque el JS del template ya espera data[i].id (ver registroinicio.html).
    comunas_list = [{'id': c['id_comuna'], 'nombre_comuna': c['nombre_comuna']} for c in comunas_list]
    return JsonResponse(comunas_list, safe=False)


@login_requerido
def mensajes_no_leidos_ajax(request):
    """
    Endpoint liviano para el polling de notificaciones en tiempo real del
    header (ver base.html) — el JS lo consulta cada ~15s y, si el conteo
    subió respecto de la última consulta, suena una alerta y actualiza el
    badge sin recargar la página. Deliberadamente no usa WebSockets/Channels
    (no hay servidor ASGI en este entorno) — polling simple es el patrón
    estándar para esto cuando no hace falta entrega instantánea.
    """
    usuario = obtener_usuario_actual(request)
    return JsonResponse({'no_leidos': contar_mensajes_no_leidos(usuario)})


# ---------------------------------------------------------------------------
# Perfil de usuario
# ---------------------------------------------------------------------------

@login_requerido
def perfil_view(request):
    """Muestra el perfil del usuario logueado: sus datos, sus publicaciones (si alguna vez publicó) y las reseñas que recibió."""
    usuario = obtener_usuario_actual(request)
    publicaciones = Publicaciones.objects.filter(usuario_publicador=usuario).order_by('-fecha_publicacion')
    resenas_recibidas = Valoracion.objects.filter(usuario_receptor=usuario).select_related('usuario_emisor').order_by('-fecha_valoracion')
    ranking = Ranking.objects.filter(usuario=usuario).first()
    return render(request, 'KeyServApp/perfil.html', {
        'usuario': usuario,
        'publicaciones': publicaciones,
        'resenas_recibidas': resenas_recibidas,
        'ranking': ranking,
    })


@login_requerido
@require_POST
def alternar_proveedor_view(request):
    """
    Única forma real de cambiar `es_proveedor` después del registro — antes
    quedaba fijo para siempre según el checkbox de /registro/, porque
    editar_perfil_view todavía no procesa datos (ver Known Issues).
    """
    usuario = obtener_usuario_actual(request)
    usuario.es_proveedor = not usuario.es_proveedor
    usuario.save(update_fields=['es_proveedor'])
    if usuario.es_proveedor:
        messages.success(request, 'Listo, ahora podés publicar servicios como proveedor.')
    else:
        messages.info(request, 'Dejaste de ofrecer servicios. Ya no podés crear nuevas publicaciones hasta que lo actives de nuevo (las que ya tenías siguen visibles).')
    return redirect('KeyServApp:perfil')


@login_requerido
def crear_perfil_view(request):
    """
    Perfil de proveedor extendido (áreas de servicio, experiencia — RF002).
    Antes era estático y no guardaba nada; ahora es un CrearPerfilForm real
    sobre los campos nuevos de Usuario (ver models.py).
    """
    usuario = obtener_usuario_actual(request)
    if request.method == 'POST':
        form = CrearPerfilForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil de proveedor actualizado.')
            return redirect('KeyServApp:perfil')
    else:
        form = CrearPerfilForm(instance=usuario)
    return render(request, 'KeyServApp/crearperfil.html', {'usuario': usuario, 'form': form})


@login_requerido
def editar_perfil_view(request):
    """Edita los datos reales del Usuario — antes el formulario se veía pero no guardaba nada (ver Known Issues)."""
    usuario = obtener_usuario_actual(request)
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado.')
            return redirect('KeyServApp:perfil')
    else:
        form = EditarPerfilForm(instance=usuario, initial={
            'region': usuario.comuna.region_id if usuario.comuna else None,
        })
    return render(request, 'KeyServApp/editarperfil.html', {
        'usuario': usuario,
        'form': form,
        'regiones': Region.objects.all(),
    })


# ---------------------------------------------------------------------------
# Publicaciones (listado/búsqueda de servicios — RF004)
# ---------------------------------------------------------------------------

def publicacion_detalle_view(request, pk):
    """Detalle de una publicación de servicio puntual (RF004/RF010), con proveedor y reseñas reales."""
    publicacion = get_object_or_404(Publicaciones, pk=pk)
    proveedor = publicacion.usuario_publicador
    # Solo reseñas ya moderadas — igual que las publicaciones, una reseña
    # recién enviada no es visible para el público hasta que se aprueba.
    resenas = Valoracion.objects.filter(
        publicacion=publicacion, estado_moderacion=Valoracion.APROBADA,
    ).select_related('usuario_emisor').order_by('-fecha_valoracion')
    ranking = Ranking.objects.filter(usuario=proveedor).first() if proveedor else None
    usuario_actual = obtener_usuario_actual(request)

    contratacion_activa = None
    if usuario_actual:
        # No dejar pedir el mismo servicio dos veces mientras ya hay una
        # solicitud en curso — antes no había ningún chequeo acá.
        contratacion_activa = Contratacion.objects.filter(
            publicacion=publicacion, cliente=usuario_actual,
            estado__in=[Contratacion.SOLICITADA, Contratacion.CONFIRMADA, Contratacion.EN_CURSO],
        ).first()

    return render(request, 'KeyServApp/detalleserv.html', {
        'publicacion': publicacion,
        'proveedor': proveedor,
        'resenas': resenas,
        'ranking': ranking,
        'puede_contratar': bool(usuario_actual) and usuario_actual != proveedor and not contratacion_activa,
        'contratacion_activa': contratacion_activa,
    })


MAX_IMAGENES_PUBLICACION = 8
MAX_DOCUMENTOS_PUBLICACION = 5


@login_requerido
def publicacion_crear_view(request):
    """
    Crear una nueva publicación de servicio (solo proveedores) — RF002.
    Admite categoría (predefinida u "Otra" de texto libre), varias fotos y
    varios documentos de respaldo, todos opcionales — todo queda pendiente
    de aprobación por un moderador junto con el resto de la publicación.

    El template trae una previsualización en vivo (JS puro, sin subir nada
    todavía) de cómo se va a ver la publicación una vez aprobada, reusando
    las mismas clases CSS que la página de detalle real — pedido explícito
    del usuario para poder ajustar texto/fotos antes de publicar.
    """
    usuario = obtener_usuario_actual(request)
    if not usuario.es_proveedor:
        messages.error(request, 'Solo los proveedores pueden publicar servicios.')
        return redirect('KeyServApp:perfil')

    if request.method == 'POST':
        form = PublicacionForm(request.POST)
        if form.is_valid():
            publicacion = form.save(commit=False)
            publicacion.usuario_publicador = usuario
            publicacion.save()

            rechazados = []
            for archivo in request.FILES.getlist('imagenes')[:MAX_IMAGENES_PUBLICACION]:
                imagen = Imagenes(publicacion=publicacion, archivo=archivo)
                try:
                    imagen.full_clean()
                except ValidationError:
                    rechazados.append(archivo.name)
                    continue
                imagen.save()

            for archivo in request.FILES.getlist('documentos')[:MAX_DOCUMENTOS_PUBLICACION]:
                documento = Documento(publicacion=publicacion, usuario=usuario, nombre_documento=archivo.name[:60], archivo_subido=archivo)
                try:
                    documento.full_clean()
                except ValidationError:
                    rechazados.append(archivo.name)
                    continue
                documento.save()

            if rechazados:
                messages.warning(request, f'No se pudieron subir estos archivos (formato, tamaño o contenido no válido): {", ".join(rechazados)}.')

            logger.info('Publicación creada: id=%s usuario=%s', publicacion.id_publicacion, usuario.id_usuario)
            messages.success(request, 'Publicación creada, queda pendiente de aprobación.')
            return redirect('KeyServApp:publicacion_detalle', pk=publicacion.id_publicacion)
    else:
        form = PublicacionForm()

    return render(request, 'KeyServApp/crear_publicacion.html', {
        'form': form,
        'usuario': usuario,
        'ranking': Ranking.objects.filter(usuario=usuario).first(),
    })


def documento_descargar_view(request, documento_id):
    """
    Único punto de acceso a un Documento — nunca se sirve directo por
    MEDIA_URL (ver storage.py: `archivo_subido.url` ni siquiera funciona).

    Un documento de respaldo ligado a una Publicacion (certificación,
    licencia) es público, mismo criterio que las imágenes de la
    publicación — es el caso de uso real hoy (ver publicacion_crear_view).
    Un documento ligado SOLO a un Usuario, sin Publicacion (documento de
    identidad — todavía no hay ningún flujo que suba uno así, pero el
    modelo ya lo soporta) solo lo puede ver su dueño o un miembro del staff;
    a cualquier otro se le devuelve 404 en vez de 403, para no confirmarle
    ni que el documento existe.
    """
    documento = get_object_or_404(Documento, pk=documento_id)
    usuario_actual = obtener_usuario_actual(request)

    if not documento.publicacion_id:
        es_dueno = usuario_actual and usuario_actual.pk == documento.usuario_id
        es_staff = request.user.is_authenticated and request.user.is_staff
        if not (es_dueno or es_staff):
            _registrar_intento_sospechoso(request, usuario_actual, 'documento', documento_id, 'documento de identidad ajeno')
            raise Http404()

    return FileResponse(
        documento.archivo_subido.open('rb'),
        filename=os.path.basename(documento.archivo_subido.name),
    )


# ---------------------------------------------------------------------------
# Contratación (BPMN "Proceso de contratación" del PDF, PAGE 136-137)
# ---------------------------------------------------------------------------

@login_requerido
def reservas_view(request):
    """Lista las Contratacion donde el usuario logueado participa (como cliente o proveedor), con el form de re-auth listo para confirmar/completar."""
    usuario = obtener_usuario_actual(request)
    contrataciones = Contratacion.objects.filter(
        cliente=usuario,
    ) | Contratacion.objects.filter(proveedor=usuario)
    return render(request, 'KeyServApp/reservas.html', {
        'contrataciones': contrataciones.distinct().select_related('publicacion', 'cliente', 'proveedor'),
        'usuario': usuario,
        'reautenticacion_form': ReautenticacionForm(),
    })


@login_requerido
def contratacion_detalle_view(request, contratacion_id):
    """
    Vista detallada de un trabajo puntual (al hacer clic en su título desde
    /inicio/ o /reservas/): descripción e imágenes de la publicación, estado
    de la contratación, las acciones disponibles según el rol (confirmar,
    completar, calificar) y el chat de esa conversación embebido — para poder
    revisar o resolver cualquier incidencia sin salir de la página del trabajo.
    """
    contratacion = get_object_or_404(
        Contratacion.objects.select_related('publicacion', 'cliente', 'proveedor'),
        pk=contratacion_id,
    )
    usuario = obtener_usuario_actual(request)
    if usuario not in (contratacion.cliente, contratacion.proveedor):
        _registrar_intento_sospechoso(request, usuario, 'contratacion', contratacion_id, 'contratación ajena')
        messages.error(request, 'No participás en esta contratación.')
        return redirect('KeyServApp:reservas')

    conversacion = _obtener_o_crear_conversacion_de_contratacion(contratacion)

    if request.method == 'POST':
        form = MensajeForm(request.POST)
        if form.is_valid():
            mensaje = form.save(commit=False)
            mensaje.conversacion = conversacion
            mensaje.usuario = usuario
            mensaje.save()
            return redirect('KeyServApp:contratacion_detalle', contratacion_id=contratacion.id_contratacion)
    else:
        form = MensajeForm()

    mensajes = Mensaje.objects.filter(conversacion=conversacion).select_related('usuario').order_by('fecha_envio')
    participacion = UsuarioConversacion.objects.filter(usuario=usuario, conversacion=conversacion).first()
    if participacion:
        participacion.ultimo_leido = timezone.now()
        participacion.save(update_fields=['ultimo_leido'])

    # NUEVO: la calificación se hace acá mismo (antes vivía en una página
    # aparte, /reservas/ con un form genérico) — `valoracion` es la ya
    # enviada (si existe) para mostrarla en modo lectura; `valoracion_form`
    # solo se arma cuando el cliente todavía puede calificar este trabajo.
    valoracion = getattr(contratacion, 'valoracion', None)
    valoracion_form = None
    if contratacion.estado == Contratacion.COMPLETADA and usuario == contratacion.cliente and valoracion is None:
        valoracion_form = ValoracionForm()

    historial = contratacion.historial_estados.all()
    fechas_por_estado = {h.estado: h.fecha for h in historial}

    # Desglose del presupuesto (opcional, solo existe si el proveedor cargó
    # ítems al confirmar) + comisión de referencia de la plataforma sobre
    # el monto acordado — puramente informativo, ver settings.COMISION_PLATAFORMA_PORCENTAJE.
    items_presupuesto = contratacion.items_presupuesto.all()
    comision_estimada = None
    neto_proveedor_estimado = None
    if contratacion.monto_acordado:
        comision_estimada = round(contratacion.monto_acordado * settings.COMISION_PLATAFORMA_PORCENTAJE / 100)
        neto_proveedor_estimado = contratacion.monto_acordado - comision_estimada

    return render(request, 'KeyServApp/contratacion_detalle.html', {
        'contratacion': contratacion,
        'usuario': usuario,
        'imagenes': contratacion.publicacion.imagenes.all(),
        'mensajes': mensajes,
        'form': form,
        'conversacion': conversacion,
        'historial': historial,
        'fechas_por_estado': fechas_por_estado,
        'reautenticacion_form': ReautenticacionForm(),
        'valoracion': valoracion,
        'valoracion_form': valoracion_form,
        'items_presupuesto': items_presupuesto,
        'comision_estimada': comision_estimada,
        'neto_proveedor_estimado': neto_proveedor_estimado,
        'comision_porcentaje': settings.COMISION_PLATAFORMA_PORCENTAJE,
    })


@login_requerido
@require_POST
def contratacion_crear_view(request, publicacion_id):
    """
    Solicita contratar el servicio de una Publicacion (primer paso del BPMN
    de contratación) — crea el registro en estado SOLICITADA y notifica al
    proveedor abriendo/reusando una Conversacion con un mensaje automático
    (en vez de email, reutiliza el sistema de mensajería ya existente).

    TODO: el pago (antes de pasar a EN_CURSO) sigue sin integrarse — depende
    de `pagos.py`/credenciales de Transbank.
    """
    publicacion = get_object_or_404(Publicaciones, pk=publicacion_id)
    cliente = obtener_usuario_actual(request)
    proveedor = publicacion.usuario_publicador

    if cliente == proveedor:
        messages.error(request, 'No podés contratar tu propia publicación.')
        return redirect('KeyServApp:publicacion_detalle', pk=publicacion_id)

    ya_activa = Contratacion.objects.filter(
        publicacion=publicacion, cliente=cliente,
        estado__in=[Contratacion.SOLICITADA, Contratacion.CONFIRMADA, Contratacion.EN_CURSO],
    ).exists()
    if ya_activa:
        messages.error(request, 'Ya tenés una solicitud en curso para este servicio — esperá a que se complete antes de volver a pedirlo.')
        return redirect('KeyServApp:publicacion_detalle', pk=publicacion_id)

    contratacion = Contratacion.objects.create(
        publicacion=publicacion,
        cliente=cliente,
        proveedor=proveedor,
    )
    HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=Contratacion.SOLICITADA)
    conversacion = _obtener_o_crear_conversacion_de_contratacion(contratacion)
    Mensaje.objects.create(
        conversacion=conversacion,
        usuario=cliente,
        contenido=f'[Sistema] {cliente} solicitó contratar "{publicacion.titulo}". Contratación #{contratacion.id_contratacion}.',
    )
    logger.info('Contratación solicitada: id=%s cliente=%s proveedor=%s', contratacion.id_contratacion, cliente.id_usuario, proveedor.id_usuario)
    messages.success(request, 'Solicitud de contratación enviada. Le avisamos al proveedor por mensaje.')
    return redirect('KeyServApp:reservas')


MAX_INTENTOS_REAUTENTICACION = 5
VENTANA_INTENTOS_REAUTENTICACION = 300  # 5 minutos


def _clave_intentos_reautenticacion(usuario, contratacion_id):
    return f'reauth_intentos:{usuario.pk}:{contratacion_id}'


def _reautenticacion_bloqueada(usuario, contratacion_id):
    return cache.get(_clave_intentos_reautenticacion(usuario, contratacion_id), 0) >= MAX_INTENTOS_REAUTENTICACION


def _registrar_intento_reautenticacion(usuario, contratacion_id, exito):
    clave = _clave_intentos_reautenticacion(usuario, contratacion_id)
    if exito:
        cache.delete(clave)
        return
    try:
        cache.incr(clave)
    except ValueError:
        cache.set(clave, 1, VENTANA_INTENTOS_REAUTENTICACION)


@login_requerido
@require_POST
def _parsear_items_presupuesto(request):
    """
    Lee las filas libres de la hoja de presupuesto opcional (name="item_descripcion"/
    "item_categoria"/"item_monto" repetidos, uno por fila — ver
    contratacion_detalle.html) y devuelve solo las filas válidas como
    tuplas (descripcion, categoria, monto). Filas vacías o con un monto no
    numérico/negativo se descartan en silencio (es un ítem que el
    proveedor dejó a medio llenar, no un error que deba bloquear todo el
    formulario de confirmación).
    """
    descripciones = request.POST.getlist('item_descripcion')
    categorias = request.POST.getlist('item_categoria')
    montos = request.POST.getlist('item_monto')
    categorias_validas = dict(ItemPresupuesto.CATEGORIAS_ITEM)

    items = []
    for descripcion, categoria, monto_bruto in zip(descripciones, categorias, montos):
        descripcion = descripcion.strip()[:200]
        if not descripcion:
            continue
        try:
            monto = int(monto_bruto)
        except (TypeError, ValueError):
            continue
        if monto <= 0:
            continue
        if categoria not in categorias_validas:
            categoria = ItemPresupuesto.OTRO
        items.append((descripcion, categoria, monto))
    return items


@login_requerido
@require_POST
def contratacion_confirmar_view(request, contratacion_id):
    """
    El PROVEEDOR confirma que acepta la solicitud (SOLICITADA -> CONFIRMADA).
    Exige re-autenticación (re-ingresar la contraseña) — lo pide el BPMN del
    PDF explícitamente para ambas partes del proceso de contratación.

    También es el momento donde se fija `monto_acordado`: el precio de la
    publicación es solo un punto de partida, cliente y proveedor pueden
    haber acordado otro por chat antes de esto. Dos formas de fijarlo,
    ambas opcionales — si no se usa ninguna, se cae al precio de la
    publicación tal cual:
      1. Hoja de presupuesto libre (`ItemPresupuesto`, ver
         _parsear_items_presupuesto): si el proveedor cargó al menos un
         ítem válido, el monto acordado es la suma de todos.
      2. Un monto único a mano (`MontoAcordadoForm`), si no cargó ítems.
    Ese monto es lo que se cobra después (ver pago_webpay_iniciar_view/
    pago_khipu_iniciar_view), nunca se vuelve a leer el precio de la
    publicación pasado este punto.

    Límite de intentos por (usuario, contratación) — mismo criterio que el
    login: sin esto, alguien con una sesión ya abierta (ej. una computadora
    compartida) podía intentar adivinar la contraseña sin ningún freno.
    """
    contratacion = get_object_or_404(
        Contratacion.objects.select_related('publicacion'), pk=contratacion_id, estado=Contratacion.SOLICITADA,
    )
    usuario = obtener_usuario_actual(request)
    if usuario != contratacion.proveedor:
        _registrar_intento_sospechoso(request, usuario, 'contratacion_confirmar', contratacion_id, 'no es el proveedor')
        messages.error(request, 'Solo el proveedor puede confirmar esta contratación.')
        return redirect('KeyServApp:reservas')

    if _reautenticacion_bloqueada(usuario, contratacion_id):
        _registrar_intento_sospechoso(request, usuario, 'reauth_bloqueado_confirmar', contratacion_id, 'demasiados intentos fallidos')
        messages.error(request, 'Demasiados intentos fallidos. Probá de nuevo en unos minutos.')
        return redirect('KeyServApp:reservas')

    form = ReautenticacionForm(request.POST)
    if form.is_valid() and usuario.check_password(form.cleaned_data['password']):
        _registrar_intento_reautenticacion(usuario, contratacion_id, exito=True)
        items_presupuesto = _parsear_items_presupuesto(request)
        monto_acordado = contratacion.publicacion.precio
        if items_presupuesto:
            monto_acordado = sum(monto for _, _, monto in items_presupuesto)
        else:
            monto_form = MontoAcordadoForm(request.POST)
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
        logger.info('Contratación confirmada por el proveedor: id=%s monto_acordado=%s items_presupuesto=%s', contratacion.id_contratacion, monto_acordado, len(items_presupuesto))
        messages.success(request, f'Contratación confirmada — monto acordado: ${monto_acordado} CLP.' if monto_acordado else 'Contratación confirmada.')
    else:
        _registrar_intento_reautenticacion(usuario, contratacion_id, exito=False)
        messages.error(request, 'Contraseña incorrecta — no se pudo confirmar.')
    return redirect('KeyServApp:reservas')


@login_requerido
@require_POST
def contratacion_completar_view(request, contratacion_id):
    """
    El CLIENTE confirma que el servicio se completó (EN_CURSO -> COMPLETADA).
    También exige re-autenticación, mismo motivo que arriba. Una vez
    completada, el cliente puede dejar una Valoracion (ver valoracion_crear_view).

    Antes esto se hacía directo desde CONFIRMADA — ahora en el medio hace
    falta pagar (CONFIRMADA -> EN_CURSO vía pago_webpay_retorno_view /
    pago_khipu_notificacion_view más abajo), así que esta vista exige
    EN_CURSO en vez de CONFIRMADA.
    """
    contratacion = get_object_or_404(Contratacion, pk=contratacion_id, estado=Contratacion.EN_CURSO)
    usuario = obtener_usuario_actual(request)
    if usuario != contratacion.cliente:
        _registrar_intento_sospechoso(request, usuario, 'contratacion_completar', contratacion_id, 'no es el cliente')
        messages.error(request, 'Solo el cliente puede marcar la contratación como completada.')
        return redirect('KeyServApp:reservas')

    if _reautenticacion_bloqueada(usuario, contratacion_id):
        _registrar_intento_sospechoso(request, usuario, 'reauth_bloqueado_completar', contratacion_id, 'demasiados intentos fallidos')
        messages.error(request, 'Demasiados intentos fallidos. Probá de nuevo en unos minutos.')
        return redirect('KeyServApp:reservas')

    form = ReautenticacionForm(request.POST)
    if form.is_valid() and usuario.check_password(form.cleaned_data['password']):
        _registrar_intento_reautenticacion(usuario, contratacion_id, exito=True)
        contratacion.estado = Contratacion.COMPLETADA
        contratacion.save()
        HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=Contratacion.COMPLETADA)
        logger.info('Contratación completada: id=%s', contratacion.id_contratacion)
        messages.success(request, '¡Servicio marcado como completado! Ya podés calificarlo.')
    else:
        _registrar_intento_reautenticacion(usuario, contratacion_id, exito=False)
        messages.error(request, 'Contraseña incorrecta — no se pudo completar.')
    return redirect('KeyServApp:reservas')


# ---------------------------------------------------------------------------
# Pagos (RF012 — Webpay Plus + Khipu, ver pagos.py). El cliente paga entre
# CONFIRMADA y EN_CURSO: el proveedor ya aceptó el trabajo, pero todavía no
# arranca hasta que el pago quede aprobado.
# ---------------------------------------------------------------------------

def _generar_orden_compra(contratacion):
    """Buy order único para Transbank (máx. 26 caracteres exigidos por Webpay Plus)."""
    return f'KS{contratacion.id_contratacion}{secrets.token_hex(4)}'


def _procesar_pago_aprobado(pago, respuesta_bruta):
    """
    Marca un Pago como pagado y hace avanzar la Contratacion de CONFIRMADA
    a EN_CURSO. Idempotente a propósito: tanto el retorno del navegador
    (Webpay) como el webhook async (Khipu) pueden llegar a confirmar el
    mismo pago, y no debe duplicarse el paso de estado ni el historial.
    """
    if pago.estado == Pago.PAGADO:
        return
    pago.estado = Pago.PAGADO
    pago.fecha_confirmacion = timezone.now()
    pago.respuesta_bruta = respuesta_bruta
    pago.save()
    contratacion = pago.contratacion
    if contratacion.estado == Contratacion.CONFIRMADA:
        contratacion.estado = Contratacion.EN_CURSO
        contratacion.save()
        HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=Contratacion.EN_CURSO)
    logger.info(
        'Pago aprobado: id=%s metodo=%s contratacion=%s monto=%s',
        pago.id_pago, pago.metodo, contratacion.id_contratacion, pago.monto,
    )


def _validar_pago_posible(request, contratacion_id):
    """Chequeos comunes a iniciar un pago por cualquier medio: dueño correcto, estado correcto, precio real."""
    contratacion = get_object_or_404(
        Contratacion.objects.select_related('publicacion'), pk=contratacion_id, estado=Contratacion.CONFIRMADA,
    )
    usuario = obtener_usuario_actual(request)
    if usuario != contratacion.cliente:
        _registrar_intento_sospechoso(request, usuario, 'pago_iniciar', contratacion_id, 'no es el cliente')
        messages.error(request, 'Solo el cliente puede pagar esta contratación.')
        return None, redirect('KeyServApp:reservas')
    if not contratacion.monto_acordado:
        messages.error(request, 'Esta contratación no tiene un monto acordado — no se puede cobrar.')
        return None, redirect('KeyServApp:contratacion_detalle', contratacion_id=contratacion_id)
    return contratacion, None


@login_requerido
@require_POST
def pago_webpay_iniciar_view(request, contratacion_id):
    """
    Crea la transacción en Transbank y muestra la página que redirige
    (vía un formulario que hace POST automático) al Webpay real.
    """
    contratacion, redireccion_error = _validar_pago_posible(request, contratacion_id)
    if redireccion_error:
        return redireccion_error

    pago, _creado = Pago.objects.get_or_create(
        contratacion=contratacion,
        defaults={'monto': contratacion.monto_acordado, 'metodo': Pago.WEBPAY},
    )
    if pago.estado == Pago.PAGADO:
        messages.info(request, 'Esta contratación ya está pagada.')
        return redirect('KeyServApp:contratacion_detalle', contratacion_id=contratacion_id)
    pago.metodo = Pago.WEBPAY
    pago.monto = contratacion.monto_acordado
    pago.estado = Pago.PENDIENTE

    orden_compra = _generar_orden_compra(contratacion)
    url_retorno = request.build_absolute_uri(reverse('KeyServApp:pago_webpay_retorno'))
    try:
        token, url_pago = pagos.TransbankService().iniciar_transaccion(
            monto=pago.monto, orden_compra=orden_compra,
            session_id=f'usuario-{contratacion.cliente_id}', url_retorno=url_retorno,
        )
    except Exception:
        logger.exception('Error iniciando transacción Webpay: contratacion=%s', contratacion_id)
        messages.error(request, 'No pudimos conectar con Webpay en este momento. Probá de nuevo en unos minutos.')
        return redirect('KeyServApp:contratacion_detalle', contratacion_id=contratacion_id)

    pago.orden_compra = orden_compra
    pago.token_webpay = token
    pago.save()
    return render(request, 'KeyServApp/pago_webpay_redirigir.html', {'url_pago': url_pago, 'token': token})


@csrf_exempt
def pago_webpay_retorno_view(request):
    """
    Webpay vuelve acá con el navegador del propio usuario (no es un
    webhook servidor-a-servidor) — por eso `csrf_exempt`: quien arma esa
    request es Transbank, no lleva el token CSRF de este sitio. En la
    práctica se observó que el token vuelve como parámetro de query en un
    GET (probado en vivo contra el sandbox de integración), aunque la
    documentación de Transbank describe un POST — por las dudas se
    aceptan los dos. Tres casos posibles, según qué campos manda Transbank:
      - `token_ws`: flujo normal, hay que confirmar (commit) la transacción.
      - `TBK_TOKEN` (sin `token_ws`): el usuario canceló el pago en Webpay.
      - ninguno de los dos: se cayó por timeout antes de completar el pago.
    """
    datos = request.POST or request.GET
    token_ws = datos.get('token_ws')
    tbk_token = datos.get('TBK_TOKEN')

    if not token_ws:
        # Cancelado o timeout — buscamos el Pago por el token que sea que tengamos, si hay alguno.
        pago = Pago.objects.filter(token_webpay=tbk_token).first() if tbk_token else None
        if pago and pago.estado == Pago.PENDIENTE:
            pago.estado = Pago.ANULADO
            pago.save()
        return render(request, 'KeyServApp/pago_resultado.html', {
            'aprobado': False,
            'mensaje': 'Cancelaste el pago en Webpay.' if tbk_token else 'El pago no se completó a tiempo.',
            'contratacion': pago.contratacion if pago else None,
        })

    pago = get_object_or_404(Pago, token_webpay=token_ws)
    try:
        respuesta = pagos.TransbankService().confirmar_transaccion(token_ws)
    except Exception:
        logger.exception('Error confirmando transacción Webpay: pago=%s', pago.id_pago)
        pago.estado = Pago.RECHAZADO
        pago.save()
        return render(request, 'KeyServApp/pago_resultado.html', {
            'aprobado': False, 'mensaje': 'No pudimos confirmar el pago con Webpay.', 'contratacion': pago.contratacion,
        })

    aprobado = respuesta.get('response_code') == 0 and respuesta.get('status') == 'AUTHORIZED'
    if aprobado:
        _procesar_pago_aprobado(pago, respuesta)
        mensaje = f'Pago aprobado — código de autorización {respuesta.get("authorization_code")}.'
    else:
        pago.estado = Pago.RECHAZADO
        pago.respuesta_bruta = respuesta
        pago.save()
        logger.warning('Pago Webpay rechazado: pago=%s respuesta=%s', pago.id_pago, respuesta)
        mensaje = 'El pago fue rechazado por el banco emisor de la tarjeta.'

    return render(request, 'KeyServApp/pago_resultado.html', {
        'aprobado': aprobado, 'mensaje': mensaje, 'contratacion': pago.contratacion,
    })


@login_requerido
@require_POST
def pago_khipu_iniciar_view(request, contratacion_id):
    """Crea el cobro en Khipu y redirige al usuario a pagar por transferencia bancaria."""
    contratacion, redireccion_error = _validar_pago_posible(request, contratacion_id)
    if redireccion_error:
        return redireccion_error

    pago, _creado = Pago.objects.get_or_create(
        contratacion=contratacion,
        defaults={'monto': contratacion.monto_acordado, 'metodo': Pago.KHIPU},
    )
    if pago.estado == Pago.PAGADO:
        messages.info(request, 'Esta contratación ya está pagada.')
        return redirect('KeyServApp:contratacion_detalle', contratacion_id=contratacion_id)
    pago.metodo = Pago.KHIPU
    pago.monto = contratacion.monto_acordado
    pago.estado = Pago.PENDIENTE
    pago.save()

    url_retorno = request.build_absolute_uri(
        reverse('KeyServApp:pago_khipu_retorno', args=[contratacion_id]),
    )
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
        messages.error(request, str(error))
        return redirect('KeyServApp:contratacion_detalle', contratacion_id=contratacion_id)
    except Exception:
        logger.exception('Error iniciando pago Khipu: contratacion=%s', contratacion_id)
        messages.error(request, 'No pudimos conectar con Khipu en este momento. Probá de nuevo en unos minutos.')
        return redirect('KeyServApp:contratacion_detalle', contratacion_id=contratacion_id)

    pago.khipu_payment_id = respuesta.get('payment_id')
    pago.save()
    return redirect(respuesta.get('payment_url') or respuesta.get('simplified_transfer_url'))


@csrf_exempt
@require_POST
def pago_khipu_notificacion_view(request):
    """
    Webhook servidor-a-servidor de Khipu — nunca se confía en el cuerpo de
    este POST para decidir que algo está pagado (recomendación explícita
    de Khipu): siempre se reconsulta el estado real contra su API antes de
    marcar nada como aprobado.
    """
    payment_id = request.POST.get('payment_id')
    if not payment_id:
        logger.warning('Webhook de Khipu sin payment_id: %s', dict(request.POST))
        return JsonResponse({'ok': False}, status=400)

    pago = Pago.objects.filter(khipu_payment_id=payment_id).first()
    if not pago:
        logger.warning('Webhook de Khipu para un payment_id desconocido: %s', payment_id)
        return JsonResponse({'ok': False}, status=404)

    try:
        respuesta = pagos.KhipuService().consultar_pago(payment_id)
    except Exception:
        logger.exception('Error reconsultando pago Khipu: pago=%s payment_id=%s', pago.id_pago, payment_id)
        return JsonResponse({'ok': False}, status=502)

    if respuesta.get('status') == 'done':
        _procesar_pago_aprobado(pago, respuesta)
    else:
        logger.info('Webhook de Khipu recibido, estado todavía no "done": pago=%s status=%s', pago.id_pago, respuesta.get('status'))
    return JsonResponse({'ok': True})


@login_requerido
def pago_khipu_retorno_view(request, contratacion_id):
    """
    Página a la que Khipu redirige al usuario (aprobado o cancelado) —
    la verdad sobre si se pagó la trae el webhook, pero acá se reconsulta
    igual por las dudas (mejor UX: evita que alguien vea "pendiente" un
    rato si el webhook todavía no llegó pero el pago ya está aprobado).
    """
    contratacion = get_object_or_404(Contratacion, pk=contratacion_id)
    pago = getattr(contratacion, 'pago', None)
    if pago and pago.estado == Pago.PENDIENTE and pago.khipu_payment_id:
        try:
            respuesta = pagos.KhipuService().consultar_pago(pago.khipu_payment_id)
            if respuesta.get('status') == 'done':
                _procesar_pago_aprobado(pago, respuesta)
        except Exception:
            logger.exception('Error reconsultando pago Khipu al volver: pago=%s', pago.id_pago)

    pago.refresh_from_db() if pago else None
    aprobado = bool(pago and pago.estado == Pago.PAGADO)
    if aprobado:
        mensaje = 'Pago confirmado por transferencia bancaria.'
    elif pago and pago.estado == Pago.PENDIENTE:
        mensaje = 'Todavía estamos esperando la confirmación de tu banco — puede tardar unos minutos.'
    else:
        mensaje = 'El pago no se completó.'
    return render(request, 'KeyServApp/pago_resultado.html', {
        'aprobado': aprobado, 'mensaje': mensaje, 'contratacion': contratacion,
    })


# ---------------------------------------------------------------------------
# Valoraciones (calificación por estrellas tras completar un servicio)
# ---------------------------------------------------------------------------

MAX_IMAGENES_VALORACION = 5


@login_requerido
@require_POST
def valoracion_crear_view(request, contratacion_id):
    """
    Crea la Valoracion del cliente sobre el proveedor de una Contratacion
    COMPLETADA y recalcula el Ranking agregado del proveedor. Vive embebida
    en contratacion_detalle.html (antes era una página aparte con un form
    genérico). Las fotos adjuntas quedan PENDIENTE de moderación —
    ValoracionImagen.estado_moderacion, mismo criterio que las imágenes y
    documentos de una Publicacion— y no se muestran en público hasta que un
    moderador las apruebe desde /admin/.
    """
    contratacion = get_object_or_404(Contratacion, pk=contratacion_id, estado=Contratacion.COMPLETADA)
    emisor = obtener_usuario_actual(request)
    if emisor != contratacion.cliente:
        _registrar_intento_sospechoso(request, emisor, 'valoracion_crear', contratacion_id, 'no es el cliente')
        messages.error(request, 'Solo el cliente puede calificar este trabajo.')
        return redirect('KeyServApp:contratacion_detalle', contratacion_id=contratacion_id)
    if getattr(contratacion, 'valoracion', None) is not None:
        messages.error(request, 'Ya calificaste este trabajo.')
        return redirect('KeyServApp:contratacion_detalle', contratacion_id=contratacion_id)

    form = ValoracionForm(request.POST)
    if form.is_valid():
        valoracion = form.save(commit=False)
        valoracion.usuario_emisor = emisor
        valoracion.usuario_receptor = contratacion.proveedor
        valoracion.publicacion = contratacion.publicacion
        valoracion.contratacion = contratacion
        valoracion.save()

        # `imagenes` es un <input multiple> plano (no hay soporte nativo de
        # Django para un ModelForm con múltiples archivos) — por eso, a
        # diferencia de PublicacionForm.imagen, esto no pasaba por ningún
        # validador. `full_clean()` corre las mismas validaciones que
        # ValoracionImagen.archivo tiene en su Meta (ver validators.py:
        # tamaño, extensión, firma de bytes, Pillow) antes de guardar cada
        # una; lo que no pasa se descarta y se avisa, no se sube igual.
        rechazadas = []
        for archivo in request.FILES.getlist('imagenes')[:MAX_IMAGENES_VALORACION]:
            imagen = ValoracionImagen(valoracion=valoracion, archivo=archivo)
            try:
                imagen.full_clean()
            except ValidationError:
                rechazadas.append(archivo.name)
                continue
            imagen.save()
        if rechazadas:
            messages.warning(request, f'No se pudieron subir estas fotos (formato, tamaño o contenido no válido): {", ".join(rechazadas)}.')

        _recalcular_ranking(contratacion.proveedor)
        messages.success(request, 'Gracias por tu calificación.')
    else:
        messages.error(request, 'No se pudo registrar la calificación — elegí una puntuación de 1 a 5 estrellas.')
    return redirect('KeyServApp:contratacion_detalle', contratacion_id=contratacion_id)


def _recalcular_ranking(usuario):
    """
    Recalcula el promedio y total de Valoracion de un usuario y actualiza (o
    crea) su Ranking — solo cuenta reseñas APROBADA, para que una reseña
    todavía sin moderar (o una rechazada) no le mueva el puntaje a nadie.
    Se llama tanto al crear una reseña como al moderarla (ver ValoracionAdmin).
    """
    from django.db.models import Avg, Count

    agregados = Valoracion.objects.filter(
        usuario_receptor=usuario, estado_moderacion=Valoracion.APROBADA,
    ).aggregate(
        promedio=Avg('puntuacion'), total=Count('id_valoracion'),
    )
    Ranking.objects.update_or_create(
        usuario=usuario,
        defaults={
            'puntuacion_promedio': agregados['promedio'] or 0,
            'total_valoraciones': agregados['total'] or 0,
        },
    )


# ---------------------------------------------------------------------------
# Biometría (RF001 — verificación obligatoria en el registro)
# ---------------------------------------------------------------------------

@login_requerido
def huella_view(request):
    """Muestra la pantalla de captura de huella. El envío real se procesa en `verificacion_huella_view`."""
    return render(request, 'KeyServApp/huella.html')


@login_requerido
@require_POST
def verificacion_huella_view(request):
    """
    Procesa la imagen de huella subida y marca al usuario como verificado si
    el pipeline de `biometria.py` corre sin errores.

    SEGURIDAD: esta vista aceptaba `ruta_imagen` como texto plano en el POST
    y se lo pasaba directo a `Image.open()` dentro del pipeline — cualquier
    usuario logueado podía mandar la ruta de CUALQUIER archivo del servidor
    (lectura arbitraria de archivos / path traversal). Ahora exige un
    archivo subido de verdad (`request.FILES`), validado con las mismas
    reglas que el resto de las imágenes del sitio (validators.validar_imagen:
    extensión, firma de bytes, que Pillow logre decodificarla), y se guarda
    en un archivo temporal generado por el propio servidor — nunca en una
    ruta que decide el cliente.

    TODO (sin resolver, no es de seguridad): hoy solo confirma que el
    pipeline corrió, no compara contra una huella previamente registrada —
    falta decidir dónde se guarda el hash de referencia por usuario para
    poder comparar en logins futuros.
    """
    usuario = obtener_usuario_actual(request)
    archivo = request.FILES.get('huella_imagen')
    if not archivo:
        messages.error(request, 'Subí una imagen de huella para verificar.')
        return redirect('KeyServApp:huella')

    try:
        validators.validar_imagen(archivo)
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
        return redirect('KeyServApp:huella')

    ruta_temporal = None
    try:
        extension = os.path.splitext(archivo.name)[1].lower()
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as destino:
            for fragmento in archivo.chunks():
                destino.write(fragmento)
            ruta_temporal = destino.name

        hash_resultado = biometria.procesar_huella_dactilar(ruta_temporal)
    finally:
        if ruta_temporal and os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)

    if hash_resultado:
        usuario.verificado_biometricamente = True
        usuario.save()
        messages.success(request, 'Huella verificada correctamente.')
    else:
        messages.error(request, 'No se pudo procesar la huella. Intenta nuevamente.')
    return redirect('KeyServApp:perfil')


# ---------------------------------------------------------------------------
# Mensajería (caso de uso UML del PDF — antes los modelos existían sin vistas)
# ---------------------------------------------------------------------------

def _obtener_o_crear_conversacion_de_contratacion(contratacion):
    """
    Devuelve la Conversacion 1:1 de esta Contratacion (la crea junto con sus
    dos filas de UsuarioConversacion si todavía no existe).

    Antes había una única Conversacion compartida por PAR DE USUARIOS, reusada
    entre todos sus trabajos — se cambió a una conversación por trabajo
    (decisión tomada con el usuario: "más ordenado", y necesaria para que el
    chat embebido en `contratacion_detalle_view` muestre solo lo de ESE
    trabajo, no mezclado con otros).
    """
    conversacion = getattr(contratacion, 'conversacion', None)
    if conversacion:
        return conversacion

    conversacion = Conversacion.objects.create(
        contratacion=contratacion,
        nombre_conversacion=f'{contratacion.publicacion.titulo} — {contratacion.cliente} / {contratacion.proveedor}',
    )
    UsuarioConversacion.objects.create(usuario=contratacion.cliente, conversacion=conversacion)
    UsuarioConversacion.objects.create(usuario=contratacion.proveedor, conversacion=conversacion)
    return conversacion


def _mensajes_no_leidos_por_conversacion(usuario):
    """
    Devuelve {conversacion_id: cantidad_no_leida} para todas las Conversacion
    del usuario — un mensaje cuenta como no leído si es de otra persona y fue
    enviado después de `UsuarioConversacion.ultimo_leido` (o si nunca se leyó
    la conversación, es decir `ultimo_leido` es None).
    """
    conteos = {}
    participaciones = UsuarioConversacion.objects.filter(usuario=usuario).select_related('conversacion')
    for participacion in participaciones:
        mensajes_otros = Mensaje.objects.filter(conversacion=participacion.conversacion).exclude(usuario=usuario)
        if participacion.ultimo_leido:
            mensajes_otros = mensajes_otros.filter(fecha_envio__gt=participacion.ultimo_leido)
        cantidad = mensajes_otros.count()
        if cantidad:
            conteos[participacion.conversacion_id] = cantidad
    return conteos


def contar_mensajes_no_leidos(usuario):
    """Total de mensajes no leídos de un usuario, sumando todas sus conversaciones."""
    if not usuario:
        return 0
    return sum(_mensajes_no_leidos_por_conversacion(usuario).values())


@login_requerido
def chat_view(request):
    """
    Lista los chats de trabajo del usuario logueado (una Conversacion por
    Contratacion), con badge de no leídos, avatar/nombre de la contraparte y
    una vista previa del último mensaje — antes la fila solo mostraba el
    título del trabajo con un icono genérico igual para todas, sin decir ni
    quién escribió ni qué decía el último mensaje.
    """
    usuario = obtener_usuario_actual(request)
    conversacion_ids = UsuarioConversacion.objects.filter(usuario=usuario).values_list('conversacion_id', flat=True)
    conversaciones = Conversacion.objects.filter(id_conversacion__in=conversacion_ids).select_related(
        'contratacion__publicacion', 'contratacion__cliente', 'contratacion__proveedor',
    ).order_by('-fecha_creacion')
    no_leidos = _mensajes_no_leidos_por_conversacion(usuario)
    for conv in conversaciones:
        conv.no_leidos = no_leidos.get(conv.id_conversacion, 0)
        conv.ultimo_mensaje = Mensaje.objects.filter(conversacion=conv).select_related('usuario').order_by('-fecha_envio').first()
        conv.contraparte = None
        if conv.contratacion:
            conv.contraparte = conv.contratacion.proveedor if usuario == conv.contratacion.cliente else conv.contratacion.cliente
    return render(request, 'KeyServApp/chat.html', {'conversaciones': conversaciones})


@login_requerido
def conversacion_detalle_view(request, conversacion_id):
    """
    Muestra los mensajes de una Conversacion puntual. Si está ligada a una
    Contratacion (el caso normal desde esta fase), redirige al detalle del
    trabajo — que ya trae el mismo chat embebido — para no duplicar la vista.
    Solo sirve como pantalla propia para conversaciones legado sin trabajo asociado.
    """
    usuario = obtener_usuario_actual(request)
    conversacion = get_object_or_404(Conversacion, pk=conversacion_id)
    participacion = UsuarioConversacion.objects.filter(usuario=usuario, conversacion=conversacion).first()
    if not participacion:
        _registrar_intento_sospechoso(request, usuario, 'conversacion', conversacion_id, 'conversación ajena')
        messages.error(request, 'No participás en esta conversación.')
        return redirect('KeyServApp:chat')

    if conversacion.contratacion_id:
        return redirect('KeyServApp:contratacion_detalle', contratacion_id=conversacion.contratacion_id)

    if request.method == 'POST':
        form = MensajeForm(request.POST)
        if form.is_valid():
            mensaje = form.save(commit=False)
            mensaje.conversacion = conversacion
            mensaje.usuario = usuario
            mensaje.save()
            return redirect('KeyServApp:conversacion_detalle', conversacion_id=conversacion.id_conversacion)
    else:
        form = MensajeForm()

    mensajes = Mensaje.objects.filter(conversacion=conversacion).select_related('usuario').order_by('fecha_envio')
    participacion.ultimo_leido = timezone.now()
    participacion.save(update_fields=['ultimo_leido'])
    return render(request, 'KeyServApp/chat.html', {
        'conversacion': conversacion,
        'mensajes': mensajes,
        'form': form,
        'usuario': usuario,
    })


@login_requerido
def conversacion_exportar_view(request, conversacion_id):
    """
    Descarga el historial de una Conversacion como texto plano — el "backup
    estilo WhatsApp" pedido por el usuario. Marca `exportado_en`, que es lo
    que protege a esta conversación del borrado automático por antigüedad
    (ver management command `limpiar_mensajes_antiguos`).
    """
    from django.http import HttpResponse

    usuario = obtener_usuario_actual(request)
    conversacion = get_object_or_404(Conversacion, pk=conversacion_id)
    if not UsuarioConversacion.objects.filter(usuario=usuario, conversacion=conversacion).exists():
        _registrar_intento_sospechoso(request, usuario, 'conversacion_exportar', conversacion_id, 'conversación ajena')
        messages.error(request, 'No participás en esta conversación.')
        return redirect('KeyServApp:chat')

    mensajes = Mensaje.objects.filter(conversacion=conversacion).select_related('usuario').order_by('fecha_envio')
    lineas = [f'Chat: {conversacion.nombre_conversacion}', f'Exportado: {timezone.now():%Y-%m-%d %H:%M}', '']
    for m in mensajes:
        lineas.append(f'[{m.fecha_envio:%Y-%m-%d %H:%M}] {m.usuario}: {m.contenido}')
    contenido = '\n'.join(lineas) or 'Todavía no hay mensajes en esta conversación.'

    conversacion.exportado_en = timezone.now()
    conversacion.save(update_fields=['exportado_en'])

    respuesta = HttpResponse(contenido, content_type='text/plain; charset=utf-8')
    respuesta['Content-Disposition'] = f'attachment; filename="chat_{conversacion.id_conversacion}.txt"'
    return respuesta

