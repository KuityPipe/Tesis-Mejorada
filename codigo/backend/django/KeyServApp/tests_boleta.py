"""
Registro del folio de la boleta de honorarios (bloque 3, docs/adr/0010): fase 1, sin SII.
"""
from datetime import timedelta
from io import StringIO

from django.core.cache import cache
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from . import derechos_titular, impacto
from .api import jwt_utils
from .models import BoletaHonorarios, Contratacion, Pago, Publicaciones
from .tests import _crear_region_comuna_tipo, _crear_usuario


class BoletaApiTests(APITestCase):
    def setUp(self):
        _, self.comuna, self.tipo = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('prov_boleta@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo)
        self.cliente = _crear_usuario('cli_boleta@test.com', comuna=self.comuna, tipo_cuenta=self.tipo)
        self.ajeno = _crear_usuario('ajeno_boleta@test.com', comuna=self.comuna, tipo_cuenta=self.tipo)
        self.contratacion = self._contratacion(estado=Contratacion.EN_CURSO, pago=Pago.PAGADO)
        self.url = f'/api/contrataciones/{self.contratacion.id_contratacion}/boleta/'

    def tearDown(self):
        cache.clear()

    def _contratacion(self, estado, pago=None, titulo='Servicio'):
        pub = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo=titulo, estado_moderacion=Publicaciones.APROBADA, precio=20000)
        c = Contratacion.objects.create(publicacion=pub, cliente=self.cliente, proveedor=self.proveedor, estado=estado, monto_acordado=20000)
        if pago:
            Pago.objects.create(contratacion=c, monto=21000, monto_servicio=20000, comision_monto=1000, metodo=Pago.WEBPAY, estado=pago)
        return c

    def _como(self, usuario):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {jwt_utils.generar_access_token(usuario)}')

    def _registrar(self, **extra):
        cuerpo = {'folio': '1234', 'es_primera_boleta': 'SI', **extra}
        return self.client.put(self.url, cuerpo, format='json')

    def test_el_proveedor_registra_el_folio_de_un_trabajo_pagado(self):
        self._como(self.proveedor)
        hoy = timezone.localdate().isoformat()
        resp = self._registrar(fecha_emision=hoy)
        self.assertEqual(resp.status_code, 201, resp.data)
        boleta = BoletaHonorarios.objects.get()
        self.assertEqual((boleta.folio, boleta.es_primera_boleta, boleta.proveedor), ('1234', True, self.proveedor))
        self.assertEqual(boleta.fecha_emision.isoformat(), hoy)

    def test_se_puede_corregir_el_folio(self):
        self._como(self.proveedor)
        self._registrar()
        resp = self._registrar(folio='9999', es_primera_boleta='NO')
        self.assertEqual(resp.status_code, 200)
        boleta = BoletaHonorarios.objects.get()
        self.assertEqual((boleta.folio, boleta.es_primera_boleta), ('9999', False))

    def test_sin_pago_aprobado_no_se_puede_registrar(self):
        for estado_pago in (None, Pago.PENDIENTE, Pago.RECHAZADO):
            contratacion = self._contratacion(Contratacion.CONFIRMADA, pago=estado_pago, titulo=f'Sin pago {estado_pago}')
            self._como(self.proveedor)
            resp = self.client.put(f'/api/contrataciones/{contratacion.id_contratacion}/boleta/', {'folio': '1', 'es_primera_boleta': 'NO'}, format='json')
            self.assertEqual(resp.status_code, 409, estado_pago)
            self.assertEqual(resp.data['code'], 'trabajo_no_pagado')
        self.assertFalse(BoletaHonorarios.objects.exists())

    def test_el_cliente_no_puede_registrar_pero_si_ver_el_folio(self):
        self._como(self.proveedor)
        self._registrar()
        self._como(self.cliente)
        self.assertEqual(self._registrar(folio='5').status_code, 403)
        self.assertEqual(self.client.delete(self.url).status_code, 403)
        resp = self.client.get(self.url)
        self.assertEqual(resp.data['boleta']['folio'], '1234')
        self.assertNotIn('es_primera_boleta', resp.data['boleta'])  # la respuesta sobre "primera boleta" es solo del proveedor
        self.assertFalse(resp.data['puede_registrar'])
        self.assertEqual(BoletaHonorarios.objects.get().folio, '1234')

    def test_alguien_ajeno_recibe_404(self):
        self._como(self.ajeno)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self._registrar().status_code, 404)
        self.assertEqual(self.client.delete(self.url).status_code, 404)

    def test_requiere_sesion(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_validaciones(self):
        self._como(self.proveedor)
        manana = (timezone.localdate() + timedelta(days=1)).isoformat()
        casos = [
            ({'folio': ''}, 'folio'), ({'folio': '12a4'}, 'folio'), ({'folio': '1' * 13}, 'folio'),
            ({'fecha_emision': manana}, 'fecha_emision'), ({'fecha_emision': '15-10-2026'}, 'fecha_emision'),
            ({'fecha_emision': '2001-01-01'}, 'fecha_emision'),
            ({'es_primera_boleta': ''}, 'es_primera_boleta'), ({'es_primera_boleta': 'quizás'}, 'es_primera_boleta'),
        ]
        for extra, campo in casos:
            resp = self._registrar(**extra)
            self.assertEqual(resp.status_code, 400, extra)
            self.assertIn(campo, resp.data)
        self.assertFalse(BoletaHonorarios.objects.exists())

    def test_el_mismo_folio_no_se_repite_para_un_proveedor(self):
        self._como(self.proveedor)
        self._registrar(folio='700', es_primera_boleta='NO')
        otra = self._contratacion(Contratacion.EN_CURSO, pago=Pago.PAGADO, titulo='Otro trabajo')
        resp = self.client.put(f'/api/contrataciones/{otra.id_contratacion}/boleta/', {'folio': '700', 'es_primera_boleta': 'NO'}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('folio', resp.data)

    def test_solo_una_boleta_puede_ser_la_primera(self):
        self._como(self.proveedor)
        self._registrar(folio='1', es_primera_boleta='SI')
        otra = self._contratacion(Contratacion.EN_CURSO, pago=Pago.PAGADO, titulo='Otro trabajo')
        resp = self.client.put(f'/api/contrataciones/{otra.id_contratacion}/boleta/', {'folio': '2', 'es_primera_boleta': 'SI'}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('es_primera_boleta', resp.data)
        resp = self.client.put(f'/api/contrataciones/{otra.id_contratacion}/boleta/', {'folio': '2', 'es_primera_boleta': 'NO'}, format='json')
        self.assertEqual(resp.status_code, 201)
        detalle = self.client.get(f'/api/contrataciones/{otra.id_contratacion}/boleta/').data
        self.assertTrue(detalle['ya_tiene_primera_boleta'])

    def test_quitar_la_boleta(self):
        self._como(self.proveedor)
        self._registrar()
        self.assertEqual(self.client.delete(self.url).status_code, 204)
        self.assertFalse(BoletaHonorarios.objects.exists())
        self.assertEqual(self.client.delete(self.url).status_code, 204)  # idempotente

    def test_el_detalle_de_la_contratacion_trae_folio_y_fecha_para_las_dos_partes(self):
        self._como(self.proveedor)
        self._registrar()
        for usuario in (self.proveedor, self.cliente):
            self._como(usuario)
            boleta = self.client.get(f'/api/contrataciones/{self.contratacion.id_contratacion}/').data['boleta']
            self.assertEqual(boleta['folio'], '1234')
            self.assertNotIn('es_primera_boleta', boleta)

    def test_sin_boleta_el_detalle_dice_null(self):
        self._como(self.cliente)
        self.assertIsNone(self.client.get(f'/api/contrataciones/{self.contratacion.id_contratacion}/').data['boleta'])

    def test_aparece_en_mis_datos_y_se_conserva_al_anonimizar(self):
        self._como(self.proveedor)
        self._registrar()
        self.assertEqual(derechos_titular.exportar_datos(self.proveedor)['boletas_de_honorarios_registradas'][0]['folio'], '1234')
        derechos_titular.eliminar_cuenta(self.proveedor)
        self.assertTrue(BoletaHonorarios.objects.exists())  # dato tributario del trabajo; la cuenta queda anonimizada


class ReporteBoletasTests(APITestCase):
    def setUp(self):
        _, self.comuna, self.tipo = _crear_region_comuna_tipo()

    def _proveedores_con_pago(self, n, con_boleta, primeras=0, demo=False):
        dominio = 'demo.keyserv' if demo else 'real.test'
        for i in range(n):
            prov = _crear_usuario(f'bp{i}@{dominio}', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo)
            cli = _crear_usuario(f'bc{i}@{dominio}', comuna=self.comuna, tipo_cuenta=self.tipo)
            pub = Publicaciones.objects.create(usuario_publicador=prov, titulo=f'S{i}', estado_moderacion=Publicaciones.APROBADA)
            c = Contratacion.objects.create(publicacion=pub, cliente=cli, proveedor=prov, estado=Contratacion.COMPLETADA)
            Pago.objects.create(contratacion=c, monto=11000, monto_servicio=10000, comision_monto=1000, metodo=Pago.WEBPAY, estado=Pago.PAGADO, fecha_confirmacion=timezone.now())
            if i < con_boleta:
                BoletaHonorarios.objects.create(contratacion=c, proveedor=prov, folio=str(100 + i), es_primera_boleta=i < primeras)

    def test_con_pocos_proveedores_se_suprime(self):
        self._proveedores_con_pago(4, con_boleta=3, primeras=2)
        d = impacto.calcular()
        self.assertIsNone(d['proveedores_con_boleta'])
        self.assertIsNone(d['servicios_con_boleta'])
        self.assertIsNone(d['primeras_boletas'])
        self.assertIsNone(d['pct_servicios_con_boleta'])

    def test_con_cinco_o_mas_se_publica(self):
        self._proveedores_con_pago(8, con_boleta=6, primeras=5)
        d = impacto.calcular()
        self.assertEqual(d['proveedores_con_boleta'], 6)
        self.assertEqual(d['servicios_con_boleta'], 6)
        self.assertEqual(d['primeras_boletas'], 5)
        self.assertEqual(d['pct_servicios_con_boleta'], 75.0)

    def test_sin_boletas_informa_cero(self):
        self._proveedores_con_pago(6, con_boleta=0)
        d = impacto.calcular()
        self.assertEqual((d['proveedores_con_boleta'], d['servicios_con_boleta'], d['primeras_boletas']), (0, 0, 0))

    def test_las_cuentas_demo_no_cuentan(self):
        self._proveedores_con_pago(6, con_boleta=6, demo=True)
        self.assertEqual(impacto.calcular()['servicios_con_boleta'], 0)

    def test_el_comando_las_muestra(self):
        self._proveedores_con_pago(6, con_boleta=5, primeras=1)
        salida = StringIO()
        call_command('reporte_impacto', stdout=salida)
        self.assertIn('Servicios con folio de boleta registrado', salida.getvalue())
        self.assertIn('sin verificar con el SII', salida.getvalue())
