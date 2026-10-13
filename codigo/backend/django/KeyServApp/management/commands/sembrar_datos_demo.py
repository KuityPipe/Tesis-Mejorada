"""
Siembra datos demo reproducibles — para el demo desplegado (docs/PLAN_PORTAFOLIO.md,
Nivel 2.2). La base de datos del demo se rearma desde cero en cada deploy, así que todo
lo que se vea ahí tiene que salir de este comando.

Contenido (todo ficticio, pensado para mostrar que la plataforma sirve para cualquier oficio):
- 24 proveedores en 24 rubros (gasfitería, clases particulares, programación, ama de casa,
  jardinería, carpintería, cuidado de personas, cocina, mecánica, etc.), cada uno con una
  publicación aprobada y una foto de portada libre de derechos (`frontend/src/assets/fotos`,
  créditos en docs/CREDITOS_IMAGENES.md).
- 3 clientes y contrataciones en cada estado del BPMN, más contrataciones completadas con
  reseñas variadas para que el ranking del catálogo se vea real.
- **Toda publicación y cuenta es de prueba y así se avisa**: cada descripción termina con un aviso
  de demo y las cuentas usan el dominio @demo.keyserv (la API las marca con `es_demo`).

Idempotente a propósito: usa `get_or_create` en todo, así que correrlo en cada deploy
(ver render_build.sh) no duplica nada — es seguro de repetir.

Las 9 comunas RM ya geocodificadas (migración 0027, "Búsqueda por geolocalización") se
reparten entre los proveedores para que el filtro de radio muestre distancias reales.

Correr con: python manage.py sembrar_datos_demo
"""
import os
import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from KeyServApp.models import (
    Comuna, Contratacion, Conversacion, HistorialEstadoContratacion, Imagenes,
    Mensaje, Pago, Publicaciones, Usuario, UsuarioConversacion, Valoracion,
)
from KeyServApp.views import _recalcular_ranking

PASSWORD_DEMO = 'Demo1234'

AVISO_DEMO = (
    '\n\n⚠️ PUBLICACIÓN DE PRUEBA (DEMO): este servicio, el proveedor, su precio y sus reseñas son ficticios y existen '
    'solo para mostrar cómo funciona KeyServ.'
)
MARCA_DEMO = 'PUBLICACIÓN DE PRUEBA (DEMO)'

# Mismos valores que la migración 0027_comuna_coordenadas_demo — duplicados
# a propósito, no importados: `loaddata catalogos_iniciales` hace un
# `save()` completo de cada Comuna con los campos del fixture original (que
# no incluye latitud/longitud), así que si se corre DESPUÉS de que la
# migración 0027 ya las puso, las vuelve a dejar en NULL — bug real,
# encontrado corriendo este comando contra la base de datos de test (ver
# SembrarDatosDemoCommandTests). En vez de depender de un orden exacto
# migrate → loaddata que ningún deploy garantiza, este comando reaplica las
# mismas coordenadas él mismo, sea cual sea el orden que corrió antes.
COORDENADAS_PLAZA_PRINCIPAL = {
    1: ('-33.437700', '-70.650500'), 6: ('-33.459300', '-70.686000'),
    10: ('-33.524900', '-70.598000'), 14: ('-33.409800', '-70.569500'),
    19: ('-33.510800', '-70.757800'), 20: ('-33.455800', '-70.598000'),
    25: ('-33.423700', '-70.611200'), 27: ('-33.611000', '-70.575700'),
    32: ('-33.592800', '-70.700300'),
}

# Foto de portada por categoría (frontend/src/assets/fotos, CC0 de StockSnap). Ruta relativa: la sirve el propio
# frontend (Netlify / ng serve), así el demo no depende de servicios externos ni del disco efímero de Render.
FOTO_POR_CATEGORIA = {
    'Gasfitería': 'reparaciones', 'Electricidad': 'electricidad', 'Jardinería': 'jardineria',
    'Limpieza del hogar': 'limpieza', 'Pintura': 'pintura', 'Carpintería': 'carpinteria',
    'Mudanzas': 'mudanzas', 'Cerrajería': 'cerrajeria', 'Cuidado de mascotas': 'mascotas',
    'Clases particulares': 'clases', 'Belleza y bienestar': 'bienestar', 'Tecnología y soporte': 'soporte-tecnico',
    'Programación y diseño web': 'programacion', 'Cuidado de niños y adultos mayores': 'cuidado',
    'Cocina y catering': 'cocina', 'Reparación de artefactos': 'reparaciones', 'Fotografía y video': 'paisaje-montana',
    'Contabilidad y trámites': 'soporte-tecnico', 'Mecánica y automotriz': 'reparaciones',
}

# (nombre, apellido, email, categoría, título, subtítulo, precio, id_comuna)
# id_comuna: de las 9 geocodificadas en la migración 0027 (todas RM). Los 8 primeros son los de siempre y se
# conservan en este orden: las contrataciones de ejemplo dependen de él.
PROVEEDORES = [
    ('Marcelo', 'Muñoz', 'marcelo.gasfiteria@demo.keyserv', 'Gasfitería', 'Gasfitería a domicilio 24/7', 'Fugas, cañerías, instalación de artefactos', 25000, 1),
    ('Valentina', 'Soto', 'valentina.electricidad@demo.keyserv', 'Electricidad', 'Instalaciones eléctricas certificadas', 'Tableros, enchufes, certificación SEC', 30000, 25),
    ('Camila', 'Rojas', 'camila.jardineria@demo.keyserv', 'Jardinería', 'Diseño y mantención de jardines', 'Poda, paisajismo y riego automatizado', 20000, 20),
    ('Ignacio', 'Fuentes', 'ignacio.limpieza@demo.keyserv', 'Limpieza del hogar', 'Limpieza profunda de hogares y oficinas', 'Aseo post-obra, mudanza y mantención periódica', 18000, 14),
    ('Diego', 'Vera', 'diego.pintura@demo.keyserv', 'Pintura', 'Pintura interior y exterior', 'Terminaciones prolijas, presupuesto gratis', 22000, 10),
    ('Francisca', 'Torres', 'francisca.carpinteria@demo.keyserv', 'Carpintería', 'Muebles a medida y reparaciones', 'Carpintería fina para el hogar', 35000, 6),
    ('Rodrigo', 'Paredes', 'rodrigo.mudanzas@demo.keyserv', 'Mudanzas', 'Mudanzas dentro de Santiago', 'Camión propio, equipo de 3 personas', 45000, 19),
    ('Constanza', 'Reyes', 'constanza.cerrajeria@demo.keyserv', 'Cerrajería', 'Cerrajería de urgencia 24/7', 'Apertura de puertas, cambio de cerraduras', 15000, 27),
    ('Paula', 'Ibáñez', 'paula.clases@demo.keyserv', 'Clases particulares', 'Profesora de matemáticas y lenguaje', 'Reforzamiento escolar, básica y media', 15000, 1),
    ('Tomás', 'Araya', 'tomas.ingles@demo.keyserv', 'Clases particulares', 'Profesor de inglés y preparación PAES', 'Conversación, gramática y ensayos', 18000, 20),
    ('Sofía', 'Maldonado', 'sofia.web@demo.keyserv', 'Programación y diseño web', 'Desarrolladora web freelance', 'Sitios, tiendas online y aplicaciones a medida', 45000, 25),
    ('Matías', 'Leiva', 'matias.soporte@demo.keyserv', 'Tecnología y soporte', 'Soporte técnico y reparación de notebooks', 'Formateo, redes, limpieza de virus, a domicilio', 20000, 14),
    ('Carmen', 'Gómez', 'carmen.aseo@demo.keyserv', 'Limpieza del hogar', 'Ama de casa: aseo y orden del hogar', 'Aseo, lavado, planchado y organización', 14000, 10),
    ('Rosa', 'Contreras', 'rosa.cuidados@demo.keyserv', 'Cuidado de niños y adultos mayores', 'Cuidado de adultos mayores', 'Acompañamiento, medicamentos y paseos', 16000, 32),
    ('Andrea', 'Pizarro', 'andrea.ninera@demo.keyserv', 'Cuidado de niños y adultos mayores', 'Niñera con primeros auxilios', 'Cuidado de niños por hora o jornada', 12000, 19),
    ('Luis', 'Navarro', 'luis.jardinero@demo.keyserv', 'Jardinería', 'Jardinero: poda, césped y limpieza de terrenos', 'Corte de pasto, poda de árboles y retiro de ramas', 22000, 27),
    ('Héctor', 'Silva', 'hector.carpintero@demo.keyserv', 'Carpintería', 'Carpintero: closets, puertas y terrazas', 'Instalación y construcción en madera', 38000, 6),
    ('Marta', 'Olivares', 'marta.catering@demo.keyserv', 'Cocina y catering', 'Cocina casera y catering para eventos', 'Menús para 10 a 80 personas', 30000, 1),
    ('Felipe', 'Cortés', 'felipe.artefactos@demo.keyserv', 'Reparación de artefactos', 'Técnico en lavadoras, refrigeradores y hornos', 'Diagnóstico y reparación a domicilio', 25000, 14),
    ('Daniela', 'Fuentealba', 'daniela.mascotas@demo.keyserv', 'Cuidado de mascotas', 'Paseos y cuidado de perros', 'Paseos diarios y cuidado en tu hogar', 8000, 20),
    ('Gabriel', 'Mena', 'gabriel.foto@demo.keyserv', 'Fotografía y video', 'Fotografía de eventos y retratos', 'Cobertura de eventos, sesiones y edición', 60000, 25),
    ('Paola', 'Venegas', 'paola.masajes@demo.keyserv', 'Belleza y bienestar', 'Masajes descontracturantes a domicilio', 'Relajación y alivio de tensión muscular', 28000, 6),
    ('Ricardo', 'Tapia', 'ricardo.contador@demo.keyserv', 'Contabilidad y trámites', 'Contador: renta y trámites en el SII', 'Declaraciones, iniciación de actividades y asesoría', 35000, 32),
    ('Esteban', 'Quiroga', 'esteban.mecanico@demo.keyserv', 'Mecánica y automotriz', 'Mecánico a domicilio', 'Revisión, cambio de aceite y frenos', 30000, 10),
]

# (nombre, apellido, email, id_comuna)
CLIENTES = [
    ('Javiera', 'Salinas', 'cliente.demo@demo.keyserv', 1),
    ('Benjamín', 'Vega', 'benjamin.cliente@demo.keyserv', 25),
    ('Antonia', 'Castro', 'antonia.cliente@demo.keyserv', 20),
]

# Reseñas de ejemplo (puntuación, comentario) para los proveedores del 5º en adelante.
RESENAS = [
    (5, 'Muy puntual y ordenado, lo recomiendo.'),
    (4, 'Buen trabajo, quedó tal como lo conversamos.'),
    (5, 'Excelente atención, resolvió todo en el día.'),
    (4, 'Cumplió con lo acordado a un precio justo.'),
    (3, 'Hizo el trabajo, aunque llegó un poco tarde.'),
    (5, 'Súper amable y profesional.'),
    (4, 'Muy buena comunicación por el chat.'),
]


class Command(BaseCommand):
    help = 'Siembra datos demo reproducibles (usuarios, publicaciones, contrataciones) para el demo desplegado.'

    def handle(self, *args, **options):
        call_command('configurar_grupo_moderador')
        self._asegurar_coordenadas_comunas()
        self._sembrar_cuentas_staff()
        proveedores = self._sembrar_proveedores()
        clientes = self._sembrar_clientes()
        self._sembrar_contrataciones(clientes, proveedores)
        self._sembrar_resenas_extra(clientes, proveedores)
        self.stdout.write(self.style.SUCCESS('Datos demo sembrados/actualizados.'))

    def _asegurar_coordenadas_comunas(self):
        for id_comuna, (latitud, longitud) in COORDENADAS_PLAZA_PRINCIPAL.items():
            Comuna.objects.filter(pk=id_comuna).update(latitud=latitud, longitud=longitud)

    def _sembrar_cuentas_staff(self):
        """Cuentas de /admin/ — auth.User nativo de Django, distinto de Usuario (clientes/proveedores)."""
        User = get_user_model()
        # La clave sale de DEMO_STAFF_PASSWORD (variable de entorno, nunca en el repo). Si está definida se
        # reaplica en cada ejecución (así se puede rotar desde Render); si no, solo las cuentas nuevas reciben
        # una clave aleatoria que nadie conoce (se entra con `changepassword` o definiendo la variable).
        clave = os.environ.get('DEMO_STAFF_PASSWORD', '')
        admin, creado = User.objects.get_or_create(
            username='admin', defaults={'email': 'admin@demo.keyserv', 'is_staff': True, 'is_superuser': True},
        )
        if creado or clave:
            admin.set_password(clave or secrets.token_urlsafe(24))
            admin.save()

        moderador, creado = User.objects.get_or_create(
            username='moderador', defaults={'email': 'moderador@demo.keyserv', 'is_staff': True},
        )
        if creado or clave:
            moderador.set_password(clave or secrets.token_urlsafe(24))
            moderador.save()
        grupo_moderador = Group.objects.get(name='Moderador')
        moderador.groups.add(grupo_moderador)

        self.admin_user = admin

    def _crear_usuario(self, nombre, apellido, email, comuna_id, es_proveedor):
        usuario, creado = Usuario.objects.get_or_create(
            email=email,
            defaults={
                'nombre_usuario': nombre,
                'apellido_usuario': apellido,
                'telefono': 900000000,
                'edad': 30,
                'comuna_id': comuna_id,
                'es_proveedor': es_proveedor,
                'verificado_biometricamente': True,
                'verificado_en': timezone.now(),
            },
        )
        if creado:
            usuario.set_password(PASSWORD_DEMO)
            usuario.save()
        return usuario

    def _sembrar_proveedores(self):
        proveedores = []
        for nombre, apellido, email, categoria, titulo, sub_titulo, precio, comuna_id in PROVEEDORES:
            usuario = self._crear_usuario(nombre, apellido, email, comuna_id, es_proveedor=True)
            publicacion, creada = Publicaciones.objects.get_or_create(
                usuario_publicador=usuario, titulo=titulo,
                defaults={
                    'sub_titulo': sub_titulo,
                    'descripcion_publicacion': f'{sub_titulo}. Servicio verificado en KeyServ, con identidad confirmada del proveedor.{AVISO_DEMO}',
                    'categoria': categoria,
                    'precio': precio,
                    'estado_moderacion': Publicaciones.APROBADA,
                    'aprobado_por': self.admin_user,
                    'fecha_moderacion': timezone.now(),
                },
            )
            if MARCA_DEMO not in (publicacion.descripcion_publicacion or ''):
                # Publicaciones sembradas en un deploy anterior: se les agrega el aviso de demo.
                publicacion.descripcion_publicacion = (publicacion.descripcion_publicacion or sub_titulo) + AVISO_DEMO
                publicacion.save(update_fields=['descripcion_publicacion'])
            self._asegurar_foto(publicacion, categoria)
            proveedores.append((usuario, publicacion))
        return proveedores

    def _asegurar_foto(self, publicacion, categoria):
        """Foto de portada local (no picsum): crea la imagen o reemplaza la URL externa de un deploy anterior."""
        url = f'assets/fotos/{FOTO_POR_CATEGORIA[categoria]}.jpg'
        imagen = Imagenes.objects.filter(publicacion=publicacion).first()
        if imagen is None:
            Imagenes.objects.create(publicacion=publicacion, url_imagen=url)
        elif not imagen.archivo and imagen.url_imagen != url:
            imagen.url_imagen = url
            imagen.save(update_fields=['url_imagen'])

    def _sembrar_clientes(self):
        return [self._crear_usuario(n, a, e, c, es_proveedor=False) for n, a, e, c in CLIENTES]

    def _sembrar_contrataciones(self, clientes, proveedores):
        """Una contratación por cada estado del BPMN — para que el demo muestre las 4 etapas reales, no solo el catálogo."""
        estados_demo = [
            Contratacion.SOLICITADA, Contratacion.CONFIRMADA,
            Contratacion.EN_CURSO, Contratacion.COMPLETADA,
        ]
        for i, estado_objetivo in enumerate(estados_demo):
            cliente = clientes[i % len(clientes)]
            proveedor, publicacion = proveedores[i]

            contratacion, creada = Contratacion.objects.get_or_create(
                cliente=cliente, proveedor=proveedor, publicacion=publicacion,
                defaults={'estado': Contratacion.SOLICITADA, 'monto_acordado': publicacion.precio},
            )
            if not creada:
                continue  # ya sembrada en una corrida anterior — idempotente, no se vuelve a avanzar el estado.

            HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=Contratacion.SOLICITADA)

            conversacion = Conversacion.objects.create(contratacion=contratacion)
            UsuarioConversacion.objects.create(usuario=cliente, conversacion=conversacion)
            UsuarioConversacion.objects.create(usuario=proveedor, conversacion=conversacion)
            Mensaje.objects.create(conversacion=conversacion, usuario=cliente, contenido=f'Hola {proveedor.nombre_usuario}, ¿podrías ayudarme con esto?')
            Mensaje.objects.create(conversacion=conversacion, usuario=proveedor, contenido='¡Claro! Coordinemos el día y horario.')

            estado_actual = Contratacion.SOLICITADA
            secuencia = [Contratacion.CONFIRMADA, Contratacion.EN_CURSO, Contratacion.COMPLETADA]
            for estado in secuencia:
                if estados_demo.index(estado_objetivo) < secuencia.index(estado) + 1:
                    break
                estado_actual = estado
                HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=estado)

            contratacion.estado = estado_actual
            contratacion.save()

            if estado_actual in (Contratacion.EN_CURSO, Contratacion.COMPLETADA):
                Pago.objects.create(
                    contratacion=contratacion, monto=contratacion.monto_acordado, metodo=Pago.WEBPAY,
                    estado=Pago.PAGADO, orden_compra=f'DEMO-{contratacion.pk}', fecha_confirmacion=timezone.now(),
                )

            if estado_actual == Contratacion.COMPLETADA:
                Valoracion.objects.create(
                    usuario_emisor=cliente, usuario_receptor=proveedor, publicacion=publicacion,
                    contratacion=contratacion, puntuacion=5,
                    comentario='Excelente trabajo, muy profesional y puntual.',
                    estado_moderacion=Valoracion.APROBADA, aprobado_por=self.admin_user, fecha_moderacion=timezone.now(),
                )
                _recalcular_ranking(proveedor)

    def _sembrar_resenas_extra(self, clientes, proveedores):
        """
        Un trabajo completado con reseña para casi todos los demás proveedores, con puntuaciones variadas:
        así el catálogo muestra estrellas y rankings creíbles en lugar de todo en blanco.
        """
        for i, (proveedor, publicacion) in enumerate(proveedores[4:-3], start=4):
            cliente = clientes[i % len(clientes)]
            contratacion, creada = Contratacion.objects.get_or_create(
                cliente=cliente, proveedor=proveedor, publicacion=publicacion,
                defaults={'estado': Contratacion.COMPLETADA, 'monto_acordado': publicacion.precio},
            )
            if not creada:
                continue
            for estado in (Contratacion.SOLICITADA, Contratacion.CONFIRMADA, Contratacion.EN_CURSO, Contratacion.COMPLETADA):
                HistorialEstadoContratacion.objects.create(contratacion=contratacion, estado=estado)
            Pago.objects.create(
                contratacion=contratacion, monto=contratacion.monto_acordado, metodo=Pago.WEBPAY,
                estado=Pago.PAGADO, orden_compra=f'DEMO-{contratacion.pk}', fecha_confirmacion=timezone.now(),
            )
            puntuacion, comentario = RESENAS[i % len(RESENAS)]
            Valoracion.objects.create(
                usuario_emisor=cliente, usuario_receptor=proveedor, publicacion=publicacion,
                contratacion=contratacion, puntuacion=puntuacion, comentario=comentario,
                estado_moderacion=Valoracion.APROBADA, aprobado_por=self.admin_user, fecha_moderacion=timezone.now(),
            )
            _recalcular_ranking(proveedor)
