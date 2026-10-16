"""
Margen de KeyServ por tramo de comisión y medio de pago. La comisión se cobra ENCIMA del precio del servicio (el cliente
paga M + c*M). Cambia MEDIOS (tarifas de las pasarelas), los tramos y los montos de ejemplo, y corre:

    python docs/seguimiento/calcular_margen.py

Imprime tablas en Markdown. Las tarifas de MEDIOS son las publicadas por terceros en octubre de 2026: confírmalas con
Transbank, Flow o Mercado Pago antes de decidir. El resultado es el margen BRUTO por transacción, antes de hosting,
revisión de identidad, soporte e impuestos a la renta.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")
IVA = 1.19

# Costo de la pasarela como % del TOTAL cobrado (sin IVA) y fijo por transacción (sin IVA).
MEDIOS = {
    'Webpay débito/prepago (1,75%)': (0.0175, 0),
    'Webpay crédito (2,35%)': (0.0235, 0),
    'Flow tarjeta (2,89%)': (0.0289, 0),
    'Flow/Khipu transferencia (0,99% + $100)': (0.0099, 100),
}

TRAMOS_DUENO = [(50_000, 0.05), (200_000, 0.04), (500_000, 0.035), (None, 0.03)]  # el hueco 200-500k se rellenó con 3,5%
TRAMOS_PROPUESTA = [(50_000, 0.06), (200_000, 0.05), (500_000, 0.045), (None, 0.04)]
MINIMA = 1000


def pct(monto, tramos):
    for tope, p in tramos:
        if tope is None or monto <= tope:
            return p


def margen(monto, tramos, g, fijo, iva_recuperable):
    c = pct(monto, tramos)
    comision = max(round(monto * c), MINIMA)
    total = monto + comision
    ingreso_neto = comision / IVA                       # la comisión incluye IVA
    costo = total * g * (1 if iva_recuperable else IVA) + fijo * (1 if iva_recuperable else IVA)
    return comision, ingreso_neto - costo


def tabla(titulo, tramos, iva_recuperable):
    print(f'\n### {titulo} — {"IVA de la pasarela recuperable" if iva_recuperable else "IVA de la pasarela NO recuperable"}')
    montos = [20_000, 50_000, 100_000, 300_000, 600_000]
    print('| Medio | ' + ' | '.join(f'${m:,}'.replace(',', '.') for m in montos) + ' |')
    print('|---|' + '---|' * len(montos))
    for nombre, (g, fijo) in MEDIOS.items():
        celdas = []
        for m in montos:
            com, mar = margen(m, tramos, g, fijo, iva_recuperable)
            celdas.append(f'{mar:+,.0f}'.replace(',', '.'))
        print(f'| {nombre} | ' + ' | '.join(celdas) + ' |')


for titulo, tramos in (('Tramos del dueño (5 / 4 / 3,5* / 3 %)', TRAMOS_DUENO), ('Propuesta (6 / 5 / 4,5 / 4 %, mínimo $1.000)', TRAMOS_PROPUESTA)):
    for rec in (True, False):
        tabla(titulo, tramos, rec)
