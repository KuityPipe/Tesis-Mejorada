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
from unittest import mock

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from .models import (
    Comuna, Contratacion, Documento, HistorialEstadoContratacion,
    IntentoAccesoSospechoso, ItemPresupuesto, Pago, Publicaciones, Ranking,
    Region, TipoCuenta, Usuario, Valoracion, ValoracionImagen,
)
from . import biometria, geolocalizacion, validators


def _imagen_de_prueba():
    """
    GIF de 1x1 válido — lo más chico que Pillow (ImageField) acepta sin
    quejarse. Función en vez de un SimpleUploadedFile compartido a propósito:
    un POST de test (o `validar_imagen`) consume el stream del archivo, así
    que reusar la misma instancia entre tests da fallas dependientes del
    orden en que corren (el segundo test que la usa la recibe ya vacía).
    """
    return SimpleUploadedFile(
        'foto.gif', b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
        content_type='image/gif',
    )


def _crear_region_comuna_tipo():
    """Helper: catálogos mínimos que casi todos los tests necesitan (región, comuna, tipo de cuenta)."""
    region = Region.objects.create(id_region=13, nombre_region='Región Metropolitana')
    comuna = Comuna.objects.create(id_comuna=1, nombre_comuna='Santiago', region=region)
    tipo_cuenta = TipoCuenta.objects.create(id_tipo_cuenta=1, nombre_tipo_cuenta='CLIENTE', valor_cuenta=0)
    return region, comuna, tipo_cuenta


def _marcar_en_curso(contratacion):
    """
    Simula el efecto de un pago aprobado (CONFIRMADA -> EN_CURSO) sin pasar
    por Webpay/Khipu de verdad — la mecánica de pago en sí (Pago, las
    vistas de pago_webpay_*/pago_khipu_*) se prueba aparte en PagoTests.
    Los tests de flujo de contratación solo necesitan que el estado avance.
    """
    contratacion.estado = Contratacion.EN_CURSO
    contratacion.save()
    HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=Contratacion.EN_CURSO)


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
            'tipo_cuenta': self.tipo_cuenta.id_tipo_cuenta, 'password': 'ClaveSegura2026!', 'password_confirm': 'ClaveSegura2026!',
        }
        datos.update(overrides)
        return datos

    def test_registro_exitoso_redirige_a_sesion(self):
        resp = self.client.post(reverse('KeyServApp:registro'), self._datos_validos())
        self.assertRedirects(resp, reverse('KeyServApp:sesion'))
        usuario = Usuario.objects.get(email='nuevo@test.com')
        self.assertTrue(usuario.check_password('ClaveSegura2026!'))

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

    def test_password_corta_falla(self):
        """Mínimo subido de 6 a 8 caracteres."""
        resp = self.client.post(reverse('KeyServApp:registro'), self._datos_validos(
            password='Cort@1', password_confirm='Cort@1', email='corta@test.com',
        ))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Usuario.objects.filter(email='corta@test.com').exists())

    def test_password_solo_numeros_falla(self):
        """AUTH_PASSWORD_VALIDATORS.NumericPasswordValidator, reusado desde RegistroForm.clean() — antes '123456' pasaba sin problema."""
        resp = self.client.post(reverse('KeyServApp:registro'), self._datos_validos(
            password='12345678', password_confirm='12345678', email='numerica@test.com',
        ))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Usuario.objects.filter(email='numerica@test.com').exists())

    def test_password_comun_falla(self):
        """AUTH_PASSWORD_VALIDATORS.CommonPasswordValidator."""
        resp = self.client.post(reverse('KeyServApp:registro'), self._datos_validos(
            password='password123', password_confirm='password123', email='comun@test.com',
        ))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Usuario.objects.filter(email='comun@test.com').exists())


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

    def test_con_sesion_abierta_no_muestra_el_login(self):
        """Antes se podía llegar a /sesion/ con una cuenta ya logueada y loguear otra encima — confuso, ver también el registro."""
        session = self.client.session
        session['usuario_id'] = self.usuario.id_usuario
        session.save()
        resp = self.client.get(reverse('KeyServApp:sesion'))
        self.assertRedirects(resp, reverse('KeyServApp:sesion_iniciada'))

    def test_con_sesion_abierta_no_muestra_el_registro(self):
        session = self.client.session
        session['usuario_id'] = self.usuario.id_usuario
        session.save()
        resp = self.client.get(reverse('KeyServApp:registro'))
        self.assertRedirects(resp, reverse('KeyServApp:sesion_iniciada'))

    def test_login_bloqueado_queda_registrado_como_sospechoso(self):
        """El bloqueo por fuerza bruta también aplica a quien no tiene usuario todavía — usuario=None a propósito."""
        from django.core.cache import cache
        from .models import IntentoAccesoSospechoso

        for _ in range(5):
            self.client.post(reverse('KeyServApp:sesion'), {'email': 'login@test.com', 'password': 'incorrecta'})

        self.client.post(reverse('KeyServApp:sesion'), {'email': 'login@test.com', 'password': 'claveok'})

        intento = IntentoAccesoSospechoso.objects.get(recurso='login_bloqueado')
        self.assertIsNone(intento.usuario)
        self.assertEqual(intento.recurso_id, 'login@test.com')
        cache.clear()


class AlternarProveedorTests(TestCase):
    """
    `es_proveedor` antes solo se podía fijar una vez, en el checkbox de
    /registro/ — no había forma de activarlo o desactivarlo después
    (editar_perfil_view no procesa datos todavía). Ahora /perfil/alternar-proveedor/
    es la única vía real de cambiarlo.
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.cliente = _crear_usuario('cliente_alt@test.com', es_proveedor=False, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.client = Client()
        session = self.client.session
        session['usuario_id'] = self.cliente.id_usuario
        session.save()

    def test_activar_proveedor(self):
        self.client.post(reverse('KeyServApp:alternar_proveedor'))
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.es_proveedor)

    def test_desactivar_proveedor(self):
        self.cliente.es_proveedor = True
        self.cliente.save(update_fields=['es_proveedor'])
        self.client.post(reverse('KeyServApp:alternar_proveedor'))
        self.cliente.refresh_from_db()
        self.assertFalse(self.cliente.es_proveedor)

    def test_get_no_esta_permitido(self):
        resp = self.client.get(reverse('KeyServApp:alternar_proveedor'))
        self.assertEqual(resp.status_code, 405)

    def test_requiere_sesion_iniciada(self):
        self.client.session.flush()
        resp = self.client.post(reverse('KeyServApp:alternar_proveedor'))
        self.assertNotEqual(resp.status_code, 200)
        self.cliente.refresh_from_db()
        self.assertFalse(self.cliente.es_proveedor)

    def test_publicaciones_pasadas_siguen_visibles_en_perfil_tras_desactivar(self):
        self.cliente.es_proveedor = True
        self.cliente.save(update_fields=['es_proveedor'])
        Publicaciones.objects.create(
            usuario_publicador=self.cliente, titulo='Servicio viejo',
            sub_titulo='sub', descripcion_publicacion='desc', categoria='Otra',
        )
        self.client.post(reverse('KeyServApp:alternar_proveedor'))
        resp = self.client.get(reverse('KeyServApp:perfil'))
        self.assertContains(resp, 'Servicio viejo')


class EditarPerfilTests(TestCase):
    """
    `editar_perfil_view` antes solo renderizaba `editarperfil.html` con
    campos (habilidades, precio, disponibilidad, galería...) que ni existían
    en el modelo `Usuario` — nada de lo que se mandaba por POST se guardaba.
    Ahora es un ModelForm real sobre los campos que sí existen.
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.otra_comuna = Comuna.objects.create(id_comuna=2, nombre_comuna='Otra comuna', region=self.comuna.region)
        self.usuario = _crear_usuario('editar@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.client = Client()
        session = self.client.session
        session['usuario_id'] = self.usuario.id_usuario
        session.save()

    def test_get_muestra_los_datos_actuales(self):
        resp = self.client.get(reverse('KeyServApp:editar_perfil'))
        self.assertContains(resp, self.usuario.email)

    def test_post_guarda_los_cambios_reales(self):
        self.client.post(reverse('KeyServApp:editar_perfil'), {
            'nombre_usuario': 'NuevoNombre', 'apellido_usuario': self.usuario.apellido_usuario,
            'telefono': 987654321, 'email': self.usuario.email,
            'direccion_usuario': 'Calle Nueva 123', 'region': self.comuna.region_id,
            'comuna': self.otra_comuna.id_comuna,
        })
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nombre_usuario, 'NuevoNombre')
        self.assertEqual(self.usuario.telefono, 987654321)
        self.assertEqual(self.usuario.comuna_id, self.otra_comuna.id_comuna)

    def test_no_permite_repetir_el_correo_de_otro_usuario(self):
        _crear_usuario('ocupado@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        resp = self.client.post(reverse('KeyServApp:editar_perfil'), {
            'nombre_usuario': self.usuario.nombre_usuario, 'apellido_usuario': self.usuario.apellido_usuario,
            'telefono': self.usuario.telefono, 'email': 'ocupado@test.com',
            'region': self.comuna.region_id, 'comuna': self.comuna.id_comuna,
        })
        self.usuario.refresh_from_db()
        self.assertNotEqual(self.usuario.email, 'ocupado@test.com')
        self.assertContains(resp, 'Ya existe una cuenta con este correo')

    def test_puede_guardar_sin_cambiar_su_propio_correo(self):
        """El clean_email() no debe rechazar al usuario contra sí mismo."""
        resp = self.client.post(reverse('KeyServApp:editar_perfil'), {
            'nombre_usuario': self.usuario.nombre_usuario, 'apellido_usuario': self.usuario.apellido_usuario,
            'telefono': self.usuario.telefono, 'email': self.usuario.email,
            'region': self.comuna.region_id, 'comuna': self.comuna.id_comuna,
        })
        self.assertRedirects(resp, reverse('KeyServApp:perfil'))

    def test_sube_una_foto_de_perfil_valida(self):
        resp = self.client.post(reverse('KeyServApp:editar_perfil'), {
            'nombre_usuario': self.usuario.nombre_usuario, 'apellido_usuario': self.usuario.apellido_usuario,
            'telefono': self.usuario.telefono, 'email': self.usuario.email,
            'region': self.comuna.region_id, 'comuna': self.comuna.id_comuna,
            'foto_perfil': _imagen_de_prueba(),
        })
        self.usuario.refresh_from_db()
        self.assertTrue(bool(self.usuario.foto_perfil))
        self.assertRedirects(resp, reverse('KeyServApp:perfil'))


class CrearPerfilTests(TestCase):
    """
    /perfil/crear/ (perfil de proveedor extendido, RF002) antes era un
    formulario estático que no guardaba nada. Ahora es un CrearPerfilForm
    real sobre Usuario.areas_servicio/experiencia.
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor_crearperfil@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.client = Client()
        session = self.client.session
        session['usuario_id'] = self.proveedor.id_usuario
        session.save()

    def test_post_guarda_areas_de_servicio_y_experiencia(self):
        self.client.post(reverse('KeyServApp:crear_perfil'), {
            'areas_servicio': ['Gasfitería', 'Electricidad'],
            'experiencia': '10 años reparando cañerías y tableros eléctricos.',
        })
        self.proveedor.refresh_from_db()
        self.assertEqual(self.proveedor.areas_servicio, 'Gasfitería, Electricidad')
        self.assertIn('10 años', self.proveedor.experiencia)

    def test_get_precarga_las_areas_ya_guardadas(self):
        self.proveedor.areas_servicio = 'Jardinería, Limpieza del hogar'
        self.proveedor.save(update_fields=['areas_servicio'])
        resp = self.client.get(reverse('KeyServApp:crear_perfil'))
        self.assertContains(resp, 'checked', count=2)


class PreferenciasCuentaTests(TestCase):
    """
    /preferencias-cuenta/ antes no guardaba ninguno de sus tres formularios
    (notificaciones, contraseña, términos). Ahora las notificaciones y el
    cambio de contraseña son reales.
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('preferencias@test.com', 'clave_actual', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.client = Client()
        session = self.client.session
        session['usuario_id'] = self.usuario.id_usuario
        session.save()

    def test_desactivar_notificaciones_de_sonido(self):
        self.client.post(reverse('KeyServApp:preferencias_cuenta'), {'form': 'preferencias'})
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.notificaciones_sonido)

    def test_cambiar_password_con_la_actual_correcta(self):
        self.client.post(reverse('KeyServApp:preferencias_cuenta'), {
            'form': 'password', 'password_actual': 'clave_actual',
            'password': 'ClaveNueva123', 'password_confirm': 'ClaveNueva123',
        })
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('ClaveNueva123'))

    def test_cambiar_password_con_la_actual_incorrecta_no_cambia_nada(self):
        resp = self.client.post(reverse('KeyServApp:preferencias_cuenta'), {
            'form': 'password', 'password_actual': 'clave-equivocada',
            'password': 'ClaveNueva123', 'password_confirm': 'ClaveNueva123',
        })
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('clave_actual'))
        self.assertContains(resp, 'no es correcta')

    def test_cambiar_password_sin_confirmar_igual_no_cambia_nada(self):
        self.client.post(reverse('KeyServApp:preferencias_cuenta'), {
            'form': 'password', 'password_actual': 'clave_actual',
            'password': 'ClaveNueva123', 'password_confirm': 'OtraCosa456',
        })
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('clave_actual'))


class HistorialPagosTests(TestCase):
    """
    Reemplaza lo que era "Mis tarjetas" (campos de número de tarjeta/CVV que
    no se guardaban en ningún lado) por el historial real de Pago del
    cliente — ver historial_pagos_view.
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor_hist@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente_hist@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.otro_cliente = _crear_usuario('otro_cliente_hist@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Pintura', estado_moderacion=Publicaciones.APROBADA, precio=10000)
        self.contratacion = Contratacion.objects.create(
            publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor,
            estado=Contratacion.EN_CURSO, monto_acordado=10000,
        )
        self.pago = Pago.objects.create(contratacion=self.contratacion, monto=10000, metodo=Pago.WEBPAY, estado=Pago.PAGADO)
        self.client = Client()
        session = self.client.session
        session['usuario_id'] = self.cliente.id_usuario
        session.save()

    def test_muestra_los_pagos_propios(self):
        resp = self.client.get(reverse('KeyServApp:historial_pagos'))
        self.assertContains(resp, 'Pintura')
        self.assertContains(resp, '10000')

    def test_no_muestra_pagos_de_otro_cliente(self):
        session = self.client.session
        session['usuario_id'] = self.otro_cliente.id_usuario
        session.save()
        resp = self.client.get(reverse('KeyServApp:historial_pagos'))
        self.assertNotContains(resp, 'Pintura')


class RecuperarPasswordTests(TestCase):
    """
    /recuperar/ antes solo mostraba un formulario que decía explícitamente
    "el envío de instrucciones por correo todavía no está implementado".
    Ahora manda un enlace firmado (django.core.signing) con expiración de 1
    hora que deja elegir una contraseña nueva de verdad.
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('recuperar@test.com', 'claveoriginal1', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.usuario.telefono = 912345678
        self.usuario.save(update_fields=['telefono'])
        self.client = Client()

    def tearDown(self):
        cache.clear()

    def test_solicitud_con_datos_correctos_manda_un_correo(self):
        from django.core import mail
        self.client.post(reverse('KeyServApp:recuperar'), {'email': self.usuario.email, 'telefono': self.usuario.telefono})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.usuario.email, mail.outbox[0].to)

    def test_mensaje_es_igual_exista_o_no_la_cuenta(self):
        """No debe revelar si el correo está registrado — mismo mensaje en ambos casos."""
        resp_real = self.client.post(reverse('KeyServApp:recuperar'), {'email': self.usuario.email, 'telefono': self.usuario.telefono}, follow=True)
        resp_falso = self.client.post(reverse('KeyServApp:recuperar'), {'email': 'nadie@test.com', 'telefono': 111111111}, follow=True)
        mensaje_real = [str(m) for m in resp_real.context['messages']]
        mensaje_falso = [str(m) for m in resp_falso.context['messages']]
        self.assertEqual(mensaje_real, mensaje_falso)

    def test_token_valido_permite_cambiar_la_contrasena(self):
        from .views import _generar_token_recuperacion
        token = _generar_token_recuperacion(self.usuario)
        resp = self.client.post(reverse('KeyServApp:recuperar_confirmar', args=[token]), {
            'password': 'ClaveNueva2026!', 'password_confirm': 'ClaveNueva2026!',
        })
        self.assertRedirects(resp, reverse('KeyServApp:sesion'))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('ClaveNueva2026!'))

    def test_token_invalido_no_deja_pasar(self):
        resp = self.client.get(reverse('KeyServApp:recuperar_confirmar', args=['token-inventado']), follow=True)
        self.assertRedirects(resp, reverse('KeyServApp:recuperar'))

    def test_token_ya_usado_no_sirve_dos_veces(self):
        """Cambiar la contraseña rota el hash embebido en el token — el mismo link no debería servir dos veces."""
        from .views import _generar_token_recuperacion
        token = _generar_token_recuperacion(self.usuario)
        self.client.post(reverse('KeyServApp:recuperar_confirmar', args=[token]), {
            'password': 'ClaveNueva2026!', 'password_confirm': 'ClaveNueva2026!',
        })
        resp = self.client.get(reverse('KeyServApp:recuperar_confirmar', args=[token]), follow=True)
        self.assertRedirects(resp, reverse('KeyServApp:recuperar'))

    def test_limite_de_intentos(self):
        for _ in range(3):
            self.client.post(reverse('KeyServApp:recuperar'), {'email': self.usuario.email, 'telefono': self.usuario.telefono})
        from django.core import mail
        mail.outbox.clear()
        resp = self.client.post(reverse('KeyServApp:recuperar'), {'email': self.usuario.email, 'telefono': self.usuario.telefono}, follow=True)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(resp, 'Demasiadas solicitudes')


class CatalogoPaginacionTests(TestCase):
    """Antes el catálogo tenía un tope fijo de 40 resultados sin forma de ver el resto — ahora es un Paginator real."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('prov_pag@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        for i in range(25):
            Publicaciones.objects.create(
                usuario_publicador=self.proveedor, titulo=f'Servicio {i}',
                estado_moderacion=Publicaciones.APROBADA,
            )

    def test_primera_pagina_respeta_el_tamano_de_pagina(self):
        resp = self.client.get(reverse('KeyServApp:catalogo'))
        self.assertEqual(len(resp.context['publicaciones']), 20)
        self.assertEqual(resp.context['total_publicaciones'], 25)

    def test_segunda_pagina_trae_el_resto(self):
        resp = self.client.get(reverse('KeyServApp:catalogo'), {'page': 2})
        self.assertEqual(len(resp.context['publicaciones']), 5)

    def test_pagina_fuera_de_rango_devuelve_la_ultima(self):
        resp = self.client.get(reverse('KeyServApp:catalogo'), {'page': 999})
        self.assertEqual(resp.context['pagina'].number, 2)


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


class VerificacionHuellaSeguridadTests(TestCase):
    """
    `verificacion_huella_view` tomaba `ruta_imagen` como texto plano del
    POST y se lo pasaba directo a Image.open() dentro del pipeline —
    cualquier usuario logueado podía pedirle al servidor que abriera
    cualquier archivo de su filesystem (lectura arbitraria de archivos).
    Ahora exige un archivo subido de verdad y valida su contenido.
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.usuario = _crear_usuario('huella@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)

    def _login(self, client):
        session = client.session
        session['usuario_id'] = self.usuario.id_usuario
        session.save()

    def test_ya_no_acepta_una_ruta_de_archivo_como_texto(self):
        """Aunque alguien mande `ruta_imagen` (el parámetro viejo y vulnerable), la vista lo ignora por completo."""
        client = Client()
        self._login(client)
        client.post(reverse('KeyServApp:verificacion_huella'), {'ruta_imagen': '/etc/passwd'})
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.verificado_biometricamente)

    def test_archivo_que_no_es_una_imagen_real_se_rechaza(self):
        client = Client()
        self._login(client)
        falso = SimpleUploadedFile('huella.png', b'no es una imagen real', content_type='image/png')
        client.post(reverse('KeyServApp:verificacion_huella'), {'huella_imagen': falso})
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.verificado_biometricamente)


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


class DocumentoAccesoTests(TestCase):
    """
    Documento.archivo_subido usa storage privado (ver storage.py) — el único
    acceso es documento_descargar_view. Uno ligado a una Publicacion es
    público (certificación); uno ligado SOLO a un Usuario (documento de
    identidad) es privado, solo su dueño o staff lo puede ver.
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.dueno = _crear_usuario('dueno_doc@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.otro = _crear_usuario('otro_doc@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.pdf = SimpleUploadedFile('doc.pdf', b'%PDF-1.4 contenido de prueba', content_type='application/pdf')

    def _login(self, client, usuario):
        session = client.session
        session['usuario_id'] = usuario.id_usuario
        session.save()

    def test_documento_de_identidad_no_lo_puede_ver_otro_usuario(self):
        documento = Documento.objects.create(usuario=self.dueno, nombre_documento='cedula.pdf', archivo_subido=self.pdf)
        client = Client()
        self._login(client, self.otro)
        resp = client.get(reverse('KeyServApp:documento_descargar', args=[documento.id_documento]))
        self.assertEqual(resp.status_code, 404)

    def test_documento_de_identidad_anonimo_no_lo_puede_ver(self):
        documento = Documento.objects.create(usuario=self.dueno, nombre_documento='cedula.pdf', archivo_subido=self.pdf)
        client = Client()
        resp = client.get(reverse('KeyServApp:documento_descargar', args=[documento.id_documento]))
        self.assertEqual(resp.status_code, 404)

    def test_documento_de_identidad_lo_puede_ver_su_dueno(self):
        documento = Documento.objects.create(usuario=self.dueno, nombre_documento='cedula.pdf', archivo_subido=self.pdf)
        client = Client()
        self._login(client, self.dueno)
        resp = client.get(reverse('KeyServApp:documento_descargar', args=[documento.id_documento]))
        self.assertEqual(resp.status_code, 200)

    def test_documento_de_publicacion_es_publico(self):
        publicacion = Publicaciones.objects.create(usuario_publicador=self.dueno, titulo='Servicio', estado_moderacion=Publicaciones.APROBADA)
        documento = Documento.objects.create(publicacion=publicacion, usuario=self.dueno, nombre_documento='cert.pdf', archivo_subido=self.pdf)
        client = Client()  # sin login
        resp = client.get(reverse('KeyServApp:documento_descargar', args=[documento.id_documento]))
        self.assertEqual(resp.status_code, 200)


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

        # 3. El pago se aprueba (CONFIRMADA -> EN_CURSO) y el cliente marca como completada con re-autenticación correcta.
        _marcar_en_curso(contratacion)
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_completar', args=[contratacion.id_contratacion]), {'password': 'clave_cli'})
        contratacion.refresh_from_db()
        self.assertEqual(contratacion.estado, Contratacion.COMPLETADA)

        # 4. El cliente valora al proveedor — la reseña nace PENDIENTE y todavía
        # no debe contar para el Ranking (recién cuenta una vez moderada).
        client.post(reverse('KeyServApp:valoracion_crear', args=[contratacion.id_contratacion]), {'puntuacion': 5, 'comentario': 'Excelente'})
        valoracion = Valoracion.objects.get(usuario_receptor=self.proveedor, puntuacion=5)
        self.assertEqual(valoracion.estado_moderacion, Valoracion.PENDIENTE)
        ranking = Ranking.objects.get(usuario=self.proveedor)
        self.assertEqual(ranking.total_valoraciones, 0)

        # 5. Un moderador la aprueba — recién ahí debe reflejarse en el Ranking.
        from .views import _recalcular_ranking
        valoracion.estado_moderacion = Valoracion.APROBADA
        valoracion.save()
        _recalcular_ranking(self.proveedor)
        ranking.refresh_from_db()
        self.assertEqual(ranking.total_valoraciones, 1)
        self.assertEqual(float(ranking.puntuacion_promedio), 5.0)

    def test_no_se_puede_recontratar_mientras_hay_una_solicitud_activa(self):
        """El cliente no puede pedir el mismo servicio dos veces mientras la primera solicitud sigue SOLICITADA/CONFIRMADA/EN_CURSO."""
        client = Client()
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_crear', args=[self.publicacion.id_publicacion]))
        client.post(reverse('KeyServApp:contratacion_crear', args=[self.publicacion.id_publicacion]))
        self.assertEqual(Contratacion.objects.filter(publicacion=self.publicacion, cliente=self.cliente).count(), 1)

    def test_se_puede_recontratar_una_vez_completada_la_anterior(self):
        """Una vez COMPLETADA la contratación anterior, sí se puede volver a pedir el mismo servicio."""
        client = Client()
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_crear', args=[self.publicacion.id_publicacion]))
        primera = Contratacion.objects.get(publicacion=self.publicacion)

        self._login_como(client, self.proveedor)
        client.post(reverse('KeyServApp:contratacion_confirmar', args=[primera.id_contratacion]), {'password': 'clave_prov'})
        _marcar_en_curso(primera)
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_completar', args=[primera.id_contratacion]), {'password': 'clave_cli'})

        client.post(reverse('KeyServApp:contratacion_crear', args=[self.publicacion.id_publicacion]))
        self.assertEqual(Contratacion.objects.filter(publicacion=self.publicacion, cliente=self.cliente).count(), 2)

    def test_valoracion_con_foto_queda_pendiente_de_moderacion(self):
        """Las fotos adjuntas a una calificación no deben quedar visibles hasta que un moderador las apruebe."""
        client = Client()
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_crear', args=[self.publicacion.id_publicacion]))
        contratacion = Contratacion.objects.get(publicacion=self.publicacion)

        self._login_como(client, self.proveedor)
        client.post(reverse('KeyServApp:contratacion_confirmar', args=[contratacion.id_contratacion]), {'password': 'clave_prov'})
        _marcar_en_curso(contratacion)
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_completar', args=[contratacion.id_contratacion]), {'password': 'clave_cli'})

        client.post(reverse('KeyServApp:valoracion_crear', args=[contratacion.id_contratacion]), {
            'puntuacion': 5, 'comentario': 'Excelente', 'imagenes': _imagen_de_prueba(),
        })

        contratacion.refresh_from_db()
        self.assertIsNotNone(contratacion.valoracion)
        imagen = ValoracionImagen.objects.get(valoracion=contratacion.valoracion)
        self.assertEqual(imagen.estado_moderacion, ValoracionImagen.PENDIENTE)
        self.assertEqual(list(contratacion.valoracion.imagenes_aprobadas), [])

        imagen.estado_moderacion = ValoracionImagen.APROBADA
        imagen.save()
        self.assertEqual(list(contratacion.valoracion.imagenes_aprobadas), [imagen])

    def test_no_se_puede_calificar_dos_veces_el_mismo_trabajo(self):
        client = Client()
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_crear', args=[self.publicacion.id_publicacion]))
        contratacion = Contratacion.objects.get(publicacion=self.publicacion)

        self._login_como(client, self.proveedor)
        client.post(reverse('KeyServApp:contratacion_confirmar', args=[contratacion.id_contratacion]), {'password': 'clave_prov'})
        _marcar_en_curso(contratacion)
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_completar', args=[contratacion.id_contratacion]), {'password': 'clave_cli'})

        client.post(reverse('KeyServApp:valoracion_crear', args=[contratacion.id_contratacion]), {'puntuacion': 5, 'comentario': 'Excelente'})
        client.post(reverse('KeyServApp:valoracion_crear', args=[contratacion.id_contratacion]), {'puntuacion': 1, 'comentario': 'Cambié de opinión'})

        self.assertEqual(Valoracion.objects.filter(contratacion=contratacion).count(), 1)
        self.assertEqual(Valoracion.objects.get(contratacion=contratacion).puntuacion, 5)

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

    def test_reautenticacion_se_bloquea_tras_varios_intentos_fallidos(self):
        """Sin esto, alguien con la sesión abierta podía probar contraseñas sin ningún freno."""
        from django.core.cache import cache
        client = Client()
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_crear', args=[self.publicacion.id_publicacion]))
        contratacion = Contratacion.objects.get(publicacion=self.publicacion)

        self._login_como(client, self.proveedor)
        for _ in range(5):
            client.post(reverse('KeyServApp:contratacion_confirmar', args=[contratacion.id_contratacion]), {'password': 'clave-incorrecta'})

        # El sexto intento, aunque mande la contraseña CORRECTA, ya debería estar bloqueado.
        response = client.post(
            reverse('KeyServApp:contratacion_confirmar', args=[contratacion.id_contratacion]),
            {'password': 'clave_prov'}, follow=True,
        )
        contratacion.refresh_from_db()
        self.assertEqual(contratacion.estado, Contratacion.SOLICITADA)
        mensajes = [str(m) for m in response.context['messages']]
        self.assertTrue(any('Demasiados intentos' in m for m in mensajes))

        from .models import IntentoAccesoSospechoso
        self.assertTrue(IntentoAccesoSospechoso.objects.filter(
            usuario=self.proveedor, recurso='reauth_bloqueado_confirmar', recurso_id=str(contratacion.id_contratacion),
        ).exists())
        cache.clear()


class MontoAcordadoConfirmarTests(TestCase):
    """
    El precio de la Publicacion es solo un punto de partida — el proveedor
    puede ajustar el monto final acordado con el cliente (por chat) al
    confirmar la solicitud. Ver contratacion_confirmar_view.
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor_monto@test.com', 'clave_prov', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente_monto@test.com', 'clave_cli', es_proveedor=False, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(
            usuario_publicador=self.proveedor, titulo='Gasfitería', estado_moderacion=Publicaciones.APROBADA, precio=15000,
        )
        self.contratacion = Contratacion.objects.create(
            publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor, estado=Contratacion.SOLICITADA,
        )
        self.client = Client()
        session = self.client.session
        session['usuario_id'] = self.proveedor.id_usuario
        session.save()

    def test_confirmar_sin_monto_usa_el_precio_de_la_publicacion(self):
        self.client.post(reverse('KeyServApp:contratacion_confirmar', args=[self.contratacion.id_contratacion]), {'password': 'clave_prov'})
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.estado, Contratacion.CONFIRMADA)
        self.assertEqual(self.contratacion.monto_acordado, 15000)

    def test_confirmar_permite_ajustar_el_monto_acordado(self):
        self.client.post(reverse('KeyServApp:contratacion_confirmar', args=[self.contratacion.id_contratacion]), {'password': 'clave_prov', 'monto': 20000})
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.monto_acordado, 20000)

    def test_confirmar_con_monto_invalido_usa_el_precio_de_la_publicacion(self):
        self.client.post(reverse('KeyServApp:contratacion_confirmar', args=[self.contratacion.id_contratacion]), {'password': 'clave_prov', 'monto': -5})
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.estado, Contratacion.CONFIRMADA)
        self.assertEqual(self.contratacion.monto_acordado, 15000)


class ItemPresupuestoTests(TestCase):
    """
    Hoja de presupuesto opcional (ItemPresupuesto, ver
    _parsear_items_presupuesto/contratacion_confirmar_view): filas libres
    que el proveedor puede cargar al confirmar en vez de un monto único —
    si carga al menos un ítem válido, la suma reemplaza tanto el precio de
    la publicación como el campo "monto" simple.
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor_item@test.com', 'clave_prov', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente_item@test.com', 'clave_cli', es_proveedor=False, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(
            usuario_publicador=self.proveedor, titulo='Gasfitería', estado_moderacion=Publicaciones.APROBADA, precio=15000,
        )
        self.contratacion = Contratacion.objects.create(
            publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor, estado=Contratacion.SOLICITADA,
        )
        self.client = Client()
        session = self.client.session
        session['usuario_id'] = self.proveedor.id_usuario
        session.save()

    def test_confirmar_con_items_suma_el_monto_acordado(self):
        self.client.post(reverse('KeyServApp:contratacion_confirmar', args=[self.contratacion.id_contratacion]), {
            'password': 'clave_prov',
            'item_descripcion': ['Cañería PVC', 'Mano de obra'],
            'item_categoria': [ItemPresupuesto.MATERIAL, ItemPresupuesto.MANO_DE_OBRA],
            'item_monto': ['8000', '12000'],
        })
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.estado, Contratacion.CONFIRMADA)
        self.assertEqual(self.contratacion.monto_acordado, 20000)
        items = list(self.contratacion.items_presupuesto.all())
        self.assertEqual(len(items), 2)
        self.assertEqual([item.descripcion for item in items], ['Cañería PVC', 'Mano de obra'])
        self.assertEqual([item.orden for item in items], [0, 1])

    def test_confirmar_con_items_ignora_el_monto_unico(self):
        self.client.post(reverse('KeyServApp:contratacion_confirmar', args=[self.contratacion.id_contratacion]), {
            'password': 'clave_prov', 'monto': '99999',
            'item_descripcion': ['Viaje'], 'item_categoria': [ItemPresupuesto.VIAJE], 'item_monto': ['5000'],
        })
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.monto_acordado, 5000)

    def test_confirmar_descarta_filas_vacias_o_con_monto_invalido(self):
        self.client.post(reverse('KeyServApp:contratacion_confirmar', args=[self.contratacion.id_contratacion]), {
            'password': 'clave_prov',
            'item_descripcion': ['', 'Materiales', 'Sin monto'],
            'item_categoria': [ItemPresupuesto.OTRO, ItemPresupuesto.MATERIAL, ItemPresupuesto.OTRO],
            'item_monto': ['1000', '-500', 'no-es-un-numero'],
        })
        self.contratacion.refresh_from_db()
        # Las tres filas son inválidas (descripción vacía, monto negativo, monto no numérico)
        # -> se descartan todas y se cae al precio de la publicación, como si no se hubiera cargado nada.
        self.assertEqual(self.contratacion.monto_acordado, 15000)
        self.assertEqual(self.contratacion.items_presupuesto.count(), 0)

    def test_confirmar_con_categoria_desconocida_usa_otro(self):
        self.client.post(reverse('KeyServApp:contratacion_confirmar', args=[self.contratacion.id_contratacion]), {
            'password': 'clave_prov',
            'item_descripcion': ['Gasto raro'], 'item_categoria': ['NO_EXISTE'], 'item_monto': ['3000'],
        })
        item = self.contratacion.items_presupuesto.get()
        self.assertEqual(item.categoria, ItemPresupuesto.OTRO)

    def test_confirmar_sin_items_conserva_el_comportamiento_del_monto_unico(self):
        self.client.post(reverse('KeyServApp:contratacion_confirmar', args=[self.contratacion.id_contratacion]), {
            'password': 'clave_prov', 'monto': '18000',
        })
        self.contratacion.refresh_from_db()
        self.assertEqual(self.contratacion.monto_acordado, 18000)
        self.assertEqual(self.contratacion.items_presupuesto.count(), 0)

    @override_settings(COMISION_PLATAFORMA_PORCENTAJE=5.0)
    def test_detalle_muestra_desglose_y_comision_estimada(self):
        self.contratacion.monto_acordado = 20000
        self.contratacion.estado = Contratacion.CONFIRMADA
        self.contratacion.save()
        ItemPresupuesto.objects.create(contratacion=self.contratacion, descripcion='Cañería', categoria=ItemPresupuesto.MATERIAL, monto=8000, orden=0)
        ItemPresupuesto.objects.create(contratacion=self.contratacion, descripcion='Mano de obra', categoria=ItemPresupuesto.MANO_DE_OBRA, monto=12000, orden=1)

        resp = self.client.get(reverse('KeyServApp:contratacion_detalle', args=[self.contratacion.id_contratacion]))

        self.assertEqual(len(resp.context['items_presupuesto']), 2)
        self.assertEqual(resp.context['comision_porcentaje'], 5.0)
        self.assertEqual(resp.context['comision_estimada'], 1000)
        self.assertEqual(resp.context['neto_proveedor_estimado'], 19000)

    def test_detalle_sin_monto_acordado_no_calcula_comision(self):
        resp = self.client.get(reverse('KeyServApp:contratacion_detalle', args=[self.contratacion.id_contratacion]))
        self.assertIsNone(resp.context['comision_estimada'])
        self.assertIsNone(resp.context['neto_proveedor_estimado'])


class PagoTests(TestCase):
    """
    Webpay Plus + Khipu (RF012) — antes `pagos.py` era un esqueleto que
    tiraba NotImplementedError. Acá se prueban las vistas propias
    (creación del Pago, avance CONFIRMADA -> EN_CURSO, control de acceso)
    con `TransbankService`/`KhipuService` mockeados — el SDK real de
    Transbank ya se probó a mano contra el sandbox de integración (no hace
    falta pegarle a la red real en cada corrida de tests).
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor_pago@test.com', 'clave_prov', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente_pago@test.com', 'clave_cli', es_proveedor=False, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(
            usuario_publicador=self.proveedor, titulo='Gasfitería', estado_moderacion=Publicaciones.APROBADA, precio=15000,
        )
        self.contratacion = Contratacion.objects.create(
            publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor,
            estado=Contratacion.CONFIRMADA, monto_acordado=15000,
        )
        self.client = Client()
        session = self.client.session
        session['usuario_id'] = self.cliente.id_usuario
        session.save()

    def test_webpay_iniciar_crea_pago_pendiente(self):
        with mock.patch('KeyServApp.pagos.TransbankService.iniciar_transaccion', return_value=('tok123', 'https://webpay.test/init')):
            resp = self.client.post(reverse('KeyServApp:pago_webpay_iniciar', args=[self.contratacion.id_contratacion]))
        self.assertContains(resp, 'tok123')
        pago = Pago.objects.get(contratacion=self.contratacion)
        self.assertEqual(pago.metodo, Pago.WEBPAY)
        self.assertEqual(pago.estado, Pago.PENDIENTE)
        self.assertEqual(pago.token_webpay, 'tok123')

    def test_webpay_retorno_aprobado_pasa_contratacion_a_en_curso(self):
        pago = Pago.objects.create(contratacion=self.contratacion, monto=15000, metodo=Pago.WEBPAY, token_webpay='tok123')
        respuesta_aprobada = {'response_code': 0, 'status': 'AUTHORIZED', 'authorization_code': 'AUTH1'}
        with mock.patch('KeyServApp.pagos.TransbankService.confirmar_transaccion', return_value=respuesta_aprobada):
            self.client.post(reverse('KeyServApp:pago_webpay_retorno'), {'token_ws': 'tok123'})
        pago.refresh_from_db()
        self.contratacion.refresh_from_db()
        self.assertEqual(pago.estado, Pago.PAGADO)
        self.assertEqual(self.contratacion.estado, Contratacion.EN_CURSO)
        self.assertTrue(HistorialEstadoContratacion.objects.filter(contratacion=self.contratacion, estado=Contratacion.EN_CURSO).exists())

    def test_webpay_retorno_rechazado_no_avanza_la_contratacion(self):
        pago = Pago.objects.create(contratacion=self.contratacion, monto=15000, metodo=Pago.WEBPAY, token_webpay='tok123')
        respuesta_rechazada = {'response_code': 1, 'status': 'FAILED'}
        with mock.patch('KeyServApp.pagos.TransbankService.confirmar_transaccion', return_value=respuesta_rechazada):
            self.client.post(reverse('KeyServApp:pago_webpay_retorno'), {'token_ws': 'tok123'})
        pago.refresh_from_db()
        self.contratacion.refresh_from_db()
        self.assertEqual(pago.estado, Pago.RECHAZADO)
        self.assertEqual(self.contratacion.estado, Contratacion.CONFIRMADA)

    def test_webpay_cancelado_por_el_usuario_queda_anulado(self):
        pago = Pago.objects.create(contratacion=self.contratacion, monto=15000, metodo=Pago.WEBPAY, token_webpay='tok123')
        self.client.post(reverse('KeyServApp:pago_webpay_retorno'), {'TBK_TOKEN': 'tok123'})
        pago.refresh_from_db()
        self.assertEqual(pago.estado, Pago.ANULADO)

    def test_solo_el_cliente_puede_iniciar_el_pago(self):
        session = self.client.session
        session['usuario_id'] = self.proveedor.id_usuario
        session.save()
        self.client.post(reverse('KeyServApp:pago_webpay_iniciar', args=[self.contratacion.id_contratacion]))
        self.assertFalse(Pago.objects.filter(contratacion=self.contratacion).exists())
        self.assertTrue(IntentoAccesoSospechoso.objects.filter(recurso='pago_iniciar').exists())

    def test_no_se_puede_pagar_sin_monto_acordado(self):
        self.contratacion.monto_acordado = None
        self.contratacion.save(update_fields=['monto_acordado'])
        self.client.post(reverse('KeyServApp:pago_webpay_iniciar', args=[self.contratacion.id_contratacion]))
        self.assertFalse(Pago.objects.filter(contratacion=self.contratacion).exists())

    def test_khipu_iniciar_sin_api_key_da_error_claro_no_500(self):
        resp = self.client.post(reverse('KeyServApp:pago_khipu_iniciar', args=[self.contratacion.id_contratacion]), follow=True)
        self.assertEqual(resp.status_code, 200)
        mensajes = [str(m) for m in resp.context['messages']]
        self.assertTrue(any('KHIPU_API_KEY' in m for m in mensajes))

    def test_khipu_notificacion_marca_pagado_tras_reconsultar(self):
        pago = Pago.objects.create(contratacion=self.contratacion, monto=15000, metodo=Pago.KHIPU, khipu_payment_id='pay123')
        with mock.patch('KeyServApp.pagos.KhipuService.consultar_pago', return_value={'status': 'done', 'payment_id': 'pay123'}):
            resp = self.client.post(reverse('KeyServApp:pago_khipu_notificacion'), {'payment_id': 'pay123'})
        self.assertEqual(resp.status_code, 200)
        pago.refresh_from_db()
        self.contratacion.refresh_from_db()
        self.assertEqual(pago.estado, Pago.PAGADO)
        self.assertEqual(self.contratacion.estado, Contratacion.EN_CURSO)

    def test_khipu_notificacion_no_marca_pagado_si_todavia_no_esta_done(self):
        pago = Pago.objects.create(contratacion=self.contratacion, monto=15000, metodo=Pago.KHIPU, khipu_payment_id='pay123')
        with mock.patch('KeyServApp.pagos.KhipuService.consultar_pago', return_value={'status': 'pending', 'payment_id': 'pay123'}):
            self.client.post(reverse('KeyServApp:pago_khipu_notificacion'), {'payment_id': 'pay123'})
        pago.refresh_from_db()
        self.assertEqual(pago.estado, Pago.PENDIENTE)


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

    def test_un_tercero_no_puede_exportar_la_conversacion_de_otros(self):
        """Mismo chequeo que ver el chat, pero para /chat/<id>/exportar/ — es otra forma de leer el contenido completo."""
        from .models import Contratacion
        from .views import _obtener_o_crear_conversacion_de_contratacion

        contratacion = Contratacion.objects.create(publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor)
        conversacion = _obtener_o_crear_conversacion_de_contratacion(contratacion)

        otro = _crear_usuario('intruso_export@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        client = Client()
        session = client.session
        session['usuario_id'] = otro.id_usuario
        session.save()
        resp = client.get(reverse('KeyServApp:conversacion_exportar', args=[conversacion.id_conversacion]))
        self.assertRedirects(resp, reverse('KeyServApp:chat'))
        conversacion.refresh_from_db()
        self.assertIsNone(conversacion.exportado_en)


class IntentoAccesoSospechosoTests(TestCase):
    """
    Cada punto de "no participás en esto" (conversación, contratación,
    documento ajenos) tiene que dejar un IntentoAccesoSospechoso, no solo
    mostrar el mensaje de error — es lo que permite a moderación/admin
    notar reconocimiento manual de IDs antes de que sea un problema real.
    """

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.cliente = _crear_usuario('cliente_iaS@test.com', es_proveedor=False, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.proveedor = _crear_usuario('proveedor_iaS@test.com', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.intruso = _crear_usuario('intruso_iaS@test.com', comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Jardinería', estado_moderacion=Publicaciones.APROBADA)

    def _login(self, client, usuario):
        session = client.session
        session['usuario_id'] = usuario.id_usuario
        session.save()

    def test_conversacion_ajena_queda_registrada(self):
        from .views import _obtener_o_crear_conversacion_de_contratacion

        contratacion = Contratacion.objects.create(publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor)
        conversacion = _obtener_o_crear_conversacion_de_contratacion(contratacion)

        client = Client()
        self._login(client, self.intruso)
        client.get(reverse('KeyServApp:conversacion_detalle', args=[conversacion.id_conversacion]))

        intento = IntentoAccesoSospechoso.objects.get(recurso='conversacion', recurso_id=str(conversacion.id_conversacion))
        self.assertEqual(intento.usuario, self.intruso)
        self.assertEqual(intento.ip, '127.0.0.1')

    def test_contratacion_ajena_queda_registrada(self):
        contratacion = Contratacion.objects.create(publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor)

        client = Client()
        self._login(client, self.intruso)
        client.get(reverse('KeyServApp:contratacion_detalle', args=[contratacion.id_contratacion]))

        self.assertTrue(IntentoAccesoSospechoso.objects.filter(
            usuario=self.intruso, recurso='contratacion', recurso_id=str(contratacion.id_contratacion),
        ).exists())

    def test_documento_ajeno_queda_registrado(self):
        pdf = SimpleUploadedFile('doc.pdf', b'%PDF-1.4 contenido de prueba', content_type='application/pdf')
        documento = Documento.objects.create(usuario=self.cliente, nombre_documento='cedula.pdf', archivo_subido=pdf)

        client = Client()
        self._login(client, self.intruso)
        client.get(reverse('KeyServApp:documento_descargar', args=[documento.id_documento]))

        self.assertTrue(IntentoAccesoSospechoso.objects.filter(
            usuario=self.intruso, recurso='documento', recurso_id=str(documento.id_documento),
        ).exists())

    def test_acceso_normal_no_genera_registro(self):
        """Que no se dispare para nadie que sí tiene permiso — solo para los rechazos reales."""
        contratacion = Contratacion.objects.create(publicacion=self.publicacion, cliente=self.cliente, proveedor=self.proveedor)
        client = Client()
        self._login(client, self.cliente)
        client.get(reverse('KeyServApp:contratacion_detalle', args=[contratacion.id_contratacion]))
        self.assertEqual(IntentoAccesoSospechoso.objects.count(), 0)


class GeolocalizacionIPTests(TestCase):
    """geolocalizar_ip (base DB-IP local, ver geolocalizacion.py) degrada a (None, None) sin reventar, nunca geolocaliza IPs privadas."""

    def test_ip_privada_no_geolocaliza(self):
        self.assertEqual(geolocalizacion.geolocalizar_ip('127.0.0.1'), (None, None))
        self.assertEqual(geolocalizacion.geolocalizar_ip('192.168.1.1'), (None, None))

    def test_ip_invalida_no_revienta(self):
        self.assertEqual(geolocalizacion.geolocalizar_ip('no-es-una-ip'), (None, None))

    def test_ip_vacia_no_revienta(self):
        self.assertEqual(geolocalizacion.geolocalizar_ip(''), (None, None))
        self.assertEqual(geolocalizacion.geolocalizar_ip(None), (None, None))

    def test_ip_publica_con_base_descargada(self):
        import os
        from django.conf import settings
        if not os.path.exists(settings.GEOIP_DB_PATH):
            self.skipTest('Base GeoIP no descargada en este entorno — correr "manage.py descargar_geoip".')
        pais, ciudad = geolocalizacion.geolocalizar_ip('8.8.8.8')
        self.assertEqual(pais, 'United States')


class ValidacionArchivosTests(TestCase):
    """
    validators.py: la extensión y el Content-Type que manda el navegador son
    fáciles de falsear (basta renombrar un .exe a .jpg) — estos tests
    confirman que lo que de verdad bloquea es el contenido real del archivo.
    """

    def test_imagen_valida_pasa(self):
        validators.validar_imagen(_imagen_de_prueba())

    def test_archivo_de_texto_disfrazado_de_imagen_se_rechaza(self):
        """Un .jpg cuyo contenido real es texto plano no es una imagen — la firma de bytes no matchea."""
        falso = SimpleUploadedFile('foto.jpg', b'esto no es una imagen, es texto plano', content_type='image/jpeg')
        with self.assertRaises(ValidationError):
            validators.validar_imagen(falso)

    def test_extension_no_permitida_se_rechaza(self):
        ejecutable = SimpleUploadedFile('certificado.exe', b'MZ\x90\x00' + b'\x00' * 20, content_type='application/octet-stream')
        with self.assertRaises(ValidationError):
            validators.validar_documento(ejecutable)

    def test_pdf_valido_pasa_como_documento(self):
        pdf = SimpleUploadedFile('certificado.pdf', b'%PDF-1.4 contenido de prueba', content_type='application/pdf')
        validators.validar_documento(pdf)

    def test_archivo_muy_pesado_se_rechaza(self):
        archivo = SimpleUploadedFile('foto.jpg', b'\xff\xd8\xff' + b'0' * 1000, content_type='image/jpeg')
        with self.assertRaises(ValidationError):
            validators._validar_tamano(archivo, maximo=500)  # tope artificialmente bajo, no hace falta un archivo de 8 MB real para probar el chequeo


class ValoracionConFotoMaliciosaTests(TestCase):
    """La subida de fotos de una reseña (request.FILES.getlist, sin ModelForm de por medio) también tiene que pasar por los validadores."""

    def setUp(self):
        _, self.comuna, self.tipo_cuenta = _crear_region_comuna_tipo()
        self.proveedor = _crear_usuario('proveedor4@test.com', 'clave_prov', es_proveedor=True, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.cliente = _crear_usuario('cliente4@test.com', 'clave_cli', es_proveedor=False, comuna=self.comuna, tipo_cuenta=self.tipo_cuenta)
        self.publicacion = Publicaciones.objects.create(usuario_publicador=self.proveedor, titulo='Carpintería', estado_moderacion=Publicaciones.APROBADA)

    def _login_como(self, client, usuario):
        session = client.session
        session['usuario_id'] = usuario.id_usuario
        session.save()

    def test_foto_falsa_se_descarta_pero_la_valida_se_guarda(self):
        client = Client()
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_crear', args=[self.publicacion.id_publicacion]))
        contratacion = Contratacion.objects.get(publicacion=self.publicacion)

        self._login_como(client, self.proveedor)
        client.post(reverse('KeyServApp:contratacion_confirmar', args=[contratacion.id_contratacion]), {'password': 'clave_prov'})
        _marcar_en_curso(contratacion)
        self._login_como(client, self.cliente)
        client.post(reverse('KeyServApp:contratacion_completar', args=[contratacion.id_contratacion]), {'password': 'clave_cli'})

        falsa = SimpleUploadedFile('script.jpg', b'<script>alert(1)</script>', content_type='image/jpeg')
        response = client.post(
            reverse('KeyServApp:valoracion_crear', args=[contratacion.id_contratacion]),
            {'puntuacion': 5, 'comentario': 'Buen trabajo', 'imagenes': [_imagen_de_prueba(), falsa]},
            follow=True,
        )

        contratacion.refresh_from_db()
        self.assertEqual(ValoracionImagen.objects.filter(valoracion=contratacion.valoracion).count(), 1)
        mensajes = [str(m) for m in response.context['messages']]
        self.assertTrue(any('script.jpg' in m for m in mensajes))
