"""
Enforcement de verificación de identidad al contratar y publicar.

Controlado por `settings.EXIGIR_IDENTIDAD_VERIFICADA` (env, apagado por defecto): la demo
pública no tiene biometría disponible, así que ahí debe seguir apagado; en producción real
se enciende. Hoy "verificada" = `verificado_biometricamente` (biometría nativa o rostro).
La vía alternativa sin biometría (multifactor + revisión de documento) se suma acá cuando
exista, sin tocar las vistas.
"""
from django.conf import settings

MENSAJE = (
    'Para contratar o publicar necesitas verificar tu identidad primero. '
    'Hazlo con la biometría de tu teléfono (recomendado) desde la sección de verificación.'
)
CODIGO = 'identidad_no_verificada'


def identidad_verificada(usuario):
    return bool(usuario.verificado_biometricamente)


def falta_verificar(usuario):
    """True si el enforcement está activo y la persona todavía no verificó su identidad."""
    return settings.EXIGIR_IDENTIDAD_VERIFICADA and not identidad_verificada(usuario)
