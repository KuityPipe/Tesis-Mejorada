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


def verificar_rostro_usuario(ruta_imagen_referencia, mostrar_ventana=False):
    """
    TODO: esqueleto — llama a `codigo/biometria/reconocimiento_facial/probando_face_recognition.py`.
    Requiere una imagen de referencia ya guardada del usuario y una webcam
    disponible; no se puede validar en este entorno (sin cámara). Devuelve
    None si las dependencias (opencv-python/face_recognition) no están
    instaladas, en vez de reventar la vista que la llama.
    """
    try:
        from probando_face_recognition import cargar_rostro_conocido, verificar_rostro
    except ImportError:
        logger.exception('No se pudo importar el módulo de reconocimiento facial (¿faltan opencv-python/face_recognition?)')
        return None

    encoding = cargar_rostro_conocido(ruta_imagen_referencia)
    return verificar_rostro(encoding, mostrar_ventana=mostrar_ventana)
