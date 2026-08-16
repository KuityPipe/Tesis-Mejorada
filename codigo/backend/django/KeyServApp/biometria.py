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
_FACIAL_DIR = os.path.join(_CODIGO_DIR, 'biometria', 'reconocimiento_facial')

if _FACIAL_DIR not in sys.path:
    sys.path.insert(0, _FACIAL_DIR)


def calcular_encoding_facial(rutas_frames):
    """
    Valida una prueba de vida por parpadeo (ver
    `probando_face_recognition.verificar_prueba_de_vida_parpadeo`) sobre una
    ráfaga de cuadros capturados en vivo (`rutas_frames`, en orden temporal)
    y calcula el encoding facial (128 floats) del cuadro elegido, listo para
    guardar en `Usuario.encoding_facial`. Devuelve una lista de floats
    (serializable en el JSONField) o None si algo falla (dependencias no
    instaladas, no se detectó un rostro con claridad en suficientes cuadros,
    no hubo un parpadeo real, o ningún cuadro disponible pasa el chequeo de
    brillo/nitidez) — nunca revienta la vista, devuelve None.
    """
    try:
        from probando_face_recognition import verificar_prueba_de_vida_parpadeo
    except ImportError:
        logger.exception('No se pudo importar el módulo de reconocimiento facial (¿faltan opencv-python/face_recognition?)')
        return None

    try:
        encoding = verificar_prueba_de_vida_parpadeo(rutas_frames)
    except (FileNotFoundError, OSError):
        logger.exception('No se pudo leer alguno de los cuadros de la ráfaga')
        return None
    except ValueError as error:
        logger.exception('La prueba de vida por parpadeo falló al registrar el rostro: %s', error)
        return None
    except ImportError:
        logger.exception('No se pudo importar opencv-python/face_recognition al ejecutar la prueba de vida')
        return None
    return list(float(valor) for valor in encoding)


def verificar_rostro_usuario(encoding_guardado, rutas_frames):
    """
    Repite la misma prueba de vida por parpadeo que `calcular_encoding_facial`
    y compara el encoding resultante contra el encoding de referencia ya
    guardado en `Usuario.encoding_facial`. No abre ninguna webcam — el flujo
    real es que el navegador del cliente capture la ráfaga y la suba como
    archivos (ver `verificacion_facial_view` en views.py).
    `verificar_rostro()` con loop de webcam en `probando_face_recognition.py`
    queda solo para pruebas manuales locales (`python probando_face_recognition.py`),
    no para el servidor.

    Devuelve True/False, o None si las dependencias no están instaladas, la
    prueba de vida falló (ver `calcular_encoding_facial`), o no se pudo leer
    algún cuadro (no revienta la vista).
    """
    try:
        from probando_face_recognition import verificar_prueba_de_vida_parpadeo, comparar_encodings
    except ImportError:
        logger.exception('No se pudo importar el módulo de reconocimiento facial (¿faltan opencv-python/face_recognition?)')
        return None

    try:
        encoding_nuevo = verificar_prueba_de_vida_parpadeo(rutas_frames)
    except (FileNotFoundError, OSError):
        logger.exception('No se pudo leer alguno de los cuadros de la ráfaga de verificación')
        return None
    except ValueError as error:
        logger.exception('La prueba de vida por parpadeo falló al verificar el rostro: %s', error)
        return None
    except ImportError:
        logger.exception('No se pudo importar opencv-python/face_recognition al ejecutar la prueba de vida')
        return None
    return comparar_encodings(encoding_guardado, encoding_nuevo)
