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
import logging

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import login_requerido, obtener_usuario_actual
from .forms import (
    RegistroForm, LoginForm, PublicacionForm, ValoracionForm, MensajeForm,
    ReautenticacionForm, ContactoForm,
)
from .models import (
    Comuna, Contratacion, Conversacion, Documento, EstadoConsulta,
    HistorialEstadoContratacion, Imagenes, Mensaje, Publicaciones, Ranking,
    Region, TipoCuenta, Transaccion, Usuario, UsuarioConversacion, Valoracion,
)
from . import biometria, pagos

logger = logging.getLogger(__name__)


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


def catalogo_view(request):
    """
    Catálogo completo de servicios (ventana aparte del home): búsqueda de
    texto + filtros reales por región del proveedor, calificación mínima y
    orden — pensada para una búsqueda más amplia que la barra rápida del home.
    """
    query = request.GET.get('q', '').strip()
    region_id = request.GET.get('region', '').strip()
    calificacion_min = request.GET.get('calificacion', '').strip()
    orden = request.GET.get('orden', 'recientes')

    publicaciones = Publicaciones.objects.filter(estado_moderacion=Publicaciones.APROBADA)
    if query:
        publicaciones = publicaciones.filter(Q(titulo__icontains=query) | Q(sub_titulo__icontains=query))
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

    return render(request, 'KeyServApp/catalogo.html', {
        'publicaciones': publicaciones[:40],
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
    """Página de preferencias/Términos y condiciones de la cuenta."""
    return render(request, 'KeyServApp/preferencias de la cuenta.html')


def recuperar_view(request):
    """Recuperación de contraseña. TODO: falta el flujo real (BPMN 'Login' del PDF menciona 'validación de contacto', ej. reenvío por email) — hoy solo muestra el formulario."""
    return render(request, 'KeyServApp/recuperar.html')


@login_requerido
def tarjeta_credito_view(request):
    """
    Pantalla de ingreso de tarjeta de crédito. El template `tarjeta credito.html`
    está vacío (0 bytes) desde antes de esta fase — falta diseñarlo; por ahora
    esta vista solo lo renderiza tal cual para que la URL exista.
    """
    return render(request, 'KeyServApp/tarjeta credito.html')


# ---------------------------------------------------------------------------
# Autenticación (real en esta fase, no esqueleto)
# ---------------------------------------------------------------------------

def register_view(request):
    """Registro de un nuevo Usuario (RF001/RF002/RF008). GET muestra el formulario, POST lo procesa."""
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


def sesion_view(request):
    """Login real (RF003): valida el email/password contra `Usuario.check_password()` y abre sesión."""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            usuario = Usuario.objects.filter(email=form.cleaned_data['email']).first()
            if usuario and usuario.check_password(form.cleaned_data['password']):
                request.session['usuario_id'] = usuario.id_usuario
                logger.info('Login exitoso: usuario_id=%s', usuario.id_usuario)
                return redirect('KeyServApp:sesion_iniciada')
            messages.error(request, 'Correo o contraseña incorrectos.')
    return render(request, 'KeyServApp/sesion.html')


def logout_view(request):
    """Cierra la sesión actual (RF005)."""
    request.session.pop('usuario_id', None)
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
    """Muestra el perfil del usuario logueado: sus datos, sus publicaciones (si es proveedor) y las reseñas que recibió."""
    usuario = obtener_usuario_actual(request)
    publicaciones = Publicaciones.objects.filter(usuario_publicador=usuario).order_by('-fecha_publicacion') if usuario.es_proveedor else []
    resenas_recibidas = Valoracion.objects.filter(usuario_receptor=usuario).select_related('usuario_emisor').order_by('-fecha_valoracion')
    ranking = Ranking.objects.filter(usuario=usuario).first()
    return render(request, 'KeyServApp/perfil.html', {
        'usuario': usuario,
        'publicaciones': publicaciones,
        'resenas_recibidas': resenas_recibidas,
        'ranking': ranking,
    })


@login_requerido
def crear_perfil_view(request):
    """
    Paso de registro extendido (habilidades, áreas de servicio — RF002).
    TODO: `crearperfil.html` es estático hoy, falta un ModelForm dedicado
    a los campos de perfil de proveedor (no existen todavía en `Usuario`
    más allá de `es_proveedor`).
    """
    usuario = obtener_usuario_actual(request)
    return render(request, 'KeyServApp/crearperfil.html', {'usuario': usuario})


@login_requerido
def editar_perfil_view(request):
    """TODO: edición real de los datos del `Usuario` — hoy solo renderiza el template."""
    usuario = obtener_usuario_actual(request)
    return render(request, 'KeyServApp/editarperfil.html', {'usuario': usuario})


# ---------------------------------------------------------------------------
# Publicaciones (listado/búsqueda de servicios — RF004)
# ---------------------------------------------------------------------------

def publicacion_detalle_view(request, pk):
    """Detalle de una publicación de servicio puntual (RF004/RF010), con proveedor y reseñas reales."""
    publicacion = get_object_or_404(Publicaciones, pk=pk)
    proveedor = publicacion.usuario_publicador
    resenas = Valoracion.objects.filter(publicacion=publicacion).select_related('usuario_emisor').order_by('-fecha_valoracion')
    ranking = Ranking.objects.filter(usuario=proveedor).first() if proveedor else None
    usuario_actual = obtener_usuario_actual(request)
    return render(request, 'KeyServApp/detalleserv.html', {
        'publicacion': publicacion,
        'proveedor': proveedor,
        'resenas': resenas,
        'ranking': ranking,
        'puede_contratar': bool(usuario_actual) and usuario_actual != proveedor,
    })


@login_requerido
def publicacion_crear_view(request):
    """
    Crear una nueva publicación de servicio (solo proveedores) — RF002.
    Admite categoría (predefinida u "Otra" de texto libre) e imagen/documento
    opcionales — todo queda pendiente de aprobación por un moderador, imagen
    y documento incluidos, junto con el resto de la publicación.
    """
    usuario = obtener_usuario_actual(request)
    if not usuario.es_proveedor:
        messages.error(request, 'Solo los proveedores pueden publicar servicios.')
        return redirect('KeyServApp:perfil')

    if request.method == 'POST':
        form = PublicacionForm(request.POST, request.FILES)
        if form.is_valid():
            publicacion = form.save(commit=False)
            publicacion.usuario_publicador = usuario
            publicacion.save()

            imagen = form.cleaned_data.get('imagen')
            if imagen:
                Imagenes.objects.create(publicacion=publicacion, archivo=imagen)

            documento = form.cleaned_data.get('documento')
            if documento:
                Documento.objects.create(
                    publicacion=publicacion, usuario=usuario,
                    nombre_documento=documento.name[:60], archivo_subido=documento,
                )

            logger.info('Publicación creada: id=%s usuario=%s', publicacion.id_publicacion, usuario.id_usuario)
            messages.success(request, 'Publicación creada, queda pendiente de aprobación.')
            return redirect('KeyServApp:publicacion_detalle', pk=publicacion.id_publicacion)
    else:
        form = PublicacionForm()

    return render(request, 'KeyServApp/crear_publicacion.html', {'form': form, 'usuario': usuario})


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

    ya_valorado = False
    if contratacion.estado == Contratacion.COMPLETADA:
        ya_valorado = Valoracion.objects.filter(
            publicacion=contratacion.publicacion, usuario_emisor=usuario,
        ).exists()

    historial = contratacion.historial_estados.all()
    fechas_por_estado = {h.estado: h.fecha for h in historial}

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
        'ya_valorado': ya_valorado,
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


@login_requerido
@require_POST
def contratacion_confirmar_view(request, contratacion_id):
    """
    El PROVEEDOR confirma que acepta la solicitud (SOLICITADA -> CONFIRMADA).
    Exige re-autenticación (re-ingresar la contraseña) — lo pide el BPMN del
    PDF explícitamente para ambas partes del proceso de contratación.
    """
    contratacion = get_object_or_404(Contratacion, pk=contratacion_id, estado=Contratacion.SOLICITADA)
    usuario = obtener_usuario_actual(request)
    if usuario != contratacion.proveedor:
        messages.error(request, 'Solo el proveedor puede confirmar esta contratación.')
        return redirect('KeyServApp:reservas')

    form = ReautenticacionForm(request.POST)
    if form.is_valid() and usuario.check_password(form.cleaned_data['password']):
        contratacion.estado = Contratacion.CONFIRMADA
        contratacion.save()
        HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=Contratacion.CONFIRMADA)
        logger.info('Contratación confirmada por el proveedor: id=%s', contratacion.id_contratacion)
        messages.success(request, 'Contratación confirmada.')
    else:
        messages.error(request, 'Contraseña incorrecta — no se pudo confirmar.')
    return redirect('KeyServApp:reservas')


@login_requerido
@require_POST
def contratacion_completar_view(request, contratacion_id):
    """
    El CLIENTE confirma que el servicio se completó (CONFIRMADA -> COMPLETADA).
    También exige re-autenticación, mismo motivo que arriba. Una vez
    completada, el cliente puede dejar una Valoracion (ver valoracion_crear_view).
    """
    contratacion = get_object_or_404(Contratacion, pk=contratacion_id, estado=Contratacion.CONFIRMADA)
    usuario = obtener_usuario_actual(request)
    if usuario != contratacion.cliente:
        messages.error(request, 'Solo el cliente puede marcar la contratación como completada.')
        return redirect('KeyServApp:reservas')

    form = ReautenticacionForm(request.POST)
    if form.is_valid() and usuario.check_password(form.cleaned_data['password']):
        contratacion.estado = Contratacion.COMPLETADA
        contratacion.save()
        HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=Contratacion.COMPLETADA)
        logger.info('Contratación completada: id=%s', contratacion.id_contratacion)
        messages.success(request, '¡Servicio marcado como completado! Ya podés calificarlo.')
    else:
        messages.error(request, 'Contraseña incorrecta — no se pudo completar.')
    return redirect('KeyServApp:reservas')


# ---------------------------------------------------------------------------
# Valoraciones (calificación por estrellas tras completar un servicio)
# ---------------------------------------------------------------------------

@login_requerido
def valoracion_crear_view(request, contratacion_id):
    """Crea una Valoracion sobre la contraparte de una Contratacion COMPLETADA, y recalcula su Ranking agregado."""
    contratacion = get_object_or_404(Contratacion, pk=contratacion_id, estado=Contratacion.COMPLETADA)
    emisor = obtener_usuario_actual(request)
    receptor = contratacion.proveedor if emisor == contratacion.cliente else contratacion.cliente

    if request.method == 'POST':
        form = ValoracionForm(request.POST)
        if form.is_valid():
            valoracion = form.save(commit=False)
            valoracion.usuario_emisor = emisor
            valoracion.usuario_receptor = receptor
            valoracion.publicacion = contratacion.publicacion
            valoracion.save()
            _recalcular_ranking(receptor)
            messages.success(request, 'Gracias por tu calificación.')
            return redirect('KeyServApp:reservas')
    else:
        form = ValoracionForm()

    return render(request, 'KeyServApp/reservas.html', {'form': form, 'contratacion': contratacion})


def _recalcular_ranking(usuario):
    """Recalcula el promedio y total de Valoracion de un usuario y actualiza (o crea) su Ranking."""
    from django.db.models import Avg, Count

    agregados = Valoracion.objects.filter(usuario_receptor=usuario).aggregate(
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
    TODO: hoy solo confirma que el pipeline corrió (no compara contra una
    huella previamente registrada — falta decidir dónde se guarda el hash
    de referencia por usuario para poder comparar en logins futuros).
    """
    usuario = obtener_usuario_actual(request)
    ruta_imagen = request.POST.get('ruta_imagen')  # TODO: en la integración real esto viene de un <input type="file">, no de una ruta de texto
    hash_resultado = biometria.procesar_huella_dactilar(ruta_imagen)
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
    """Lista los chats de trabajo del usuario logueado (una Conversacion por Contratacion), con badge de no leídos y fecha del último mensaje."""
    usuario = obtener_usuario_actual(request)
    conversacion_ids = UsuarioConversacion.objects.filter(usuario=usuario).values_list('conversacion_id', flat=True)
    conversaciones = Conversacion.objects.filter(id_conversacion__in=conversacion_ids).select_related(
        'contratacion__publicacion', 'contratacion__cliente', 'contratacion__proveedor',
    ).order_by('-fecha_creacion')
    no_leidos = _mensajes_no_leidos_por_conversacion(usuario)
    for conv in conversaciones:
        conv.no_leidos = no_leidos.get(conv.id_conversacion, 0)
        conv.ultimo_mensaje = Mensaje.objects.filter(conversacion=conv).order_by('-fecha_envio').first()
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


# ---------------------------------------------------------------------------
# Pagos (RF012) — ESQUELETO, ver pagos.py
# ---------------------------------------------------------------------------

@login_requerido
def pago_view(request):
    """
    Pantalla de pago. TODO: al confirmar, debería llamar a
    `pagos.TransbankService.iniciar_transaccion()` y redirigir a la URL de
    pago que devuelva Transbank — hoy eso lanza NotImplementedError porque
    no hay credenciales de comercio configuradas (ver .env.example).
    """
    return render(request, 'KeyServApp/pago.html')


@login_requerido
def pago_exitoso_view(request):
    """Pantalla de confirmación tras un pago exitoso (redirección de retorno de Transbank, TODO)."""
    return render(request, 'KeyServApp/pagoexitoso.html')
