import json

from django.core.management.base import BaseCommand

from KeyServApp import impacto

ETIQUETAS = {
    'proveedores': 'Proveedores registrados',
    'proveedores_verificados': 'Proveedores con identidad verificada (vigente)',
    'proveedores_con_primer_pago': 'Proveedores que ya recibieron un pago',
    'servicios_pagados': 'Servicios pagados',
    'ingreso_mensual_mediano_por_proveedor': 'Ingreso mensual mediano por proveedor activo (CLP, sin comisión)',
    'proveedores_con_boleta': 'Proveedores que registraron al menos una boleta de honorarios',
    'servicios_con_boleta': 'Servicios con folio de boleta registrado (declarado por el proveedor, sin verificar con el SII)',
    'primeras_boletas': 'Boletas marcadas como la primera del proveedor',
    'pct_servicios_con_boleta': '% de servicios pagados con boleta registrada',
    'pct_reparacion_mantencion': '% de servicios pagados que son reparación o mantención',
    'reparaciones_que_evitaron_reemplazo': 'Reparaciones que evitaron comprar uno nuevo (respuestas "sí")',
    'reparaciones_con_respuesta': 'Reparaciones/mantenciones con esa pregunta respondida',
    'pct_ingreso_misma_comuna': '% del ingreso con cliente en la misma comuna del proveedor (economía local)',
    'pct_mujeres': '% de mujeres entre los proveedores que respondieron género',
}


def _valor(v):
    return f'<{impacto.MINIMO_GRUPO} (suprimido)' if v is None else str(v)


class Command(BaseCommand):
    help = (
        'Indicadores agregados de impacto (inclusión laboral, formalización, reparación). Solo entrega agregados y '
        'suprime grupos de menos de 5 personas. Excluye las cuentas de demostración salvo --incluir-demo.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--json', action='store_true', help='Salida en JSON')
        parser.add_argument('--incluir-demo', action='store_true', help='Incluye las cuentas @demo.keyserv (no son personas reales)')

    def handle(self, *args, **opciones):
        datos = impacto.calcular(incluir_demo=opciones['incluir_demo'])
        if opciones['json']:
            self.stdout.write(json.dumps(datos, ensure_ascii=False, indent=2))
            return
        self.stdout.write(self.style.MIGRATE_HEADING('Reporte de impacto de KeyServ'))
        if datos['incluye_demo']:
            self.stdout.write(self.style.WARNING('Incluye cuentas de demostración: no usar estas cifras en la postulación.'))
        for clave, etiqueta in ETIQUETAS.items():
            self.stdout.write(f'{etiqueta}: {_valor(datos[clave])}')
        self.stdout.write('Verificados por vía:')
        for via, n in datos['proveedores_verificados_por_via'].items():
            self.stdout.write(f'  {via}: {_valor(n)}')
        self.stdout.write('Situación laboral previa (voluntaria):')
        for clave, n in datos['situacion_laboral_previa'].items():
            self.stdout.write(f'  {clave or "sin responder"}: {_valor(n)}')
        calc = datos['calculadora']
        self.stdout.write('Calculadora de valorización (contador anónimo):')
        self.stdout.write(f"  valorizaciones terminadas: {_valor(calc['valorizaciones'])}")
        self.stdout.write(f"  con boleta de honorarios: {_valor(calc['valorizaciones_con_boleta'])}")
        self.stdout.write(f"  con material reutilizado: {_valor(calc['valorizaciones_con_material_reutilizado'])}")
        for periodo, n in calc['visitantes_por_mes'].items():
            self.stdout.write(f'  visitantes {periodo}: {_valor(n)}')
        self.stdout.write(f'Grupos con menos de {impacto.MINIMO_GRUPO} personas se suprimen; son datos agregados y voluntarios.')
