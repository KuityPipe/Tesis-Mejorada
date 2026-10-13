"""
Re-cifra los vectores faciales (`Usuario.encoding_facial`) con la primera clave de
`BIOMETRIC_ENCRYPTION_KEYS`. Rotación de llaves, paso a paso (ver docs/cumplimiento/rotacion-de-llaves.md):

 1. Generar una clave nueva y ponerla PRIMERA en `BIOMETRIC_ENCRYPTION_KEYS`, dejando las anteriores
    detrás (la primera cifra, todas descifran).
 2. Correr `manage.py rotar_llaves_biometricas --dry-run` y luego sin `--dry-run`.
 3. Cuando el comando informe 0 filas por rotar y 0 ilegibles, retirar la clave vieja de la variable.

Nunca borra ni sobrescribe un vector que no se pudo descifrar: lo cuenta como ilegible y lo deja intacto.
"""
from django.core.management.base import BaseCommand

from KeyServApp import campos
from KeyServApp.models import Usuario


class Command(BaseCommand):
    help = 'Re-cifra los vectores faciales con la clave actual (la primera de BIOMETRIC_ENCRYPTION_KEYS).'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        fernet = campos._fernet()
        primera = fernet._fernets[0]
        rotadas = ya_actuales = ilegibles = 0
        filas = Usuario.objects.exclude(encoding_facial__isnull=True).values_list('pk', flat=True)
        for pk in filas:
            usuario = Usuario.objects.get(pk=pk)
            if usuario.encoding_facial is None:  # no se pudo descifrar con ninguna clave
                ilegibles += 1
                continue
            crudo = Usuario.objects.extra(select={'crudo': '"ENCODING_FACIAL"'}).filter(pk=pk).values_list('crudo', flat=True).first()
            try:
                primera.decrypt(crudo.encode())
                ya_actuales += 1
                continue
            except Exception:
                pass
            if not opts['dry_run']:
                usuario.save(update_fields=['encoding_facial'])
            rotadas += 1
        verbo = 'Por rotar' if opts['dry_run'] else 'Rotadas'
        self.stdout.write(self.style.SUCCESS(f'{verbo}: {rotadas}. Ya con la clave actual: {ya_actuales}. Ilegibles (intactas): {ilegibles}.'))
