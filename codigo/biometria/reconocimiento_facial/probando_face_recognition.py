"""
Reconocimiento facial vía webcam — segundo método de verificación biométrica
exigido por RF001 del PDF de la tesis (junto a la huella dactilar).

Refactor Fase 3: el archivo original NO era Python válido — era un volcado
de bytes en decimal (issue ya documentado en CODE_ANALYSIS_FINDINGS.md).
Se reconstruyó a partir de ese volcado decodificado (comparaba una foto fija
"Images/foto1.jpg" contra el feed de la webcam, dibujando un rectángulo con
la etiqueta "Gaby"/"Desconocido"). Acá queda reescrito como funciones
reutilizables e importables desde `KeyServApp/biometria.py`.

`opencv-python`/`face_recognition`/`dlib` ya están instalados. Pruebas en
vivo contra una webcam real mostraron dos problemas con la comparación de
1 sola foto original: (1) con poca luz, la foto de una persona distinta
podía "matchear" por error contra la referencia guardada, y (2) el código
original tomaba el primer rostro detectado en la imagen sin rechazar fotos
con cero o más de un rostro. Una primera solución probó una prueba de vida
de 3 fotos con giro de cabeza (de frente/derecha/izquierda, vía
`cv2.solvePnP`) — funcionó, pero en el uso real resultó tediosa y lenta de
capturar bien. Se reemplaza por una prueba de vida de parpadeo: se captura
una ráfaga corta de cuadros mientras el usuario mira a la cámara y parpadea
una vez (mismo patrón que usan sistemas de e-KYC livianos que no quieren
pedir múltiples poses), se mide el Eye Aspect Ratio (EAR, Soukupová & Čech)
de cada cuadro con los landmarks de ojos que `face_recognition`/dlib ya
calculan, y se confirma que hubo una transición ojos-abiertos → cerrados →
abiertos otra vez antes de aceptar el cuadro más nítido/mejor iluminado
(ojos abiertos) para el encoding. Una foto impresa o un archivo estático no
puede parpadear, así que esto cubre el mismo caso de spoofing que buscaba
cubrir el giro de cabeza, con una sola acción del usuario en vez de 3 poses
distintas. El requisito de "un solo rostro por cuadro" sigue cerrando el
problema (2), y un chequeo de brillo/nitidez por cuadro más una tolerancia
de comparación más estricta (0.5 en vez de 0.6) atacan el problema (1)
directamente, en vez de depender de la pose.

Una prueba en vivo con poca luz (ver CLAUDE.md) encontró un tercer problema,
de rendimiento: `_detectar_rostro_unico` tenía un fallback a
`model='cnn'` cuando el detector rápido (HOG) no encontraba nada, y con
poca luz HOG fallaba en casi todos los cuadros de la ráfaga — el fallback
lento se disparaba para cada uno y una ráfaga entera tardó ~13 minutos,
bloqueando el resto del servidor de paso. Se sacó el fallback a CNN por
completo y el chequeo de brillo/nitidez ahora corre POR CUADRO, antes de
intentar detectar nada — un cuadro oscuro se descarta con un cálculo barato
en vez de pagar el costo de detección facial.
"""
import math
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Umbral de EAR: por debajo, se considera que los ojos están cerrados (rango
# típico citado en la literatura de blink-detection con dlib es 0.2-0.25).
UMBRAL_EAR_CERRADO = 0.21

# Cuántos cuadros con exactamente un rostro detectado se necesitan como
# mínimo (de los ~15-20 que manda el navegador) para poder evaluar el
# parpadeo con confianza — unos pocos cuadros perdidos por motion blur
# durante el parpadeo mismo son normales y no deberían tirar abajo la prueba.
FRAMES_MIN_PARPADEO = 8

# Chequeo de calidad sobre el cuadro elegido para el encoding — calibrar acá
# primero si en la práctica rechaza fotos que deberían pasar (o al revés).
BRILLO_MINIMO = 40.0
NITIDEZ_MINIMA = 30.0

# Tolerancia de `face_recognition.compare_faces` — bajada de 0.6 (default de
# la librería) a 0.5 después de que pruebas en vivo con poca luz mostraran
# falsos positivos entre personas distintas con el valor por defecto.
TOLERANCIA_COMPARACION = 0.5


def _distancia(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def _ear_de_ojo(puntos):
    """
    Eye Aspect Ratio de un ojo a partir de sus 6 puntos 2D en el orden que
    ya entrega `face_recognition.face_landmarks` (`left_eye`/`right_eye`,
    mismo orden que el modelo de 68 puntos de dlib: comisura, 2 párpado
    superior, comisura, 2 párpado inferior) — fórmula estándar de
    Soukupová & Čech: (dist(p2,p6) + dist(p3,p5)) / (2 * dist(p1,p4)).
    Baja cuando el ojo se cierra porque la distancia vertical colapsa
    mientras la horizontal (ancho del ojo) se mantiene.
    """
    vertical_1 = _distancia(puntos[1], puntos[5])
    vertical_2 = _distancia(puntos[2], puntos[4])
    horizontal = _distancia(puntos[0], puntos[3])
    return (vertical_1 + vertical_2) / (2.0 * horizontal)


def _ear_promedio_de_landmarks(landmarks):
    """Promedio del EAR de ambos ojos — más robusto que un solo ojo si algún landmark queda un poco torcido."""
    return (_ear_de_ojo(landmarks['left_eye']) + _ear_de_ojo(landmarks['right_eye'])) / 2.0


def _hubo_parpadeo(ears):
    """
    True si la secuencia de EAR (en orden temporal) tiene un parpadeo real:
    al menos un cuadro con los ojos abiertos, seguido de al menos uno con
    los ojos cerrados, seguido de al menos uno con los ojos abiertos otra
    vez. Un solo cuadro "cerrado" aislado sin apertura previa no cuenta (evita
    falsos positivos por un cuadro borroso al arrancar la ráfaga).
    """
    estado = 'esperando_apertura_inicial'
    for ear in ears:
        cerrado = ear < UMBRAL_EAR_CERRADO
        if estado == 'esperando_apertura_inicial' and not cerrado:
            estado = 'esperando_cierre'
        elif estado == 'esperando_cierre' and cerrado:
            estado = 'esperando_reapertura'
        elif estado == 'esperando_reapertura' and not cerrado:
            return True
    return False


def _detectar_rostro_unico(imagen, opcional=False):
    """
    Devuelve `(ubicacion, landmarks)` del único rostro presente en `imagen`
    (ya cargada con `face_recognition.load_image_file`). Si detecta cero
    rostros o más de uno: lanza `ValueError`, o devuelve `None` si
    `opcional=True` — usado por `verificar_prueba_de_vida_parpadeo` para
    descartar en silencio los cuadros ruidosos de una ráfaga en vez de
    abortar toda la prueba de vida por un solo cuadro malo.
    """
    import face_recognition

    # Solo HOG (el detector rápido, default) — una prueba en vivo con poca
    # luz mostró que el fallback a `model='cnn'` que este código tenía antes
    # convertía cada cuadro oscuro en varios segundos de cómputo sin GPU
    # (una ráfaga entera con poca luz tardó ~13 minutos y bloqueó el resto
    # del servidor). Ya no giramos la cabeza en este flujo (solo de frente),
    # así que HOG alcanza, y `verificar_prueba_de_vida_parpadeo` ya descarta
    # los cuadros oscuros/borrosos ANTES de intentar detectar nada — un
    # cuadro que llega hasta acá ya tiene buena luz.
    ubicaciones = face_recognition.face_locations(imagen)
    if not ubicaciones or len(ubicaciones) > 1:
        if opcional:
            return None
        motivo = 'No se detectó ningún rostro en la imagen' if not ubicaciones else 'Se detectó más de un rostro en la imagen'
        raise ValueError(motivo)
    landmarks = face_recognition.face_landmarks(imagen, face_locations=ubicaciones)[0]
    return ubicaciones[0], landmarks


def _calidad_de_imagen_aceptable(imagen):
    """
    Chequeo barato de brillo/nitidez sobre el cuadro que se va a usar para
    el encoding — el problema real que motivó esto no era la falta de
    parpadeo, era que con poca luz una foto de otra persona podía matchear
    por error (ver docstring del módulo). Devuelve `(True, None)` o
    `(False, motivo)`.
    """
    import cv2

    gris = cv2.cvtColor(imagen, cv2.COLOR_RGB2GRAY)
    brillo = float(gris.mean())
    nitidez = float(cv2.Laplacian(gris, cv2.CV_64F).var())
    if brillo < BRILLO_MINIMO:
        return False, 'La imagen está muy oscura — probá con más luz.'
    if nitidez < NITIDEZ_MINIMA:
        return False, 'La imagen está borrosa — mantené la cámara firme durante la captura.'
    return True, None


def verificar_prueba_de_vida_parpadeo(rutas_frames):
    """
    Valida una prueba de vida por parpadeo sobre una ráfaga de cuadros
    capturados en vivo (`rutas_frames`, en orden temporal) y devuelve el
    encoding facial (128 floats) del mejor cuadro si todo es válido.

    Por cada cuadro, primero corre `_calidad_de_imagen_aceptable` (brillo/
    nitidez, cálculo barato con numpy/cv2) y recién si pasa intenta detectar
    el rostro (`_detectar_rostro_unico`, más caro) — en ese orden, y no al
    revés, a propósito: una prueba en vivo con poca luz mostró que
    detectar/descartar primero y recién filtrar por calidad al final dejaba
    pagar el costo completo de detección facial en cuadros que de entrada
    iban a ser descartados por oscuros. Descarta en silencio los cuadros que
    no pasan calidad o donde no se detecta exactamente un rostro (normal
    durante el parpadeo mismo o por motion blur). Lanza `ValueError` con el
    motivo específico si quedan menos de `FRAMES_MIN_PARPADEO` cuadros
    utilizables, o si la secuencia de EAR no muestra un parpadeo real. El
    cuadro elegido para el encoding es el de mayor EAR (ojos más abiertos)
    entre los utilizables.
    """
    import face_recognition

    candidatos = []
    for ruta in rutas_frames:
        imagen = face_recognition.load_image_file(ruta)
        if not _calidad_de_imagen_aceptable(imagen)[0]:
            continue
        deteccion = _detectar_rostro_unico(imagen, opcional=True)
        if deteccion is None:
            continue
        ubicacion, landmarks = deteccion
        candidatos.append((_ear_promedio_de_landmarks(landmarks), imagen, ubicacion))

    if len(candidatos) < FRAMES_MIN_PARPADEO:
        raise ValueError('No se detectó tu rostro con claridad durante la captura — mirá directo a la cámara, con buena luz, y probá de nuevo.')

    if not _hubo_parpadeo([ear for ear, _, _ in candidatos]):
        raise ValueError('No se detectó un parpadeo real durante la captura — mirá a la cámara y parpadeá una vez mientras se captura.')

    _, imagen_elegida, ubicacion_elegida = max(candidatos, key=lambda c: c[0])
    return face_recognition.face_encodings(imagen_elegida, known_face_locations=[ubicacion_elegida])[0]


def comparar_encodings(encoding_a, encoding_b, tolerancia=TOLERANCIA_COMPARACION):
    """Wrapper de `face_recognition.compare_faces` — para que `biometria.py` no tenga que importar `face_recognition` directamente."""
    import face_recognition

    return bool(face_recognition.compare_faces([encoding_a], encoding_b, tolerance=tolerancia)[0])


def verificar_rostro(encoding_conocido, mostrar_ventana=False, camara_index=0):
    """
    Abre la webcam y compara cada frame contra `encoding_conocido`.

    Devuelve True apenas encuentra una coincidencia, False si el usuario
    cierra la ventana (tecla ESC) sin que haya match. `mostrar_ventana=True`
    abre una ventana de escritorio con el feed (solo tiene sentido corriendo
    esto localmente, no en un servidor headless — en producción esto debería
    ejecutarse desde el navegador del cliente, no desde el backend). Uso
    manual/local únicamente — el flujo web real usa
    `verificar_prueba_de_vida_parpadeo`.
    """
    import cv2
    import face_recognition

    captura = cv2.VideoCapture(camara_index, cv2.CAP_DSHOW)
    encontrado = False
    try:
        while True:
            ret, frame = captura.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            ubicaciones = face_recognition.face_locations(frame, model='cnn')
            for ubicacion in ubicaciones:
                encoding_frame = face_recognition.face_encodings(frame, known_face_locations=[ubicacion])[0]
                resultado = face_recognition.compare_faces([encoding_conocido], encoding_frame)
                if resultado[0]:
                    encontrado = True
                    texto, color = 'Verificado', (0, 220, 125)
                else:
                    texto, color = 'Desconocido', (50, 50, 255)
                top, right, bottom, left = ubicacion
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, texto, (left, bottom + 20), 2, 0.7, (255, 255, 255), 1)

            if mostrar_ventana:
                cv2.imshow('Verificación facial - KeyServ', frame)

            if encontrado:
                break
            tecla = cv2.waitKey(1)
            if tecla & 0xFF == 27:  # ESC
                break
    finally:
        captura.release()
        cv2.destroyAllWindows()

    return encontrado


if __name__ == '__main__':
    # Uso manual/pruebas: python codigo/biometria/reconocimiento_facial/probando_face_recognition.py
    # TODO: reemplazar por una imagen de referencia real antes de probar.
    ruta_ejemplo = os.path.join(BASE_DIR, 'Images', 'foto1.jpg')
    import face_recognition
    imagen_ejemplo = face_recognition.load_image_file(ruta_ejemplo)
    _, landmarks_ejemplo = _detectar_rostro_unico(imagen_ejemplo)
    encoding = face_recognition.face_encodings(imagen_ejemplo)[0]
    print('Verificado:', verificar_rostro(encoding, mostrar_ventana=True))
