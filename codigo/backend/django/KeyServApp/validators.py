"""
Validación de archivos subidos por usuarios sin sesión de confianza
(imágenes/documentos de una Publicacion, fotos de una Valoracion).

Por qué existe este archivo: el ImageField de Django solo garantiza que
Pillow pueda *abrir* el archivo — no pone límite de tamaño, no bloquea SVG
o HTML explícitamente, y el FileField genérico de Documento (que acepta
cualquier cosa, porque hoy admite PDF o imagen) no validaba absolutamente
nada, ni siquiera la extensión. Nada de esto pasaba por python-magic (no
está instalado en este entorno) — en su lugar se comparan a mano los
primeros bytes del archivo contra la firma real de cada formato permitido,
que es la parte que un atacante no puede falsear con solo renombrar un
archivo o mentir en el Content-Type que manda el navegador.

Se completa con un escaneo antivirus opcional (ver antivirus.py) — acá
sólo se llama al hook, la lógica de si hay ClamAV configurado vive allá.
"""
import os
import warnings

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

from .antivirus import escanear_archivo

MB = 1024 * 1024

TAMANO_MAXIMO_IMAGEN = 8 * MB
TAMANO_MAXIMO_DOCUMENTO = 10 * MB

EXTENSIONES_IMAGEN_PERMITIDAS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
EXTENSIONES_DOCUMENTO_PERMITIDAS = {'.pdf', '.jpg', '.jpeg', '.png'}

# Firmas de bytes reales al inicio del archivo (magic numbers). La extensión
# y el Content-Type que manda el navegador son triviales de falsear (basta
# renombrar un .exe a .jpg); esto no — si el contenido no empieza con la
# firma esperada para esa extensión, se rechaza sin llegar a intentar
# decodificarlo. De paso esto ya descarta SVG (es XML, no matchea ninguna
# firma binaria) y HTML disfrazado de imagen/documento.
_FIRMAS = {
    '.pdf': [b'%PDF-'],
    '.jpg': [b'\xff\xd8\xff'],
    '.jpeg': [b'\xff\xd8\xff'],
    '.png': [b'\x89PNG\r\n\x1a\n'],
    '.gif': [b'GIF87a', b'GIF89a'],
    '.webp': [b'RIFF'],  # contenedor RIFF genérico; Pillow confirma después que el contenido es WEBP de verdad
}


def _extension(archivo):
    return os.path.splitext(archivo.name)[1].lower()


def _verificar_firma(archivo, extension):
    firmas = _FIRMAS.get(extension, [])
    inicio = archivo.read(16)
    archivo.seek(0)
    return any(inicio.startswith(firma) for firma in firmas)


def _validar_tamano(archivo, maximo):
    if archivo.size > maximo:
        raise ValidationError(
            f'El archivo pesa {archivo.size / MB:.1f} MB — el máximo permitido es {maximo / MB:.0f} MB.'
        )


def validar_imagen(archivo):
    """Para ImageField (fotos de publicaciones y de reseñas): tamaño + extensión + firma real + que Pillow logre decodificarla sin ser una bomba de descompresión."""
    _validar_tamano(archivo, TAMANO_MAXIMO_IMAGEN)

    extension = _extension(archivo)
    if extension not in EXTENSIONES_IMAGEN_PERMITIDAS:
        raise ValidationError(f'Formato de imagen no permitido ({extension or "sin extensión"}). Usa JPG, PNG, WEBP o GIF.')

    if not _verificar_firma(archivo, extension):
        raise ValidationError('El contenido del archivo no coincide con su extensión — no parece ser una imagen real.')

    try:
        with warnings.catch_warnings():
            # Por defecto Pillow solo *advierte* (no bloquea) ante una imagen
            # con una cantidad de píxeles sospechosamente alta — acá se trata
            # esa advertencia como error también, no solo el caso extremo que
            # ya bloquea por su cuenta.
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(archivo) as img:
                img.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning, OSError, ValueError):
        raise ValidationError('No se pudo procesar el archivo como imagen — puede estar corrupto, ser demasiado pesado en píxeles, o no ser una imagen real.')
    finally:
        archivo.seek(0)

    escanear_archivo(archivo)


def validar_documento(archivo):
    """Para el FileField de Documento: whitelist de extensión + tamaño + firma real. Nada de .exe/.php/.html/.svg/.js disfrazado de documento."""
    _validar_tamano(archivo, TAMANO_MAXIMO_DOCUMENTO)

    extension = _extension(archivo)
    if extension not in EXTENSIONES_DOCUMENTO_PERMITIDAS:
        raise ValidationError(f'Formato de documento no permitido ({extension or "sin extensión"}). Usa PDF, JPG o PNG.')

    if not _verificar_firma(archivo, extension):
        raise ValidationError('El contenido del archivo no coincide con su extensión — puede estar disfrazado de otro tipo de archivo.')

    # Si es imagen (jpg/png), que además sea una imagen real y no una bomba
    # de descompresión — mismo chequeo que para las fotos.
    if extension in EXTENSIONES_IMAGEN_PERMITIDAS:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(archivo) as img:
                    img.load()
        except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning, OSError, ValueError):
            raise ValidationError('No se pudo procesar el archivo — puede estar corrupto o no ser una imagen real.')
        finally:
            archivo.seek(0)

    escanear_archivo(archivo)
