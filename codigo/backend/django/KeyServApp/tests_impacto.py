"""
Medición de impacto (docs/adr/0008): preguntas voluntarias, tipo de servicio, pregunta de reparación y el reporte
agregado con supresión de grupos pequeños.
"""
import json
from io import StringIO

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from . import derechos_titular, impacto
from .api import jwt_utils
from .models import Contratacion, Pago, Publicaciones, Usuario, Valoracion
from .tests import _crear_region_comuna_tipo, _crear_usuario


def _autenticar(client, usuario):
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {jwt_utils.generar_access_token(usuario)}')


class RegistroImpactoApiTests(APITestCase):
    def setUp(self):
        self.region, self.comuna, _ = _crear_region_comuna_tipo()

    def _datos(self, **extra):
        datos = {
            'rut': '11111111-1', 'nombre1': 'Test', 'apellido1': 'Usuario', 'edad': 30, 'telefono': 912345678,
            'email': 'impacto@test.com', 'region': self.region.id_region, 'comuna': self.comuna.id_comuna,
            'password': 'ClaveSegura2026!', 'password_confirm': 'ClaveSegura2026!', 'acepta_politica': True,
        }
        datos.update(extra)
        return datos

    def test_registro_sin_responder_las_preguntas_funciona(self):
        resp = self.client.post('/api/auth/registro/', self._datos(), format='json')
        self.assertEqual(resp.status_code, 201)
        usuario = Usuario.objects.get(email='impacto@test.com')
        self.assertEqual(usuario.situacion_laboral_previa, '')
        self.assertEqual(usuario.genero, '')

    def test_registro_guarda_las_respuestas_voluntarias(self):
        resp = self.client.post('/api/auth/registro/', self._datos(situacion_laboral_previa='SIN_TRABAJO', genero='MUJER'), format='json')
        self.assertEqual(resp.status_code, 201)
        usuario = Usuario.objects.get(email='impacto@test.com')
        self.assertEqual((usuario.situacion_laboral_previa, usuario.genero), ('SIN_TRABAJO', 'MUJER'))

    def test_valor_invalido_se_rechaza(self):
        resp = self.client.post('/api/auth/registro/', self._datos(genero='XX'), format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('genero', resp.data)


class DatosImpactoApiTests(APITestCase):
    def setUp(self):
        _, self.comuna, self.tipo = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('datos@test.com', comuna=self.comuna, tipo_cuenta=self.tipo)
        _autenticar(self.client, self.usuario)

    def test_se_editan_y_se_pueden_borrar(self):
        resp = self.client.put('/api/auth/datos-impacto/', {'situacion_laboral_previa': 'INFORMAL', 'genero': 'HOMBRE'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['situacion_laboral_previa'], 'INFORMAL')
        resp = self.client.put('/api/auth/datos-impacto/', {'situacion_laboral_previa': '', 'genero': ''}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertEqual((self.usuario.situacion_laboral_previa, self.usuario.genero), ('', ''))

    def test_preferencias_de_sonido_no_borran_las_respuestas(self):
        self.client.put('/api/auth/datos-impacto/', {'situacion_laboral_previa': 'FORMAL', 'genero': 'OTRO'}, format='json')
        self.client.put('/api/auth/preferencias/', {'notificaciones_sonido': False}, format='json')
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.situacion_laboral_previa, 'FORMAL')

    def test_requiere_sesion(self):
        self.client.credentials()
        self.assertEqual(self.client.put('/api/auth/datos-impacto/', {}, format='json').status_code, 401)

    def test_aparecen_en_la_exportacion_y_se_borran_al_anonimizar(self):
        self.usuario.situacion_laboral_previa, self.usuario.genero = 'ESTUDIANTE', 'MUJER'
        self.usuario.save()
        perfil = derechos_titular.exportar_datos(self.usuario)['perfil']
        self.assertEqual((perfil['situacion_laboral_previa'], perfil['genero']), ('ESTUDIANTE', 'MUJER'))
        derechos_titular.eliminar_cuenta(self.usuario)
        self.usuario.refresh_from_db()
        self.assertEqual((self.usuario.situacion_laboral_previa, self.usuario.genero), ('', ''))

    def test_otros_usuarios_no_ven_las_respuestas(self):
        self.usuario.situacion_laboral_previa = 'SIN_TRABAJO'
        self.usuario.es_proveedor = True
        self.usuario.save()
        pub = Publicaciones.objects.create(usuario_publicador=self.usuario, titulo='X', estado_moderacion=Publicaciones.APROBADA, precio=1000)
        self.client.credentials()
        resp = self.client.get(f'/api/publicaciones/{pub.id_publicacion}/')
        self.assertNotIn('SIN_TRABAJO', json.dumps(resp.data))


class TipoServicioYReemplazoApiTests(APITestCase):
    def setUp(self):
        _, self.comuna, self.tipo = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('prov_tipo@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo)
        self.cliente = _crear_usuario('cli_tipo@test.com', comuna=self.comuna, tipo_cuenta=self.tipo)

    def _publicar(self, **extra):
        _autenticar(self.client, self.proveedor)
        datos = {'titulo': 'Arreglo de lavadoras', 'descripcion_publicacion': 'Reparo lavadoras', 'categoria': 'Gasfitería', 'precio': 20000}
        datos.update(extra)
        return self.client.post('/api/publicaciones/crear/', datos, format='json')

    def test_publicar_sin_tipo_queda_como_otro(self):
        resp = self._publicar()
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['publicacion']['tipo_servicio'], 'OTRO')

    def test_publicar_con_tipo(self):
        resp = self._publicar(tipo_servicio='REPARACION')
        self.assertEqual(resp.data['publicacion']['tipo_servicio'], 'REPARACION')

    def test_tipo_invalido_se_rechaza(self):
        self.assertEqual(self._publicar(tipo_servicio='NADA').status_code, 400)

    def test_valoracion_guarda_si_evito_reemplazo(self):
        pub = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='R', estado_moderacion=Publicaciones.APROBADA, tipo_servicio='REPARACION')
        contratacion = Contratacion.objects.create(publicacion=pub, cliente=self.cliente, proveedor=self.proveedor, estado=Contratacion.COMPLETADA)
        _autenticar(self.client, self.cliente)
        resp = self.client.post(f'/api/contrataciones/{contratacion.id_contratacion}/valoracion/', {'puntuacion': 5, 'comentario': 'ok', 'evito_reemplazo': 'SI'}, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(Valoracion.objects.get(contratacion=contratacion).evito_reemplazo, 'SI')

    def test_valoracion_sin_responder_queda_vacia(self):
        pub = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='R', estado_moderacion=Publicaciones.APROBADA)
        contratacion = Contratacion.objects.create(publicacion=pub, cliente=self.cliente, proveedor=self.proveedor, estado=Contratacion.COMPLETADA)
        _autenticar(self.client, self.cliente)
        self.client.post(f'/api/contrataciones/{contratacion.id_contratacion}/valoracion/', {'puntuacion': 4}, format='json')
        self.assertEqual(Valoracion.objects.get(contratacion=contratacion).evito_reemplazo, '')


def _proveedor_con_pago(indice, comuna, tipo, tipo_servicio='REPARACION', monto=40000, situacion='', genero='', demo=False, misma_comuna=True, evito=''):
    dominio = 'demo.keyserv' if demo else 'real.test'
    proveedor = _crear_usuario(f'p{indice}@{dominio}', es_proveedor=True, comuna=comuna, tipo_cuenta=tipo)
    proveedor.situacion_laboral_previa, proveedor.genero = situacion, genero
    proveedor.save()
    cliente = _crear_usuario(f'c{indice}@{dominio}', comuna=comuna if misma_comuna else None, tipo_cuenta=tipo)
    pub = Publicaciones.objects.create(usuario_publicador=proveedor, titulo=f'S{indice}', estado_moderacion=Publicaciones.APROBADA, tipo_servicio=tipo_servicio)
    contratacion = Contratacion.objects.create(publicacion=pub, cliente=cliente, proveedor=proveedor, estado=Contratacion.COMPLETADA)
    Pago.objects.create(
        contratacion=contratacion, monto=monto + 2000, monto_servicio=monto, comision_monto=2000, metodo=Pago.WEBPAY,
        estado=Pago.PAGADO, fecha_confirmacion=timezone.now(),
    )
    if evito:
        Valoracion.objects.create(
            puntuacion=5, usuario_emisor=cliente, usuario_receptor=proveedor, publicacion=pub, contratacion=contratacion,
            evito_reemplazo=evito,
        )
    return proveedor


class ReporteImpactoTests(APITestCase):
    def setUp(self):
        _, self.comuna, self.tipo = _crear_region_comuna_tipo()

    def _crear(self, n, **kw):
        return [_proveedor_con_pago(i, self.comuna, self.tipo, **kw) for i in range(n)]

    def test_con_pocos_proveedores_todo_se_suprime(self):
        self._crear(3, situacion='SIN_TRABAJO', genero='MUJER')
        datos = impacto.calcular()
        self.assertIsNone(datos['proveedores'])
        self.assertIsNone(datos['proveedores_con_primer_pago'])
        self.assertIsNone(datos['ingreso_mensual_mediano_por_proveedor'])
        self.assertIsNone(datos['pct_mujeres'])
        self.assertIsNone(datos['situacion_laboral_previa']['SIN_TRABAJO'])

    def test_con_cinco_proveedores_se_publican_los_agregados(self):
        self._crear(5, tipo_servicio='REPARACION', monto=40000, situacion='SIN_TRABAJO')
        datos = impacto.calcular()
        self.assertEqual(datos['proveedores'], 5)
        self.assertEqual(datos['proveedores_con_primer_pago'], 5)
        self.assertEqual(datos['servicios_pagados'], 5)
        self.assertEqual(datos['ingreso_mensual_mediano_por_proveedor'], 40000)  # sin la comisión
        self.assertEqual(datos['pct_reparacion_mantencion'], 100.0)
        self.assertEqual(datos['pct_ingreso_misma_comuna'], 100.0)
        self.assertEqual(datos['situacion_laboral_previa']['SIN_TRABAJO'], 5)

    def test_economia_local_mide_solo_la_misma_comuna(self):
        self._crear(5, misma_comuna=True, monto=10000)
        for i in range(10, 15):
            _proveedor_con_pago(i, self.comuna, self.tipo, monto=10000, misma_comuna=False)
        self.assertEqual(impacto.calcular()['pct_ingreso_misma_comuna'], 50.0)

    def test_reparaciones_que_evitaron_reemplazo(self):
        for i in range(5):
            _proveedor_con_pago(i, self.comuna, self.tipo, tipo_servicio='REPARACION', evito='SI' if i < 4 else 'NO')
        datos = impacto.calcular()
        self.assertEqual(datos['reparaciones_que_evitaron_reemplazo'], 4)
        self.assertEqual(datos['reparaciones_con_respuesta'], 5)

    def test_supresion_complementaria_en_una_distribucion(self):
        self._crear(6, situacion='INFORMAL')            # 6 visibles
        for i in range(20, 23):                          # 3: suprimidos
            _proveedor_con_pago(i, self.comuna, self.tipo, situacion='SIN_TRABAJO')
        for i in range(30, 38):                          # 8 visibles
            _proveedor_con_pago(i, self.comuna, self.tipo, situacion='FORMAL')
        dist = impacto.calcular()['situacion_laboral_previa']
        self.assertIsNone(dist['SIN_TRABAJO'])
        self.assertIsNone(dist['INFORMAL'])  # el menor de los visibles también, para que no se despeje restando
        self.assertEqual(dist['FORMAL'], 8)

    def test_las_cuentas_de_demo_se_excluyen_por_defecto(self):
        for i in range(6):
            _proveedor_con_pago(i, self.comuna, self.tipo, demo=True)
        self.assertEqual(impacto.calcular()['proveedores'], 0)
        self.assertEqual(impacto.calcular(incluir_demo=True)['proveedores'], 6)

    def test_el_comando_imprime_y_exporta_json(self):
        self._crear(5)
        salida = StringIO()
        call_command('reporte_impacto', stdout=salida)
        self.assertIn('Proveedores registrados: 5', salida.getvalue())
        salida = StringIO()
        call_command('reporte_impacto', '--json', stdout=salida)
        self.assertEqual(json.loads(salida.getvalue())['proveedores'], 5)

    def test_la_salida_no_contiene_datos_personales(self):
        self._crear(5, situacion='SIN_TRABAJO')
        salida = StringIO()
        call_command('reporte_impacto', '--json', stdout=salida)
        self.assertNotIn('@', salida.getvalue())
