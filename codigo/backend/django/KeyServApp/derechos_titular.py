"""
Derechos del titular de datos (Ley 21.719): acceso/portabilidad y supresión.

- `exportar_datos`: copia de los datos personales de una persona, en un dict serializable a JSON.
  No incluye el hash de contraseña, los tokens ni el vector facial (solo si existe uno).
- `eliminar_cuenta`: supresión por anonimización. Se borra o vacía lo identificable (perfil,
  rostro, documentos, mensajes, fotos, sesiones) pero se conservan las filas de contratos y
  pagos, porque hay obligaciones tributarias/contables de retención y los datos de la otra
  parte dependen de ellas. La cuenta queda inutilizable (email y contraseña reemplazados).

BORRADOR técnico: los plazos de retención de contratos/pagos y el alcance exacto de lo que
se conserva deben validarse con un abogado (ver docs/cumplimiento/).
"""
import secrets

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    ConsentimientoBiometrico, Consulta, Contratacion, Documento, EventoVerificacion,
    IntentoAccesoSospechoso, Mensaje, Pago, Publicaciones, SolicitudTitular, TokenSesion,
    Valoracion, ValoracionImagen,
)

MENSAJE_BLOQUEADO = (
    'Bloqueaste el tratamiento de tus datos: tu cuenta se conserva pero no puedes publicar ni contratar. '
    'Puedes desbloquearla cuando quieras desde "Mis datos".'
)
CODIGO_BLOQUEADO = 'tratamiento_bloqueado'


def tratamiento_bloqueado(usuario):
    return bool(usuario.tratamiento_bloqueado_en)


@transaction.atomic
def fijar_bloqueo(usuario, bloquear):
    """Derecho de bloqueo: reversible; deja constancia como solicitud resuelta al instante."""
    if bloquear == tratamiento_bloqueado(usuario):
        return
    usuario.tratamiento_bloqueado_en = timezone.now() if bloquear else None
    usuario.save(update_fields=['tratamiento_bloqueado_en'])
    SolicitudTitular.objects.create(
        usuario=usuario, tipo=SolicitudTitular.BLOQUEO, estado=SolicitudTitular.RESUELTA,
        detalle='Bloqueo del tratamiento' if bloquear else 'Desbloqueo del tratamiento',
        respuesta='Aplicado automáticamente.', resuelto_en=timezone.now(),
    )


@transaction.atomic
def solicitar_oposicion_biometria(usuario):
    """Oposición al tratamiento biométrico: se revoca el consentimiento y se borra el vector, al instante."""
    ConsentimientoBiometrico.revocar(usuario)
    return SolicitudTitular.objects.create(
        usuario=usuario, tipo=SolicitudTitular.OPOSICION, estado=SolicitudTitular.RESUELTA,
        detalle='Oposición al tratamiento biométrico',
        respuesta='Consentimiento revocado y vector facial eliminado.', resuelto_en=timezone.now(),
    )

ESTADOS_ACTIVOS = [Contratacion.SOLICITADA, Contratacion.CONFIRMADA, Contratacion.EN_CURSO]


def contrataciones_activas(usuario):
    return Contratacion.objects.filter(Q(cliente=usuario) | Q(proveedor=usuario), estado__in=ESTADOS_ACTIVOS)


def exportar_datos(usuario):
    perfil = {
        'id': usuario.id_usuario,
        'rut': usuario.rut_usuario,
        'nombre': usuario.nombre_usuario,
        'segundo_nombre': usuario.nombre2_usuario,
        'apellido': usuario.apellido_usuario,
        'segundo_apellido': usuario.apellido2_usuario,
        'email': usuario.email,
        'telefono': usuario.telefono,
        'direccion': usuario.direccion_usuario,
        'comuna': usuario.comuna.nombre_comuna if usuario.comuna_id else None,
        'edad': usuario.edad,
        'es_proveedor': usuario.es_proveedor,
        'areas_servicio': usuario.areas_servicio,
        'experiencia': usuario.experiencia,
        'tiene_foto_perfil': bool(usuario.foto_perfil),
        'verificado_biometricamente': usuario.verificado_biometricamente,
        'verificado_en': usuario.verificado_en,
        'tratamiento_bloqueado': bool(usuario.tratamiento_bloqueado_en),
        'tiene_rostro_registrado': bool(usuario.encoding_facial),
    }
    return {
        'perfil': perfil,
        'consentimientos_biometricos': [
            {'version': c.version, 'otorgado_en': c.otorgado_en, 'revocado_en': c.revocado_en}
            for c in ConsentimientoBiometrico.objects.filter(usuario=usuario)
        ],
        'publicaciones': [
            {'id': p.id_publicacion, 'titulo': p.titulo, 'descripcion': p.descripcion_publicacion,
             'categoria': p.categoria, 'precio': p.precio, 'estado': p.estado_moderacion, 'fecha': p.fecha_publicacion}
            for p in Publicaciones.objects.filter(usuario_publicador=usuario)
        ],
        'contrataciones': [
            {'id': c.id_contratacion, 'rol': 'cliente' if c.cliente_id == usuario.pk else 'proveedor',
             'publicacion': c.publicacion.titulo, 'estado': c.estado, 'monto_acordado': c.monto_acordado,
             'fecha': c.fecha_creacion}
            for c in Contratacion.objects.filter(Q(cliente=usuario) | Q(proveedor=usuario)).select_related('publicacion')
        ],
        'mensajes_enviados': [
            {'contratacion': m.conversacion.contratacion_id, 'contenido': m.contenido,
             'tiene_imagen': bool(m.imagen), 'fecha': m.fecha_envio}
            for m in Mensaje.objects.filter(usuario=usuario).select_related('conversacion')
        ],
        'valoraciones_emitidas': [
            {'puntuacion': v.puntuacion, 'comentario': v.comentario, 'fecha': v.fecha_valoracion}
            for v in Valoracion.objects.filter(usuario_emisor=usuario)
        ],
        'valoraciones_recibidas': [
            {'puntuacion': v.puntuacion, 'comentario': v.comentario, 'fecha': v.fecha_valoracion}
            for v in Valoracion.objects.filter(usuario_receptor=usuario)
        ],
        # Sin `respuesta_bruta` (respuesta cruda del medio de pago): es dato de terceros.
        'pagos': [
            {'contratacion': p.contratacion_id, 'monto': p.monto, 'metodo': p.metodo, 'estado': p.estado,
             'fecha': p.fecha_creacion}
            for p in Pago.objects.filter(Q(contratacion__cliente=usuario) | Q(contratacion__proveedor=usuario))
        ],
        'documentos': [
            {'nombre': d.nombre_documento, 'fecha': d.fecha_subida_documento}
            for d in Documento.objects.filter(usuario=usuario)
        ],
        'consultas_de_soporte': [
            {'asunto': c.asunto_consulta, 'descripcion': c.descripcion, 'fecha': c.fecha_consulta}
            for c in Consulta.objects.filter(usuario_consulta=usuario)
        ],
        'eventos_de_verificacion': [
            {'fecha': e.fecha, 'metodo': e.metodo, 'accion': e.accion, 'resultado': e.resultado}
            for e in EventoVerificacion.objects.filter(usuario=usuario)
        ],
        'solicitudes_de_derechos': [
            {'tipo': s.tipo, 'estado': s.estado, 'detalle': s.detalle, 'respuesta': s.respuesta,
             'fecha': s.creado_en, 'resuelta_en': s.resuelto_en}
            for s in SolicitudTitular.objects.filter(usuario=usuario)
        ],
        'accesos_sospechosos_asociados': [
            {'fecha': i.fecha, 'ruta': i.ruta, 'detalle': i.detalle}
            for i in IntentoAccesoSospechoso.objects.filter(usuario=usuario)
        ],
    }


def _borrar_archivo(campo):
    if campo:
        campo.delete(save=False)


@transaction.atomic
def eliminar_cuenta(usuario):
    """Anonimiza la cuenta (ver docstring del módulo). Llamar solo sin contrataciones activas."""
    ConsentimientoBiometrico.revocar(usuario)  # borra el vector facial y baja la verificación
    TokenSesion.objects.filter(usuario=usuario).delete()
    EventoVerificacion.objects.filter(usuario=usuario).delete()
    SolicitudTitular.objects.filter(usuario=usuario).delete()

    for documento in Documento.objects.filter(usuario=usuario):
        _borrar_archivo(documento.archivo_subido)
        documento.delete()

    for mensaje in Mensaje.objects.filter(usuario=usuario):
        _borrar_archivo(mensaje.imagen)
        mensaje.contenido = ''
        mensaje.imagen = None
        mensaje.save()

    for imagen in ValoracionImagen.objects.filter(valoracion__usuario_emisor=usuario):
        _borrar_archivo(imagen.archivo)
        imagen.delete()
    Valoracion.objects.filter(usuario_emisor=usuario).update(comentario=None)

    # Las publicaciones dejan de ser visibles; se conservan porque los contratos las referencian.
    Publicaciones.objects.filter(usuario_publicador=usuario).update(
        estado_moderacion=Publicaciones.RECHAZADA, descripcion_publicacion='', sub_titulo='',
    )
    IntentoAccesoSospechoso.objects.filter(usuario=usuario).update(usuario=None)
    Consulta.objects.filter(usuario_consulta=usuario).update(usuario_consulta=None, nombre_contacto='', email_contacto='')

    _borrar_archivo(usuario.foto_perfil)
    usuario.foto_perfil = None
    usuario.rut_usuario = 'ELIMINADO'
    usuario.nombre_usuario = 'Usuario'
    usuario.nombre2_usuario = None
    usuario.apellido_usuario = 'eliminado'
    usuario.apellido2_usuario = None
    usuario.email = f'eliminado-{usuario.pk}@eliminado.invalid'
    usuario.telefono = 0
    usuario.direccion_usuario = ''
    usuario.areas_servicio = ''
    usuario.experiencia = ''
    usuario.es_proveedor = False
    usuario.verificado_biometricamente = False
    usuario.verificado_en = None
    usuario.tratamiento_bloqueado_en = None
    usuario.set_password(secrets.token_urlsafe(32))
    usuario.save()
