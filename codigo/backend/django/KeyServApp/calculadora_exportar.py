"""
Exportación de la calculadora de valorización (docs/adr/0009): una planilla .xlsx con las **fórmulas visibles y editables**
(las celdas amarillas son los datos; todo lo demás se recalcula) y un PDF de una página con el resumen.

Ni la planilla ni el PDF son documentos tributarios: son una ayuda para fijar un precio.
"""
from io import BytesIO

from django.conf import settings
from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from . import calculadora, comisiones

AMARILLO = PatternFill('solid', fgColor='FFF2CC')
GRIS = PatternFill('solid', fgColor='E7E6E6')
NEGRITA = Font(bold=True)
FORMATO_PESOS = '"$"#,##0'
FILAS_MATERIALES_MIN = 8

AVISO = (
    'Esta valorización es una ayuda para fijar un precio: no es un documento tributario ni una oferta. La retención de la '
    'boleta de honorarios es una estimación; confirma la cifra vigente con un contador.'
)


def _formula_porcentaje_comision(celda):
    """Fórmula de Excel con el porcentaje del tramo de comisión para el monto de `celda` (mismos tramos que `comisiones.py`)."""
    tramos = comisiones._tramos()
    formula = str(tramos[-1][1])
    for tope, porcentaje in reversed(tramos[:-1]):
        formula = f'IF({celda}<={tope},{porcentaje},{formula})'
    return formula


def generar_xlsx(datos):
    """Planilla con las fórmulas de `calculadora.calcular`. `datos` es el mismo cuerpo JSON que recibe la calculadora."""
    d = calculadora.normalizar(datos)
    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Valorización'
    hoja.column_dimensions['A'].width = 46
    for col in 'BCDEF':
        hoja.column_dimensions[col].width = 18

    def titulo(fila, texto):
        celda = hoja.cell(fila, 1, texto)
        celda.font = NEGRITA
        for col in range(1, 7):
            hoja.cell(fila, col).fill = GRIS

    def dato(fila, col, valor, formato=None):
        celda = hoja.cell(fila, col, valor)
        celda.fill = AMARILLO
        if formato:
            celda.number_format = formato
        return celda

    def formula(fila, col, texto, formato=FORMATO_PESOS, negrita=False):
        celda = hoja.cell(fila, col, texto)
        celda.number_format = formato
        if negrita:
            celda.font = NEGRITA
        return celda

    hoja['A1'] = 'Valorización de un trabajo - KeyServ'
    hoja['A1'].font = Font(bold=True, size=14)
    hoja['A2'] = 'Las celdas amarillas son datos que puedes cambiar; el resto son fórmulas que se recalculan.'

    # --- Materiales
    titulo(4, 'MATERIALES')
    for col, texto in enumerate(['Descripción', 'Cantidad', 'Unidad', 'Precio unitario', '¿Reutilizado o reparado? (sí/no)', 'Subtotal'], start=1):
        hoja.cell(5, col, texto).font = NEGRITA
    n_filas = max(len(d['materiales']), FILAS_MATERIALES_MIN)
    primera = 6
    for i in range(n_filas):
        fila = primera + i
        m = d['materiales'][i] if i < len(d['materiales']) else None
        dato(fila, 1, m['descripcion'] if m else None)
        dato(fila, 2, float(m['cantidad']) if m else None, '#,##0.##')
        dato(fila, 3, m['unidad'] if m else None)
        dato(fila, 4, float(m['precio_unitario']) if m else None, FORMATO_PESOS)
        dato(fila, 5, ('sí' if m['reutilizado'] else 'no') if m else None)
        formula(fila, 6, f'=B{fila}*D{fila}')
    ultima = primera + n_filas - 1
    fila = ultima + 1
    hoja.cell(fila, 1, 'Total materiales').font = NEGRITA
    formula(fila, 6, f'=SUM(F{primera}:F{ultima})', negrita=True)
    f_materiales = fila

    # --- Traslado
    fila += 2
    titulo(fila, 'TRASLADO')
    t = d['traslado']
    fijo = t['modo'] == 'fijo'
    f_km, f_costo, f_fijo, f_peajes, f_traslado = fila + 1, fila + 2, fila + 3, fila + 4, fila + 5
    hoja.cell(f_km, 1, 'Kilómetros de ida y vuelta')
    dato(f_km, 2, None if fijo else float(t['km_ida_vuelta']), '#,##0.##')
    hoja.cell(f_costo, 1, 'Costo por kilómetro')
    dato(f_costo, 2, None if fijo else float(t['costo_km']), FORMATO_PESOS)
    hoja.cell(f_fijo, 1, 'Monto fijo (si lo usas, reemplaza kilómetros × costo)')
    dato(f_fijo, 2, float(t['monto_fijo']) if fijo else None, FORMATO_PESOS)
    hoja.cell(f_peajes, 1, 'Peajes y estacionamiento')
    dato(f_peajes, 2, float(t['peajes_estacionamiento']), FORMATO_PESOS)
    hoja.cell(f_traslado, 1, 'Total traslado').font = NEGRITA
    formula(f_traslado, 6, f'=IF(N(B{f_fijo})>0,B{f_fijo},N(B{f_km})*N(B{f_costo}))+N(B{f_peajes})', negrita=True)

    # --- Mano de obra
    fila = f_traslado + 2
    titulo(fila, 'MANO DE OBRA')
    mo = d['mano_obra']
    f_horas, f_vh, f_personas, f_mo = fila + 1, fila + 2, fila + 3, fila + 4
    hoja.cell(f_horas, 1, 'Horas de trabajo')
    dato(f_horas, 2, float(mo['horas']), '#,##0.##')
    hoja.cell(f_vh, 1, 'Valor por hora')
    dato(f_vh, 2, float(mo['valor_hora']), FORMATO_PESOS)
    hoja.cell(f_personas, 1, 'Personas')
    dato(f_personas, 2, float(mo['personas']), '#,##0.##')
    hoja.cell(f_mo, 1, 'Total mano de obra').font = NEGRITA
    formula(f_mo, 6, f'=B{f_horas}*B{f_vh}*B{f_personas}', negrita=True)

    # --- Herramientas
    fila = f_mo + 2
    titulo(fila, 'HERRAMIENTAS')
    h = d['herramientas']
    por_monto = h['modo'] == 'monto'
    f_hm, f_hp, f_herr = fila + 1, fila + 2, fila + 3
    hoja.cell(f_hm, 1, 'Monto (si lo usas, reemplaza el porcentaje)')
    dato(f_hm, 2, float(h['monto']) if por_monto else None, FORMATO_PESOS)
    hoja.cell(f_hp, 1, 'O porcentaje sobre la mano de obra (%)')
    dato(f_hp, 2, None if por_monto else float(h['porcentaje']), '0.##')
    hoja.cell(f_herr, 1, 'Total herramientas').font = NEGRITA
    formula(f_herr, 6, f'=IF(N(B{f_hm})>0,B{f_hm},F{f_mo}*N(B{f_hp})/100)', negrita=True)

    # --- Parámetros
    fila = f_herr + 2
    titulo(fila, 'PARÁMETROS')
    f_imp, f_gan, f_ret, f_boleta = fila + 1, fila + 2, fila + 3, fila + 4
    hoja.cell(f_imp, 1, 'Imprevistos (%)')
    dato(f_imp, 2, float(d['imprevistos_pct']), '0.##')
    hoja.cell(f_gan, 1, 'Ganancia (%)')
    dato(f_gan, 2, float(d['ganancia_pct']), '0.##')
    hoja.cell(f_ret, 1, 'Retención de la boleta de honorarios (%) - estimación')
    dato(f_ret, 2, float(d['retencion_pct']), '0.##')
    hoja.cell(f_boleta, 1, '¿Emites boleta de honorarios? (1 = sí, 0 = no)')
    dato(f_boleta, 2, 1 if d['documento'] == 'BOLETA_HONORARIOS' else 0, '0')

    # --- Resultado
    fila = f_boleta + 2
    titulo(fila, 'RESULTADO')
    f_c, f_i, f_g, f_neto, f_pb, f_rm, f_liq, f_com, f_tot = (fila + k for k in range(1, 10))
    filas = [
        (f_c, 'Costo directo (materiales + traslado + mano de obra + herramientas)', f'=F{f_materiales}+F{f_traslado}+F{f_mo}+F{f_herr}'),
        (f_i, 'Imprevistos', f'=ROUND(F{f_c}*B{f_imp}/100,0)'),
        (f_g, 'Ganancia', f'=ROUND((F{f_c}+F{f_i})*B{f_gan}/100,0)'),
        (f_neto, 'Precio neto (lo que quieres que te quede)', f'=F{f_c}+F{f_i}+F{f_g}'),
        (f_pb, 'Precio a cobrar (con boleta, ya incluye la retención)', f'=IF(B{f_boleta}=1,ROUNDUP(F{f_neto}/(1-B{f_ret}/100),0),F{f_neto})'),
        (f_rm, 'Retención estimada', f'=IF(B{f_boleta}=1,ROUNDDOWN(F{f_pb}*B{f_ret}/100,0),0)'),
        (f_liq, 'Te quedan líquidos', f'=F{f_pb}-F{f_rm}'),
        (f_com, 'Comisión de KeyServ (la paga el cliente encima)',
         f'=IF(F{f_pb}<=0,0,MAX({int(settings.COMISION_MINIMA)},ROUND(F{f_pb}*({_formula_porcentaje_comision("F" + str(f_pb))})/100,0)))'),
        (f_tot, 'Total que paga el cliente', f'=F{f_pb}+F{f_com}'),
    ]
    for f, texto, texto_formula in filas:
        hoja.cell(f, 1, texto)
        formula(f, 6, texto_formula)
    for f in (f_neto, f_pb, f_liq, f_tot):
        hoja.cell(f, 1).font = NEGRITA
        hoja.cell(f, 6).font = NEGRITA

    hoja.cell(f_tot + 2, 1, AVISO).alignment = Alignment(wrap_text=True, vertical='top')
    hoja.merge_cells(start_row=f_tot + 2, start_column=1, end_row=f_tot + 2, end_column=6)
    hoja.row_dimensions[f_tot + 2].height = 48
    hoja.freeze_panes = 'A4'
    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _l1(texto):
    """Las fuentes base de PDF solo traen Latin-1: lo que no entra se reemplaza en vez de romper."""
    return str(texto).encode('latin-1', 'replace').decode('latin-1')


def _pesos(n):
    return '$' + f'{int(n):,}'.replace(',', '.')


def generar_pdf(datos):
    """PDF de una página con el desglose de `calculadora.calcular`."""
    r = calculadora.calcular(datos)
    pdf = FPDF(format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, _l1('Valorización de un trabajo'), new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 5, _l1('Calculado con la calculadora gratuita de KeyServ'), new_x='LMARGIN', new_y='NEXT')
    pdf.ln(4)

    def fila(texto, monto, negrita=False, sangria=0):
        pdf.set_font('Helvetica', 'B' if negrita else '', 10)
        pdf.set_x(pdf.l_margin + sangria)
        ancho = 190 - sangria - 40
        pdf.cell(ancho, 6, _l1(texto))
        pdf.cell(40, 6, _l1(_pesos(monto)), align='R', new_x='LMARGIN', new_y='NEXT')

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 7, 'Materiales', new_x='LMARGIN', new_y='NEXT')
    if r['materiales']:
        for m in r['materiales']:
            cantidad = f"{m['cantidad']:g}"
            unidad = f" {m['unidad']}" if m['unidad'] else ''
            marca = ' (reutilizado)' if m['reutilizado'] else ''
            fila(f"{m['descripcion']} - {cantidad}{unidad} x {_pesos(m['precio_unitario'])}{marca}", m['subtotal'], sangria=4)
    else:
        pdf.set_font('Helvetica', 'I', 10)
        pdf.cell(0, 6, '(sin materiales)', new_x='LMARGIN', new_y='NEXT')
    fila('Total materiales', r['materiales_total'], negrita=True)
    pdf.ln(2)

    fila('Traslado, peajes y estacionamiento', r['traslado_total'])
    fila('Mano de obra', r['mano_obra_total'])
    fila('Herramientas', r['herramientas_total'])
    fila('Costo directo', r['costo_directo'], negrita=True)
    pdf.ln(2)
    fila(f"Imprevistos ({r['imprevistos_pct']:g} %)", r['imprevistos_monto'])
    fila(f"Ganancia ({r['ganancia_pct']:g} %)", r['ganancia_monto'])
    fila('Precio neto (lo que quieres que te quede)', r['precio_neto'], negrita=True)
    pdf.ln(2)

    if r['documento'] == 'BOLETA_HONORARIOS':
        fila(f"Precio a cobrar con boleta de honorarios (retención estimada {r['retencion_pct']:g} %)", r['precio_boleta'], negrita=True)
        fila('Retención estimada', r['retencion_monto'])
    else:
        fila('Precio a cobrar (sin documento)', r['precio_boleta'], negrita=True)
    fila('Te quedan líquidos', r['liquido'], negrita=True)
    pdf.ln(2)
    fila(f"Comisión de KeyServ ({r['comision_porcentaje']:g} %, la paga el cliente encima)", r['comision_monto'])
    fila('Total que paga el cliente', r['total_cliente'], negrita=True)

    pdf.ln(6)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.multi_cell(0, 4, _l1(AVISO))
    return bytes(pdf.output())
