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
from .models import IntentoAccesoSospechoso, TokenSesion
from .tests import _crear_region_comuna_tipo, _crear_usuario


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
