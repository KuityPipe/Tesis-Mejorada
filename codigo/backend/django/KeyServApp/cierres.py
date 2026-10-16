"""
Cierre de contrataciones que no llegaron a COMPLETADA (todas terminan en CANCELADA), compartido por:

- rechazo del proveedor y cancelación del cliente (`api/views.py`),
- cancelación automática de las solicitudes abiertas al pedir la eliminación de la cuenta (`derechos_titular.py`),
- expiración de solicitudes sin respuesta (`manage.py expirar_solicitudes`).

Una sola implementación para que el efecto (estado, historial, cobro pendiente anulado, aviso en el chat) no pueda
divergir entre los tres caminos.
"""
from .models import Contratacion, HistorialEstadoContratacion, Mensaje, Pago


def cancelar_contratacion(contratacion, autor, texto):
    """
    Lleva la contratación a CANCELADA, anula un cobro iniciado y no completado, y deja `texto` como mensaje de sistema
    en el chat (a nombre de `autor`). El caller decide si la transición es válida y debe llamar dentro de una
    transacción con la contratación (y su pago) bloqueadas.
    """
    from . import views as vistas_legacy  # import tardío: views importa módulos que importan este

    pago = Pago.objects.filter(contratacion=contratacion).first()
    if pago and pago.estado == Pago.PENDIENTE:
        pago.estado = Pago.ANULADO
        pago.save(update_fields=['estado'])
    contratacion.estado = Contratacion.CANCELADA
    contratacion.save()
    HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=Contratacion.CANCELADA)
    conversacion = vistas_legacy._obtener_o_crear_conversacion_de_contratacion(contratacion)
    Mensaje.objects.create(conversacion=conversacion, usuario=autor, contenido=f'[Sistema] {texto} Contratación #{contratacion.id_contratacion}.')
