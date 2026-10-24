"""
Calculadora de valorización de trabajos (bloque 2, docs/adr/0009). Pública y gratuita: ayuda a una persona que ofrece un
oficio a ponerle precio a un trabajo sin olvidar traslado, herramientas, imprevistos, ganancia ni la retención de la
boleta de honorarios. Todo es aritmética pura, sin base de datos: la ruta pública no necesita cuenta.

Fórmula (la misma que reproduce la planilla exportada, `calculadora_exportar.py`):

    C        = Σ materiales + traslado + horas × valor hora × personas + herramientas
    P_neto   = C × (1 + imprevistos) × (1 + ganancia)
    P_boleta = P_neto / (1 − r)            con boleta de honorarios (r = retención, `settings.CALCULADORA_RETENCION_BOLETA`)
             = P_neto                      sin documento
    Total cliente = P_boleta + comisión de KeyServ (`comisiones.calcular`, la misma que se cobra de verdad)

Se trabaja en pesos enteros: cada componente se redondea al peso, imprevistos y ganancia se calculan sobre los enteros y
la boleta se redondea hacia arriba, de modo que la lista de ítems de la hoja de presupuesto suma exactamente `P_boleta`.
La retención de honorarios se muestra como estimación: la cifra vigente y su tratamiento exacto debe confirmarlos un contador.
"""
import math
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal, InvalidOperation

from django.conf import settings

from . import comisiones

DOCUMENTOS = ('SIN_DOCUMENTO', 'BOLETA_HONORARIOS', 'DOCUMENTO_IVA')
MAX_MATERIALES = 60
MAX_VALOR = Decimal('100000000')   # 100 millones: cualquier cifra mayor es un error de tipeo
IMPREVISTOS_DEFECTO = Decimal('10')
GANANCIA_DEFECTO = Decimal('15')


class DatosInvalidos(ValueError):
    """Error de validación con un mensaje apto para mostrar a la persona."""


def retencion_defecto():
    return Decimal(str(settings.CALCULADORA_RETENCION_BOLETA))


def iva_defecto():
    return Decimal(str(settings.CALCULADORA_IVA))


def configuracion_publica():
    """Valores por defecto y tramos de comisión para que la interfaz los muestre sin duplicarlos."""
    return {
        'retencion_porcentaje': float(retencion_defecto()),
        'iva_porcentaje': float(iva_defecto()),
        'imprevistos_porcentaje': float(IMPREVISTOS_DEFECTO),
        'ganancia_porcentaje': float(GANANCIA_DEFECTO),
        'comision_tramos': comisiones.tramos_para_publico(),
        'comision_minima': int(settings.COMISION_MINIMA),
        'documentos': list(DOCUMENTOS),
    }


def _numero(valor, nombre, maximo=MAX_VALOR, defecto=Decimal('0')):
    """Decimal no negativo; vacío o ausente = `defecto`."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return defecto
    if isinstance(valor, bool):
        raise DatosInvalidos(f'{nombre}: valor no válido.')
    try:
        numero = Decimal(str(valor).replace(',', '.'))
    except (InvalidOperation, ValueError):
        raise DatosInvalidos(f'{nombre}: escribe un número.')
    if not numero.is_finite() or numero < 0:
        raise DatosInvalidos(f'{nombre}: debe ser un número positivo.')
    if numero > maximo:
        raise DatosInvalidos(f'{nombre}: el valor es demasiado grande.')
    return numero


def _entero(numero, modo=ROUND_HALF_UP):
    return int(numero.quantize(Decimal('1'), rounding=modo))


def _porcentaje(valor, nombre, defecto, maximo=Decimal('100')):
    return _numero(valor, nombre, maximo=maximo, defecto=defecto)


def normalizar(datos):
    """Valida el cuerpo recibido y lo deja como Decimales/booleanos listos para calcular (lanza `DatosInvalidos`)."""
    if not isinstance(datos, dict):
        raise DatosInvalidos('Los datos de la valorización no son válidos.')

    materiales = []
    filas = datos.get('materiales') or []
    if not isinstance(filas, list):
        raise DatosInvalidos('Materiales: formato no válido.')
    if len(filas) > MAX_MATERIALES:
        raise DatosInvalidos(f'Materiales: máximo {MAX_MATERIALES} filas.')
    for i, fila in enumerate(filas, start=1):
        if not isinstance(fila, dict):
            raise DatosInvalidos(f'Material {i}: formato no válido.')
        cantidad = _numero(fila.get('cantidad'), f'Material {i}, cantidad', defecto=Decimal('1'))
        precio = _numero(fila.get('precio_unitario'), f'Material {i}, precio unitario')
        descripcion = str(fila.get('descripcion') or '').strip()[:120]
        if not descripcion and precio == 0:
            continue  # fila vacía
        materiales.append({
            'descripcion': descripcion or f'Material {i}',
            'cantidad': cantidad,
            'unidad': str(fila.get('unidad') or '').strip()[:20],
            'precio_unitario': precio,
            'reutilizado': bool(fila.get('reutilizado')),
        })

    traslado = datos.get('traslado') or {}
    mano = datos.get('mano_obra') or {}
    herr = datos.get('herramientas') or {}
    if not all(isinstance(x, dict) for x in (traslado, mano, herr)):
        raise DatosInvalidos('Los datos de la valorización no son válidos.')

    documento = datos.get('documento') or 'SIN_DOCUMENTO'
    if documento not in DOCUMENTOS:
        raise DatosInvalidos('Documento: elige sin documento, boleta de honorarios o documento con IVA.')

    retencion = datos.get('retencion_pct')
    normalizado = {
        'simple': False,
        'materiales': materiales,
        'traslado': {
            'modo': 'fijo' if traslado.get('modo') == 'fijo' else 'km',
            'km_ida_vuelta': _numero(traslado.get('km_ida_vuelta'), 'Traslado, kilómetros'),
            'costo_km': _numero(traslado.get('costo_km'), 'Traslado, costo por kilómetro'),
            'monto_fijo': _numero(traslado.get('monto_fijo'), 'Traslado, monto fijo'),
            'peajes_estacionamiento': _numero(traslado.get('peajes_estacionamiento'), 'Peajes y estacionamiento'),
        },
        'mano_obra': {
            'horas': _numero(mano.get('horas'), 'Mano de obra, horas', maximo=Decimal('10000')),
            'valor_hora': _numero(mano.get('valor_hora'), 'Mano de obra, valor por hora'),
            'personas': max(_numero(mano.get('personas'), 'Mano de obra, personas', maximo=Decimal('100'), defecto=Decimal('1')), Decimal('1')),
        },
        'herramientas': {
            'modo': 'porcentaje' if herr.get('modo') == 'porcentaje' else 'monto',
            'monto': _numero(herr.get('monto'), 'Herramientas, monto'),
            'porcentaje': _porcentaje(herr.get('porcentaje'), 'Herramientas, porcentaje', Decimal('0')),
        },
        'imprevistos_pct': _porcentaje(datos.get('imprevistos_pct'), 'Imprevistos', IMPREVISTOS_DEFECTO),
        'ganancia_pct': _porcentaje(datos.get('ganancia_pct'), 'Ganancia', GANANCIA_DEFECTO, maximo=Decimal('500')),
        'documento': documento,
        'retencion_pct': _porcentaje(retencion, 'Retención', retencion_defecto(), maximo=Decimal('50')),
    }
    if datos.get('modo') == 'simple':
        # Modo normal: la persona ya sabe cuánto quiere cobrar por el servicio; solo falta ver el efecto de la boleta y la comisión.
        precio = _numero(datos.get('precio_simple'), 'Precio del servicio')
        normalizado.update({
            'simple': True,
            'materiales': [],
            'traslado': {'modo': 'fijo', 'km_ida_vuelta': Decimal('0'), 'costo_km': Decimal('0'), 'monto_fijo': Decimal('0'), 'peajes_estacionamiento': Decimal('0')},
            'mano_obra': {'horas': Decimal('1'), 'valor_hora': precio, 'personas': Decimal('1')},
            'herramientas': {'modo': 'monto', 'monto': Decimal('0'), 'porcentaje': Decimal('0')},
            'imprevistos_pct': Decimal('0'),
            'ganancia_pct': Decimal('0'),
        })
    return normalizado


def calcular(datos):
    """
    Devuelve el desglose completo en pesos enteros. `datos` es el JSON de la interfaz (ver `normalizar`). Incluye
    `items`: la valorización como filas de la hoja de presupuesto (`ItemPresupuesto`), que suman exactamente `precio_boleta`.
    """
    d = normalizar(datos)

    lineas = []
    for m in d['materiales']:
        subtotal = _entero(m['cantidad'] * m['precio_unitario'])
        lineas.append({
            'descripcion': m['descripcion'], 'cantidad': float(m['cantidad']), 'unidad': m['unidad'],
            'precio_unitario': _entero(m['precio_unitario']), 'reutilizado': m['reutilizado'], 'subtotal': subtotal,
        })
    materiales_total = sum(linea['subtotal'] for linea in lineas)

    t = d['traslado']
    traslado_base = t['monto_fijo'] if t['modo'] == 'fijo' else t['km_ida_vuelta'] * t['costo_km']
    traslado_total = _entero(traslado_base + t['peajes_estacionamiento'])

    mo = d['mano_obra']
    mano_obra_total = _entero(mo['horas'] * mo['valor_hora'] * mo['personas'])

    h = d['herramientas']
    herramientas_total = _entero(h['monto'] if h['modo'] == 'monto' else Decimal(mano_obra_total) * h['porcentaje'] / 100)

    costo_directo = materiales_total + traslado_total + mano_obra_total + herramientas_total
    imprevistos_monto = _entero(Decimal(costo_directo) * d['imprevistos_pct'] / 100)
    ganancia_monto = _entero(Decimal(costo_directo + imprevistos_monto) * d['ganancia_pct'] / 100)
    precio_neto = costo_directo + imprevistos_monto + ganancia_monto

    con_boleta = d['documento'] == 'BOLETA_HONORARIOS'
    con_iva = d['documento'] == 'DOCUMENTO_IVA'
    retencion_pct = d['retencion_pct']
    iva_pct = iva_defecto()
    retencion_monto = iva_monto = 0
    if con_boleta:
        precio_boleta = math.ceil(Decimal(precio_neto) / (1 - retencion_pct / 100))
        retencion_monto = _entero(Decimal(precio_boleta) * retencion_pct / 100, ROUND_FLOOR)
    elif con_iva:
        # El IVA se suma encima del precio neto y no es de quien cobra: se traspasa al SII, así que no cuenta en lo que recibe.
        iva_monto = _entero(Decimal(precio_neto) * iva_pct / 100)
        precio_boleta = precio_neto + iva_monto
    else:
        precio_boleta = precio_neto
    liquido = precio_boleta - retencion_monto - iva_monto
    ajuste_boleta = precio_boleta - precio_neto if con_boleta else 0  # sube el precio para que, tras la retención, queden `precio_neto`

    desglose = comisiones.calcular(precio_boleta)

    items = []
    for linea in lineas:
        if linea['subtotal'] > 0:
            items.append({
                'descripcion': linea['descripcion'], 'categoria': 'MATERIAL', 'monto': linea['subtotal'],
                'cantidad': linea['cantidad'], 'unidad': linea['unidad'], 'precio_unitario': linea['precio_unitario'],
                'reutilizado': linea['reutilizado'],
            })
    for descripcion, categoria, monto in (
        ('Traslado, peajes y estacionamiento', 'VIAJE', traslado_total),
        ('Servicio', 'OTRO', mano_obra_total) if d['simple'] else ('Mano de obra', 'MANO_DE_OBRA', mano_obra_total),
        ('Herramientas', 'HERRAMIENTAS', herramientas_total),
        (f'Imprevistos ({_texto_pct(d["imprevistos_pct"])} %)', 'IMPREVISTOS', imprevistos_monto),
        (f'Ganancia ({_texto_pct(d["ganancia_pct"])} %)', 'OTRO', ganancia_monto),
        (f'Retención de la boleta de honorarios ({_texto_pct(retencion_pct)} %)', 'OTRO', ajuste_boleta),
        (f'IVA ({_texto_pct(iva_pct)} %)', 'OTRO', iva_monto),
    ):
        if monto > 0:
            items.append({'descripcion': descripcion, 'categoria': categoria, 'monto': monto})

    return {
        'materiales': lineas,
        'materiales_total': materiales_total,
        'traslado_total': traslado_total,
        'mano_obra_total': mano_obra_total,
        'herramientas_total': herramientas_total,
        'costo_directo': costo_directo,
        'imprevistos_pct': float(d['imprevistos_pct']),
        'imprevistos_monto': imprevistos_monto,
        'ganancia_pct': float(d['ganancia_pct']),
        'ganancia_monto': ganancia_monto,
        'precio_neto': precio_neto,
        'documento': d['documento'],
        'retencion_pct': float(retencion_pct) if con_boleta else 0.0,
        'retencion_monto': retencion_monto,
        'iva_pct': float(iva_pct) if con_iva else 0.0,
        'iva_monto': iva_monto,
        'precio_boleta': precio_boleta,
        'liquido': liquido,
        'comision_porcentaje': float(desglose.porcentaje),
        'comision_monto': desglose.comision,
        'total_cliente': desglose.total,
        'simple': d['simple'],
        'tiene_reutilizado': any(m['reutilizado'] for m in d['materiales']),
        'items': items,
    }


def _texto_pct(valor):
    texto = format(valor.normalize(), 'f')
    return texto.rstrip('0').rstrip('.') if '.' in texto else texto
