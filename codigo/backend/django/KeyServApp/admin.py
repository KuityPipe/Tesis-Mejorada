"""
Registro de modelos en el panel /admin/ de Django.

Refactor Fase 3: antes este archivo estaba vacío — 0 de los ~25 modelos
eran visibles/editables desde /admin/, sin forma de inspeccionar datos
durante desarrollo/QA.
"""
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.utils import timezone

from .models import (
    AreaAdministrativa, Autentificacion, Comuna, Consulta, Contratacion,
    Conversacion, Documento, EstadoAutentificacion, EstadoConsulta,
    EstadoDocumento, Firma, Gasto, HistorialEstadoContratacion, Imagenes,
    Mensaje, Publicaciones, Ranking, Region, RolCuentaAdministrativa,
    TipoCuenta, TipoFirma, Transaccion, Usuario, UsuarioAdministrativo,
    UsuarioConversacion, Valoracion,
)


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

    def save_model(self, request, obj, form, change):
        if 'estado_moderacion' in form.changed_data:
            obj.aprobado_por = request.user
            obj.fecha_moderacion = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(Contratacion)
class ContratacionAdmin(admin.ModelAdmin):
    """`fecha_creacion` (inicio del trabajo) y `fecha_actualizacion` son de solo lectura — timestamps fijos por integridad, no se puede reescribir cuándo empezó un trabajo."""
    list_display = ('id_contratacion', 'publicacion', 'cliente', 'proveedor', 'estado', 'fecha_creacion')
    list_filter = ('estado',)
    search_fields = ('publicacion__titulo', 'cliente__nombre_usuario', 'proveedor__nombre_usuario')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')


@admin.register(HistorialEstadoContratacion)
class HistorialEstadoContratacionAdmin(admin.ModelAdmin):
    """Registro append-only: `fecha` es de solo lectura (no se puede alterar cuándo pasó cada cambio de estado)."""
    list_display = ('contratacion', 'estado', 'fecha')
    list_filter = ('estado',)
    readonly_fields = ('contratacion', 'estado', 'fecha')

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Valoracion)
class ValoracionAdmin(admin.ModelAdmin):
    list_display = ('id_valoracion', 'usuario_emisor', 'usuario_receptor', 'puntuacion', 'fecha_valoracion')


@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'puntuacion_promedio', 'total_valoraciones')


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """
    Auditoría nativa de Django (quién cambió qué y cuándo — ej. quién aprobó
    una publicación). Visible SOLO para superusers ("el moderador tiene todo
    menos los logs"): las tres `has_*_permission` devuelven False para
    cualquiera que no sea superuser, así Django ni siquiera lo muestra en su
    panel — no hace falta ocultarlo a mano en la plantilla.
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


# Catálogos y modelos sin necesidad de una vista de admin a medida —
# se registran con la vista por defecto para poder al menos verlos/editarlos.
for _modelo in (
    AreaAdministrativa, Autentificacion, Comuna, Conversacion,
    Documento, EstadoAutentificacion, EstadoConsulta, EstadoDocumento,
    Firma, Gasto, Imagenes, Mensaje, Region, RolCuentaAdministrativa,
    TipoCuenta, TipoFirma, Transaccion, UsuarioAdministrativo,
    UsuarioConversacion,
):
    admin.site.register(_modelo)
