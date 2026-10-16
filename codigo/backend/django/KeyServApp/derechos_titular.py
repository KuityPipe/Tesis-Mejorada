"""
Derechos del titular de datos (Ley 21.719): acceso/portabilidad y supresión.

- `exportar_datos`: copia de los datos personales de una persona, en un dict serializable a JSON.
  No incluye el hash de contraseña, los tokens ni el vector facial (solo si existe uno).
- `solicitar_eliminacion` + `anonimizar_cuentas_vencidas`: la supresión no es inmediata; la cuenta queda bloqueada
  `settings.CUENTA_ELIMINACION_DIAS` (15) días y luego se anonimiza (decisión del dueño, para no perder la cuenta si
  surge una queja o un problema con la otra parte del trabajo). Qué más se conserva como evidencia es una decisión
  legal pendiente: docs/adr/0007-retencion-y-evidencia.md.
- `eliminar_cuenta`: supresión por anonimización. Se borra o vacía lo identificable (perfil,
  rostro, documentos, mensajes, fotos, sesiones) pero se conservan las filas de contratos y
  pagos, porque hay obligaciones tributarias/contables de retención y los datos de la otra
  parte dependen de ellas. La cuenta queda inutilizable (email y contraseña reemplazados).

BORRADOR técnico: los plazos de retención de contratos/pagos y el alcance exacto de lo que
se conserva deben validarse con un abogado (ver docs/cumplimiento/).
"""
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from . import cierres, notificaciones_correo
from .api import jwt_utils

from .models import (
    CodigoSeguridad, ConsentimientoBiometrico, Consulta, Contratacion, Documento, EventoVerificacion,
    IntentoAccesoSospechoso, Mensaje, Pago, Publicaciones, SolicitudTitular, TokenSesion,
    Usuario, Valoracion, ValoracionImagen,
)

logger = logging.getLogger(__name__)

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
    if not bloquear:
        # Desbloquear una cuenta con eliminación programada la cancela: si no, la persona creería que recuperó su
        # cuenta y días después se anonimizaría igual.
        usuario.eliminacion_solicitada_en = None
    usuario.save(update_fields=['tratamiento_bloqueado_en', 'eliminacion_solicitada_en'])
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
def fecha_eliminacion_programada(usuario):
    """Cuándo se anonimizará la cuenta (solicitud + plazo de espera), o `None` si no pidió eliminarla."""
    if not usuario.eliminacion_solicitada_en:
        return None
    return usuario.eliminacion_solicitada_en + timedelta(days=settings.CUENTA_ELIMINACION_DIAS)


@transaction.atomic
def solicitar_eliminacion(usuario):
    """
    Programa la eliminación de la cuenta: se cancelan sus solicitudes aún sin confirmar (para que nadie pueda impedir
    la supresión solicitándole un servicio), la cuenta queda bloqueada (fuera del catálogo, sin publicar ni contratar)
    y sus sesiones se cierran. La anonimización real ocurre pasado el plazo de espera. Llamar solo sin contrataciones
    confirmadas o en curso. Devuelve la fecha de anonimización; repetirlo no reinicia el plazo.
    """
    ya_programada = fecha_eliminacion_programada(usuario)
    if ya_programada:
        return ya_programada

    texto = 'cerró su cuenta, así que la solicitud se canceló.'
    solicitadas = Contratacion.objects.select_for_update().filter(
        Q(cliente=usuario) | Q(proveedor=usuario), estado=Contratacion.SOLICITADA,
    ).select_related('cliente', 'proveedor', 'publicacion')
    for contratacion in solicitadas:
        cierres.cancelar_contratacion(contratacion, usuario, f'{usuario} {texto}')
        otra_parte = contratacion.proveedor if contratacion.cliente_id == usuario.pk else contratacion.cliente
        notificaciones_correo.avisar(
            otra_parte, 'una solicitud se canceló',
            f'La solicitud del servicio "{contratacion.publicacion.titulo}" se canceló porque la otra persona cerró su cuenta.',
        )

    usuario.eliminacion_solicitada_en = timezone.now()
    if not usuario.tratamiento_bloqueado_en:
        usuario.tratamiento_bloqueado_en = usuario.eliminacion_solicitada_en
    usuario.save(update_fields=['eliminacion_solicitada_en', 'tratamiento_bloqueado_en'])
    jwt_utils.revocar_todas_las_sesiones(usuario)
    fecha = fecha_eliminacion_programada(usuario)
    notificaciones_correo.avisar(
        usuario, 'tu cuenta se eliminará',
        f'Pediste eliminar tu cuenta. Quedó bloqueada y se eliminará el {fecha:%d/%m/%Y}. Si no fuiste tú, escríbenos antes de esa fecha desde la sección Contacto.',
    )
    return fecha


def anonimizar_cuentas_vencidas(dias=None, dry_run=False):
    """
    Anonimiza (`eliminar_cuenta`) las cuentas cuyo plazo de espera ya venció. Una que, pese a todo, tenga una
    contratación confirmada o en curso se deja para la próxima corrida. Idempotente. Devuelve la cantidad.
    """
    dias = settings.CUENTA_ELIMINACION_DIAS if dias is None else dias
    limite = timezone.now() - timedelta(days=dias)
    pendientes = Usuario.objects.filter(eliminacion_solicitada_en__lte=limite).exclude(rut_usuario='ELIMINADO')
    total = 0
    for usuario in pendientes:
        if contrataciones_activas(usuario).exists():
            logger.warning('Cuenta con plazo vencido pero con contrataciones activas, se pospone: usuario_id=%s', usuario.pk)
            continue
        if not dry_run:
            eliminar_cuenta(usuario)
        total += 1
    return total


def eliminar_cuenta(usuario):
    """Anonimiza la cuenta (ver docstring del módulo). Llamar solo sin contrataciones activas."""
    ConsentimientoBiometrico.revocar(usuario)  # borra el vector facial y baja la verificación
    TokenSesion.objects.filter(usuario=usuario).delete()
    EventoVerificacion.objects.filter(usuario=usuario).delete()
    CodigoSeguridad.objects.filter(usuario=usuario).delete()
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
