"""
Registro de modelos en el panel /admin/ de Django.

Refactor Fase 3: antes este archivo estaba vacío — 0 de los ~25 modelos
eran visibles/editables desde /admin/, sin forma de inspeccionar datos
durante desarrollo/QA.
"""
from django.contrib import admin

from .models import (
    AreaAdministrativa, Autentificacion, Comuna, Consulta, Contratacion,
    Conversacion, Documento, EstadoAutentificacion, EstadoConsulta,
    EstadoDocumento, Firma, Gasto, Imagenes, Mensaje, Publicaciones, Ranking,
    Region, RolCuentaAdministrativa, TipoCuenta, TipoFirma, Transaccion,
    Usuario, UsuarioAdministrativo, UsuarioConversacion, Valoracion,
)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """No se muestra `password` en list_display a propósito (aunque ya está hasheado, no hace falta exponerlo)."""
    list_display = ('id_usuario', 'nombre_usuario', 'apellido_usuario', 'email', 'es_proveedor', 'verificado_biometricamente')
    search_fields = ('nombre_usuario', 'apellido_usuario', 'email', 'rut_usuario')
    list_filter = ('es_proveedor', 'verificado_biometricamente', 'tipo_cuenta')


@admin.register(Publicaciones)
class PublicacionesAdmin(admin.ModelAdmin):
    """`list_editable` en estado_moderacion: permite aprobar/rechazar publicaciones directo desde el listado (BPMN 'Crear publicación')."""
    list_display = ('id_publicacion', 'titulo', 'usuario_publicador', 'estado_moderacion', 'fecha_publicacion')
    list_filter = ('estado_moderacion',)
    list_editable = ('estado_moderacion',)


@admin.register(Contratacion)
class ContratacionAdmin(admin.ModelAdmin):
    list_display = ('id_contratacion', 'publicacion', 'cliente', 'proveedor', 'estado', 'fecha_creacion')
    list_filter = ('estado',)


@admin.register(Valoracion)
class ValoracionAdmin(admin.ModelAdmin):
    list_display = ('id_valoracion', 'usuario_emisor', 'usuario_receptor', 'puntuacion', 'fecha_valoracion')


@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'puntuacion_promedio', 'total_valoraciones')


# Catálogos y modelos sin necesidad de una vista de admin a medida —
# se registran con la vista por defecto para poder al menos verlos/editarlos.
for _modelo in (
    AreaAdministrativa, Autentificacion, Comuna, Consulta, Conversacion,
    Documento, EstadoAutentificacion, EstadoConsulta, EstadoDocumento,
    Firma, Gasto, Imagenes, Mensaje, Region, RolCuentaAdministrativa,
    TipoCuenta, TipoFirma, Transaccion, UsuarioAdministrativo,
    UsuarioConversacion,
):
    admin.site.register(_modelo)
