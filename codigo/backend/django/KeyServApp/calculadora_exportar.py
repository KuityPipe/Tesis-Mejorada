"""
Exportación de la calculadora de valorización (docs/adr/0009): una planilla .xlsx con las **fórmulas visibles y editables**
(las celdas amarillas son los datos; todo lo demás se recalcula) y un PDF de una página con el resumen.

Ni la planilla ni el PDF son documentos tributarios: son una ayuda para fijar un precio.
"""
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ImagenExcel
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from . import calculadora, comisiones

AMARILLO = PatternFill('solid', fgColor='FFF2CC')
GRIS = PatternFill('solid', fgColor='E7E6E6')
NEGRITA = Font(bold=True)
FORMATO_PESOS = '"$"#,##0'
FILAS_MATERIALES_MIN = 8

AVISO = (
    'Esta valorización es una ayuda para fijar un precio: no es un documento tributario ni una oferta. La retención de la '
    'boleta de honorarios es una estimación; confirma la cifra vigente y el tratamiento del IVA con un contador.'
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

    hoja['A1'] = 'Valorización de un trabajo'
    hoja['A1'].font = Font(bold=True, size=16, color='0B3D78')
    hoja['A1'].alignment = Alignment(vertical='center')
    hoja.row_dimensions[1].height = 54
    for col in range(1, 7):
        hoja.cell(1, col).border = Border(bottom=Side(style='thick', color='0C7F6D'))
    hoja['A2'] = 'Las celdas amarillas son datos que puedes cambiar; el resto son fórmulas que se recalculan.'
    if LOGO.exists():
        logo = ImagenExcel(str(LOGO))
        logo.width, logo.height = 90, int(90 * logo.height / logo.width)
        hoja.add_image(logo, 'F1')

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
    f_imp, f_gan, f_ret, f_iva_pct, f_boleta = fila + 1, fila + 2, fila + 3, fila + 4, fila + 5
    hoja.cell(f_imp, 1, 'Imprevistos (%)')
    dato(f_imp, 2, float(d['imprevistos_pct']), '0.##')
    hoja.cell(f_gan, 1, 'Ganancia (%)')
    dato(f_gan, 2, float(d['ganancia_pct']), '0.##')
    hoja.cell(f_ret, 1, 'Retención de la boleta de honorarios (%) - estimación')
    dato(f_ret, 2, float(d['retencion_pct']), '0.##')
    hoja.cell(f_iva_pct, 1, 'IVA (%), solo si emites un documento afecto')
    dato(f_iva_pct, 2, float(calculadora.iva_defecto()), '0.##')
    hoja.cell(f_boleta, 1, 'Documento: 0 = sin documento, 1 = boleta de honorarios (lleva retención), 2 = con IVA')
    dato(f_boleta, 2, {'BOLETA_HONORARIOS': 1, 'DOCUMENTO_IVA': 2}.get(d['documento'], 0), '0')

    # --- Resultado
    fila = f_boleta + 2
    titulo(fila, 'RESULTADO')
    f_c, f_i, f_g, f_neto, f_pb, f_rm, f_iva, f_liq, f_com, f_tot = (fila + k for k in range(1, 11))
    filas = [
        (f_c, 'Costo directo (materiales + traslado + mano de obra + herramientas)', f'=F{f_materiales}+F{f_traslado}+F{f_mo}+F{f_herr}'),
        (f_i, 'Imprevistos', f'=ROUND(F{f_c}*B{f_imp}/100,0)'),
        (f_g, 'Ganancia', f'=ROUND((F{f_c}+F{f_i})*B{f_gan}/100,0)'),
        (f_neto, 'Precio neto (lo que quieres que te quede)', f'=F{f_c}+F{f_i}+F{f_g}'),
        (f_pb, 'Precio a cobrar (con boleta incluye la retención; con IVA incluye el IVA)',
         f'=IF(B{f_boleta}=1,ROUNDUP(F{f_neto}/(1-B{f_ret}/100),0),IF(B{f_boleta}=2,F{f_neto}+ROUND(F{f_neto}*B{f_iva_pct}/100,0),F{f_neto}))'),
        (f_rm, 'Retención estimada (adelanto de tu impuesto a la renta: se recupera en tu declaración anual)', f'=IF(B{f_boleta}=1,ROUNDDOWN(F{f_pb}*B{f_ret}/100,0),0)'),
        (f_iva, 'IVA (no es tuyo: se traspasa al SII)', f'=IF(B{f_boleta}=2,F{f_pb}-F{f_neto},0)'),
        (f_liq, 'Te quedan líquidos', f'=F{f_pb}-F{f_rm}-F{f_iva}'),
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
    if d['documento'] == 'BOLETA_HONORARIOS':
        _hoja_boleta(libro, f_pb, f_rm, f_liq)
    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _hoja_boleta(libro, f_pb, f_rm, f_liq):
    """Segunda hoja con la forma de una boleta de honorarios; sus montos salen de las fórmulas de la primera hoja."""
    hoja = libro.create_sheet('Boleta (referencia)')
    hoja.sheet_view.showGridLines = False
    hoja.column_dimensions['A'].width = 6
    hoja.column_dimensions['B'].width = 46
    hoja.column_dimensions['C'].width = 22
    azul = PatternFill('solid', fgColor='0B3D78')
    verde = PatternFill('solid', fgColor='E6F4F1')
    borde = Border(bottom=Side(style='thin', color='999999'))
    marco = Side(style='medium', color='0B3D78')
    hoja['B2'] = 'BOLETA DE HONORARIOS - REFERENCIA'
    hoja['B2'].font = Font(bold=True, size=13, color='FFFFFF')
    for col in 'BC':
        hoja[f'{col}2'].fill = azul
    hoja.row_dimensions[2].height = 26
    hoja['B2'].alignment = Alignment(vertical='center')
    if LOGO.exists():
        logo = ImagenExcel(str(LOGO))
        logo.width, logo.height = 80, int(80 * logo.height / logo.width)
        hoja.add_image(logo, 'E2')
    hoja['B4'] = 'Prestador:'
    hoja['B5'] = 'RUT:'
    hoja['B6'] = 'Por servicios de:'
    for fila in (4, 5, 6):
        hoja[f'C{fila}'].border = borde
        hoja[f'C{fila}'].fill = AMARILLO
    hoja['B8'] = 'Honorarios brutos (monto de la boleta)'
    hoja['C8'] = f"='Valorización'!F{f_pb}"
    hoja['B9'] = 'Retención de impuesto estimada'
    hoja['C9'] = f"=-'Valorización'!F{f_rm}"
    hoja['B10'] = 'Líquido que recibes'
    hoja['C10'] = f"='Valorización'!F{f_liq}"
    for fila in (8, 9, 10):
        hoja[f'C{fila}'].number_format = FORMATO_PESOS
    for fila in (8, 10):
        for col in 'BC':
            hoja[f'{col}{fila}'].font = NEGRITA
            hoja[f'{col}{fila}'].fill = verde
    hoja['B12'] = (
        'Esta hoja NO es una boleta oficial ni tiene valor tributario: emite tu boleta en sii.cl con estos montos. '
        'La retención es una estimación y un adelanto de tu impuesto a la renta; confírmala con un contador.'
    )
    hoja['B12'].alignment = Alignment(wrap_text=True, vertical='top')
    hoja['B12'].font = Font(italic=True, size=9, color='5A5A5A')
    hoja.merge_cells('B12:C12')
    hoja.row_dimensions[12].height = 48
    for fila in range(2, 13):
        hoja[f'B{fila}'].border = Border(left=marco, bottom=hoja[f'B{fila}'].border.bottom)
        hoja[f'C{fila}'].border = Border(right=marco, bottom=hoja[f'C{fila}'].border.bottom)


def _l1(texto):
    """Las fuentes base de PDF solo traen Latin-1: lo que no entra se reemplaza en vez de romper."""
    return str(texto).replace('–', '-').replace('—', '-').encode('latin-1', 'replace').decode('latin-1')


def _pesos(n):
    return ('-' if n < 0 else '') + '$' + f'{abs(int(n)):,}'.replace(',', '.')


AZUL = (11, 61, 120)
VERDE = (12, 127, 109)
VERDE_CLARO = (230, 244, 241)
GRIS_CLARO = (245, 245, 245)
GRIS_TEXTO = (90, 90, 90)
LOGO = Path(__file__).resolve().parent / 'static' / 'KeyServApp' / 'imagenes' / 'logo_documentos.png'


def generar_pdf(datos):
    """
    Documento de valorización listo para entregar: logo de KeyServ, detalle del trabajo en tabla, totales y, si se elige
    boleta de honorarios, una hoja de referencia con la forma de una boleta (prestador, honorarios, retención y líquido).
    No es una boleta ni un documento tributario: la boleta se emite en sii.cl (ver ADR 0009).
    """
    r = calculadora.calcular(datos)
    pdf = FPDF(format='A4')
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    ancho = 180

    def color(rgb):
        pdf.set_text_color(*rgb)

    def relleno(rgb):
        pdf.set_fill_color(*rgb)

    def hay_espacio(alto):
        if pdf.get_y() + alto > pdf.h - 18:
            pdf.add_page()

    # --- Encabezado: logo a la izquierda, tipo de documento y fecha a la derecha
    if LOGO.exists():
        pdf.image(str(LOGO), x=15, y=10, w=36)
    pdf.set_xy(100, 12)
    pdf.set_font('Helvetica', 'B', 15)
    color(AZUL)
    pdf.cell(95, 8, _l1('VALORIZACIÓN DE TRABAJO'), align='R', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(100)
    pdf.set_font('Helvetica', '', 9)
    color(GRIS_TEXTO)
    pdf.cell(95, 5, _l1(f'Fecha: {timezone.localdate():%d/%m/%Y}'), align='R', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(100)
    pdf.cell(95, 5, _l1('Calculada con la calculadora gratuita de KeyServ'), align='R', new_x='LMARGIN', new_y='NEXT')
    pdf.set_draw_color(*VERDE)
    pdf.set_line_width(0.8)
    pdf.line(15, 36, 195, 36)
    pdf.set_line_width(0.2)
    pdf.set_y(42)

    # --- Detalle del trabajo (tabla)
    pdf.set_font('Helvetica', 'B', 10)
    relleno(AZUL)
    color((255, 255, 255))
    columnas = [(92, 'Concepto', 'L'), (20, 'Cant.', 'R'), (34, 'P. unitario', 'R'), (34, 'Subtotal', 'R')]
    for w, texto, alin in columnas:
        pdf.cell(w, 7, _l1(' ' + texto if alin == 'L' else texto + ' '), fill=True, align=alin)
    pdf.ln(7)

    filas = []
    for m in r['materiales']:
        marca = ' (reutilizado)' if m['reutilizado'] else ''
        unidad = f" {m['unidad']}" if m['unidad'] else ''
        filas.append((f"{m['descripcion']}{marca}", f"{m['cantidad']:g}{unidad}", _pesos(m['precio_unitario']), _pesos(m['subtotal'])))
    if r['simple']:
        filas.append(('Servicio', '', '', _pesos(r['mano_obra_total'])))
    else:
        for texto, monto in (('Traslado, peajes y estacionamiento', r['traslado_total']), ('Mano de obra', r['mano_obra_total']), ('Herramientas', r['herramientas_total'])):
            if monto:
                filas.append((texto, '', '', _pesos(monto)))
    if not filas:
        filas.append(('(sin conceptos)', '', '', _pesos(0)))
    pdf.set_font('Helvetica', '', 10)
    color((30, 30, 30))
    for n, (concepto, cant, unitario, subtotal) in enumerate(filas):
        hay_espacio(7)
        relleno(GRIS_CLARO)
        for (w, _t, alin), texto in zip(columnas, (concepto, cant, unitario, subtotal)):
            pdf.cell(w, 6.5, _l1((' ' + texto) if alin == 'L' else (texto + ' ')), fill=n % 2 == 0, align=alin)
        pdf.ln(6.5)
    pdf.ln(3)

    # --- Totales (a la derecha)
    def total(texto, monto, negrita=False, fondo=None):
        pdf.set_x(105)
        pdf.set_font('Helvetica', 'B' if negrita else '', 10)
        if fondo:
            relleno(fondo)
        pdf.cell(55, 7, _l1(' ' + texto), fill=bool(fondo))
        pdf.cell(35, 7, _l1(_pesos(monto) + ' '), align='R', fill=bool(fondo), new_x='LMARGIN', new_y='NEXT')

    hay_espacio(40)
    color((30, 30, 30))
    total('Costo directo', r['costo_directo'])
    if r['imprevistos_pct'] > 0:
        total(f"Imprevistos ({r['imprevistos_pct']:g} %)", r['imprevistos_monto'])
    if r['ganancia_pct'] > 0:
        total(f"Ganancia ({r['ganancia_pct']:g} %)", r['ganancia_monto'])
    total('Precio neto', r['precio_neto'], negrita=True, fondo=GRIS_CLARO)
    pdf.ln(5)

    # --- Documento que se entrega
    if r['documento'] == 'BOLETA_HONORARIOS':
        _caja_boleta(pdf, r, hay_espacio, color, relleno)
    else:
        hay_espacio(30)
        etiqueta = 'TOTAL A COBRAR (con IVA)' if r['documento'] == 'DOCUMENTO_IVA' else 'TOTAL A COBRAR (sin documento tributario)'
        relleno(VERDE_CLARO)
        pdf.set_font('Helvetica', 'B', 11)
        color(AZUL)
        pdf.cell(ancho - 45, 11, _l1(' ' + etiqueta), fill=True)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(45, 11, _l1(_pesos(r['precio_boleta']) + ' '), fill=True, align='R', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 9)
        color(GRIS_TEXTO)
        if r['documento'] == 'DOCUMENTO_IVA':
            pdf.cell(0, 6, _l1(f"Incluye IVA de {_pesos(r['iva_monto'])} ({r['iva_pct']:g} %), que se traspasa al SII. Te quedan {_pesos(r['liquido'])}."), new_x='LMARGIN', new_y='NEXT')
        else:
            pdf.cell(0, 6, _l1(f"Te quedan {_pesos(r['liquido'])}. Sin documento no hay respaldo tributario del trabajo."), new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    # --- Reparto del cobro en KeyServ
    hay_espacio(36)
    pdf.set_font('Helvetica', 'B', 10)
    color(AZUL)
    pdf.cell(0, 7, _l1('Así se reparte el cobro en KeyServ'), new_x='LMARGIN', new_y='NEXT')
    pdf.set_draw_color(200, 200, 200)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    color((30, 30, 30))
    for texto, monto, negrita in (
        ('Precio que cobras', r['precio_boleta'], False),
        (f"Comisión de KeyServ ({r['comision_porcentaje']:g} %), la paga quien contrata", r['comision_monto'], False),
        ('Total que paga el cliente', r['total_cliente'], True),
    ):
        pdf.set_font('Helvetica', 'B' if negrita else '', 9.5)
        pdf.cell(ancho - 40, 6.5, _l1(texto))
        pdf.cell(40, 6.5, _l1(_pesos(monto)), align='R', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(6)
    pdf.set_font('Helvetica', 'I', 8)
    color(GRIS_TEXTO)
    pdf.multi_cell(0, 4, _l1(AVISO))
    return bytes(pdf.output())


def _caja_boleta(pdf, r, hay_espacio, color, relleno):
    """Hoja de referencia con la forma de una boleta de honorarios: se emite en sii.cl, esto solo ordena los montos."""
    hay_espacio(92)
    x, ancho = 15, 180
    y0 = pdf.get_y()
    relleno(AZUL)
    pdf.set_xy(x, y0)
    pdf.set_font('Helvetica', 'B', 11)
    color((255, 255, 255))
    pdf.cell(ancho - 70, 9, _l1('  BOLETA DE HONORARIOS - REFERENCIA'), fill=True)
    pdf.set_font('Helvetica', '', 8.5)
    pdf.cell(70, 9, _l1('Los montos para tu boleta en sii.cl  '), fill=True, align='R', new_x='LMARGIN', new_y='NEXT')
    # Datos del prestador, para completar a mano
    color((30, 30, 30))
    pdf.set_font('Helvetica', '', 9.5)
    pdf.ln(2)
    pdf.set_x(x + 3)
    pdf.cell(32, 8, 'Prestador:')
    pdf.cell(80, 8, '', border='B')
    pdf.cell(12, 8, '')
    pdf.cell(12, 8, 'RUT:')
    pdf.cell(38, 8, '', border='B', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(x + 3)
    pdf.cell(32, 8, 'Por servicios de:')
    pdf.cell(142, 8, '', border='B', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    def linea(texto, monto, negrita=False, fondo=None):
        pdf.set_x(x + 3)
        pdf.set_font('Helvetica', 'B' if negrita else '', 10.5 if negrita else 10)
        if fondo:
            relleno(fondo)
        pdf.cell(ancho - 6 - 45, 8, _l1(' ' + texto), fill=bool(fondo))
        pdf.cell(45, 8, _l1(_pesos(monto) + ' '), align='R', fill=bool(fondo), new_x='LMARGIN', new_y='NEXT')

    linea('Honorarios brutos (monto de la boleta)', r['precio_boleta'], negrita=True, fondo=VERDE_CLARO)
    linea(f"Retención de impuesto estimada ({r['retencion_pct']:g} %)", -r['retencion_monto'])
    linea('Líquido que recibes', r['liquido'], negrita=True, fondo=VERDE_CLARO)
    pdf.ln(1)
    pdf.set_x(x + 3)
    pdf.set_font('Helvetica', 'I', 8)
    color(GRIS_TEXTO)
    pdf.multi_cell(ancho - 6, 4, _l1(
        'La retención es un adelanto de tu impuesto a la renta, no un costo: se recupera en tu declaración anual. Esta hoja '
        'NO es una boleta oficial ni tiene valor tributario: emite tu boleta en sii.cl con estos montos y confirma la '
        'retención vigente con un contador.'
    ))
    pdf.set_draw_color(*AZUL)
    pdf.set_line_width(0.5)
    pdf.rect(x, y0, ancho, pdf.get_y() + 2 - y0)
    pdf.set_line_width(0.2)
    pdf.set_y(pdf.get_y() + 5)
