"""
Reconocimiento facial vía webcam — segundo método de verificación biométrica
exigido por RF001 del PDF de la tesis (junto a la huella dactilar).

Refactor Fase 3: el archivo original NO era Python válido — era un volcado
de bytes en decimal (issue ya documentado en CODE_ANALYSIS_FINDINGS.md).
Se reconstruyó a partir de ese volcado decodificado (comparaba una foto fija
"Images/foto1.jpg" contra el feed de la webcam, dibujando un rectángulo con
la etiqueta "Gaby"/"Desconocido"). Acá queda reescrito como funciones
reutilizables e importables desde `KeyServApp/biometria.py`.

TODO (pendiente, requiere hardware/pruebas manuales):
  - Esto sigue siendo un ESQUELETO funcional, no probado contra una cámara
    real en este entorno (no hay webcam disponible en el entorno de
    desarrollo actual).
  - `cargar_rostro_conocido()` hoy espera una sola imagen de referencia por
    archivo; en la integración real, la imagen de referencia debe salir del
    registro biométrico del Usuario (ver modelo `Usuario`), no de un archivo
    fijo en disco.
  - Falta decidir dónde se persiste el encoding facial calculado (¿un campo
    nuevo en `Usuario`? ¿una tabla aparte?) — no existe todavía en el
    diccionario de datos de la tesis.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def cargar_rostro_conocido(ruta_imagen):
    """
    Carga una imagen de referencia y devuelve su encoding facial (vector de
    128 dimensiones que representa el rostro, calculado por `face_recognition`).
    Lanza `ValueError` si no se detecta ningún rostro en la imagen.
    """
    import face_recognition  # import local: dependencia pesada (dlib), solo se carga si se usa esta función

    imagen = face_recognition.load_image_file(ruta_imagen)
    ubicaciones = face_recognition.face_locations(imagen)
    if not ubicaciones:
        raise ValueError(f'No se detectó ningún rostro en {ruta_imagen}')
    encoding = face_recognition.face_encodings(imagen, known_face_locations=[ubicaciones[0]])[0]
    return encoding


def verificar_rostro(encoding_conocido, mostrar_ventana=False, camara_index=0):
    """
    Abre la webcam y compara cada frame contra `encoding_conocido`.

    Devuelve True apenas encuentra una coincidencia, False si el usuario
    cierra la ventana (tecla ESC) sin que haya match. `mostrar_ventana=True`
    abre una ventana de escritorio con el feed (solo tiene sentido corriendo
    esto localmente, no en un servidor headless — en producción esto debería
    ejecutarse desde el navegador del cliente, no desde el backend).
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
    encoding = cargar_rostro_conocido(ruta_ejemplo)
    print('Verificado:', verificar_rostro(encoding, mostrar_ventana=True))
