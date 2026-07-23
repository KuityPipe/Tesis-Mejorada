"""
Tests automatizados de KeyServ.

NUEVO en Fase 4 — antes este archivo era el stub vacío que deja `startapp`
por defecto (0% de cobertura, ver docs/CODE_ANALYSIS_FINDINGS.md). Cubre,
en orden de lo que `docs/CODE_ANALYSIS_FINDINGS.md` §10 identificó como
mayor retorno: hashing de password, `register_view`, `load_comunas`, import
de los módulos de biometría — y de paso todo lo agregado en Fase 4
(publicaciones, contratación con re-autenticación, valoraciones, mensajería).

Corre contra una base de datos de prueba real (Django la crea y destruye
sola en Postgres) — no son mocks, así que si algo similar al bug de
Fase 3 (nombres de campo desalineados) vuelve a aparecer, estos tests lo
detectan igual que detectaron los bugs originales cuando se armó Fase 3.
"""
from django.test import TestCase, Client
from django.urls import reverse

from .models import (
    Comuna, Contratacion, Publicaciones, Ranking, Region, TipoCuenta, Usuario,
    Valoracion,
)
from . import biometria


def _crear_region_comuna_tipo():
    """Helper: catálogos mínimos que casi todos los tests necesitan (región, comuna, tipo de cuenta)."""
    region = Region.objects.create(id_region=13, nombre_region='Región Metropolitana')
    comuna = Comuna.objects.create(id_comuna=1, nombre_comuna='Santiago', region=region)
    tipo_cuenta = TipoCuenta.objects.create(id_tipo_cuenta=1, nombre_tipo_cuenta='CLIENTE', valor_cuenta=0)
    return region, comuna, tipo_cuenta


def _crear_usuario(email, password='clave123', es_proveedor=False, comuna=None, tipo_cuenta=None):
    """Helper: crea un Usuario con password ya hasheado correctamente (como lo hace RegistroForm.crear_usuario)."""
    usuario = Usuario(
        rut_usuario='11111111-1', nombre_usuario='Test', apellido_usuario='Usuario',
        telefono=912345678, email=email, edad=30, comuna=comuna, tipo_cuenta=tipo_cuenta,
        es_proveedor=es_proveedor,
    )
    usuario.set_password(password)
    usuario.save()
    return usuario


class UsuarioPasswordTests(TestCase):
    """El bug más grave que había en el código original: el password se re-hasheaba en cada save()."""

    def test_hash_no_es_texto_plano(self):
        u = Usuario(rut_usuario='1', nombre_usuario='a', apellido_usuario='b', telefono=1, edad=20)
        u.set_password('miclave')
        self.assertNotEqual(u.password, 'miclave')

    def test_check_password_acepta_la_correcta(self):
        u = Usuario(rut_usuario='1', nombre_usuario='a', apellido_usuario='b', telefono=1, edad=20)
        u.set_password('miclave')
        self.assertTrue(u.check_password('miclave'))

    def test_check_password_rechaza_incorrecta(self):
        u = Usuario(rut_usuario='1', nombre_usuario='a', apellido_usuario='b', telefono=1, edad=20)
        u.set_password('miclave')
        self.assertFalse(u.check_password('otraclave'))

    def test_guardar_dos_veces_no_rompe_el_password(self):
        """Este es el bug exacto de la versión anterior: guardar dos veces destruía el password (hash del hash)."""
        _, comuna, tipo_cuenta = _crear_region_comuna_tipo()
        usuario = _crear_usuario('doble@save.com', 'miclave', comuna=comuna, tipo_cuenta=tipo_cuenta)
        usuario.direccion_usuario = 'otra direccion'
        usuario.save()  # segundo save() — con el bug viejo, esto habría vuelto a hashear el hash
        self.assertTrue(usuario.check_password('miclave'))


class RegistroViewTests(TestCase):
    """register_view: el bug de nombres de campo desalineados hacía que esto tirara TypeError garantizado."""

    def setUp(self):
        self.region, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.client = Client()

    def _datos_validos(self, **overrides):
        datos = {
            'rut': '11111111-1', 'nombre1': 'Test', 'nombre2': '', 'apellido1': 'Usuario', 'apellido2': '',
            'edad': 30, 'telefono': 912345678, 'email': 'nuevo@test.com',
            'region': self.region.id_region, 'comuna': self.comuna.id_comuna, 'direccion': 'Calle Falsa 123',
            'tipo_cuenta': self.tipo_cuenta.id_tipo_cuenta, 'password': '123456', 'password_confirm': '123456',
        }
        datos.update(overrides)
        return datos

    def test_registro_exitoso_redirige_a_sesion(self):
        resp = self.client.post(reverse('KeyServApp:registro'), self._datos_validos())
        self.assertRedirects(resp, reverse('KeyServApp:sesion'))
        usuario = Usuario.objects.get(email='nuevo@test.com')
        self.assertTrue(usuario.check_password('123456'))

    def test_registro_con_contrasenas_distintas_falla(self):
        resp = self.client.post(reverse('KeyServApp:registro'), self._datos_validos(password_confirm='otra'))
        self.assertEqual(resp.status_code, 200)  # se re-muestra el formulario, no redirige
        self.assertFalse(Usuario.objects.filter(email='nuevo@test.com').exists())

    def test_registro_con_email_duplicado_falla(self):
        _crear_usuario('nuevo@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        resp = self.client.post(reverse('KeyServApp:registro'), self._datos_validos())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Usuario.objects.filter(email='nuevo@test.com').count(), 1)

    def test_registro_menor_de_edad_falla(self):
        """RNF011 del PDF: mayoría de edad."""
        resp = self.client.post(reverse('KeyServApp:registro'), self._datos_validos(edad=15, email='menor@test.com'))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Usuario.objects.filter(email='menor@test.com').exists())


class LoginViewTests(TestCase):
    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('login@test.com', 'claveok', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.client = Client()

    def test_login_correcto_redirige_a_inicio(self):
        resp = self.client.post(reverse('KeyServApp:sesion'), {'email': 'login@test.com', 'password': 'claveok'})
        self.assertRedirects(resp, reverse('KeyServApp:sesion_iniciada'))

    def test_login_incorrecto_no_redirige(self):
        resp = self.client.post(reverse('KeyServApp:sesion'), {'email': 'login@test.com', 'password': 'incorrecta'})
        self.assertEqual(resp.status_code, 200)


class LoadComunasTests(TestCase):
    """load_comunas: el bug de FK_REGION como IntegerField plano (no ForeignKey) hacía que `region_id` no existiera."""

    def test_devuelve_solo_comunas_de_la_region_pedida(self):
        region1 = Region.objects.create(id_region=1, nombre_region='Región 1')
        region2 = Region.objects.create(id_region=2, nombre_region='Región 2')
        Comuna.objects.create(id_comuna=1, nombre_comuna='Comuna A', region=region1)
        Comuna.objects.create(id_comuna=2, nombre_comuna='Comuna B', region=region2)

        resp = self.client.get(reverse('KeyServApp:ajax_load_comunas'), {'region_id': region1.id_region})
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['nombre_comuna'], 'Comuna A')


class BiometriaImportTests(TestCase):
    """Un test de import trivial habría detectado el AttributeError de CONEXION_BD.cur antes de llegar a producción."""

    def test_modulo_huella_importa_sin_reventar(self):
        # No requiere que Pillow/la imagen de ejemplo funcionen — solo que el import no explote.
        self.assertTrue(hasattr(biometria, 'procesar_huella_dactilar'))

    def test_procesar_huella_con_ruta_invalida_devuelve_none_no_excepcion(self):
        resultado = biometria.procesar_huella_dactilar('/ruta/que/no/existe.png')
        self.assertIsNone(resultado)


class PublicacionYModeracionTests(TestCase):
    """Publicaciones.estado_moderacion (nuevo en Fase 3) — solo lo aprobado debe verse en el listado público."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)

    def test_publicacion_nace_pendiente(self):
        pub = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Gasfitería')
        self.assertEqual(pub.estado_moderacion, Publicaciones.PENDIENTE)

    def test_catalogo_solo_muestra_aprobadas(self):
        Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Pendiente', estado_moderacion=Publicaciones.PENDIENTE)
        Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Aprobada', estado_moderacion=Publicaciones.APROBADA)
        resp = self.client.get(reverse('KeyServApp:catalogo'))
        publicaciones = list(resp.context['publicaciones'])
        self.assertEqual(len(publicaciones), 1)
        self.assertEqual(publicaciones[0].titulo, 'Aprobada')

    def test_solo_proveedores_pueden_crear_publicaciones(self):
        cliente = _crear_usuario('cliente_no_prov@test.com', es_proveedor=False, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        client = Client()
        # OJO: `client.session` crea una SessionStore nueva en cada acceso — hay
        # que capturarla en una variable antes de modificarla, si no el save()
        # guarda una sesión vacía distinta y el login nunca queda activo.
        session = client.session
        session['usuario_id'] = cliente.id_usuario
        session.save()
        resp = client.get(reverse('KeyServApp:publicacion_crear'))
        self.assertRedirects(resp, reverse('KeyServApp:perfil'))


class ContratacionFlowTests(TestCase):
    """
    Flujo completo del BPMN 'Proceso de contratación' del PDF (PAGE 136-137):
    solicitar -> confirmar (proveedor, re-auth) -> completar (cliente, re-auth) -> valorar.
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor2@test.com', 'clave_prov', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente2@test.com', 'clave_cli', es_proveedor=False, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Electricidad', estado_moderacion=Publicaciones.APROBADA)

    def _login_como(self, client, usuario):
        session = client.session
        session['usuario_id'] = usuario.id_usuario
        session.save()

    def test_flujo_completo_de_contratacion_y_valoracion(self):
        client = Client()

        # 1. El cliente solicita contratar.
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_crear', args=[self.publicacion.id_publicacion]))
        contratacion = Contratacion.objects.get(publicacion=self.publicacion)
        self.assertEqual(contratacion.estado, Contratacion.SOLICITADA)
        # La notificación al proveedor vía mensajería se prueba en MensajeriaTests.

        # 2. El proveedor confirma con re-autenticación correcta.
        self._login_como(client, self.proveedor)
        client.post(reverse('KeyServApp:contratacion_confirmar', args=[contratacion.id_contratacion]), {'password': 'clave_prov'})
        contratacion.refresh_from_db()
        self.assertEqual(contratacion.estado, Contratacion.CONFIRMADA)

        # 3. El cliente marca como completada con re-autenticación correcta.
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_completar', args=[contratacion.id_contratacion]), {'password': 'clave_cli'})
        contratacion.refresh_from_db()
        self.assertEqual(contratacion.estado, Contratacion.COMPLETADA)

        # 4. El cliente valora al proveedor — el Ranking del proveedor debe recalcularse.
        client.post(reverse('KeyServApp:valoracion_crear', args=[contratacion.id_contratacion]), {'puntuacion': 5, 'comentario': 'Excelente'})
        self.assertTrue(Valoracion.objects.filter(usuario_receptor=self.proveedor, puntuacion=5).exists())
        ranking = Ranking.objects.get(usuario=self.proveedor)
        self.assertEqual(ranking.total_valoraciones, 1)
        self.assertEqual(float(ranking.puntuacion_promedio), 5.0)

    def test_confirmar_con_password_incorrecta_no_avanza_estado(self):
        client = Client()
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_crear', args=[self.publicacion.id_publicacion]))
        contratacion = Contratacion.objects.get(publicacion=self.publicacion)

        self._login_como(client, self.proveedor)
        client.post(reverse('KeyServApp:contratacion_confirmar', args=[contratacion.id_contratacion]), {'password': 'clave-mala'})
        contratacion.refresh_from_db()
        self.assertEqual(contratacion.estado, Contratacion.SOLICITADA)

    def test_solo_el_proveedor_puede_confirmar(self):
        """El cliente no puede confirmar su propia solicitud (eso rompería el sentido de la re-autenticación de 'ambas partes')."""
        client = Client()
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_crear', args=[self.publicacion.id_publicacion]))
        contratacion = Contratacion.objects.get(publicacion=self.publicacion)

        client.post(reverse('KeyServApp:contratacion_confirmar', args=[contratacion.id_contratacion]), {'password': 'clave_cli'})
        contratacion.refresh_from_db()
        self.assertEqual(contratacion.estado, Contratacion.SOLICITADA)


class MensajeriaTests(TestCase):
    """La contratación debe notificar al proveedor vía el sistema de mensajería (en vez de email)."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor3@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente3@test.com', es_proveedor=False, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Pintura', estado_moderacion=Publicaciones.APROBADA)

    def test_contratar_crea_conversacion_con_mensaje_de_aviso(self):
        from .models import Conversacion, Mensaje

        client = Client()
        session = client.session
        session['usuario_id'] = self.cliente.id_usuario
        session.save()
        client.post(reverse('KeyServApp:contratacion_crear', args=[self.publicacion.id_publicacion]))

        self.assertEqual(Conversacion.objects.count(), 1)
        mensaje = Mensaje.objects.first()
        self.assertIn('Pintura', mensaje.contenido)
        self.assertEqual(mensaje.usuario, self.cliente)

    def test_ambos_pueden_ver_la_conversacion_pero_un_tercero_no(self):
        """El chat ahora es 1:1 con la Contratacion (antes era por par de usuarios)."""
        from .models import Contratacion
        from .views import _obtener_o_crear_conversacion_de_contratacion

        contratacion = Contratacion.objects.create(publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor)
        conversacion = _obtener_o_crear_conversacion_de_contratacion(contratacion)

        client = Client()
        session = client.session
        session['usuario_id'] = self.proveedor.id_usuario
        session.save()
        # /chat/<id>/ redirige al detalle del trabajo, que trae el mismo chat embebido.
        resp = client.get(reverse('KeyServApp:conversacion_detalle', args=[conversacion.id_conversacion]))
        self.assertRedirects(resp, reverse('KeyServApp:contratacion_detalle', args=[contratacion.id_contratacion]))
        resp_detalle = client.get(reverse('KeyServApp:contratacion_detalle', args=[contratacion.id_contratacion]))
        self.assertEqual(resp_detalle.status_code, 200)

        otro = _crear_usuario('intruso@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        client2 = Client()
        session2 = client2.session
        session2['usuario_id'] = otro.id_usuario
        session2.save()
        resp2 = client2.get(reverse('KeyServApp:conversacion_detalle', args=[conversacion.id_conversacion]))
        self.assertRedirects(resp2, reverse('KeyServApp:chat'))
