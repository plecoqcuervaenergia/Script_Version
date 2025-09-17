# contar_dedos_mejorado.py
import cv2
import mediapipe as mp
import math
import os
import time
from collections import deque

# ---------------------------
# Utilidades geométricas
# ---------------------------
def angle_between(a, b, c):
    """
    Devuelve ángulo en grados en el punto b (a-b-c).
    a, b, c son tuplas (x, y) en coordenadas normalizadas o píxeles.
    """
    bax = a[0] - b[0]; bay = a[1] - b[1]
    bcx = c[0] - b[0]; bcy = c[1] - b[1]
    dot = bax * bcx + bay * bcy
    mag1 = math.hypot(bax, bay)
    mag2 = math.hypot(bcx, bcy)
    if mag1 * mag2 == 0:
        return 0.0
    cosang = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cosang))

def lm_to_xy(lm, w, h):
    """Convierte landmark (normalizado) a coordenadas de píxel (x,y)."""
    return (lm.x * w, lm.y * h)

# ---------------------------
# Inicialización MediaPipe
# ---------------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1,
                       min_detection_confidence=0.6,
                       min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)
# opcional: ajustar resolución si quieres más FPS
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Suavizado: ventana móvil de N últimos contadores
SMOOTH_N = 5
last_counts = deque(maxlen=SMOOTH_N)

# Carpeta para dataset (si quieres guardar)
DATASET_DIR = "dataset"
os.makedirs(DATASET_DIR, exist_ok=True)
for i in range(6):
    os.makedirs(os.path.join(DATASET_DIR, str(i)), exist_ok=True)

print("Teclas: ESC para salir. Teclas 0..5 para guardar imagen etiquetada en dataset/<n>/")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    h, w, _ = frame.shape

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    dedos_levantados = None  # por defecto no detectado

    if result.multi_hand_landmarks:
        # usamos solo la primera mano (max_num_hands=1)
        hand_landmarks = result.multi_hand_landmarks[0]
        # handedness (derecha/izquierda)
        hand_label = None
        if result.multi_handedness:
            hand_label = result.multi_handedness[0].classification[0].label  # 'Left' o 'Right'

        # Dibujar landmarks para debug
        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        lm = hand_landmarks.landmark  # lista de 21 landmarks (normalizados)

        # Calculamos ángulos (usamos puntos en coordenadas normalizadas, da igual escala)
        # Pulgar: usar 1-2-4 (base- joint -tip) -> ángulo en 2
        a_thumb = (lm[1].x, lm[1].y)
        b_thumb = (lm[2].x, lm[2].y)
        c_thumb = (lm[4].x, lm[4].y)
        angle_thumb = angle_between(a_thumb, b_thumb, c_thumb)

        # Índice: 5(MCP)-6(PIP)-8(TIP) -> ángulo en 6
        a_ind = (lm[5].x, lm[5].y); b_ind = (lm[6].x, lm[6].y); c_ind = (lm[8].x, lm[8].y)
        angle_ind = angle_between(a_ind, b_ind, c_ind)

        # Medio: 9-10-12 (ángulo en 10)
        a_mid = (lm[9].x, lm[9].y); b_mid = (lm[10].x, lm[10].y); c_mid = (lm[12].x, lm[12].y)
        angle_mid = angle_between(a_mid, b_mid, c_mid)

        # Anular: 13-14-16 (ángulo en 14)
        a_ring = (lm[13].x, lm[13].y); b_ring = (lm[14].x, lm[14].y); c_ring = (lm[16].x, lm[16].y)
        angle_ring = angle_between(a_ring, b_ring, c_ring)

        # Meñique: 17-18-20 (ángulo en 18)
        a_pinky = (lm[17].x, lm[17].y); b_pinky = (lm[18].x, lm[18].y); c_pinky = (lm[20].x, lm[20].y)
        angle_pinky = angle_between(a_pinky, b_pinky, c_pinky)

        # Thresholds empíricos (ajustables según pruebas)
        # Si el ángulo es cercano a 180º => falange extendida.
        TH_FINGER = 160  # índice/medio/anular/meñique
        TH_THUMB = 150   # pulgar suele necesitar menos umbral

        # Decidir si cada dedo está extendido
        thumb_up = angle_thumb > TH_THUMB
        index_up = angle_ind > TH_FINGER
        middle_up = angle_mid > TH_FINGER
        ring_up = angle_ring > TH_FINGER
        pinky_up = angle_pinky > TH_FINGER

        # Construir contador
        dedos_levantados = sum([thumb_up, index_up, middle_up, ring_up, pinky_up])

        # Mostrar ángulos en pantalla (útil para calibrar thresholds)
        cv2.putText(frame, f'Thumb:{int(angle_thumb)}', (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,0), 1)
        cv2.putText(frame, f'Ind:{int(angle_ind)} Mid:{int(angle_mid)}', (10,40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,0), 1)
        cv2.putText(frame, f'Ring:{int(angle_ring)} Pinky:{int(angle_pinky)}', (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,0), 1)

        # Opcional: dibujar bounding box de la mano (útil para dataset)
        xs = [p.x for p in lm]; ys = [p.y for p in lm]
        x_min = int(max(min(xs) * w - 20, 0))
        x_max = int(min(max(xs) * w + 20, w))
        y_min = int(max(min(ys) * h - 20, 0))
        y_max = int(min(max(ys) * h + 20, h))
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0,255,0), 1)

        # Añadir al buffer de suavizado
        last_counts.append(dedos_levantados)

        # Mostrar mano (Left/Right)
        if hand_label:
            cv2.putText(frame, f'Hand: {hand_label}', (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)

    else:
        # Si no detecta mano, reset o añadir None
        last_counts.append(None)

    # Suavizado: si hay valores válidos en last_counts tomamos la moda (o mediana)
    valid = [c for c in last_counts if c is not None]
    if valid:
        # usar la moda simple
        from statistics import mode
        try:
            display_count = mode(valid)
        except:
            # si hay empate, tomar la mediana
            display_count = int(sorted(valid)[len(valid)//2])
    else:
        display_count = 0

    # Mostrar el contador en la imagen (big)
    cv2.putText(frame, f'Dedos: {display_count}', (w - 180, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 3)

    cv2.imshow("Conteo dedos (mejorado)", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC -> salir
        break

    # Guardar captura etiquetada al pulsar 0..5
    if key in [ord(str(i)) for i in range(6)]:
        label = int(chr(key))
        # si hay bbox calculada, guardar el recorte; si no, guardar frame completo
        timestamp = int(time.time() * 1000)
        if 'x_min' in locals():
            roi = frame[y_min:y_max, x_min:x_max]
        else:
            roi = frame
        fname = os.path.join(DATASET_DIR, str(label), f'{label}_{timestamp}.jpg')
        cv2.imwrite(fname, roi)
        print(f'Guardado: {fname}')

# Cleanup
cap.release()
cv2.destroyAllWindows()
hands.close()
