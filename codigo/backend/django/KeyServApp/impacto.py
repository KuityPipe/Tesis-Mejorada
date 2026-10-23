"""
Indicadores de impacto (inclusión laboral y formalización) para la postulación a Corfo y el seguimiento interno.

Solo entrega **agregados**: nunca ids, nombres ni filas individuales. Cualquier grupo de personas con menos de
`MINIMO_GRUPO` integrantes se suprime (se informa `None`), y si en una distribución queda un único grupo suprimido se
suprime también el menor de los restantes, para que no se pueda despejar restando del total (supresión complementaria).
Las cuentas de demostración (`@demo.keyserv`) se excluyen salvo que se pida lo contrario: no son personas reales.
Decisiones y justificación: docs/adr/0008-medicion-de-impacto.md.
"""
from collections import Counter, defaultdict
from statistics import median

from . import identidad
from django.db.models import Sum

from .models import BoletaHonorarios, EventoVerificacion, Pago, Publicaciones, UsoCalculadora, Usuario, Valoracion, VerificacionAlternativa

MINIMO_GRUPO = 5
SUFIJO_DEMO = '@demo.keyserv'


def _suprimir(n):
    """Un conteo de personas: `None` si es un grupo pequeño (1 a 4), el número en otro caso (0 no identifica a nadie)."""
    return None if 0 < n < MINIMO_GRUPO else n


def _distribucion(contador, claves):
    """
    {clave: personas} con supresión de grupos pequeños más la complementaria. `claves` fija el orden y las categorías
    que siempre aparecen, aunque tengan 0.
    """
    conteos = {k: contador.get(k, 0) for k in claves}
    resultado = {k: _suprimir(v) for k, v in conteos.items()}
    suprimidos = [k for k, v in resultado.items() if v is None]
    if len(suprimidos) == 1:
        restantes = [k for k, v in resultado.items() if v]  # visibles y no cero
        if restantes:
            resultado[min(restantes, key=lambda k: conteos[k])] = None
    return resultado


def _porcentaje(parte, total):
    return round(100 * parte / total, 1) if total else None


def _excluir_demo(queryset, campo_email):
    return queryset.exclude(**{f'{campo_email}__endswith': SUFIJO_DEMO})


def _via_de_verificacion(usuario):
    """Cómo quedó verificada una cuenta con identidad vigente: 'alternativa', 'rostro', 'nativa' o 'biometria' (sin evento)."""
    alternativa = VerificacionAlternativa.objects.filter(
        usuario=usuario, estado=VerificacionAlternativa.APROBADA, correo_verificado_en__isnull=False,
    )
    if any(identidad._reciente(v.revisado_en) for v in alternativa) and not (
            usuario.verificado_biometricamente and identidad._reciente(usuario.verificado_en)):
        return 'alternativa'
    evento = EventoVerificacion.objects.filter(
        usuario=usuario, resultado=EventoVerificacion.EXITOSO, metodo__in=[EventoVerificacion.NATIVA, EventoVerificacion.ROSTRO],
    ).order_by('-fecha').first()
    if evento is None:
        return 'biometria'
    return 'rostro' if evento.metodo == EventoVerificacion.ROSTRO else 'nativa'


def _uso_calculadora():
    """
    Contador anónimo de la calculadora (sin datos personales, ver `UsoCalculadora`): visitantes distintos por mes y totales
    de valorizaciones terminadas. Un mes con menos de 5 visitantes se suprime; los totales solo se informan si hubo al
    menos 5 visitantes en total.
    """
    filas = UsoCalculadora.objects.all()
    por_mes = Counter(filas.values_list('periodo', flat=True))
    visitantes = {periodo: _suprimir(n) for periodo, n in sorted(por_mes.items())[-12:]}
    totales = filas.aggregate(v=Sum('valorizaciones'), b=Sum('con_boleta'), r=Sum('con_reutilizado'))
    suficiente = sum(por_mes.values()) >= MINIMO_GRUPO
    return {
        'visitantes_por_mes': visitantes,
        'valorizaciones': (totales['v'] or 0) if suficiente else None,
        'valorizaciones_con_boleta': (totales['b'] or 0) if suficiente else None,
        'valorizaciones_con_material_reutilizado': (totales['r'] or 0) if suficiente else None,
    }


def calcular(incluir_demo=False):
    """Devuelve el diccionario de indicadores (ver las claves en `docs/adr/0008-medicion-de-impacto.md`)."""
    proveedores = Usuario.objects.filter(es_proveedor=True)
    if not incluir_demo:
        proveedores = _excluir_demo(proveedores, 'email')
    ids_proveedores = set(proveedores.values_list('pk', flat=True))

    # --- Verificación de identidad -------------------------------------------------------------------------------
    vias = Counter()
    for proveedor in proveedores:
        if identidad.identidad_verificada(proveedor):
            vias[_via_de_verificacion(proveedor)] += 1
    verificados = sum(vias.values())

    # --- Pagos: solo cobros efectivamente pagados de proveedores incluidos ----------------------------------------
    pagos = list(
        Pago.objects.filter(estado=Pago.PAGADO, contratacion__proveedor_id__in=ids_proveedores)
        .select_related('contratacion__publicacion', 'contratacion__cliente__comuna', 'contratacion__proveedor__comuna')
    )
    proveedores_con_pago = {p.contratacion.proveedor_id for p in pagos}

    # Ingreso mensual por proveedor (monto del servicio, sin la comisión), mediana entre pares proveedor-mes.
    por_proveedor_mes = defaultdict(int)
    for p in pagos:
        fecha = p.fecha_confirmacion or p.fecha_creacion
        por_proveedor_mes[(p.contratacion.proveedor_id, fecha.year, fecha.month)] += p.monto_servicio if p.monto_servicio is not None else p.monto
    ingreso_mediano = round(median(por_proveedor_mes.values())) if len(proveedores_con_pago) >= MINIMO_GRUPO else None

    # --- Formalización: boletas de honorarios que los proveedores declararon (fase 1, sin SII) ----------------------
    boletas = list(BoletaHonorarios.objects.filter(proveedor_id__in=ids_proveedores).values_list('proveedor_id', 'es_primera_boleta'))
    proveedores_con_boleta = {p for p, _ in boletas}
    primeras = sum(1 for _, primera in boletas if primera)

    # --- Tipo de servicio y circularidad ---------------------------------------------------------------------------
    por_tipo = Counter(p.contratacion.publicacion.tipo_servicio for p in pagos)
    reparar_mantener = por_tipo[Publicaciones.REPARACION] + por_tipo[Publicaciones.MANTENCION]

    valoraciones = Valoracion.objects.filter(
        contratacion__proveedor_id__in=ids_proveedores,
        publicacion__tipo_servicio__in=[Publicaciones.REPARACION, Publicaciones.MANTENCION],
    ).exclude(evito_reemplazo='')
    respuestas = Counter(valoraciones.values_list('evito_reemplazo', flat=True))
    respondieron = sum(respuestas.values())

    # --- Economía local: parte del ingreso cuyo cliente vive en la misma comuna del proveedor --------------------
    total_ingreso = misma_comuna = 0
    for p in pagos:
        monto = p.monto_servicio if p.monto_servicio is not None else p.monto
        total_ingreso += monto
        c, v = p.contratacion.cliente, p.contratacion.proveedor
        if c.comuna_id and c.comuna_id == v.comuna_id:
            misma_comuna += monto

    # --- Perfil de los proveedores (preguntas voluntarias) --------------------------------------------------------
    n_prov = len(ids_proveedores)
    situaciones = Counter(proveedores.values_list('situacion_laboral_previa', flat=True))
    generos = Counter(proveedores.values_list('genero', flat=True))
    claves_situacion = [c for c, _ in Usuario.SITUACIONES_LABORALES] + ['']
    claves_genero = [c for c, _ in Usuario.GENEROS] + ['']
    mujeres = generos.get(Usuario.MUJER, 0)
    declararon_genero = sum(v for k, v in generos.items() if k)

    return {
        'proveedores': _suprimir(n_prov),
        'proveedores_verificados': _suprimir(verificados),
        'proveedores_verificados_por_via': _distribucion(vias, ['nativa', 'rostro', 'alternativa', 'biometria']),
        'proveedores_con_primer_pago': _suprimir(len(proveedores_con_pago)),
        'servicios_pagados': len(pagos) if not pagos or len(proveedores_con_pago) >= MINIMO_GRUPO else None,
        'ingreso_mensual_mediano_por_proveedor': ingreso_mediano,
        'proveedores_con_boleta': _suprimir(len(proveedores_con_boleta)),
        'servicios_con_boleta': len(boletas) if not boletas or len(proveedores_con_boleta) >= MINIMO_GRUPO else None,
        'primeras_boletas': primeras if not boletas or len(proveedores_con_boleta) >= MINIMO_GRUPO else None,
        'pct_servicios_con_boleta': _porcentaje(len(boletas), len(pagos)) if len(proveedores_con_boleta) >= MINIMO_GRUPO and len(pagos) else None,
        'pct_reparacion_mantencion': _porcentaje(reparar_mantener, len(pagos)) if len(pagos) >= MINIMO_GRUPO else None,
        'reparaciones_que_evitaron_reemplazo': respuestas.get(Valoracion.SI, 0) if respondieron >= MINIMO_GRUPO else None,
        'reparaciones_con_respuesta': respondieron if respondieron >= MINIMO_GRUPO else None,
        'pct_ingreso_misma_comuna': _porcentaje(misma_comuna, total_ingreso) if len(proveedores_con_pago) >= MINIMO_GRUPO else None,
        'situacion_laboral_previa': _distribucion(situaciones, claves_situacion),
        'pct_mujeres': _porcentaje(mujeres, declararon_genero) if mujeres >= MINIMO_GRUPO and declararon_genero - mujeres >= MINIMO_GRUPO else None,
        'calculadora': _uso_calculadora(),
        'incluye_demo': incluir_demo,
        'minimo_grupo': MINIMO_GRUPO,
    }
