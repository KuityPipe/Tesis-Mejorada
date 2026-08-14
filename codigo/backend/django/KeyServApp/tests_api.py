"""
Tests de la API REST — separado de `KeyServApp/tests.py` a propósito
mientras dura la migración (Fase 1 del plan): las vistas basadas en
templates y las de la API van a coexistir varias fases, y mezclar ambos
mundos en un solo archivo gigante habría sido más fricción de merge que
seguridad extra. Cada escenario acá espeja uno ya cubierto en
`LoginViewTests` (tests.py) para la ruta equivalente `/api/auth/`.
"""
from django.core.cache import cache
from rest_framework.test import APITestCase

from .api import jwt_utils
from .models import Comuna, IntentoAccesoSospechoso, Publicaciones, Region, TokenSesion, Usuario, Valoracion
from .tests import _crear_region_comuna_tipo, _crear_usuario, _imagen_de_prueba
from .views import _generar_token_recuperacion


class LoginApiTests(APITestCase):
    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('login@test.com', 'claveok', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)

    def tearDown(self):
        # El límite de intentos vive en `cache` (LocMemCache persiste entre
        # métodos de test, a diferencia de la base de datos), keyeado por
        # (IP, email) — sin esto, un test que agota el límite deja
        # bloqueados a los que corren después con el mismo email. Mismo
        # patrón que LoginViewTests.test_login_bloqueado_... (tests.py).
        cache.clear()

    def test_login_correcto_devuelve_tokens_y_usuario(self):
        resp = self.client.post('/api/auth/login/', {'email': 'login@test.com', 'password': 'claveok'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access_token', resp.data)
        self.assertIn('refresh_token', resp.data)
        self.assertEqual(resp.data['usuario']['email'], 'login@test.com')
        # El refresh token queda respaldado por una TokenSesion propia (no una sesión de Django).
        self.assertEqual(TokenSesion.objects.filter(usuario=self.usuario).count(), 1)

    def test_login_incorrecto_devuelve_401(self):
        resp = self.client.post('/api/auth/login/', {'email': 'login@test.com', 'password': 'incorrecta'}, format='json')
        self.assertEqual(resp.status_code, 401)
        self.assertNotIn('access_token', resp.data)

    def test_login_bloqueado_queda_registrado_como_sospechoso(self):
        """Mismo bloqueo por fuerza bruta que LoginViewTests, ahora contra /api/auth/login/."""
        for _ in range(5):
            self.client.post('/api/auth/login/', {'email': 'login@test.com', 'password': 'incorrecta'}, format='json')

        resp = self.client.post('/api/auth/login/', {'email': 'login@test.com', 'password': 'claveok'}, format='json')
        self.assertEqual(resp.status_code, 429)

        intento = IntentoAccesoSospechoso.objects.get(recurso='login_bloqueado')
        self.assertIsNone(intento.usuario)
        self.assertEqual(intento.recurso_id, 'login@test.com')


class MeApiTests(APITestCase):
    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('me@test.com', 'claveok', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)

    def test_sin_token_devuelve_401(self):
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 401)

    def test_con_token_valido_devuelve_el_perfil(self):
        access_token = jwt_utils.generar_access_token(self.usuario)
        resp = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['id_usuario'], self.usuario.id_usuario)
        self.assertEqual(resp.data['email'], 'me@test.com')
        self.assertNotIn('password', resp.data)

    def test_con_token_manipulado_devuelve_401(self):
        access_token = jwt_utils.generar_access_token(self.usuario)
        resp = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Bearer {access_token}x')
        self.assertEqual(resp.status_code, 401)

    def test_con_usuario_borrado_despues_de_emitido_el_token_devuelve_401(self):
        access_token = jwt_utils.generar_access_token(self.usuario)
        self.usuario.delete()
        resp = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self.assertEqual(resp.status_code, 401)


class JWTUtilsTests(APITestCase):
    """Cobertura directa de jwt_utils.py — la parte de la que dependen todos los endpoints autenticados."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('jwt@test.com', 'claveok', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)

    def test_crear_sesion_guarda_solo_el_hash_del_refresh_token(self):
        _access, refresh_plano, sesion = jwt_utils.crear_sesion(self.usuario, dispositivo='pytest')
        self.assertNotEqual(sesion.refresh_token_hash, refresh_plano)
        self.assertEqual(len(sesion.refresh_token_hash), 64)  # sha256 hexdigest

    def test_obtener_sesion_vigente_encuentra_la_sesion_activa(self):
        _access, refresh_plano, sesion = jwt_utils.crear_sesion(self.usuario)
        encontrada = jwt_utils.obtener_sesion_vigente(refresh_plano)
        self.assertEqual(encontrada.pk, sesion.pk)

    def test_sesion_revocada_no_se_encuentra_vigente(self):
        _access, refresh_plano, sesion = jwt_utils.crear_sesion(self.usuario)
        jwt_utils.revocar_sesion(sesion)
        self.assertIsNone(jwt_utils.obtener_sesion_vigente(refresh_plano))

    def test_refresh_token_incorrecto_no_encuentra_nada(self):
        jwt_utils.crear_sesion(self.usuario)
        self.assertIsNone(jwt_utils.obtener_sesion_vigente('token-que-no-existe'))


class PublicacionesApiTests(APITestCase):
    """`GET /api/publicaciones/` y `/api/publicaciones/<pk>/` — públicos, sin token (ver PublicacionListView/PublicacionDetailView)."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor_api@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)

    def test_no_requiere_token(self):
        Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Gasfitería', estado_moderacion=Publicaciones.APROBADA)
        resp = self.client.get('/api/publicaciones/')
        self.assertEqual(resp.status_code, 200)

    def test_listado_solo_muestra_aprobadas(self):
        """Mismo criterio que CatalogoViewTests.test_catalogo_solo_muestra_aprobadas (tests.py), ahora contra /api/publicaciones/."""
        Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Pendiente', estado_moderacion=Publicaciones.PENDIENTE)
        Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Aprobada', estado_moderacion=Publicaciones.APROBADA)

        resp = self.client.get('/api/publicaciones/')

        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['titulo'], 'Aprobada')

    def test_listado_incluye_proveedor_embebido(self):
        Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Electricidad', estado_moderacion=Publicaciones.APROBADA)

        resp = self.client.get('/api/publicaciones/')

        proveedor = resp.data['results'][0]['proveedor']
        self.assertEqual(proveedor['nombre_usuario'], self.proveedor.nombre_usuario)
        # Sin Ranking todavía (nadie lo calificó) — el default de los campos
        # anidados en ProveedorSerializer tiene que cubrir esto sin romper.
        self.assertIsNone(proveedor['puntuacion_promedio'])
        self.assertEqual(proveedor['total_valoraciones'], 0)

    def test_filtro_region(self):
        otra_region = Region.objects.create(id_region=5, nombre_region='Valparaíso')
        otra_comuna = Comuna.objects.create(id_comuna=5, nombre_comuna='Viña del Mar', region=otra_region)
        otro_proveedor = _crear_usuario('otro_proveedor_api@test.com', es_proveedor=True, comuna=otra_comuna, tipo_cuenta=self.tipo_cuenta)
        Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='De acá', estado_moderacion=Publicaciones.APROBADA)
        Publicaciones.objects.create(usuario_publicador=otro_proveedor, titulo='De allá', estado_moderacion=Publicaciones.APROBADA)

        resp = self.client.get(f'/api/publicaciones/?region={self.comuna.region_id}')

        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['titulo'], 'De acá')

    def test_no_requiere_token_detalle(self):
        publicacion = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Detalle', estado_moderacion=Publicaciones.APROBADA)
        resp = self.client.get(f'/api/publicaciones/{publicacion.pk}/')
        self.assertEqual(resp.status_code, 200)

    def test_detalle_incluye_resenas_aprobadas_solamente(self):
        publicacion = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Pintura', estado_moderacion=Publicaciones.APROBADA)
        cliente = _crear_usuario('cliente_api@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        Valoracion.objects.create(
            usuario_emisor=cliente, usuario_receptor=self.proveedor, publicacion=publicacion,
            puntuacion=5, comentario='Aprobada', estado_moderacion=Valoracion.APROBADA,
        )
        Valoracion.objects.create(
            usuario_emisor=cliente, usuario_receptor=self.proveedor, publicacion=publicacion,
            puntuacion=1, comentario='Pendiente', estado_moderacion=Valoracion.PENDIENTE,
        )

        resp = self.client.get(f'/api/publicaciones/{publicacion.pk}/')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['resenas']), 1)
        self.assertEqual(resp.data['resenas'][0]['comentario'], 'Aprobada')


class RegistroApiTests(APITestCase):
    """`POST /api/auth/registro/` — espeja RegistroViewTests (tests.py), mismos escenarios contra la ruta de la API."""

    def setUp(self):
        self.region, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()

    def _datos_validos(self, **overrides):
        datos = {
            'rut': '11111111-1', 'nombre1': 'Test', 'nombre2': '', 'apellido1': 'Usuario', 'apellido2': '',
            'edad': 30, 'telefono': 912345678, 'email': 'nuevo_api@test.com',
            'region': self.region.id_region, 'comuna': self.comuna.id_comuna, 'direccion': 'Calle Falsa 123',
            'tipo_cuenta': self.tipo_cuenta.id_tipo_cuenta, 'password': 'ClaveSegura2026!', 'password_confirm': 'ClaveSegura2026!',
        }
        datos.update(overrides)
        return datos

    def test_registro_exitoso_crea_usuario_y_devuelve_201(self):
        resp = self.client.post('/api/auth/registro/', self._datos_validos(), format='json')

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['email'], 'nuevo_api@test.com')
        self.assertNotIn('password', resp.data)
        # Sin tokens: mismo criterio que register_view, "ahora iniciá sesión" en vez de auto-login.
        self.assertNotIn('access_token', resp.data)
        usuario = Usuario.objects.get(email='nuevo_api@test.com')
        self.assertTrue(usuario.check_password('ClaveSegura2026!'))

    def test_registro_con_contrasenas_distintas_devuelve_400(self):
        resp = self.client.post('/api/auth/registro/', self._datos_validos(password_confirm='otra'), format='json')

        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Usuario.objects.filter(email='nuevo_api@test.com').exists())

    def test_registro_con_email_duplicado_devuelve_400(self):
        _crear_usuario('nuevo_api@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)

        resp = self.client.post('/api/auth/registro/', self._datos_validos(), format='json')

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Usuario.objects.filter(email='nuevo_api@test.com').count(), 1)

    def test_registro_menor_de_edad_devuelve_400(self):
        resp = self.client.post('/api/auth/registro/', self._datos_validos(edad=15, email='menor_api@test.com'), format='json')

        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Usuario.objects.filter(email='menor_api@test.com').exists())


class CatalogosApiTests(APITestCase):
    """`GET /api/catalogos/*` — catálogos públicos que alimentan los selects del registro en Ionic."""

    def setUp(self):
        self.region, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()

    def test_regiones_no_requiere_token(self):
        resp = self.client.get('/api/catalogos/regiones/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data[0]['nombre_region'], self.region.nombre_region)

    def test_comunas_filtra_por_region(self):
        otra_region = Region.objects.create(id_region=5, nombre_region='Valparaíso')
        Comuna.objects.create(id_comuna=5, nombre_comuna='Viña del Mar', region=otra_region)

        resp = self.client.get(f'/api/catalogos/comunas/?region={self.region.id_region}')

        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['nombre_comuna'], self.comuna.nombre_comuna)

    def test_tipos_cuenta_no_requiere_token(self):
        resp = self.client.get('/api/catalogos/tipos-cuenta/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data[0]['id_tipo_cuenta'], self.tipo_cuenta.id_tipo_cuenta)


class PerfilApiTests(APITestCase):
    """`PUT /api/auth/perfil/` — espeja EditarPerfilTests (tests.py), mismos escenarios contra la ruta de la API."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.otra_comuna = Comuna.objects.create(id_comuna=2, nombre_comuna='Otra comuna', region=self.comuna.region)
        self.usuario = _crear_usuario('editar_api@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.access_token = jwt_utils.generar_access_token(self.usuario)

    def _autenticado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def _datos_validos(self, **overrides):
        datos = {
            'nombre_usuario': self.usuario.nombre_usuario, 'apellido_usuario': self.usuario.apellido_usuario,
            'telefono': self.usuario.telefono, 'email': self.usuario.email,
            'region': self.comuna.region_id, 'comuna': self.comuna.id_comuna,
        }
        datos.update(overrides)
        return datos

    def test_sin_token_devuelve_401(self):
        resp = self.client.put('/api/auth/perfil/', self._datos_validos())
        self.assertEqual(resp.status_code, 401)

    def test_guarda_los_cambios_reales(self):
        self._autenticado()

        resp = self.client.put('/api/auth/perfil/', self._datos_validos(
            nombre_usuario='NuevoNombreApi', telefono=987654321, comuna=self.otra_comuna.id_comuna,
        ))

        self.assertEqual(resp.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nombre_usuario, 'NuevoNombreApi')
        self.assertEqual(self.usuario.telefono, 987654321)
        self.assertEqual(self.usuario.comuna_id, self.otra_comuna.id_comuna)

    def test_no_permite_repetir_el_correo_de_otro_usuario(self):
        _crear_usuario('ocupado_api@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self._autenticado()

        resp = self.client.put('/api/auth/perfil/', self._datos_validos(email='ocupado_api@test.com'))

        self.assertEqual(resp.status_code, 400)
        self.usuario.refresh_from_db()
        self.assertNotEqual(self.usuario.email, 'ocupado_api@test.com')

    def test_puede_guardar_sin_cambiar_su_propio_correo(self):
        """clean_email() no debe rechazar al usuario contra sí mismo."""
        self._autenticado()

        resp = self.client.put('/api/auth/perfil/', self._datos_validos())

        self.assertEqual(resp.status_code, 200)

    def test_sube_una_foto_de_perfil_valida(self):
        self._autenticado()

        resp = self.client.put('/api/auth/perfil/', self._datos_validos(foto_perfil=_imagen_de_prueba()), format='multipart')

        self.assertEqual(resp.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertTrue(bool(self.usuario.foto_perfil))


class RecuperarApiTests(APITestCase):
    """`POST /api/auth/recuperar/` + `/confirmar/<token>/` — espeja RecuperarPasswordTests (tests.py)."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('recuperar_api@test.com', 'claveoriginal1', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.usuario.telefono = 912345678
        self.usuario.save(update_fields=['telefono'])

    def tearDown(self):
        cache.clear()

    def test_solicitud_con_datos_correctos_manda_un_correo_con_link_al_frontend_ionic(self):
        from django.conf import settings
        from django.core import mail

        resp = self.client.post('/api/auth/recuperar/', {'email': self.usuario.email, 'telefono': self.usuario.telefono}, format='json')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.usuario.email, mail.outbox[0].to)
        self.assertIn(f'{settings.IONIC_FRONTEND_URL}/recuperar/confirmar/', mail.outbox[0].body)

    def test_mensaje_es_igual_exista_o_no_la_cuenta(self):
        resp_real = self.client.post('/api/auth/recuperar/', {'email': self.usuario.email, 'telefono': self.usuario.telefono}, format='json')
        resp_falso = self.client.post('/api/auth/recuperar/', {'email': 'nadie_api@test.com', 'telefono': 111111111}, format='json')
        self.assertEqual(resp_real.data, resp_falso.data)

    def test_limite_de_intentos(self):
        from django.core import mail

        for _ in range(3):
            self.client.post('/api/auth/recuperar/', {'email': self.usuario.email, 'telefono': self.usuario.telefono}, format='json')
        mail.outbox.clear()

        resp = self.client.post('/api/auth/recuperar/', {'email': self.usuario.email, 'telefono': self.usuario.telefono}, format='json')

        self.assertEqual(resp.status_code, 429)
        self.assertEqual(len(mail.outbox), 0)

    def test_get_confirmar_con_token_valido(self):
        token = _generar_token_recuperacion(self.usuario)
        resp = self.client.get(f'/api/auth/recuperar/confirmar/{token}/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['valido'])

    def test_get_confirmar_con_token_invalido_devuelve_404(self):
        resp = self.client.get('/api/auth/recuperar/confirmar/token-inventado/')
        self.assertEqual(resp.status_code, 404)

    def test_post_confirmar_con_token_valido_cambia_la_contrasena(self):
        token = _generar_token_recuperacion(self.usuario)

        resp = self.client.post(f'/api/auth/recuperar/confirmar/{token}/', {
            'password': 'ClaveNueva2026!', 'password_confirm': 'ClaveNueva2026!',
        }, format='json')

        self.assertEqual(resp.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('ClaveNueva2026!'))

    def test_token_ya_usado_no_sirve_dos_veces(self):
        """Cambiar la contraseña rota el hash embebido en el token — el mismo link no debería servir dos veces."""
        token = _generar_token_recuperacion(self.usuario)
        self.client.post(f'/api/auth/recuperar/confirmar/{token}/', {
            'password': 'ClaveNueva2026!', 'password_confirm': 'ClaveNueva2026!',
        }, format='json')

        resp = self.client.get(f'/api/auth/recuperar/confirmar/{token}/')

        self.assertEqual(resp.status_code, 404)
