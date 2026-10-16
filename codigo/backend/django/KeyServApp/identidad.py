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
    'Hazlo desde la sección de verificación: con el reconocimiento facial o enviando tu documento para revisión. '
    'Una vez verificado, puedes reconfirmarla con la biometría de tu teléfono.'
)
CODIGO = 'identidad_no_verificada'


def _reciente(fecha):
    """True si `fecha` cae dentro de la vigencia (`settings.IDENTIDAD_VIGENCIA_DIAS`)."""
    return bool(fecha) and timezone.now() - fecha <= timedelta(days=settings.IDENTIDAD_VIGENCIA_DIAS)


def tiene_documento_aprobado(usuario):
    """
    True si una persona del staff ya revisó y aprobó un documento de identidad de esta cuenta (vía sin biometría, con
    el correo confirmado). Es la única prueba que hoy ata la cuenta a una persona real: la biometría nativa solo
    cuenta como reconfirmación de quien ya pasó por acá (ADR 0006, opción c).
    """
    from .models import VerificacionAlternativa
    return VerificacionAlternativa.objects.filter(
        usuario=usuario, estado=VerificacionAlternativa.APROBADA, correo_verificado_en__isnull=False,
    ).exists()


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
