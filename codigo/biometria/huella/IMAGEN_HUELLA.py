"""
Pipeline de procesamiento de huella dactilar: carga -> binarización ->
adelgazamiento -> poda -> hash SHA-256 final.

Refactor Fase 3: antes este archivo ejecutaba todo el pipeline como código
top-level apenas se importaba (incluyendo `img.show()`, que abre una ventana
de escritorio — inutilizable en un servidor). Ahora la lógica vive en
funciones reutilizables; `procesar_huella()` es el punto de entrada que usa
`KeyServApp/biometria.py` para integrarlo a Django. El bloque `__main__` de
abajo permite seguir corriendo este archivo como script suelto para pruebas
manuales (`python codigo/biometria/huella/IMAGEN_HUELLA.py`), igual que antes.

Ver codigo/viejo/backup_fase3/biometria_huella/IMAGEN_HUELLA.py para la
versión previa (script plano, sin funciones).
"""
from PIL import Image
import math
import hashlib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _ruta(*partes):
    """Arma una ruta absoluta dentro de esta carpeta (evita depender del cwd desde el que se ejecute)."""
    return os.path.join(BASE_DIR, *partes)


def carga(img):
    """Convierte la imagen PIL en su arreglo de píxeles editable."""
    arr = img.load()
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            arr[x, y] = img.getpixel((x, y))
    return arr


def binarizacion(img, umbral):
    """Convierte cada píxel a blanco (255) o negro (0) según un umbral de intensidad."""
    arrBina = img.load()
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            pixel = img.getpixel((x, y))
            arrBina[x, y] = 255 if pixel > umbral else 0
    return arrBina


def _convolucion_bordes(img, mascaraH, mascaraV):
    """
    Aplica un operador tipo Sobel (una máscara horizontal y una vertical) a
    cada píxel interior de la imagen. La usan tanto `adelgazamiento` como
    `poda` — son el mismo cálculo, solo cambian las máscaras de entrada.
    """
    arr = img.load()

    Ha, Hb, Hc = mascaraH[0]
    Hd, He, Hf = mascaraH[1]
    Hg, Hh, Hi = mascaraH[2]

    Va, Vb, Vc = mascaraV[0]
    Vd, Ve, Vf = mascaraV[1]
    Vg, Vh, Vi = mascaraV[2]

    for x in range(1, img.size[0] - 1):
        for y in range(1, img.size[1] - 1):
            Ia = img.getpixel((x - 1, y - 1))
            Ib = img.getpixel((x - 1, y))
            Ic = img.getpixel((x - 1, y + 1))
            Id = img.getpixel((x, y - 1))
            Ie = img.getpixel((x, y))
            If = img.getpixel((x, y + 1))
            Ig = img.getpixel((x + 1, y - 1))
            Ih = img.getpixel((x + 1, y))
            Ii = img.getpixel((x + 1, y + 1))
            Gx = Ha * Ia + Hb * Ib + Hc * Ic + Hd * Id + He * Ie + Hf * If + Hg * Ig + Hh * Ih + Hi * Ii
            Gy = Va * Ia + Vb * Ib + Vc * Ic + Vd * Id + Ve * Ie + Vf * If + Vg * Ig + Vh * Ih + Vi * Ii
            valor = math.sqrt(Gx * Gx + Gy * Gy)
            if valor > 255.0:
                valor = 255.0
            arr[x - 1, y - 1] = int(valor)
    return arr


# Máscaras de adelgazamiento (reduce el grosor de las crestas de la huella,
# evita ruido si el dedo se movió al escanear).
_THINNING_X = [
    [0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 1.0],
    [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [1.0, 0.0, 0.0],
    [1.0, 1.0, 1.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0],
    [0.0, 0.0, 1.0], [0.0, 1.0, 1.0], [0.0, 0.0, 1.0],
]
_THINNING_Y = [
    [0.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0], [1.0, 1.0, 0.0], [0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0], [0.0, 1.0, 1.0], [0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0], [0.0, 1.0, 1.0], [0.0, 1.0, 0.0],
]


def adelgazamiento(img, mascaraH, mascaraV):
    """Adelgaza las crestas de la huella ya binarizada."""
    return _convolucion_bordes(img, mascaraH, mascaraV)


def poda(img, mascaraH, mascaraV):
    """Pule/limpia los bordes de la huella ya adelgazada."""
    return _convolucion_bordes(img, mascaraH, mascaraV)


def archivo_hash(ruta_imagen):
    """Calcula el SHA-256 del contenido binario de un archivo de imagen."""
    imghash = hashlib.sha256()
    with open(ruta_imagen, 'rb') as file:
        imghash.update(file.read())
    return imghash.hexdigest()


def procesar_huella(ruta_imagen_entrada=None):
    """
    Punto de entrada del pipeline completo. Recibe la ruta de una imagen de
    huella (por defecto, la imagen de ejemplo del repo) y devuelve el hash
    SHA-256 final, que es lo que se compara/guarda como "contraseña dactilar".
    """
    ruta_imagen_entrada = ruta_imagen_entrada or _ruta('Huella Imagen', 'imagenInput', 'ejemplohuella.png')

    huella = Image.open(ruta_imagen_entrada).convert('L')
    carga(huella)
    ruta_carga = _ruta('Huella Imagen', 'imagenOutput', 'cargahuella.png')
    huella.save(ruta_carga)

    huella = Image.open(ruta_carga).convert('L')
    binarizacion(huella, 128)
    ruta_binarizada = _ruta('Huella Imagen', 'imagenOutput', 'Binarihuella.png')
    huella.save(ruta_binarizada)

    img = Image.open(ruta_binarizada).convert('L')
    adelgazamiento(img, _THINNING_X, _THINNING_Y)
    ruta_adelgazada = _ruta('Huella Imagen', 'imagenOutput', 'Adelgahuella.png')
    img.save(ruta_adelgazada)

    img = Image.open(ruta_adelgazada).convert('L')
    poda(img, _THINNING_X, _THINNING_Y)
    ruta_podada = _ruta('Huella Imagen', 'imagenOutput', 'Podahuella.png')
    img.save(ruta_podada)

    hash_final = archivo_hash(ruta_podada)

    ruta_codigo = _ruta('Contraseña dactilar', 'CodigoHuella.txt')
    with open(ruta_codigo, 'w') as codigo:
        codigo.write(hash_final)

    return hash_final


if __name__ == '__main__':
    # Uso manual/pruebas: python codigo/biometria/huella/IMAGEN_HUELLA.py
    print(procesar_huella())
