"""
Reconocimiento facial vía webcam — segundo método de verificación biométrica
exigido por RF001 del PDF de la tesis (junto a la huella dactilar).

Refactor Fase 3: el archivo original NO era Python válido — era un volcado
de bytes en decimal (issue ya documentado en CODE_ANALYSIS_FINDINGS.md).
Se reconstruyó a partir de ese volcado decodificado (comparaba una foto fija
"Images/foto1.jpg" contra el feed de la webcam, dibujando un rectángulo con
la etiqueta "Gaby"/"Desconocido"). Acá queda reescrito como funciones
reutilizables e importables desde `KeyServApp/biometria.py`.

`opencv-python`/`face_recognition`/`dlib` ya están instalados y el pipeline
se probó en vivo contra una webcam real (ver CLAUDE.md, Known Issues). Esas
mismas pruebas en vivo mostraron dos problemas reales que este archivo debía
resolver: (1) con poca luz, la foto de una persona distinta podía "matchear"
por error contra la referencia guardada, y (2) el código original tomaba el
primer rostro detectado en la imagen sin rechazar fotos con cero o más de un
rostro. La solución (pedida por el usuario, mismo patrón que usan Mercado
Libre y la mayoría de flujos KYC) es una prueba de vida por desafío: en vez
de comparar una sola foto estática, se piden 3 fotos en secuencia (de frente,
girando a la derecha, girando a la izquierda) y se valida que el giro de
cabeza sea real (`calcular_yaw`, vía `cv2.solvePnP` con un modelo genérico de
6 puntos 3D — mismo enfoque que la mayoría de tutoriales de head-pose con
dlib/OpenCV, no depende de tener una cámara calibrada real) — esto hace mucho
más difícil pasar la verificación con una foto impresa o un archivo, y de
paso el requisito de "un solo rostro por foto" cierra el problema (2).
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Umbrales en grados para la prueba de vida (ver `verificar_prueba_de_vida`).
# Calibrados contra pruebas en vivo reales (ver CLAUDE.md, Known Issues) — si
# se ajusta la iluminación/cámara y empieza a fallar en el mundo real, este es
# el primer lugar para tocar.
UMBRAL_YAW_CENTRO = 15.0
UMBRAL_YAW_GIRO = 15.0


def _detectar_rostro_unico(imagen):
    """
    Devuelve `(ubicacion, landmarks)` del único rostro presente en `imagen`
    (ya cargada con `face_recognition.load_image_file`). Lanza `ValueError`
    si detecta cero rostros o más de uno — a diferencia del código original,
    acá una foto con dos personas no se procesa silenciosamente eligiendo la
    primera, se rechaza.
    """
    import face_recognition

    ubicaciones = face_recognition.face_locations(imagen)
    if not ubicaciones:
        # El detector rápido (HOG, el default) puede no encontrar nada con la
        # cabeza girada — antes de rendirse, reintentar con el modelo 'cnn'
        # (más lento, pero más robusto a ángulos pronunciados).
        ubicaciones = face_recognition.face_locations(imagen, model='cnn')
    if not ubicaciones:
        raise ValueError('No se detectó ningún rostro en la imagen')
    if len(ubicaciones) > 1:
        raise ValueError('Se detectó más de un rostro en la imagen')
    landmarks = face_recognition.face_landmarks(imagen, face_locations=ubicaciones)[0]
    return ubicaciones[0], landmarks


def calcular_yaw(landmarks, ancho, alto):
    """
    Estima el ángulo de yaw (giro izquierda/derecha de la cabeza, en grados)
    a partir de 6 puntos 2D de los landmarks de dlib (punta de la nariz,
    mentón, esquinas externas de los ojos, comisuras de la boca) y un modelo
    3D genérico de rostro, vía `cv2.solvePnP` — el mismo modelo de 6 puntos
    que usan la mayoría de tutoriales de head-pose estimation con dlib/OpenCV
    (ver fuentes citadas en el plan/commit). No hay una cámara calibrada real
    detrás de esto, así que la matriz de cámara se aproxima a partir del
    tamaño de la imagen (mismo truco que esos mismos tutoriales) — es una
    estimación aproximada, no una medición precisa, pero alcanza para
    distinguir "de frente" de "girado" a ojo.
    """
    import cv2
    import numpy as np

    puntos_2d = np.array([
        landmarks['nose_tip'][2],
        landmarks['chin'][8],
        landmarks['left_eye'][0],
        landmarks['right_eye'][3],
        landmarks['top_lip'][0],
        landmarks['top_lip'][6],
    ], dtype='double')

    puntos_3d = np.array([
        (0.0, 0.0, 0.0),
        (0.0, -330.0, -65.0),
        (-225.0, 170.0, -135.0),
        (225.0, 170.0, -135.0),
        (-150.0, -150.0, -125.0),
        (150.0, -150.0, -125.0),
    ])

    matriz_camara = np.array([
        [ancho, 0, ancho / 2],
        [0, ancho, alto / 2],
        [0, 0, 1],
    ], dtype='double')

    _, rvec, _ = cv2.solvePnP(puntos_3d, puntos_2d, matriz_camara, np.zeros((4, 1)))
    matriz_rotacion, _ = cv2.Rodrigues(rvec)
    angulos = cv2.RQDecomp3x3(matriz_rotacion)[0]
    return angulos[1]


def verificar_prueba_de_vida(ruta_centro, ruta_derecha, ruta_izquierda):
    """
    Valida una prueba de vida de 3 fotos (de frente, girando a la derecha,
    girando a la izquierda) y devuelve el encoding facial (128 floats) de la
    foto central si todo es válido. Lanza `ValueError` con el motivo
    específico si: alguna foto tiene cero o más de un rostro, la foto
    "centro" no está razonablemente de frente, alguno de los 2 giros no
    supera el umbral esperado en su dirección, o las 3 fotos no parecen ser
    de la misma persona.
    """
    import face_recognition

    imagen_centro = face_recognition.load_image_file(ruta_centro)
    imagen_derecha = face_recognition.load_image_file(ruta_derecha)
    imagen_izquierda = face_recognition.load_image_file(ruta_izquierda)

    ubicacion_centro, landmarks_centro = _detectar_rostro_unico(imagen_centro)
    ubicacion_derecha, landmarks_derecha = _detectar_rostro_unico(imagen_derecha)
    ubicacion_izquierda, landmarks_izquierda = _detectar_rostro_unico(imagen_izquierda)

    alto_centro, ancho_centro = imagen_centro.shape[:2]
    alto_derecha, ancho_derecha = imagen_derecha.shape[:2]
    alto_izquierda, ancho_izquierda = imagen_izquierda.shape[:2]

    yaw_centro = calcular_yaw(landmarks_centro, ancho_centro, alto_centro)
    yaw_derecha = calcular_yaw(landmarks_derecha, ancho_derecha, alto_derecha)
    yaw_izquierda = calcular_yaw(landmarks_izquierda, ancho_izquierda, alto_izquierda)

    if abs(yaw_centro) > UMBRAL_YAW_CENTRO:
        raise ValueError(f'La foto de frente no está suficientemente centrada (yaw={yaw_centro:.1f}°)')
    # Con la cámara frontal del navegador (efecto espejo), girar hacia la
    # derecha de la pantalla dio yaw negativo en las pruebas iniciales en
    # vivo — si al recalibrar se observa lo contrario, invertir estas dos
    # comparaciones (no los umbrales).
    if yaw_derecha > -UMBRAL_YAW_GIRO:
        raise ValueError(f'No se detectó un giro real hacia la derecha (yaw={yaw_derecha:.1f}°)')
    if yaw_izquierda < UMBRAL_YAW_GIRO:
        raise ValueError(f'No se detectó un giro real hacia la izquierda (yaw={yaw_izquierda:.1f}°)')

    encoding_centro = face_recognition.face_encodings(imagen_centro, known_face_locations=[ubicacion_centro])[0]
    encoding_derecha = face_recognition.face_encodings(imagen_derecha, known_face_locations=[ubicacion_derecha])[0]
    encoding_izquierda = face_recognition.face_encodings(imagen_izquierda, known_face_locations=[ubicacion_izquierda])[0]

    if not face_recognition.compare_faces([encoding_centro], encoding_derecha)[0]:
        raise ValueError('La foto girando a la derecha no parece ser la misma persona que la foto de frente')
    if not face_recognition.compare_faces([encoding_centro], encoding_izquierda)[0]:
        raise ValueError('La foto girando a la izquierda no parece ser la misma persona que la foto de frente')

    return encoding_centro


def comparar_encodings(encoding_a, encoding_b, tolerancia=0.6):
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
    manual/local únicamente — el flujo web real usa `verificar_prueba_de_vida`.
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
