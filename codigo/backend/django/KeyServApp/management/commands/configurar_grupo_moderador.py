"""
Crea (o actualiza) el grupo "Moderador" de /admin/ con permisos acotados —
Groups + Permissions nativos de Django, no un sistema de roles a medida
(es el patrón recomendado: asignar permisos a grupos, no a usuarios
individuales, y usar `is_superuser` para el rol "Admin" que ya tiene acceso
total por diseño de Django).

Alcance REVISADO (2026-08-15, pedido explícito del usuario tras el retema
de /admin/): el moderador NO es un segundo soporte de operaciones — solo
debe ver lo que le corresponde a moderación de contenido y los casos que se
le derivan, más las alertas de seguridad automáticas. Ya no es "todo menos
logs y bases de datos" (decisión anterior, ver historial de git); esa
versión le daba visibilidad de conversaciones privadas y del pipeline
completo de contrataciones, que no es su función.

Un moderador puede:
  - Aprobar/rechazar publicaciones (Publicaciones: view, change) y ver sus imágenes.
  - Revisar documentos de respaldo subidos (Documento: view, change).
  - Atender incidencias derivadas a moderación (Consulta: view, change) —
    "casos que deriven".
  - Aprobar/rechazar reseñas y sus fotos adjuntas (Valoracion,
    ValoracionImagen: view, change) — ya no solo las fotos se moderaban,
    la reseña completa también puede ser difamatoria/abusiva.
  - Ver el Ranking agregado (Ranking: view) — es el resultado de las
    valoraciones que sí modera, no un dato operativo aparte.
  - Ver los intentos de acceso sospechoso registrados automáticamente
    (IntentoAccesoSospechoso: view) — "solo ve las alertas".

Un moderador NO puede (a propósito, alcance acotado):
  - Ver conversaciones ni mensajes entre cliente y proveedor (Conversacion,
    Mensaje) — son privados, no le corresponden salvo que un caso se le
    derive explícitamente como Consulta.
  - Ver contrataciones ni su historial de estado (Contratacion,
    HistorialEstadoContratacion) — "trabajos pendientes" del negocio, no
    de moderación; el moderador reacciona a alertas e incidencias
    derivadas, no monitorea el pipeline operativo completo.
  - Ver Usuario ni ninguna tabla de datos sensibles/catálogos/pagos
    (Transaccion, Gasto, Autentificacion, Firma, UsuarioAdministrativo,
    RolCuentaAdministrativa, AreaAdministrativa, catálogos de referencia)
    — simplemente no se le da permiso, así que Django ni siquiera muestra
    esos modelos en su panel (comportamiento nativo de admin.site).
  - Ver el registro de auditoría (LogEntry) — ver admin.py, restringido a
    `is_superuser` directamente en el ModelAdmin, no vía Group.

Correr con: python manage.py configurar_grupo_moderador
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from KeyServApp.models import (
    Consulta, Documento, Imagenes, IntentoAccesoSospechoso, Publicaciones,
    Ranking, Valoracion, ValoracionImagen,
)

PERMISOS_MODERADOR = {
    Publicaciones: ['view', 'change'],
    Imagenes: ['view'],
    Documento: ['view', 'change'],
    Consulta: ['view', 'change'],
    Valoracion: ['view', 'change'],
    ValoracionImagen: ['view', 'change'],
    Ranking: ['view'],
    IntentoAccesoSospechoso: ['view'],
}


class Command(BaseCommand):
    help = 'Crea/actualiza el grupo Moderador con permisos acotados de admin.'

    def handle(self, *args, **options):
        grupo, creado = Group.objects.get_or_create(name='Moderador')
        grupo.permissions.clear()

        total = 0
        for modelo, acciones in PERMISOS_MODERADOR.items():
            content_type = ContentType.objects.get_for_model(modelo)
            for accion in acciones:
                codename = f'{accion}_{modelo._meta.model_name}'
                permiso = Permission.objects.filter(content_type=content_type, codename=codename).first()
                if permiso:
                    grupo.permissions.add(permiso)
                    total += 1
                else:
                    self.stdout.write(self.style.WARNING(f'No se encontró el permiso {codename} (¿faltó migrar?)'))

        verbo = 'creado' if creado else 'actualizado'
        self.stdout.write(self.style.SUCCESS(f'Grupo "Moderador" {verbo} con {total} permisos.'))
