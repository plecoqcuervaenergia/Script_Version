# capture_and_label.py
# Captura imágenes desde la webcam, detecta la mano con MediaPipe,
# muestra landmarks en pantalla y guarda:
#  - imagen recortada (bounding box de la mano) en dataset_images/<label>/
#  - una fila en landmarks.csv: label, x0,y0, x1,y1, ..., x20,y20
#
# Uso:
#  - Ejecutar: python capture_and_label.py
#  - Pulsar 0,1,2,3,4 o 5 para guardar un ejemplo con esa etiqueta
#  - Pulsar ESC para salir

import cv2
import mediapipe as mp
import os
import csv
import time

# --- Configuración ---
IMG_DIR = "dataset_images"   # directorio donde guardar imágenes recortadas
CSV_FILE = "landmarks.csv"   # fichero CSV de salida (label + 21*(x,y))
LABELS = [str(i) for i in range(6)]  # etiquetas: '0','1','2','3','4','5'
os.makedirs(IMG_DIR, exist_ok=True)
for lbl in LABELS:
    os.makedirs(os.path.join(IMG_DIR, lbl), exist_ok=True)

# Inicializar MediaPipe Hands
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1,
                       min_detection_confidence=0.6,
                       min_tracking_confidence=0.5)

# Si el CSV no existe, crear con cabecera
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        header = ['label'] + [f'x{i}' for i in range(21)] + [f'y{i}' for i in range(21)]
        writer.writerow(header)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Captura lista. Pulsa 0..5 para guardar ejemplo con esa etiqueta. ESC para salir.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # espejo opcional para verse tipo selfie (comoda para etiquetar)
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # MediaPipe usa RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    bbox = None  # bounding box en píxeles (x_min,y_min,x_max,y_max)
    landmarks_row = None  # lista [label, x0..x20, y0..y20]

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]  # primera mano
        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # extraer coords normalizadas y calcular bbox
        xs = [lm.x for lm in hand_landmarks.landmark]
        ys = [lm.y for lm in hand_landmarks.landmark]
        x_min = int(max(min(xs) * w - 20, 0))
        x_max = int(min(max(xs) * w + 20, w))
        y_min = int(max(min(ys) * h - 20, 0))
        y_max = int(min(max(ys) * h + 20, h))
        bbox = (x_min, y_min, x_max, y_max)
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0,255,0), 1)

        # construir fila de landmarks normalizados (x0..x20, y0..y20)
        xs_norm = [lm.x for lm in hand_landmarks.landmark]
        ys_norm = [lm.y for lm in hand_landmarks.landmark]
        landmarks_row = xs_norm + ys_norm  # 42 valores

    # instrucciones en pantalla
    cv2.putText(frame, "Keys: 0..5 save, ESC exit", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0),2)
    if bbox:
        cv2.putText(frame, "Hand detected", (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0),2)

    cv2.imshow("Capture & Label", frame)
    key = cv2.waitKey(1) & 0xFF

    # --- Guardar si se pulsa 0..5 ---
    if key in [ord(str(i)) for i in range(6)] and landmarks_row is not None:
        label = int(chr(key))
        timestamp = int(time.time()*1000)
        # guardar imagen recortada (si hay bbox)
        if bbox:
            x1,y1,x2,y2 = bbox
            roi = frame[y1:y2, x1:x2]
        else:
            roi = frame

        fname = os.path.join(IMG_DIR, str(label), f'{label}_{timestamp}.jpg')
        cv2.imwrite(fname, roi)

        # guardar fila en CSV (label, x0..x20, y0..y20)
        with open(CSV_FILE, mode='a', newline='') as f:
            writer = csv.writer(f)
            row = [label] + landmarks_row
            writer.writerow(row)

        print(f"Guardado imagen: {fname}  y fila en {CSV_FILE}")

    if key == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
hands.close()
