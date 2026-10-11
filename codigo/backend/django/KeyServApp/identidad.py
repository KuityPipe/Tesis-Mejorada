"""
Enforcement de verificación de identidad al contratar y publicar.

Controlado por `settings.EXIGIR_IDENTIDAD_VERIFICADA` (env, apagado por defecto): la demo
pública no tiene biometría disponible, así que ahí debe seguir apagado; en producción real
se enciende. "Verificada" = biometría (nativa o rostro) o vía alternativa sin biometría aprobada
(`verificacion_alternativa.py`).
"""
from django.conf import settings

MENSAJE = (
    'Para contratar o publicar necesitas verificar tu identidad primero. '
    'Hazlo con la biometría de tu teléfono (recomendado) desde la sección de verificación.'
)
CODIGO = 'identidad_no_verificada'


def identidad_verificada(usuario):
    """Biometría (nativa o rostro) o, alternativamente, verificación sin biometría aprobada por el staff."""
    if usuario.verificado_biometricamente:
        return True
    from .models import VerificacionAlternativa
    return VerificacionAlternativa.objects.filter(
        usuario=usuario, estado=VerificacionAlternativa.APROBADA, correo_verificado_en__isnull=False,
    ).exists()


def falta_verificar(usuario):
    """True si el enforcement está activo y la persona todavía no verificó su identidad."""
    return settings.EXIGIR_IDENTIDAD_VERIFICADA and not identidad_verificada(usuario)
