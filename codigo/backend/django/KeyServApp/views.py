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
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .decorators import login_requerido, obtener_usuario_actual
from .forms import RegistroForm, LoginForm, PublicacionForm, ValoracionForm
from .models import (
    Comuna, Contratacion, Publicaciones, Ranking, Region, TipoCuenta,
    Transaccion, Valoracion,
)
from . import biometria, pagos

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Páginas simples (solo renderizan un template, sin lógica de negocio propia)
# ---------------------------------------------------------------------------

def paginicio_view(request):
    """Página de inicio / catálogo: muestra las publicaciones ya aprobadas por moderación (RF004)."""
    publicaciones = Publicaciones.objects.filter(estado_moderacion=Publicaciones.APROBADA).order_by('-fecha_publicacion')[:20]
    return render(request, 'KeyServApp/paginicio.html', {'publicaciones': publicaciones})


def acerca_de_nosotros_view(request):
    """Página institucional estática 'Acerca de nosotros'."""
    return render(request, 'KeyServApp/Acercadeenosotros.html')


def contacto_view(request):
    """Página de contacto. TODO: no envía el formulario a ningún lado todavía (falta definir canal: email/ticket)."""
    return render(request, 'KeyServApp/contacto.html')


@login_requerido
def sesion_iniciada_view(request):
    """Home alternativo para un usuario ya logueado (Sesioniniciadainicio.html)."""
    usuario = obtener_usuario_actual(request)
    return render(request, 'KeyServApp/Sesioniniciadainicio.html', {'usuario': usuario})


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
            from .models import Usuario
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


# ---------------------------------------------------------------------------
# Perfil de usuario
# ---------------------------------------------------------------------------

@login_requerido
def perfil_view(request):
    """Muestra el perfil del usuario logueado."""
    usuario = obtener_usuario_actual(request)
    return render(request, 'KeyServApp/perfil.html', {'usuario': usuario})


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
    """Detalle de una publicación de servicio puntual (RF004/RF010)."""
    publicacion = get_object_or_404(Publicaciones, pk=pk)
    return render(request, 'KeyServApp/detalleserv.html', {'publicacion': publicacion})


@login_requerido
def publicacion_crear_view(request):
    """
    Crear una nueva publicación de servicio (solo proveedores).
    ESQUELETO: no existe todavía un template de creación entre las páginas
    heredadas de la tesis — se deja la lógica de guardado lista (usa
    `PublicacionForm`) pero renderiza sobre `crearperfil.html` como
    placeholder hasta que se diseñe una pantalla dedicada.
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
            logger.info('Publicación creada: id=%s usuario=%s', publicacion.id_publicacion, usuario.id_usuario)
            messages.success(request, 'Publicación creada, queda pendiente de aprobación.')
            return redirect('KeyServApp:publicacion_detalle', pk=publicacion.id_publicacion)
    else:
        form = PublicacionForm()

    # TODO: reemplazar por un template real de "crear publicación" (no existe en el diseño heredado de la tesis).
    return render(request, 'KeyServApp/crearperfil.html', {'form': form, 'usuario': usuario})


# ---------------------------------------------------------------------------
# Contratación (BPMN "Proceso de contratación" del PDF, PAGE 136-137) — ESQUELETO
# ---------------------------------------------------------------------------

@login_requerido
def reservas_view(request):
    """Lista las Contratacion donde el usuario logueado participa (como cliente o proveedor)."""
    usuario = obtener_usuario_actual(request)
    contrataciones = Contratacion.objects.filter(
        cliente=usuario,
    ) | Contratacion.objects.filter(proveedor=usuario)
    return render(request, 'KeyServApp/reservas.html', {'contrataciones': contrataciones.distinct()})


@login_requerido
@require_POST
def contratacion_crear_view(request, publicacion_id):
    """
    Solicita contratar el servicio de una Publicacion (primer paso del BPMN
    de contratación). ESQUELETO: crea el registro en estado SOLICITADA, pero
    todavía falta:
      - Notificar al proveedor (email/mensaje).
      - Forzar la re-autenticación de ambas partes antes de CONFIRMADA
        (el PDF lo pide explícitamente).
      - Disparar el flujo de pago (ver `pagos.py`) antes de EN_CURSO.
    """
    publicacion = get_object_or_404(Publicaciones, pk=publicacion_id)
    cliente = obtener_usuario_actual(request)
    contratacion = Contratacion.objects.create(
        publicacion=publicacion,
        cliente=cliente,
        proveedor=publicacion.usuario_publicador,
    )
    logger.info('Contratación solicitada: id=%s', contratacion.id_contratacion)
    messages.success(request, 'Solicitud de contratación enviada.')
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
# Mensajería — ESQUELETO (modelos Mensaje/Conversacion ya existen, sin vistas)
# ---------------------------------------------------------------------------

@login_requerido
def chat_view(request):
    """
    TODO: listar las Conversacion del usuario y permitir enviar Mensaje —
    hoy solo renderiza el template estático, sin datos reales.
    """
    return render(request, 'KeyServApp/chat.html')


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
