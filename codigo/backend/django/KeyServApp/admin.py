"""
Registro de modelos en el panel /admin/ de Django.

Refactor Fase 3: antes este archivo estaba vacío — 0 de los ~25 modelos
eran visibles/editables desde /admin/, sin forma de inspeccionar datos
durante desarrollo/QA.
"""
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    AreaAdministrativa, Autentificacion, Comuna, Consulta, Contratacion,
    Conversacion, Documento, EstadoAutentificacion, EstadoConsulta,
    EstadoDocumento, Firma, Gasto, HistorialEstadoContratacion, Imagenes,
    IntentoAccesoSospechoso, ItemPresupuesto, Mensaje, Pago, Publicaciones,
    Ranking, Region, RolCuentaAdministrativa, TipoCuenta, TipoFirma,
    Transaccion, Usuario, UsuarioAdministrativo, UsuarioConversacion,
    Valoracion, ValoracionImagen,
)
from .views import _recalcular_ranking


def _miniatura(url, alto=70):
    """Vista previa chica de una imagen — usada en varios ModelAdmin/inlines para no tener que abrir el archivo aparte."""
    if not url:
        return '—'
    return format_html('<img src="{}" style="height:{}px; border-radius:6px; object-fit:cover;">', url, alto)


def _ver_documento(documento):
    """
    Link "Ver documento" para un Documento — pasa siempre por
    documento_descargar_view (views.py), nunca por `.archivo_subido.url`
    directo: ese storage es privado a propósito (ver storage.py) y ni
    siquiera tiene una URL pública que se le pueda pedir.
    """
    if not documento.pk or not documento.archivo_subido:
        return '—'
    return format_html(
        '<a href="{}" target="_blank" rel="noopener">Ver documento ↗</a>',
        reverse('KeyServApp:documento_descargar', args=[documento.pk]),
    )


def _badge(texto, tono):
    """
    Badge de color para un estado de solo lectura en list_display — mismo
    lenguaje visual que `.ks-badge-*` del sitio público y que los <select>
    de list_editable coloreados por ks_admin_badges.js (ver
    static/admin/css/ks_admin_theme.css). `tono` es 'coral'/'teal'/'navy'/
    'gray', no el código del estado — cada ModelAdmin decide el mapeo
    porque los estados de Contratacion y de Pago no comparten vocabulario.
    """
    return format_html('<span class="ks-badge ks-badge-{}">{}</span>', tono, texto)


_TONOS_ESTADO_CONTRATACION = {
    'SOLICITADA': 'coral',
    'CONFIRMADA': 'teal',
    'EN_CURSO': 'teal',
    'COMPLETADA': 'navy',
    'CANCELADA': 'gray',
}

_TONOS_ESTADO_PAGO = {
    'PENDIENTE': 'coral',
    'PAGADO': 'teal',
    'RECHAZADO': 'gray',
    'ANULADO': 'gray',
}


class ImagenesInline(admin.TabularInline):
    """Fotos de la publicación, visibles directo en su ficha — antes había que ir a buscarlas aparte en 'Imágenes' por id."""
    model = Imagenes
    extra = 0
    fields = ('miniatura', 'archivo', 'url_imagen')
    readonly_fields = ('miniatura',)

    @admin.display(description='Vista previa')
    def miniatura(self, obj):
        return _miniatura(obj.url) if obj.pk else '—'


class DocumentoInline(admin.TabularInline):
    """Documentos de respaldo (certificación, licencia, etc.) de la publicación, visibles en la misma ficha."""
    model = Documento
    extra = 0
    fields = ('nombre_documento', 'ver_documento', 'estado_documento')
    readonly_fields = ('ver_documento',)

    @admin.display(description='Archivo')
    def ver_documento(self, obj):
        return _ver_documento(obj)


class ValoracionImagenInline(admin.TabularInline):
    """Fotos adjuntas a la reseña, moderables ahí mismo — mismo criterio que las de una publicación."""
    model = ValoracionImagen
    extra = 0
    fields = ('miniatura', 'archivo', 'estado_moderacion')
    readonly_fields = ('miniatura',)

    @admin.display(description='Vista previa')
    def miniatura(self, obj):
        return _miniatura(obj.archivo.url) if obj.pk and obj.archivo else '—'


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """No se muestra `password` en list_display a propósito (aunque ya está hasheado, no hace falta exponerlo)."""
    list_display = ('id_usuario', 'nombre_usuario', 'apellido_usuario', 'email', 'es_proveedor', 'verificado_biometricamente')
    search_fields = ('nombre_usuario', 'apellido_usuario', 'email', 'rut_usuario')
    list_filter = ('es_proveedor', 'verificado_biometricamente', 'tipo_cuenta')


@admin.register(Publicaciones)
class PublicacionesAdmin(admin.ModelAdmin):
    """
    `list_editable` en estado_moderacion: permite aprobar/rechazar
    publicaciones directo desde el listado (BPMN 'Crear publicación').
    `save_model` deja constancia de qué moderador aprobó/rechazó y cuándo
    (`aprobado_por`/`fecha_moderacion`) — se dispara tanto al editar desde el
    listado (list_editable) como desde el formulario completo, Django llama
    a `save_model` en ambos casos. `fecha_publicacion` es de solo lectura:
    es el timestamp de creación real de la publicación y no debe poder
    tocarse (integridad del historial).
    """
    list_display = ('id_publicacion', 'titulo', 'categoria', 'usuario_publicador', 'estado_moderacion', 'aprobado_por', 'fecha_publicacion')
    list_filter = ('estado_moderacion', 'categoria')
    list_editable = ('estado_moderacion',)
    search_fields = ('titulo', 'sub_titulo', 'categoria', 'usuario_publicador__nombre_usuario', 'usuario_publicador__apellido_usuario')
    readonly_fields = ('fecha_publicacion', 'actualizado_en', 'aprobado_por', 'fecha_moderacion')
    inlines = [ImagenesInline, DocumentoInline]

    def save_model(self, request, obj, form, change):
        if 'estado_moderacion' in form.changed_data:
            obj.aprobado_por = request.user
            obj.fecha_moderacion = timezone.now()
        super().save_model(request, obj, form, change)


class ItemPresupuestoInline(admin.TabularInline):
    """
    Hoja de presupuesto opcional que haya cargado el proveedor al confirmar
    — de solo lectura, se arma una sola vez desde contratacion_confirmar_view,
    nadie la edita a mano desde acá.
    """
    model = ItemPresupuesto
    extra = 0
    fields = ('descripcion', 'categoria', 'monto')
    readonly_fields = ('descripcion', 'categoria', 'monto')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Contratacion)
class ContratacionAdmin(admin.ModelAdmin):
    """`fecha_creacion` (inicio del trabajo) y `fecha_actualizacion` son de solo lectura — timestamps fijos por integridad, no se puede reescribir cuándo empezó un trabajo."""
    list_display = ('id_contratacion', 'publicacion', 'cliente', 'proveedor', 'estado_badge', 'monto_acordado', 'fecha_creacion')
    list_filter = ('estado',)
    search_fields = ('publicacion__titulo', 'cliente__nombre_usuario', 'proveedor__nombre_usuario')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    inlines = [ItemPresupuestoInline]

    @admin.display(description='Estado', ordering='estado')
    def estado_badge(self, obj):
        return _badge(obj.get_estado_display(), _TONOS_ESTADO_CONTRATACION.get(obj.estado, 'gray'))


@admin.register(HistorialEstadoContratacion)
class HistorialEstadoContratacionAdmin(admin.ModelAdmin):
    """Registro append-only: `fecha` es de solo lectura (no se puede alterar cuándo pasó cada cambio de estado)."""
    list_display = ('contratacion', 'estado', 'fecha')
    list_filter = ('estado',)
    readonly_fields = ('contratacion', 'estado', 'fecha')

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(IntentoAccesoSospechoso)
class IntentoAccesoSospechosoAdmin(admin.ModelAdmin):
    """
    Registro append-only (ver views._registrar_intento_sospechoso) de
    intentos de acceder a una conversación, contratación o documento ajenos,
    o de un login/re-autenticación agotado a fuerza bruta — nunca se genera
    desde un 404 común, solo desde un chequeo real de pertenencia o un
    bloqueo por intentos. Ni se puede agregar a mano ni editar: es
    evidencia, no un dato operativo.

    Geolocalización por IP (país/ciudad) vía DB-IP (ver geolocalizacion.py)
    — CC-BY 4.0, atribución obligatoria: ver el pie de este listado.
    """
    list_display = ('fecha', 'usuario', 'ip', 'ciudad', 'pais', 'recurso', 'recurso_id', 'ruta')
    list_filter = ('recurso', 'pais')
    search_fields = ('usuario__nombre_usuario', 'usuario__apellido_usuario', 'usuario__email', 'ip', 'ruta', 'ciudad', 'pais')
    readonly_fields = ('usuario', 'fecha', 'ip', 'pais', 'ciudad', 'user_agent', 'ruta', 'recurso', 'recurso_id', 'detalle')
    date_hierarchy = 'fecha'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Valoracion)
class ValoracionAdmin(admin.ModelAdmin):
    """
    Moderación de reseñas — no solo las fotos adjuntas se revisan, la reseña
    completa (puntuación + comentario) pasa por el mismo flujo que
    Publicaciones antes de contarle al público y al Ranking del receptor
    (ver `Valoracion.imagenes_aprobadas`/`_recalcular_ranking` en views.py).
    `save_model` deja constancia de quién moderó y recalcula el Ranking del
    receptor en el momento — no solo al crearse la reseña, también cada vez
    que se aprueba/rechaza acá.
    """
    list_display = ('id_valoracion', 'usuario_emisor', 'usuario_receptor', 'puntuacion', 'estado_moderacion', 'contratacion', 'fecha_valoracion')
    list_filter = ('estado_moderacion', 'puntuacion')
    list_editable = ('estado_moderacion',)
    search_fields = ('usuario_emisor__nombre_usuario', 'usuario_receptor__nombre_usuario', 'comentario')
    readonly_fields = ('fecha_valoracion', 'aprobado_por', 'fecha_moderacion')
    inlines = [ValoracionImagenInline]

    def save_model(self, request, obj, form, change):
        if 'estado_moderacion' in form.changed_data:
            obj.aprobado_por = request.user
            obj.fecha_moderacion = timezone.now()
        super().save_model(request, obj, form, change)
        _recalcular_ranking(obj.usuario_receptor)


@admin.register(ValoracionImagen)
class ValoracionImagenAdmin(admin.ModelAdmin):
    """
    Moderación de fotos adjuntas a una calificación — mismo patrón que
    PublicacionesAdmin: `list_editable` en estado_moderacion para
    aprobar/rechazar directo desde el listado. A diferencia de una
    Publicacion, acá no hay "quién aprobó" registrado a propósito (el
    volumen esperado es bajo y no se pidió ese nivel de auditoría para esto).
    """
    list_display = ('id_valoracion_imagen', 'miniatura', 'valoracion', 'estado_moderacion', 'fecha_subida')
    list_filter = ('estado_moderacion',)
    list_editable = ('estado_moderacion',)
    readonly_fields = ('fecha_subida', 'miniatura')

    @admin.display(description='Vista previa')
    def miniatura(self, obj):
        return _miniatura(obj.archivo.url) if obj.archivo else '—'


@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'puntuacion_promedio', 'total_valoraciones')


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """
    Auditoría nativa de Django (quién cambió qué y cuándo — ej. quién aprobó
    una publicación). Visible SOLO para superusers: las tres
    `has_*_permission` devuelven False para cualquiera que no sea superuser,
    así Django ni siquiera lo muestra en su panel — no hace falta ocultarlo
    a mano en la plantilla.
    """
    list_display = ('action_time', 'usuario_responsable', 'content_type', 'object_repr', 'action_flag', 'change_message')
    list_filter = ('action_flag', 'content_type')
    search_fields = ('object_repr', 'change_message', 'user__username', 'user__first_name', 'user__last_name')
    date_hierarchy = 'action_time'

    @admin.display(description='Usuario')
    def usuario_responsable(self, obj):
        """Nombre completo + username — pedido del usuario: dejar constancia de QUIÉN hizo el cambio, no solo el username."""
        nombre_completo = obj.user.get_full_name()
        if nombre_completo:
            return f'{nombre_completo} ({obj.user.username})'
        return obj.user.username

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    """
    Panel de incidencias/soporte — `list_editable` en estado_consulta para
    poder resolverlas directo desde el listado, igual que la moderación de
    publicaciones. `fecha_consulta` (cuándo se abrió) es de solo lectura por
    la misma razón que el resto de los timestamps de inicio; `fecha_termino_consulta`
    sí queda editable a propósito, para que el staff registre cuándo se resolvió.
    """
    list_display = ('id_consulta', 'asunto_consulta', 'nombre_contacto', 'email_contacto', 'estado_consulta', 'fecha_consulta')
    list_filter = ('estado_consulta',)
    list_editable = ('estado_consulta',)
    search_fields = ('asunto_consulta', 'descripcion', 'nombre_contacto', 'email_contacto')
    readonly_fields = ('fecha_consulta',)


@admin.register(Imagenes)
class ImagenesAdmin(admin.ModelAdmin):
    """Vista plana de todas las imágenes de publicaciones — para revisar una puntual, mejor entrar por la Publicacion (ver ImagenesInline)."""
    list_display = ('id_imagen', 'miniatura', 'publicacion', 'fecha_subida')
    readonly_fields = ('miniatura',)

    @admin.display(description='Vista previa')
    def miniatura(self, obj):
        return _miniatura(obj.url)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    """Vista plana de todos los documentos (identidad + respaldo de publicaciones) — para uno puntual de una publicación, mejor entrar por ahí (ver DocumentoInline)."""
    list_display = ('id_documento', 'nombre_documento', 'ver_documento', 'publicacion', 'usuario', 'estado_documento', 'fecha_subida_documento')
    list_filter = ('estado_documento',)
    search_fields = ('nombre_documento', 'usuario__nombre_usuario', 'publicacion__titulo')

    @admin.display(description='Archivo')
    def ver_documento(self, obj):
        return _ver_documento(obj)


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    """Solo lectura de la parte financiera (nadie edita un pago a mano) — respuesta_bruta queda como referencia de auditoría/soporte."""
    list_display = ('id_pago', 'contratacion', 'metodo', 'estado_badge', 'monto', 'fecha_creacion', 'fecha_confirmacion')
    list_filter = ('metodo', 'estado')
    search_fields = ('orden_compra', 'token_webpay', 'khipu_payment_id', 'contratacion__id_contratacion')
    readonly_fields = (
        'contratacion', 'monto', 'metodo', 'orden_compra', 'token_webpay',
        'khipu_payment_id', 'respuesta_bruta', 'fecha_creacion', 'fecha_confirmacion',
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description='Estado', ordering='estado')
    def estado_badge(self, obj):
        return _badge(obj.get_estado_display(), _TONOS_ESTADO_PAGO.get(obj.estado, 'gray'))


# Catálogos y modelos sin necesidad de una vista de admin a medida —
# se registran con la vista por defecto para poder al menos verlos/editarlos.
for _modelo in (
    AreaAdministrativa, Autentificacion, Comuna, Conversacion,
    EstadoAutentificacion, EstadoConsulta, EstadoDocumento,
    Firma, Gasto, Mensaje, Region, RolCuentaAdministrativa,
    TipoCuenta, TipoFirma, Transaccion, UsuarioAdministrativo,
    UsuarioConversacion,
):
    admin.site.register(_modelo)


# ---------------------------------------------------------------------------
# Reorganización del panel /admin/: por defecto Django agrupa TODO bajo un
# único bloque "Keyservapp" con los ~25 modelos sueltos uno detrás de otro —
# para alguien de soporte/moderación eso lee como un explorador de base de
# datos crudo, no como una herramienta de trabajo. Se reagrupan los mismos
# modelos (sin tocar registros ni permisos de nadie) en categorías por
# tarea. Un moderador solo tiene permisos sobre un subconjunto acotado (ver
# configurar_grupo_moderador.py), así que para él la mayoría de estas
# categorías directamente no aparecen — ve "Solicitudes y moderación" y
# "Mensajería", nada de usuarios/catálogos/finanzas.
# ---------------------------------------------------------------------------

_CATEGORIAS_ADMIN = [
    ('solicitudes', 'Solicitudes y moderación', [
        'publicaciones', 'imagenes', 'documento', 'consulta',
        'valoracion', 'valoracionimagen', 'contratacion',
        'historialestadocontratacion', 'ranking',
    ]),
    ('seguridad', 'Seguridad', ['intentoaccesosospechoso']),
    ('mensajeria', 'Mensajería', ['conversacion', 'mensaje', 'usuarioconversacion']),
    ('cuentas', 'Usuarios y cuentas', [
        'usuario', 'usuarioadministrativo', 'rolcuentaadministrativa',
        'areaadministrativa', 'group', 'user',
    ]),
    ('catalogos', 'Catálogos de referencia', [
        'region', 'comuna', 'tipocuenta', 'estadoautentificacion',
        'estadoconsulta', 'estadodocumento', 'tipofirma',
    ]),
    ('finanzas', 'Finanzas e infraestructura', ['transaccion', 'gasto', 'autentificacion', 'firma', 'pago']),
    ('auditoria', 'Auditoría', ['logentry']),
]

_get_app_list_original = admin.AdminSite.get_app_list


def _get_app_list_agrupado(self, request, app_label=None):
    """
    Reemplaza `AdminSite.get_app_list` (usada tanto por la página de inicio
    del admin como por el sidebar persistente) para devolver los modelos
    agrupados por `_CATEGORIAS_ADMIN` en vez de por app de Django. Si se pide
    una app puntual (`app_label`, ej. al clickear el breadcrumb de una app)
    se delega al comportamiento original — acá arriba las categorías son
    "apps" inventadas que no existen como tal.
    """
    if app_label:
        return _get_app_list_original(self, request, app_label)

    modelos_por_nombre = {}
    for app in self._build_app_dict(request).values():
        for model_dict in app['models']:
            modelos_por_nombre[model_dict['model']._meta.model_name] = model_dict

    usados = set()
    grupos = []
    for app_label_falso, nombre, nombres_modelo in _CATEGORIAS_ADMIN:
        modelos = [modelos_por_nombre[n] for n in nombres_modelo if n in modelos_por_nombre]
        if not modelos:
            continue
        modelos.sort(key=lambda m: m['name'])
        usados.update(nombres_modelo)
        grupos.append({
            'name': nombre, 'app_label': app_label_falso, 'app_url': '#',
            'has_module_perms': True, 'models': modelos,
        })

    # Cualquier modelo que se agregue después y nadie clasifique todavía en
    # _CATEGORIAS_ADMIN cae acá — mejor que desaparecer en silencio del admin.
    restantes = [m for nombre, m in modelos_por_nombre.items() if nombre not in usados]
    if restantes:
        restantes.sort(key=lambda m: m['name'])
        grupos.append({
            'name': 'Otros', 'app_label': 'otros', 'app_url': '#',
            'has_module_perms': True, 'models': restantes,
        })

    return grupos


admin.site.get_app_list = _get_app_list_agrupado.__get__(admin.site, admin.AdminSite)
