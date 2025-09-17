import cv2                       # OpenCV: captura de cámara y manejo de imágenes
import mediapipe as mp           # MediaPipe: modelo preentrenado para detectar manos y landmarks

# -----------------------
# Inicialización de MediaPipe
# -----------------------
mp_hands = mp.solutions.hands    # acceso a la solución "Hands" de MediaPipe
mp_draw = mp.solutions.drawing_utils  # utilidades para dibujar landmarks y conexiones

# Crear el objeto "hands" que hará la detección en vídeo.
# Parametros:
# - static_image_mode=False -> modo vídeo (usa tracking temporal para ser más eficiente).
# - max_num_hands=1 -> detectar como mucho 1 mano (reduce coste). Cambia si quieres multi-mano.
# - min_detection_confidence -> umbral para considerar una detección inicial.
# - min_tracking_confidence -> umbral para mantener el tracking entre frames.
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# -----------------------
# Abrir la cámara
# -----------------------
cap = cv2.VideoCapture(0)  # 0 = cámara por defecto (portátil). Cambia a 1,2,... si tienes varias.

# Bucle principal: se ejecuta mientras la cámara esté abierta
while cap.isOpened():
    ret, frame = cap.read()   # lectura de un frame (ret=False si hay fallo)
    if not ret:
        break                 # salir si no se puede leer el frame

    # MediaPipe trabaja con imágenes en RGB; OpenCV da BGR por defecto, así que convertimos.
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Procesar el frame con MediaPipe: devuelve detecciones, landmarks y handedness
    result = hands.process(rgb_frame)

    # Si detectó al menos una mano, result.multi_hand_landmarks no es None
    if result.multi_hand_landmarks:
        # mediaPipe puede devolver varias manos; iteramos (aunque max_num_hands=1 en este ejemplo)
        for hand_landmarks in result.multi_hand_landmarks:
            # Dibuja sobre el frame original (BGR) los 21 puntos y sus conexiones
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # 'landmark' es una lista de 21 objetos, cada uno con .x, .y, .z (normalizados 0..1)
            lm = hand_landmarks.landmark

            # Pares (tip, comparador) para cada dedo: (índice_del_tip, índice_del_punto_con_el_que_comparar)
            # estos índices siguen el mapeado de MediaPipe:
            # 4=pulgar_tips, 8=indice_tip, 12=medio_tip, 16=anular_tip, 20=meñique_tip
            # se compara con la articulación anterior (3 para pulgar, 6 para índice, etc.)
            fingers = [
                (4, 3),    # pulgar (punta, articulación precedente)
                (8, 6),    # índice
                (12, 10),  # medio
                (16, 14),  # anular
                (20, 18),  # meñique
            ]

            dedos_levantados = 0  # contador que iremos incrementando

            # Pulgar: el patrón de apertura es lateral (x), no vertical (y).
            # Heurística simple para distinguir mano derecha/izquierda:
            # si lm[17].x < lm[5].x -> la mano está orientada como "derecha" en la vista de la cámara
            # (esta es una aproximación; también puedes usar result.multi_handedness si lo necesitas)
            if lm[17].x < lm[5].x:  # mano derecha (aprox)
                # Si la x de la punta (4) es menor (más a la izquierda) que la x de 3 -> pulgar extendido
                if lm[4].x < lm[3].x:
                    dedos_levantados += 1
            else:  # mano izquierda (aprox)
                # para mano izquierda invertimos la comparación
                if lm[4].x > lm[3].x:
                    dedos_levantados += 1

            # Para los demás dedos (índice->meñique) comparamos verticalmente:
            # si la y del tip < y de la articulación (tip más arriba en la imagen), está extendido.
            # ojo: en coordenadas de imagen y=0 está arriba, y aumenta hacia abajo.
            for tip, dip in fingers[1:]:
                if lm[tip].y < lm[dip].y:
                    dedos_levantados += 1

            # Mostrar el resultado en consola (puedes cambiar por dibujo en la imagen)
            print(f'Dedos levantados: {dedos_levantados}')

    # Mostrar la imagen con los landmarks dibujados
    cv2.imshow("Deteccion de mano", frame)

    # Esperar 1 ms por tecla; si se pulsa ESC (27) salimos del bucle
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Liberar recursos: cerrar cámara y ventanas
cap.release()
cv2.destroyAllWindows()
