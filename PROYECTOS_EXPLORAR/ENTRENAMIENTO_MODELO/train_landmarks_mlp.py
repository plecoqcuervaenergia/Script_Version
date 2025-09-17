# train_landmarks_mlp.py
# Entrena un MLP usando los landmarks guardados en landmarks.csv
# Salidas:
#  - scaler_landmarks.pkl   -> StandardScaler para inferencia
#  - landmark_mlp.h5        -> Mejor modelo Keras guardado por ModelCheckpoint
#  - labels.txt             -> listado de clases (una por línea)
#  - training_curves.png    -> gráfico de loss/accuracy
#  - history.json           -> historial de entrenamiento en JSON
#
# Uso:
#  - Activa tu venv (venv310) y ejecuta:
#      python train_landmarks_mlp.py

import os
import json
import random
import joblib
import numpy as np
import pandas as pd
import matplotlib

# Si ejecutas en entorno sin display (ej. servidor), seleccionamos backend 'Agg'
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

import tensorflow as tf

# ---------------------------
# Configuración y seeds
# ---------------------------
SEED = 42
np.random.seed(SEED)
random.seed(SEED)
tf.random.set_seed(SEED)

CSV_FILE = "landmarks.csv"                 # fichero de entrada: label,x0..x20,y0..y20
SCALER_OUT = "scaler_landmarks.pkl"
MODEL_OUT = "landmark_mlp.h5"
LABELS_OUT = "labels.txt"
HISTORY_JSON = "history.json"
CURVES_PNG = "training_curves.png"

EPOCHS = 200
BATCH = 32
VERBOSE = 1

# ---------------------------
# Comprobaciones iniciales
# ---------------------------
if not os.path.exists(CSV_FILE):
    raise SystemExit(f"No se encontró {CSV_FILE}. Ejecuta primero capture_and_label.py para generar datos.")

print("Cargando CSV...", CSV_FILE)
df = pd.read_csv(CSV_FILE)

# Esperamos formato: 'label', 'x0'..'x20', 'y0'..'y20'
x_cols = [f'x{i}' for i in range(21)]
y_cols = [f'y{i}' for i in range(21)]
expected_cols = ['label'] + x_cols + y_cols

missing = [c for c in expected_cols if c not in df.columns]
if missing:
    raise SystemExit(f"Faltan columnas en {CSV_FILE}: {missing}. Esperado: {expected_cols}")

# ---------------------------
# Limpieza básica de datos
# ---------------------------

# 1) quitar filas con NaNs
n_before = len(df)
df = df.dropna()
n_after = len(df)
print(f"Filas: {n_before} -> {n_after} tras dropna()")

# 2) quitar filas donde todas las coordenadas sean 0 (probablemente inválidas)
coords_cols = x_cols + y_cols
all_zero_mask = (df[coords_cols] == 0).all(axis=1)
n_all_zero = all_zero_mask.sum()
if n_all_zero > 0:
    print(f"Eliminando {n_all_zero} filas con todas las coords = 0 (posible error de captura).")
    df = df.loc[~all_zero_mask].reset_index(drop=True)

if len(df) == 0:
    raise SystemExit("No quedan filas válidas después de limpieza. Recolecta datos con capture_and_label.py")

# 3) mostrar balance por clase
print("Recuento por clase:")
print(df['label'].value_counts())

# ---------------------------
# Preparar X, y
# ---------------------------
labels = df['label'].values
X = df[coords_cols].values.astype(np.float32)  # formato: x0..x20,y0..y20
y = labels.astype(np.int32)

# ---------------------------
# Guardar label map (ordenado)
# ---------------------------
labels_unique = sorted(df['label'].unique())
with open(LABELS_OUT, 'w') as f:
    for l in labels_unique:
        f.write(str(l) + '\n')
print(f"Labels guardadas en {LABELS_OUT}: {labels_unique}")

# ---------------------------
# Dividir train/val/test de forma segura
# ---------------------------
# Intentamos hacer stratify; si falla por pocas muestras, caemos a split sin stratify.
try:
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, random_state=SEED, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.1765, random_state=SEED, stratify=y_train_val
    )
except ValueError as e:
    print("Warning: stratified split falló (posible clase con muy pocas muestras). Haciendo split sin stratify.")
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, random_state=SEED, stratify=None
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.1765, random_state=SEED, stratify=None
    )

print("Split sizes -> train:", X_train.shape[0], "val:", X_val.shape[0], "test:", X_test.shape[0])

# ---------------------------
# Normalización
# ---------------------------
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)
X_test = scaler.transform(X_test)

# Guardar el scaler para inferencia posterior
joblib.dump(scaler, SCALER_OUT)
print(f"Scaler guardado en {SCALER_OUT}")

# ---------------------------
# Preparar pesos de clase (opcional) para balancear el entrenamiento si hay desbalance
# ---------------------------
from collections import Counter
counter = Counter(y_train)
print("Distribución en train:", counter)
# calcular class_weight (scikit-learn style) si quieres
total_train = sum(counter.values())
class_weight = {int(k): total_train / (len(counter) * int(v)) for k, v in counter.items()}
print("class_weight:", class_weight)

# ---------------------------
# Construcción del modelo MLP
# ---------------------------
num_features = X_train.shape[1]
num_classes = len(np.unique(y))

print("Número de features:", num_features, "Número de clases:", num_classes)

layers = tf.keras.layers
models_tf = tf.keras.models  # evitar sombra con nombre 'models'
# Usamos namespaced tf.keras callbacks
EarlyStopping = tf.keras.callbacks.EarlyStopping
ModelCheckpoint = tf.keras.callbacks.ModelCheckpoint

model = models_tf.Sequential([
    layers.Input(shape=(num_features,)),
    layers.Dense(128, activation='relu', name='dense_128'),
    layers.Dropout(0.3, name='dropout_0'),
    layers.Dense(64, activation='relu', name='dense_64'),
    layers.Dropout(0.2, name='dropout_1'),
    layers.Dense(num_classes, activation='softmax', name='output')
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

# ---------------------------
# Callbacks
# ---------------------------
callbacks = [
    EarlyStopping(monitor='val_loss', patience=8, restore_best_weights=True),
    ModelCheckpoint(MODEL_OUT, save_best_only=True)
]

# ---------------------------
# Entrenamiento
# ---------------------------
history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=EPOCHS,
    batch_size=BATCH,
    callbacks=callbacks,
    verbose=VERBOSE,
    class_weight=class_weight  # ayuda si desbalance importante
)

# ---------------------------
# Evaluación final en test
# ---------------------------
loss, acc = model.evaluate(X_test, y_test, verbose=0)
print(f"Test accuracy: {acc:.4f}   Test loss: {loss:.4f}")

# ---------------------------
# Guardar modelo (ModelCheckpoint ya guarda el mejor; guardamos una copia final si quieres)
# ---------------------------
if not os.path.exists(MODEL_OUT):
    model.save(MODEL_OUT)
print(f"Modelo guardado en {MODEL_OUT}")

# ---------------------------
# Guardar history en JSON
# ---------------------------
hist = history.history
with open(HISTORY_JSON, 'w') as f:
    json.dump(hist, f)
print(f"History guardado en {HISTORY_JSON}")

# ---------------------------
# Dibujar curvas de entrenamiento
# ---------------------------
plt.figure(figsize=(10,4))
plt.subplot(1,2,1)
plt.plot(hist.get('loss', []), label='train_loss')
plt.plot(hist.get('val_loss', []), label='val_loss')
plt.xlabel('Época')
plt.ylabel('Loss')
plt.legend()
plt.title('Pérdida')

plt.subplot(1,2,2)
plt.plot(hist.get('accuracy', []), label='train_acc')
plt.plot(hist.get('val_accuracy', []), label='val_acc')
plt.xlabel('Época')
plt.ylabel('Accuracy')
plt.legend()
plt.title('Accuracy')

plt.tight_layout()
plt.savefig(CURVES_PNG, dpi=150)
print(f"Curvas guardadas en {CURVES_PNG}")

# Si quieres ver la imagen en local (no se recomienda en servidor), descomenta:
# plt.show()

print("Entrenamiento finalizado correctamente.")
