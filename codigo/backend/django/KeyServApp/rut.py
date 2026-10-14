"""
RUT chileno: normalización y validación del dígito verificador (módulo 11).

El RUT se guarda sin puntos y con guion (`12345678-5`, máx. 10 caracteres). Antes solo se revisaba el largo, así que
cualquier texto de hasta 10 caracteres pasaba como "RUT" en una plataforma que se vende por su identidad verificada.
"""
import re

_FORMATO = re.compile(r'^\d{7,8}-[\dK]$')


def normalizar_rut(valor):
    """`12.345.678-5`, `12345678-5` o `123456785` → `12345678-5`. Si no se puede interpretar, devuelve el texto limpio."""
    limpio = re.sub(r'[.\s]', '', str(valor or '')).upper()
    if '-' not in limpio and len(limpio) >= 2:
        limpio = f'{limpio[:-1]}-{limpio[-1]}'
    return limpio


def digito_verificador(cuerpo):
    suma, factor = 0, 2
    for digito in reversed(str(cuerpo)):
        suma += int(digito) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    return 'K' if resto == 10 else '0' if resto == 11 else str(resto)


def rut_valido(valor):
    """`True` si el RUT (ya normalizado o no) tiene formato correcto y su dígito verificador coincide."""
    rut = normalizar_rut(valor)
    if not _FORMATO.match(rut):
        return False
    cuerpo, dv = rut.split('-')
    return digito_verificador(cuerpo) == dv
