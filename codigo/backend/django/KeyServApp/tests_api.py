"""
Tests de la API REST — separado de `KeyServApp/tests.py` a propósito
mientras dura la migración (Fase 1 del plan): las vistas basadas en
templates y las de la API van a coexistir varias fases, y mezclar ambos
mundos en un solo archivo gigante habría sido más fricción de merge que
seguridad extra. Cada escenario acá espeja uno ya cubierto en
`LoginViewTests` (tests.py) para la ruta equivalente `/api/auth/`.
"""
from unittest import mock

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from .api import jwt_utils
from .models import (
    Comuna, Consulta, Contratacion, Documento, EstadoDocumento, HistorialEstadoContratacion,
    IntentoAccesoSospechoso, ItemPresupuesto, Mensaje, Pago, Publicaciones, Ranking, Region, TokenSesion,
    Usuario, Valoracion, ValoracionImagen,
)
from .tests import _crear_region_comuna_tipo, _crear_usuario, _frames_prueba_de_vida, _imagen_de_prueba, _marcar_en_curso
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


class JWTAuthenticationTokenVencidoTests(APITestCase):
    """
    Regresión: un token vencido/inválido ya no debe bloquear la request con
    un 401 duro (`AuthenticationFailed`) — debe tratarse como "sin
    credenciales" (`AnonymousUser`), dejando que cada vista decida según
    su propio `permission_classes`. Encontrado probando `/api/contacto/`
    a mano: `authInterceptor` (Ionic) adjunta el access token guardado a
    *toda* request hacia la API, incluido `/api/auth/login/` — con el
    comportamiento viejo, una sesión vencida en el navegador dejaba a
    cualquiera sin forma de volver a loguearse (el login mismo devolvía
    401 antes de mirar el email/password del body).
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('vencido@test.com', 'ClaveOk123!', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)

    def _token_vencido(self):
        from datetime import timedelta

        import jwt as pyjwt
        from django.conf import settings
        from django.utils import timezone
        return pyjwt.encode(
            {'sub': str(self.usuario.id_usuario), 'iat': timezone.now() - timedelta(minutes=40), 'exp': timezone.now() - timedelta(minutes=20)},
            settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM,
        )

    def test_token_vencido_no_bloquea_login_allowany(self):
        # Antes del fix, este 401-eaba antes de siquiera validar el email/password.
        resp = self.client.post(
            '/api/auth/login/', {'email': 'vencido@test.com', 'password': 'ClaveOk123!'}, format='json',
            HTTP_AUTHORIZATION=f'Bearer {self._token_vencido()}',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access_token', resp.data)

    def test_token_vencido_no_bloquea_publicaciones_allowany(self):
        resp = self.client.get('/api/publicaciones/', HTTP_AUTHORIZATION=f'Bearer {self._token_vencido()}')
        self.assertEqual(resp.status_code, 200)

    def test_token_vencido_en_endpoint_protegido_sigue_devolviendo_401(self):
        resp = self.client.get('/api/auth/me/', HTTP_AUTHORIZATION=f'Bearer {self._token_vencido()}')
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


class PublicacionCrearApiTests(APITestCase):
    """`POST /api/publicaciones/crear/` — espeja PublicacionCrearViewTests (tests.py) sobre la ruta de la API."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor_crea_api@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente_no_proveedor_api@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)

    def _autenticado_como(self, usuario):
        token = jwt_utils.generar_access_token(usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def _datos_validos(self, **overrides):
        datos = {
            'titulo': 'Gasfitería a domicilio', 'sub_titulo': 'Reparaciones rápidas',
            'descripcion_publicacion': 'Reparo filtraciones y cambio artefactos.',
            'categoria': 'Gasfitería', 'precio': 25000,
        }
        datos.update(overrides)
        return datos

    def test_proveedor_crea_publicacion_exitosamente(self):
        self._autenticado_como(self.proveedor)

        resp = self.client.post('/api/publicaciones/crear/', self._datos_validos(), format='json')

        self.assertEqual(resp.status_code, 201)
        publicacion = Publicaciones.objects.get(titulo='Gasfitería a domicilio')
        self.assertEqual(publicacion.usuario_publicador, self.proveedor)
        self.assertEqual(publicacion.estado_moderacion, Publicaciones.PENDIENTE)
        self.assertEqual(resp.data['publicacion']['titulo'], 'Gasfitería a domicilio')

    def test_no_proveedor_no_puede_publicar(self):
        self._autenticado_como(self.cliente)

        resp = self.client.post('/api/publicaciones/crear/', self._datos_validos(), format='json')

        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Publicaciones.objects.filter(titulo='Gasfitería a domicilio').exists())

    def test_sin_token_devuelve_401(self):
        resp = self.client.post('/api/publicaciones/crear/', self._datos_validos(), format='json')
        self.assertEqual(resp.status_code, 401)

    def test_categoria_otra_usa_el_texto_libre(self):
        self._autenticado_como(self.proveedor)

        resp = self.client.post('/api/publicaciones/crear/', self._datos_validos(categoria='Otra', categoria_otra='Paisajismo'), format='json')

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Publicaciones.objects.get(titulo='Gasfitería a domicilio').categoria, 'Paisajismo')

    def test_titulo_vacio_devuelve_400(self):
        self._autenticado_como(self.proveedor)

        resp = self.client.post('/api/publicaciones/crear/', self._datos_validos(titulo=''), format='json')

        self.assertEqual(resp.status_code, 400)

    def test_sube_imagenes_validas(self):
        self._autenticado_como(self.proveedor)

        datos = self._datos_validos()
        datos['imagenes'] = [_imagen_de_prueba()]
        resp = self.client.post('/api/publicaciones/crear/', datos, format='multipart')

        self.assertEqual(resp.status_code, 201)
        publicacion = Publicaciones.objects.get(titulo='Gasfitería a domicilio')
        self.assertEqual(publicacion.imagenes.count(), 1)
        self.assertEqual(resp.data['imagenes_rechazadas'], [])


class MisPublicacionesApiTests(APITestCase):
    """`GET /api/publicaciones/mias/` — solo publicaciones propias, con cualquier estado_moderacion."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('mias_api@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.otro_proveedor = _crear_usuario('otro_mias_api@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        token = jwt_utils.generar_access_token(self.proveedor)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_sin_token_devuelve_401(self):
        self.client.credentials()
        resp = self.client.get('/api/publicaciones/mias/')
        self.assertEqual(resp.status_code, 401)

    def test_incluye_pendientes_y_rechazadas_propias(self):
        Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Pendiente', estado_moderacion=Publicaciones.PENDIENTE)
        Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Rechazada', estado_moderacion=Publicaciones.RECHAZADA)

        resp = self.client.get('/api/publicaciones/mias/')

        self.assertEqual(resp.status_code, 200)
        titulos = {p['titulo'] for p in resp.data}
        self.assertEqual(titulos, {'Pendiente', 'Rechazada'})

    def test_no_incluye_publicaciones_de_otro_usuario(self):
        Publicaciones.objects.create(usuario_publicador=self.otro_proveedor, titulo='No es mía', estado_moderacion=Publicaciones.APROBADA)

        resp = self.client.get('/api/publicaciones/mias/')

        self.assertEqual(resp.data, [])


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


class ContactoApiTests(APITestCase):
    """`POST /api/contacto/` — equivalente API de `contacto_view` (views.py), no existe un ContactoViewTests del lado template para espejar."""

    def test_anonimo_con_datos_de_contacto_crea_consulta_abierta(self):
        resp = self.client.post('/api/contacto/', {
            'asunto_consulta': 'No puedo pagar', 'descripcion': 'El botón de Webpay no responde.',
            'nombre_contacto': 'Alguien', 'email_contacto': 'alguien@test.com',
        }, format='json')

        self.assertEqual(resp.status_code, 201)
        consulta = Consulta.objects.get(asunto_consulta='No puedo pagar')
        self.assertIsNone(consulta.usuario_consulta)
        self.assertEqual(consulta.nombre_contacto, 'Alguien')
        self.assertEqual(consulta.estado_consulta_id, 1)  # 1 = Abierta

    def test_anonimo_sin_datos_de_contacto_devuelve_400(self):
        resp = self.client.post('/api/contacto/', {
            'asunto_consulta': 'No puedo pagar', 'descripcion': 'El botón de Webpay no responde.',
        }, format='json')

        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Consulta.objects.filter(asunto_consulta='No puedo pagar').exists())

    def test_autenticado_usa_sus_propios_datos_de_contacto(self):
        region, comuna, tipo_cuenta = _crear_region_comuna_tipo()
        usuario = _crear_usuario('con_sesion@test.com', comuna=comuna, tipo_cuenta=tipo_cuenta)
        token = jwt_utils.generar_access_token(usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        resp = self.client.post('/api/contacto/', {
            'asunto_consulta': 'Duda sobre una reseña', 'descripcion': 'Quiero editar mi calificación.',
        }, format='json')

        self.assertEqual(resp.status_code, 201)
        consulta = Consulta.objects.get(asunto_consulta='Duda sobre una reseña')
        self.assertEqual(consulta.usuario_consulta, usuario)
        self.assertEqual(consulta.email_contacto, usuario.email)


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

    def test_categorias_no_requiere_token(self):
        resp = self.client.get('/api/catalogos/categorias/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Gasfitería', resp.data)


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


class PerfilProveedorApiTests(APITestCase):
    """`PUT /api/auth/perfil-proveedor/` + documentos — espeja CrearPerfilTests (tests.py), mismos escenarios contra la ruta de la API."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        EstadoDocumento.objects.get_or_create(id_estado_documento=2, defaults={'nombre_estado_documento': 'No firmado'})
        self.proveedor = _crear_usuario('proveedor_api_perfil@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.access_token = jwt_utils.generar_access_token(self.proveedor)

    def _autenticado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_sin_token_devuelve_401(self):
        resp = self.client.put('/api/auth/perfil-proveedor/', {'areas_servicio': ['Gasfitería']})
        self.assertEqual(resp.status_code, 401)

    def test_guarda_areas_de_servicio_y_experiencia(self):
        self._autenticado()

        resp = self.client.put('/api/auth/perfil-proveedor/', {
            'areas_servicio': ['Gasfitería', 'Electricidad'],
            'experiencia': '10 años reparando cañerías y tableros eléctricos.',
        }, format='multipart')

        self.assertEqual(resp.status_code, 200)
        self.proveedor.refresh_from_db()
        self.assertEqual(self.proveedor.areas_servicio, 'Gasfitería, Electricidad')
        self.assertIn('10 años', self.proveedor.experiencia)

    def test_agrega_un_area_libre_no_predefinida(self):
        self._autenticado()

        resp = self.client.put('/api/auth/perfil-proveedor/', {
            'areas_servicio': ['Gasfitería'], 'otra_area_servicio': 'Reparación de piscinas',
        }, format='multipart')

        self.assertEqual(resp.status_code, 200)
        self.proveedor.refresh_from_db()
        self.assertEqual(self.proveedor.areas_servicio, 'Gasfitería, Reparación de piscinas')

    def test_sube_un_certificado_valido(self):
        self._autenticado()
        pdf = SimpleUploadedFile('certificado.pdf', b'%PDF-1.4 contenido de prueba', content_type='application/pdf')

        resp = self.client.put('/api/auth/perfil-proveedor/', {
            'areas_servicio': ['Gasfitería'], 'documentos': [pdf],
        }, format='multipart')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['documentos_rechazados'], [])
        documentos = Documento.objects.filter(usuario=self.proveedor, publicacion__isnull=True)
        self.assertEqual(documentos.count(), 1)
        self.assertEqual(documentos.first().nombre_documento, 'certificado.pdf')

    def test_certificado_disfrazado_se_rechaza_pero_el_resto_del_perfil_se_guarda(self):
        self._autenticado()
        falso = SimpleUploadedFile('script.pdf', b'<script>alert(1)</script>', content_type='application/pdf')

        resp = self.client.put('/api/auth/perfil-proveedor/', {
            'areas_servicio': ['Gasfitería'], 'documentos': [falso],
        }, format='multipart')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['documentos_rechazados'], ['script.pdf'])
        self.assertEqual(Documento.objects.filter(usuario=self.proveedor).count(), 0)
        self.proveedor.refresh_from_db()
        self.assertEqual(self.proveedor.areas_servicio, 'Gasfitería')

    def test_lista_los_certificados_ya_subidos(self):
        Documento.objects.create(
            usuario=self.proveedor, nombre_documento='certificado.pdf',
            archivo_subido=SimpleUploadedFile('certificado.pdf', b'%PDF-1.4 x', content_type='application/pdf'),
        )
        self._autenticado()

        resp = self.client.get('/api/auth/perfil-proveedor/documentos/')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['nombre_documento'], 'certificado.pdf')

    def test_puede_eliminar_su_propio_certificado(self):
        documento = Documento.objects.create(
            usuario=self.proveedor, nombre_documento='certificado.pdf',
            archivo_subido=SimpleUploadedFile('certificado.pdf', b'%PDF-1.4 x', content_type='application/pdf'),
        )
        self._autenticado()

        resp = self.client.delete(f'/api/auth/perfil-proveedor/documentos/{documento.id_documento}/')

        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Documento.objects.filter(pk=documento.id_documento).exists())

    def test_no_puede_eliminar_el_certificado_de_otro_proveedor(self):
        otro_proveedor = _crear_usuario('otro_proveedor_api_doc@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        documento = Documento.objects.create(
            usuario=otro_proveedor, nombre_documento='certificado.pdf',
            archivo_subido=SimpleUploadedFile('certificado.pdf', b'%PDF-1.4 x', content_type='application/pdf'),
        )
        self._autenticado()

        resp = self.client.delete(f'/api/auth/perfil-proveedor/documentos/{documento.id_documento}/')

        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Documento.objects.filter(pk=documento.id_documento).exists())


class PreferenciasApiTests(APITestCase):
    """`PUT /api/auth/preferencias/` + `POST /api/auth/cambiar-password/` — espeja PreferenciasCuentaTests (tests.py)."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('preferencias_api@test.com', 'clave_actual', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.access_token = jwt_utils.generar_access_token(self.usuario)

    def _autenticado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_desactivar_notificaciones_de_sonido(self):
        self._autenticado()

        resp = self.client.put('/api/auth/preferencias/', {'notificaciones_sonido': False}, format='json')

        self.assertEqual(resp.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.notificaciones_sonido)

    def test_cambiar_password_sin_token_devuelve_401(self):
        resp = self.client.post('/api/auth/cambiar-password/', {
            'password_actual': 'clave_actual', 'password': 'ClaveNueva123', 'password_confirm': 'ClaveNueva123',
        }, format='json')
        self.assertEqual(resp.status_code, 401)

    def test_cambiar_password_con_la_actual_correcta(self):
        self._autenticado()

        resp = self.client.post('/api/auth/cambiar-password/', {
            'password_actual': 'clave_actual', 'password': 'ClaveNueva123', 'password_confirm': 'ClaveNueva123',
        }, format='json')

        self.assertEqual(resp.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('ClaveNueva123'))

    def test_cambiar_password_con_la_actual_incorrecta_no_cambia_nada(self):
        self._autenticado()

        resp = self.client.post('/api/auth/cambiar-password/', {
            'password_actual': 'clave-equivocada', 'password': 'ClaveNueva123', 'password_confirm': 'ClaveNueva123',
        }, format='json')

        self.assertEqual(resp.status_code, 400)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('clave_actual'))


class ContratacionApiTests(APITestCase):
    """`GET`/`POST /api/contrataciones/` — espeja ContratacionFlowTests/MensajeriaTests (tests.py, la parte de "solicitar")."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor_api_c@test.com', 'clave_prov', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente_api_c@test.com', 'clave_cli', es_proveedor=False, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Electricidad', estado_moderacion=Publicaciones.APROBADA, precio=15000)

    def _autenticado_como(self, usuario):
        token = jwt_utils.generar_access_token(usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_sin_token_devuelve_401(self):
        resp = self.client.get('/api/contrataciones/')
        self.assertEqual(resp.status_code, 401)

    def test_solicitar_crea_contratacion_y_notifica_por_chat(self):
        self._autenticado_como(self.cliente)

        resp = self.client.post('/api/contrataciones/', {'publicacion': self.publicacion.id_publicacion}, format='json')

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['estado'], Contratacion.SOLICITADA)
        contratacion = Contratacion.objects.get(publicacion=self.publicacion)
        self.assertEqual(contratacion.cliente, self.cliente)
        mensaje = Mensaje.objects.get(conversacion=contratacion.conversacion)
        self.assertIn('Electricidad', mensaje.contenido)
        self.assertEqual(mensaje.usuario, self.cliente)

    def test_no_se_puede_contratar_la_propia_publicacion(self):
        self._autenticado_como(self.proveedor)
        resp = self.client.post('/api/contrataciones/', {'publicacion': self.publicacion.id_publicacion}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Contratacion.objects.filter(publicacion=self.publicacion).exists())

    def test_no_se_puede_recontratar_mientras_hay_una_solicitud_activa(self):
        self._autenticado_como(self.cliente)
        self.client.post('/api/contrataciones/', {'publicacion': self.publicacion.id_publicacion}, format='json')
        resp = self.client.post('/api/contrataciones/', {'publicacion': self.publicacion.id_publicacion}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Contratacion.objects.filter(publicacion=self.publicacion, cliente=self.cliente).count(), 1)

    def test_listado_incluye_las_del_cliente_y_las_del_proveedor(self):
        Contratacion.objects.create(publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor)

        self._autenticado_como(self.cliente)
        resp_cliente = self.client.get('/api/contrataciones/')
        self.assertEqual(len(resp_cliente.data), 1)

        self._autenticado_como(self.proveedor)
        resp_proveedor = self.client.get('/api/contrataciones/')
        self.assertEqual(len(resp_proveedor.data), 1)

        otro = _crear_usuario('otro_api_c@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self._autenticado_como(otro)
        resp_otro = self.client.get('/api/contrataciones/')
        self.assertEqual(len(resp_otro.data), 0)


class ContratacionDetalleMensajesApiTests(APITestCase):
    """`GET /api/contrataciones/<id>/` + `GET`/`POST /api/contrataciones/<id>/mensajes/` — espeja la parte de detalle+chat de `contratacion_detalle_view` y el control de acceso de `MensajeriaTests`/`IntentoAccesoSospechosoTests`."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor_api_d@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente_api_d@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.intruso = _crear_usuario('intruso_api_d@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Pintura', estado_moderacion=Publicaciones.APROBADA)
        self.contratacion = Contratacion.objects.create(publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor)

    def _autenticado_como(self, usuario):
        token = jwt_utils.generar_access_token(usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_detalle_visible_para_cliente_y_proveedor(self):
        self._autenticado_como(self.cliente)
        self.assertEqual(self.client.get(f'/api/contrataciones/{self.contratacion.id_contratacion}/').status_code, 200)
        self._autenticado_como(self.proveedor)
        self.assertEqual(self.client.get(f'/api/contrataciones/{self.contratacion.id_contratacion}/').status_code, 200)

    def test_detalle_ajeno_devuelve_404_y_queda_registrado(self):
        self._autenticado_como(self.intruso)
        resp = self.client.get(f'/api/contrataciones/{self.contratacion.id_contratacion}/')
        self.assertEqual(resp.status_code, 404)
        intento = IntentoAccesoSospechoso.objects.get(recurso='contratacion', recurso_id=str(self.contratacion.id_contratacion))
        self.assertEqual(intento.usuario, self.intruso)

    def test_enviar_mensaje_y_listarlo(self):
        self._autenticado_como(self.cliente)
        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/mensajes/', {'contenido': 'Hola, ¿seguís disponible?'}, format='json')
        self.assertEqual(resp.status_code, 201)

        self._autenticado_como(self.proveedor)
        resp_lista = self.client.get(f'/api/contrataciones/{self.contratacion.id_contratacion}/mensajes/')
        self.assertEqual(len(resp_lista.data), 1)
        self.assertEqual(resp_lista.data[0]['contenido'], 'Hola, ¿seguís disponible?')

    def test_mensajes_ajenos_devuelve_404(self):
        self._autenticado_como(self.intruso)
        resp = self.client.get(f'/api/contrataciones/{self.contratacion.id_contratacion}/mensajes/')
        self.assertEqual(resp.status_code, 404)


class ContratacionConfirmarCompletarApiTests(APITestCase):
    """`POST /api/contrataciones/<id>/confirmar/` y `/completar/` — espeja ContratacionFlowTests/MontoAcordadoConfirmarTests/ItemPresupuestoTests (tests.py)."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor_api_cc@test.com', 'clave_prov', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente_api_cc@test.com', 'clave_cli', es_proveedor=False, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Gasfitería', estado_moderacion=Publicaciones.APROBADA, precio=15000)
        self.contratacion = Contratacion.objects.create(publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor, estado=Contratacion.SOLICITADA)

    def tearDown(self):
        cache.clear()

    def _autenticado_como(self, usuario):
        token = jwt_utils.generar_access_token(usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_confirmar_sin_monto_usa_el_precio_de_la_publicacion(self):
        self._autenticado_como(self.proveedor)
        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/confirmar/', {'password': 'clave_prov'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.estado, Contratacion.CONFIRMADA)
        self.assertEqual(self.contratacion.monto_acordado, 15000)

    def test_confirmar_permite_ajustar_el_monto_acordado(self):
        self._autenticado_como(self.proveedor)
        self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/confirmar/', {'password': 'clave_prov', 'monto': 20000}, format='json')
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.monto_acordado, 20000)

    def test_confirmar_con_items_suma_el_monto_acordado_e_ignora_el_monto_unico(self):
        self._autenticado_como(self.proveedor)
        self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/confirmar/', {
            'password': 'clave_prov', 'monto': 99999,
            'items': [
                {'descripcion': 'Cañería PVC', 'categoria': ItemPresupuesto.MATERIAL, 'monto': 8000},
                {'descripcion': 'Mano de obra', 'categoria': ItemPresupuesto.MANO_DE_OBRA, 'monto': 12000},
            ],
        }, format='json')
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.monto_acordado, 20000)
        items = list(self.contratacion.items_presupuesto.all())
        self.assertEqual([item.descripcion for item in items], ['Cañería PVC', 'Mano de obra'])

    def test_confirmar_con_password_incorrecta_no_avanza_estado(self):
        self._autenticado_como(self.proveedor)
        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/confirmar/', {'password': 'mala'}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.estado, Contratacion.SOLICITADA)

    def test_solo_el_proveedor_puede_confirmar(self):
        self._autenticado_como(self.cliente)
        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/confirmar/', {'password': 'clave_cli'}, format='json')
        self.assertEqual(resp.status_code, 403)
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.estado, Contratacion.SOLICITADA)

    def test_reautenticacion_se_bloquea_tras_varios_intentos_fallidos(self):
        self._autenticado_como(self.proveedor)
        for _ in range(5):
            self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/confirmar/', {'password': 'mala'}, format='json')

        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/confirmar/', {'password': 'clave_prov'}, format='json')
        self.assertEqual(resp.status_code, 429)
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.estado, Contratacion.SOLICITADA)

    def test_completar_avanza_a_completada(self):
        _marcar_en_curso(self.contratacion)
        self._autenticado_como(self.cliente)
        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/completar/', {'password': 'clave_cli'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.estado, Contratacion.COMPLETADA)

    def test_solo_el_cliente_puede_completar(self):
        _marcar_en_curso(self.contratacion)
        self._autenticado_como(self.proveedor)
        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/completar/', {'password': 'clave_prov'}, format='json')
        self.assertEqual(resp.status_code, 403)
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.estado, Contratacion.EN_CURSO)

    def test_no_se_puede_completar_sin_pasar_por_en_curso(self):
        """CONFIRMADA -> COMPLETADA directo no está permitido, hace falta el pago (EN_CURSO) en el medio."""
        self.contratacion.estado = Contratacion.CONFIRMADA
        self.contratacion.save()
        self._autenticado_como(self.cliente)
        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/completar/', {'password': 'clave_cli'}, format='json')
        self.assertEqual(resp.status_code, 404)


class ValoracionApiTests(APITestCase):
    """`POST /api/contrataciones/<id>/valoracion/` — espeja la parte de valoración de `ContratacionFlowTests`."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor_api_v@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente_api_v@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Carpintería', estado_moderacion=Publicaciones.APROBADA)
        self.contratacion = Contratacion.objects.create(
            publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor, estado=Contratacion.COMPLETADA,
        )

    def _autenticado_como(self, usuario):
        token = jwt_utils.generar_access_token(usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_valorar_crea_una_resena_pendiente_y_no_cuenta_para_el_ranking_todavia(self):
        self._autenticado_como(self.cliente)

        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/valoracion/', {
            'puntuacion': 5, 'comentario': 'Excelente',
        }, format='json')

        self.assertEqual(resp.status_code, 201)
        valoracion = Valoracion.objects.get(usuario_receptor=self.proveedor, puntuacion=5)
        self.assertEqual(valoracion.estado_moderacion, Valoracion.PENDIENTE)
        self.assertEqual(Ranking.objects.get(usuario=self.proveedor).total_valoraciones, 0)

    def test_solo_el_cliente_puede_valorar(self):
        self._autenticado_como(self.proveedor)
        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/valoracion/', {'puntuacion': 5, 'comentario': 'x'}, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_no_se_puede_valorar_dos_veces(self):
        self._autenticado_como(self.cliente)
        self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/valoracion/', {'puntuacion': 5, 'comentario': 'x'}, format='json')
        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/valoracion/', {'puntuacion': 1, 'comentario': 'y'}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Valoracion.objects.filter(contratacion=self.contratacion).count(), 1)

    def test_foto_valida_queda_pendiente_de_moderacion(self):
        self._autenticado_como(self.cliente)

        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/valoracion/', {
            'puntuacion': 4, 'comentario': 'Bien', 'imagenes': [_imagen_de_prueba()],
        }, format='multipart')

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['imagenes_rechazadas'], [])
        imagen = ValoracionImagen.objects.get(valoracion__contratacion=self.contratacion)
        self.assertEqual(imagen.estado_moderacion, ValoracionImagen.PENDIENTE)


class PagoApiTests(APITestCase):
    """`/api/contrataciones/<id>/pagos/*` + `/api/pagos/webpay/confirmar/` — espeja `PagoTests` (tests.py), mismos escenarios contra la ruta de la API. `TransbankService`/`KhipuService` mockeados igual que el lado template."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor_pago_api@test.com', 'clave_prov', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente_pago_api@test.com', 'clave_cli', es_proveedor=False, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(
            usuario_publicador=self.proveedor, titulo='Gasfitería', estado_moderacion=Publicaciones.APROBADA, precio=15000,
        )
        self.contratacion = Contratacion.objects.create(
            publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor,
            estado=Contratacion.CONFIRMADA, monto_acordado=15000,
        )

    def _autenticado_como(self, usuario):
        token = jwt_utils.generar_access_token(usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_webpay_iniciar_crea_pago_pendiente(self):
        self._autenticado_como(self.cliente)
        with mock.patch('KeyServApp.pagos.TransbankService.iniciar_transaccion', return_value=('tok123', 'https://webpay.test/init')):
            resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/pagos/webpay/iniciar/')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['token'], 'tok123')
        self.assertEqual(resp.data['url_pago'], 'https://webpay.test/init')
        pago = Pago.objects.get(contratacion=self.contratacion)
        self.assertEqual(pago.metodo, Pago.WEBPAY)
        self.assertEqual(pago.estado, Pago.PENDIENTE)
        self.assertEqual(pago.token_webpay, 'tok123')

    def test_solo_el_cliente_puede_iniciar_el_pago(self):
        self._autenticado_como(self.proveedor)
        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/pagos/webpay/iniciar/')
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Pago.objects.filter(contratacion=self.contratacion).exists())
        self.assertTrue(IntentoAccesoSospechoso.objects.filter(recurso='pago_iniciar').exists())

    def test_no_se_puede_pagar_sin_monto_acordado(self):
        self.contratacion.monto_acordado = None
        self.contratacion.save(update_fields=['monto_acordado'])
        self._autenticado_como(self.cliente)
        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/pagos/webpay/iniciar/')
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Pago.objects.filter(contratacion=self.contratacion).exists())

    def test_webpay_confirmar_aprobado_pasa_contratacion_a_en_curso(self):
        pago = Pago.objects.create(contratacion=self.contratacion, monto=15000, metodo=Pago.WEBPAY, token_webpay='tok123')
        respuesta_aprobada = {'response_code': 0, 'status': 'AUTHORIZED', 'authorization_code': 'AUTH1'}
        with mock.patch('KeyServApp.pagos.TransbankService.confirmar_transaccion', return_value=respuesta_aprobada):
            resp = self.client.post('/api/pagos/webpay/confirmar/', {'token_ws': 'tok123'}, format='json')

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['aprobado'])
        pago.refresh_from_db()
        self.contratacion.refresh_from_db()
        self.assertEqual(pago.estado, Pago.PAGADO)
        self.assertEqual(self.contratacion.estado, Contratacion.EN_CURSO)
        self.assertTrue(HistorialEstadoContratacion.objects.filter(contratacion=self.contratacion, estado=Contratacion.EN_CURSO).exists())

    def test_webpay_confirmar_rechazado_no_avanza_la_contratacion(self):
        pago = Pago.objects.create(contratacion=self.contratacion, monto=15000, metodo=Pago.WEBPAY, token_webpay='tok123')
        respuesta_rechazada = {'response_code': 1, 'status': 'FAILED'}
        with mock.patch('KeyServApp.pagos.TransbankService.confirmar_transaccion', return_value=respuesta_rechazada):
            resp = self.client.post('/api/pagos/webpay/confirmar/', {'token_ws': 'tok123'}, format='json')

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['aprobado'])
        pago.refresh_from_db()
        self.contratacion.refresh_from_db()
        self.assertEqual(pago.estado, Pago.RECHAZADO)
        self.assertEqual(self.contratacion.estado, Contratacion.CONFIRMADA)

    def test_webpay_cancelado_por_el_usuario_queda_anulado(self):
        pago = Pago.objects.create(contratacion=self.contratacion, monto=15000, metodo=Pago.WEBPAY, token_webpay='tok123')
        resp = self.client.post('/api/pagos/webpay/confirmar/', {'TBK_TOKEN': 'tok123'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['aprobado'])
        pago.refresh_from_db()
        self.assertEqual(pago.estado, Pago.ANULADO)

    def test_webpay_confirmar_no_requiere_token(self):
        """Igual que la vista de template — Transbank redirige acá sin ningún JWT nuestro."""
        resp = self.client.post('/api/pagos/webpay/confirmar/', {'TBK_TOKEN': 'no-existe'}, format='json')
        self.assertEqual(resp.status_code, 200)

    def test_khipu_iniciar_sin_api_key_da_error_claro(self):
        self._autenticado_como(self.cliente)
        resp = self.client.post(f'/api/contrataciones/{self.contratacion.id_contratacion}/pagos/khipu/iniciar/')
        self.assertEqual(resp.status_code, 503)
        self.assertIn('KHIPU_API_KEY', resp.data['detail'])

    def test_khipu_estado_reconsulta_y_marca_pagado(self):
        pago = Pago.objects.create(contratacion=self.contratacion, monto=15000, metodo=Pago.KHIPU, khipu_payment_id='pay123')
        self._autenticado_como(self.cliente)
        with mock.patch('KeyServApp.pagos.KhipuService.consultar_pago', return_value={'status': 'done', 'payment_id': 'pay123'}):
            resp = self.client.get(f'/api/contrataciones/{self.contratacion.id_contratacion}/pagos/khipu/estado/')

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['aprobado'])
        pago.refresh_from_db()
        self.contratacion.refresh_from_db()
        self.assertEqual(pago.estado, Pago.PAGADO)
        self.assertEqual(self.contratacion.estado, Contratacion.EN_CURSO)

    def test_khipu_estado_no_marca_pagado_si_todavia_pendiente(self):
        Pago.objects.create(contratacion=self.contratacion, monto=15000, metodo=Pago.KHIPU, khipu_payment_id='pay123')
        self._autenticado_como(self.cliente)
        with mock.patch('KeyServApp.pagos.KhipuService.consultar_pago', return_value={'status': 'pending', 'payment_id': 'pay123'}):
            resp = self.client.get(f'/api/contrataciones/{self.contratacion.id_contratacion}/pagos/khipu/estado/')

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['aprobado'])

    def test_khipu_estado_ajeno_devuelve_404(self):
        Pago.objects.create(contratacion=self.contratacion, monto=15000, metodo=Pago.KHIPU, khipu_payment_id='pay123')
        intruso = _crear_usuario('intruso_pago_api@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self._autenticado_como(intruso)
        resp = self.client.get(f'/api/contrataciones/{self.contratacion.id_contratacion}/pagos/khipu/estado/')
        self.assertEqual(resp.status_code, 404)

    def test_detalle_incluye_el_pago(self):
        Pago.objects.create(contratacion=self.contratacion, monto=15000, metodo=Pago.WEBPAY, estado=Pago.PAGADO)
        self._autenticado_como(self.cliente)
        resp = self.client.get(f'/api/contrataciones/{self.contratacion.id_contratacion}/')
        self.assertEqual(resp.data['pago']['metodo'], Pago.WEBPAY)
        self.assertEqual(resp.data['pago']['estado'], Pago.PAGADO)


class VerificarBiometriaNativaApiTests(APITestCase):
    """`POST /api/auth/verificar-biometria-nativa/` — Fase 5 del plan de migración (biometría nativa vía Capacitor, en vez del reconocimiento facial/huella pesados del servidor)."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('biometria_nativa_api@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)

    def test_sin_token_devuelve_401(self):
        resp = self.client.post('/api/auth/verificar-biometria-nativa/')
        self.assertEqual(resp.status_code, 401)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.verificado_biometricamente)

    def test_con_token_marca_verificado(self):
        token = jwt_utils.generar_access_token(self.usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        resp = self.client.post('/api/auth/verificar-biometria-nativa/')

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['verificado_biometricamente'])
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.verificado_biometricamente)


class RostroApiTests(APITestCase):
    """`/api/auth/rostro/*` — espeja `ReconocimientoFacialTests` (tests.py). `biometria.calcular_encoding_facial`/`verificar_rostro_usuario` mockeados, mismo criterio que el resto del proyecto (ver esa clase para el porqué)."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('rostro_api@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.access_token = jwt_utils.generar_access_token(self.usuario)

    def _autenticado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_estado_sin_referencia(self):
        self._autenticado()
        resp = self.client.get('/api/auth/rostro/estado/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['tiene_referencia'])

    def test_estado_con_referencia_no_expone_el_encoding(self):
        self.usuario.encoding_facial = [0.1] * 128
        self.usuario.save()
        self._autenticado()
        resp = self.client.get('/api/auth/rostro/estado/')
        self.assertTrue(resp.data['tiene_referencia'])
        self.assertNotIn('encoding_facial', resp.data)

    def test_registrar_sin_token_devuelve_401(self):
        resp = self.client.post('/api/auth/rostro/registrar/', _frames_prueba_de_vida(), format='multipart')
        self.assertEqual(resp.status_code, 401)

    def test_registrar_con_captura_incompleta_no_guarda_nada(self):
        self._autenticado()
        frames = _frames_prueba_de_vida(cantidad=2)  # menos que _FRAMES_MINIMOS_CAPTURA
        with mock.patch('KeyServApp.biometria.calcular_encoding_facial', return_value=[0.1] * 128) as calcular:
            resp = self.client.post('/api/auth/rostro/registrar/', frames, format='multipart')
            calcular.assert_not_called()
        self.assertEqual(resp.status_code, 400)
        self.usuario.refresh_from_db()
        self.assertIsNone(self.usuario.encoding_facial)

    def test_registrar_con_encoding_calculado_lo_guarda(self):
        encoding_falso = [0.1] * 128
        self._autenticado()
        with mock.patch('KeyServApp.biometria.calcular_encoding_facial', return_value=encoding_falso):
            resp = self.client.post('/api/auth/rostro/registrar/', _frames_prueba_de_vida(), format='multipart')
        self.assertEqual(resp.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.encoding_facial, encoding_falso)

    def test_registrar_sin_prueba_de_vida_valida_no_guarda_nada(self):
        self._autenticado()
        with mock.patch('KeyServApp.biometria.calcular_encoding_facial', return_value=None):
            resp = self.client.post('/api/auth/rostro/registrar/', _frames_prueba_de_vida(), format='multipart')
        self.assertEqual(resp.status_code, 400)
        self.usuario.refresh_from_db()
        self.assertIsNone(self.usuario.encoding_facial)

    def test_verificar_sin_referencia_registrada_no_llama_al_pipeline(self):
        self._autenticado()
        with mock.patch('KeyServApp.biometria.verificar_rostro_usuario', return_value=True) as verificar:
            resp = self.client.post('/api/auth/rostro/verificar/', _frames_prueba_de_vida(), format='multipart')
            verificar.assert_not_called()
        self.assertEqual(resp.status_code, 400)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.verificado_biometricamente)

    def test_verificar_exitosa_marca_al_usuario_verificado(self):
        self.usuario.encoding_facial = [0.1] * 128
        self.usuario.save()
        self._autenticado()
        with mock.patch('KeyServApp.biometria.verificar_rostro_usuario', return_value=True):
            resp = self.client.post('/api/auth/rostro/verificar/', _frames_prueba_de_vida(), format='multipart')
        self.assertEqual(resp.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.verificado_biometricamente)

    def test_verificar_rechazada_no_marca_al_usuario_verificado(self):
        self.usuario.encoding_facial = [0.1] * 128
        self.usuario.save()
        self._autenticado()
        with mock.patch('KeyServApp.biometria.verificar_rostro_usuario', return_value=False):
            resp = self.client.post('/api/auth/rostro/verificar/', _frames_prueba_de_vida(), format='multipart')
        self.assertEqual(resp.status_code, 400)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.verificado_biometricamente)
