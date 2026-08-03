"""
Puente entre la app Django y los scripts de biometría que viven en
`codigo/biometria/` (fuera del árbol de Django, ver docs/RECOMMENDED_ARCHITECTURE.md
§3 — se decidió no duplicar la lógica de procesamiento de imagen dentro de la
app, sino importarla desde ahí).

NUEVO en Fase 3. Antes no existía ningún punto de conexión entre la
biometría y las vistas de Django (RF001 del PDF, verificación biométrica
obligatoria en el registro, no estaba implementado en absoluto).
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)

# codigo/backend/django/KeyServApp/biometria.py -> subir 3 niveles llega a codigo/
_CODIGO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_HUELLA_DIR = os.path.join(_CODIGO_DIR, 'biometria', 'huella')
_FACIAL_DIR = os.path.join(_CODIGO_DIR, 'biometria', 'reconocimiento_facial')

for _dir in (_HUELLA_DIR, _FACIAL_DIR):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)


def procesar_huella_dactilar(ruta_imagen=None):
    """
    Llama al pipeline de `codigo/biometria/huella/IMAGEN_HUELLA.py` y
    devuelve el hash SHA-256 de la huella procesada, o None si algo falla
    (ej. Pillow no está instalado, o la imagen no existe).
    """
    try:
        from IMAGEN_HUELLA import procesar_huella
    except ImportError:
        logger.exception('No se pudo importar el módulo de procesamiento de huella')
        return None

    try:
        return procesar_huella(ruta_imagen)
    except (FileNotFoundError, OSError):
        logger.exception('No se pudo procesar la imagen de huella: %s', ruta_imagen)
        return None


def calcular_encoding_facial(ruta_centro, ruta_derecha, ruta_izquierda):
    """
    Valida una prueba de vida de 3 fotos (de frente, girando a la derecha,
    girando a la izquierda — mismo patrón "challenge-response" que usan la
    mayoría de flujos KYC) y calcula el encoding facial (128 floats) de la
    foto central, listo para guardar en `Usuario.encoding_facial`. Devuelve
    una lista de floats (serializable en el JSONField) o None si algo falla
    (dependencias no instaladas, no se detectó ningún rostro o se detectó más
    de uno en alguna foto, el giro de cabeza no fue válido, o las 3 fotos no
    parecen ser de la misma persona) — mismo patrón "None en vez de reventar
    la vista" que `procesar_huella_dactilar`.
    """
    try:
        from probando_face_recognition import verificar_prueba_de_vida
    except ImportError:
        logger.exception('No se pudo importar el módulo de reconocimiento facial (¿faltan opencv-python/face_recognition?)')
        return None

    try:
        encoding = verificar_prueba_de_vida(ruta_centro, ruta_derecha, ruta_izquierda)
    except (FileNotFoundError, OSError):
        logger.exception('No se pudo leer alguna de las fotos de referencia')
        return None
    except ValueError as error:
        logger.exception('La prueba de vida falló al registrar el rostro: %s', error)
        return None
    return list(float(valor) for valor in encoding)


def verificar_rostro_usuario(encoding_guardado, ruta_centro, ruta_derecha, ruta_izquierda):
    """
    Repite la misma prueba de vida de 3 fotos que `calcular_encoding_facial`
    y compara el encoding resultante contra el encoding de referencia ya
    guardado en `Usuario.encoding_facial`. No abre ninguna webcam — el flujo
    real es que el navegador del cliente capture las 3 fotos y las suba como
    archivos, igual que la huella (ver `verificacion_facial_view` en views.py).
    `verificar_rostro()` con loop de webcam en `probando_face_recognition.py`
    queda solo para pruebas manuales locales (`python probando_face_recognition.py`),
    no para el servidor.

    Devuelve True/False, o None si las dependencias no están instaladas, la
    prueba de vida falló (ver `calcular_encoding_facial`), o no se pudo leer
    alguna foto (no revienta la vista).
    """
    try:
        from probando_face_recognition import verificar_prueba_de_vida, comparar_encodings
    except ImportError:
        logger.exception('No se pudo importar el módulo de reconocimiento facial (¿faltan opencv-python/face_recognition?)')
        return None

    try:
        encoding_nuevo = verificar_prueba_de_vida(ruta_centro, ruta_derecha, ruta_izquierda)
    except (FileNotFoundError, OSError):
        logger.exception('No se pudo leer alguna de las fotos de verificación')
        return None
    except ValueError as error:
        logger.exception('La prueba de vida falló al verificar el rostro: %s', error)
        return None
    return comparar_encodings(encoding_guardado, encoding_nuevo)
