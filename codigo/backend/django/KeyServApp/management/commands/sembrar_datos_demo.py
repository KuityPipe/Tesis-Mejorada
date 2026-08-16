"""
Siembra datos demo reproducibles — para el demo desplegado (docs/PLAN_PORTAFOLIO.md,
Nivel 2.2). Antes, la data demo local (12 usuarios, 8 publicaciones, etc. —
ver CLAUDE.md) vivía solo en el Postgres local, sembrada a mano; no
sobrevivía a un `migrate` fresco. Esta versión es más chica (8 proveedores,
3 clientes, 4 contrataciones — una por cada estado) pero 100% reproducible
desde cero, exactamente lo que necesita un despliegue nuevo.

Idempotente a propósito: usa `get_or_create` en todo, así que correrlo en
cada deploy (ver render_build.sh) no duplica nada — es seguro de repetir.

Los 8 proveedores usan las 9 comunas RM ya geocodificadas (migración 0027,
"Búsqueda por geolocalización") para que el filtro de radio muestre
distancias reales, no ceros/null.

Correr con: python manage.py sembrar_datos_demo
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils import timezone

from KeyServApp.models import (
    Comuna, Contratacion, Conversacion, HistorialEstadoContratacion, Imagenes,
    Mensaje, Pago, Publicaciones, Usuario, UsuarioConversacion, Valoracion,
)
from KeyServApp.views import _recalcular_ranking

PASSWORD_DEMO = 'Demo1234'

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

# (nombre, apellido, email, categoría, título, subtítulo, precio, id_comuna)
# id_comuna: de las 9 geocodificadas en la migración 0027 (todas RM).
PROVEEDORES = [
    ('Marcelo', 'Muñoz', 'marcelo.gasfiteria@demo.keyserv', 'Gasfitería', 'Gasfitería a domicilio 24/7', 'Fugas, cañerías, instalación de artefactos', 25000, 1),
    ('Valentina', 'Soto', 'valentina.electricidad@demo.keyserv', 'Electricidad', 'Instalaciones eléctricas certificadas', 'Tableros, enchufes, certificación SEC', 30000, 25),
    ('Camila', 'Rojas', 'camila.jardineria@demo.keyserv', 'Jardinería', 'Diseño y mantención de jardines', 'Poda, paisajismo y riego automatizado', 20000, 20),
    ('Ignacio', 'Fuentes', 'ignacio.limpieza@demo.keyserv', 'Limpieza del hogar', 'Limpieza profunda de hogares y oficinas', 'Aseo post-obra, mudanza y mantención periódica', 18000, 14),
    ('Diego', 'Vera', 'diego.pintura@demo.keyserv', 'Pintura', 'Pintura interior y exterior', 'Terminaciones prolijas, presupuesto gratis', 22000, 10),
    ('Francisca', 'Torres', 'francisca.carpinteria@demo.keyserv', 'Carpintería', 'Muebles a medida y reparaciones', 'Carpintería fina para el hogar', 35000, 6),
    ('Rodrigo', 'Paredes', 'rodrigo.mudanzas@demo.keyserv', 'Mudanzas', 'Mudanzas dentro de Santiago', 'Camión propio, equipo de 3 personas', 45000, 19),
    ('Constanza', 'Reyes', 'constanza.cerrajeria@demo.keyserv', 'Cerrajería', 'Cerrajería de urgencia 24/7', 'Apertura de puertas, cambio de cerraduras', 15000, 27),
]

# (nombre, apellido, email, id_comuna)
CLIENTES = [
    ('Javiera', 'Salinas', 'cliente.demo@demo.keyserv', 1),
    ('Benjamín', 'Vega', 'benjamin.cliente@demo.keyserv', 25),
    ('Antonia', 'Castro', 'antonia.cliente@demo.keyserv', 20),
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
        self.stdout.write(self.style.SUCCESS('Datos demo sembrados/actualizados.'))

    def _asegurar_coordenadas_comunas(self):
        for id_comuna, (latitud, longitud) in COORDENADAS_PLAZA_PRINCIPAL.items():
            Comuna.objects.filter(pk=id_comuna).update(latitud=latitud, longitud=longitud)

    def _sembrar_cuentas_staff(self):
        """Cuentas de /admin/ — auth.User nativo de Django, distinto de Usuario (clientes/proveedores)."""
        User = get_user_model()
        admin, creado = User.objects.get_or_create(
            username='admin', defaults={'email': 'admin@demo.keyserv', 'is_staff': True, 'is_superuser': True},
        )
        if creado:
            admin.set_password('KeyServ2026!')
            admin.save()

        moderador, creado = User.objects.get_or_create(
            username='moderador', defaults={'email': 'moderador@demo.keyserv', 'is_staff': True},
        )
        if creado:
            moderador.set_password('Moderador2026!')
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
                    'descripcion_publicacion': f'{sub_titulo}. Servicio verificado en KeyServ, con identidad confirmada del proveedor.',
                    'categoria': categoria,
                    'precio': precio,
                    'estado_moderacion': Publicaciones.APROBADA,
                    'aprobado_por': self.admin_user,
                    'fecha_moderacion': timezone.now(),
                },
            )
            if creada:
                slug = categoria.lower().replace(' ', '-')
                Imagenes.objects.create(publicacion=publicacion, url_imagen=f'https://picsum.photos/seed/keyserv-{slug}/800/600')
            proveedores.append((usuario, publicacion))
        return proveedores

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
