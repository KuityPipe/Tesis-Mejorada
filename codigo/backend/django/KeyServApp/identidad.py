"""
Enforcement de verificación de identidad al contratar y publicar.

Controlado por `settings.EXIGIR_IDENTIDAD_VERIFICADA` (env, apagado por defecto): la demo
pública no tiene biometría disponible, así que ahí debe seguir apagado; en producción real
se enciende. "Verificada" = biometría (nativa o rostro) o vía alternativa sin biometría aprobada
(`verificacion_alternativa.py`), y además RECIENTE: vale `IDENTIDAD_VIGENCIA_DIAS` días.
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

MENSAJE = (
    'Para contratar o publicar necesitas verificar tu identidad primero. '
    'Hazlo con la biometría de tu teléfono (recomendado) desde la sección de verificación.'
)
CODIGO = 'identidad_no_verificada'


def _reciente(fecha):
    """True si `fecha` cae dentro de la vigencia (`settings.IDENTIDAD_VIGENCIA_DIAS`)."""
    return bool(fecha) and timezone.now() - fecha <= timedelta(days=settings.IDENTIDAD_VIGENCIA_DIAS)


def identidad_verificada(usuario):
    """
    Verificación **válida y reciente**: biometría (nativa o rostro) hecha dentro de la vigencia, o
    verificación sin biometría aprobada por el staff dentro de la vigencia. Pasada la vigencia hay
    que volver a verificar.
    """
    if usuario.verificado_biometricamente and _reciente(usuario.verificado_en):
        return True
    from .models import VerificacionAlternativa
    return any(
        _reciente(v.revisado_en)
        for v in VerificacionAlternativa.objects.filter(
            usuario=usuario, estado=VerificacionAlternativa.APROBADA, correo_verificado_en__isnull=False,
        )
    )


def falta_verificar(usuario):
    """True si el enforcement está activo y la persona todavía no tiene una verificación vigente."""
    return settings.EXIGIR_IDENTIDAD_VERIFICADA and not identidad_verificada(usuario)
