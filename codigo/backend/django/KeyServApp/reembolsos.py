"""
Registro y resolución de reembolsos. **No mueve dinero**: deja constancia de lo que hay que devolver y de quién lo
resolvió; la devolución real (transferencia o reverso en la pasarela) la hace una persona del staff y aquí solo se anota.
Ver docs/PLAN_FLUJO_DE_DINERO.md para lo que falta (reembolsos automáticos por pasarela, parciales, contracargos).

Casos que abren un reembolso:
- `PAGO_TARDIO`: un pago se aprobó sobre una contratación que ya estaba cancelada (típico de Khipu, cuyo webhook llega tarde).
- `CANCELACION`: el cliente pidió cancelar un trabajo ya pagado (`POST /api/contrataciones/<id>/reembolso/`).
"""
import logging

from django.db import transaction
from django.utils import timezone

from .models import Contratacion, HistorialEstadoContratacion, Pago, Reembolso

logger = logging.getLogger(__name__)


def abrir(pago, motivo, detalle=''):
    """
    Abre un reembolso PENDIENTE por el total del pago. Idempotente: si ya hay uno abierto o resuelto por el mismo
    motivo para ese pago, no crea otro y devuelve `(reembolso, False)`.
    """
    existente = Reembolso.objects.filter(pago=pago, motivo=motivo).exclude(estado=Reembolso.RECHAZADO).first()
    if existente:
        return existente, False
    reembolso = Reembolso.objects.create(pago=pago, monto=pago.monto, motivo=motivo, detalle=(detalle or '')[:300])
    logger.warning('Reembolso abierto: id=%s pago=%s motivo=%s monto=%s', reembolso.pk, pago.pk, motivo, pago.monto)
    return reembolso, True


@transaction.atomic
def marcar_reembolsado(reembolso, staff, referencia=''):
    """
    El staff confirma que devolvió el dinero (fuera del sistema). Si el trabajo seguía EN_CURSO se cancela y el pago
    queda ANULADO, para que la contratación y el pago reflejen lo que ocurrió.
    """
    if reembolso.estado != Reembolso.PENDIENTE:
        return reembolso
    reembolso.estado = Reembolso.REEMBOLSADO
    reembolso.resuelto_por = staff
    reembolso.resuelto_en = timezone.now()
    reembolso.referencia = (referencia or '')[:120]
    reembolso.save()

    contratacion = reembolso.pago.contratacion
    if contratacion.estado == Contratacion.EN_CURSO:
        contratacion.estado = Contratacion.CANCELADA
        contratacion.save()
        HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=Contratacion.CANCELADA)
    Pago.objects.filter(pk=reembolso.pago_id).update(estado=Pago.ANULADO)
    return reembolso


@transaction.atomic
def rechazar(reembolso, staff, nota=''):
    """El staff decide no devolver (queda anotado quién y por qué). El trabajo sigue como estaba."""
    if reembolso.estado != Reembolso.PENDIENTE:
        return reembolso
    reembolso.estado = Reembolso.RECHAZADO
    reembolso.resuelto_por = staff
    reembolso.resuelto_en = timezone.now()
    reembolso.referencia = (nota or '')[:120]
    reembolso.save()
    return reembolso
