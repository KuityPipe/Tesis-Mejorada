"""
Comisión de la plataforma por tramos. Se cobra **encima** del precio acordado y la paga el cliente: el cliente paga
`monto_servicio + comisión` en la pasarela y el proveedor recibe el `monto_servicio` completo (cuando existan los pagos
al proveedor, ver docs/PLAN_FLUJO_DE_DINERO.md). Se calcula y se congela en el `Pago` al iniciar el cobro, así que
cambiar los tramos después no altera pagos ya iniciados.

Tramos configurables (`settings.COMISION_TRAMOS`, variable de entorno `COMISION_TRAMOS` en JSON): lista de
`[tope_en_CLP, porcentaje]` ordenada de menor a mayor; el último con tope `null` cubre todo lo que sigue. Hay una
comisión mínima (`settings.COMISION_MINIMA`). Los valores por defecto salen del análisis de costos de las pasarelas en
`docs/ANALISIS_COMISION.md`: con 3 % o menos en montos grandes y pago con tarjeta, KeyServ pierde dinero.

La comisión se asume con IVA incluido (precio al consumidor). El tratamiento tributario real (IVA de la comisión,
boleta o factura) está pendiente de un contador, ver PLAN_FLUJO_DE_DINERO.md §4.
"""
from collections import namedtuple
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings

Desglose = namedtuple('Desglose', 'monto_servicio porcentaje comision total')


def _tramos():
    tramos = []
    for tope, porcentaje in settings.COMISION_TRAMOS:
        tramos.append((None if tope is None else int(tope), Decimal(str(porcentaje))))
    return tramos


def porcentaje_para(monto):
    """Porcentaje del tramo que corresponde a `monto` (CLP)."""
    tramos = _tramos()
    for tope, porcentaje in tramos:
        if tope is None or monto <= tope:
            return porcentaje
    return tramos[-1][1]


def calcular(monto_servicio):
    """Desglose de lo que paga el cliente por un servicio de `monto_servicio` CLP: comisión (entera, mínimo aplicado) y total."""
    monto = int(monto_servicio)
    porcentaje = porcentaje_para(monto)
    comision = int((Decimal(monto) * porcentaje / 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    comision = max(comision, int(settings.COMISION_MINIMA)) if monto > 0 else 0
    return Desglose(monto, porcentaje, comision, monto + comision)


def aplicar(pago, contratacion):
    """Fija en el `Pago` el desglose de la contratación; `pago.monto` pasa a ser el TOTAL que se cobra en la pasarela."""
    desglose = calcular(contratacion.monto_acordado)
    pago.monto_servicio = desglose.monto_servicio
    pago.comision_porcentaje = desglose.porcentaje
    pago.comision_monto = desglose.comision
    pago.monto = desglose.total
    return desglose


def tramos_para_publico():
    """Tramos como lista de `[tope, porcentaje]` (números) para pasarlos a la UI."""
    return [[tope, float(porcentaje)] for tope, porcentaje in _tramos()]
