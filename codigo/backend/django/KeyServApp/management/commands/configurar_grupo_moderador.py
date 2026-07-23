"""
Crea (o actualiza) el grupo "Moderador" de /admin/ con permisos acotados —
Groups + Permissions nativos de Django, no un sistema de roles a medida
(es el patrón recomendado: asignar permisos a grupos, no a usuarios
individuales, y usar `is_superuser` para el rol "Admin" que ya tiene acceso
total por diseño de Django).

Alcance pedido por el usuario: "el moderador tiene todo menos los logs y
bases de datos" — se interpreta como: todo lo OPERATIVO del negocio
(publicaciones, solicitudes/contrataciones, mensajería, incidencias,
valoraciones) sí; las tablas sensibles/de infraestructura (datos de
Usuario con su hash de password, Transaccion, Gasto, Autentificacion, Firma,
la estructura interna UsuarioAdministrativo/Rol/Area, y los catálogos) no.

Un moderador puede:
  - Aprobar/rechazar publicaciones (Publicaciones: view, change) y ver sus imágenes.
  - Revisar documentos de respaldo subidos (Documento: view, change).
  - Atender incidencias/soporte (Consulta: view, change).
  - Ver solicitudes/contrataciones y su historial de estado (Contratacion,
    HistorialEstadoContratacion: view) — "solicitudes pendientes".
  - Revisar mensajería y valoraciones en caso de disputa (Conversacion,
    Mensaje, Valoracion, Ranking: view).

Un moderador NO puede (a propósito — "todo menos logs y bases de datos"):
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
    Consulta, Contratacion, Conversacion, Documento, HistorialEstadoContratacion,
    Imagenes, Mensaje, Publicaciones, Ranking, Valoracion,
)

PERMISOS_MODERADOR = {
    Publicaciones: ['view', 'change'],
    Imagenes: ['view'],
    Documento: ['view', 'change'],
    Consulta: ['view', 'change'],
    Contratacion: ['view'],
    HistorialEstadoContratacion: ['view'],
    Conversacion: ['view'],
    Mensaje: ['view'],
    Valoracion: ['view'],
    Ranking: ['view'],
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
