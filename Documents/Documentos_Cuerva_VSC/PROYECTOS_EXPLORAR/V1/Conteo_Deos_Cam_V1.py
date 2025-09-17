import cv2
import mediapipe as mp
import numpy as np
import math
import os
import time
from collections import deque
from typing import Tuple, Optional, List, Dict, Any
from statistics import mode, median
import json
from dataclasses import dataclass
from enum import Enum

class HandType(Enum):
    """Tipos de mano detectados."""
    LEFT = "Left"
    RIGHT = "Right"
    UNKNOWN = "Unknown"

class GestureType(Enum):
    """Tipos de gestos reconocidos."""
    FIST = "Puño"
    OPEN_HAND = "Mano abierta"
    THUMBS_UP = "Pulgar arriba"
    PEACE = "Paz/Victoria"
    ROCK = "Rock/Cuernos"
    OK = "OK"
    POINTING = "Señalar"
    CUSTOM = "Personalizado"

@dataclass
class FingerAngles:
    """Estructura para almacenar ángulos de los dedos."""
    thumb: float
    index: float
    middle: float
    ring: float
    pinky: float

@dataclass
class HandDetection:
    """Estructura para almacenar información de detección de mano."""
    finger_count: int
    finger_states: List[bool]
    angles: FingerAngles
    hand_type: HandType
    gesture: GestureType
    confidence: float
    bounding_box: Tuple[int, int, int, int]

class AngleBasedFingerDetector:
    """
    Detector de dedos avanzado basado en análisis de ángulos entre landmarks.
    """
    
    def __init__(self, 
                 max_num_hands: int = 1,
                 detection_confidence: float = 0.7,
                 tracking_confidence: float = 0.6,
                 smooth_window: int = 7):
        """
        Inicializar el detector.
        
        Args:
            max_num_hands: Número máximo de manos a detectar
            detection_confidence: Confianza mínima para detección
            tracking_confidence: Confianza mínima para tracking
            smooth_window: Tamaño de ventana para suavizado
        """
        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )
        
        # Configuración de ángulos (calibrable)
        self.angle_thresholds = {
            'thumb': 140,    # Pulgar necesita menos apertura
            'fingers': 150,  # Otros dedos
            'strict': 160,   # Modo estricto
            'loose': 130     # Modo permisivo
        }
        
        # Suavizado
        self.smooth_window = smooth_window
        self.count_history = deque(maxlen=smooth_window)
        self.gesture_history = deque(maxlen=5)
        
        # Dataset management
        self.dataset_dir = "advanced_dataset"
        self.setup_dataset_structure()
        
        # Estadísticas
        self.stats = {
            'total_frames': 0,
            'hands_detected': 0,
            'gesture_counts': {gesture.value: 0 for gesture in GestureType}
        }
        
        # FPS tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
        # Calibración automática
        self.calibration_mode = False
        self.calibration_data = []
        
    def setup_dataset_structure(self):
        """Crear estructura de directorios para dataset."""
        os.makedirs(self.dataset_dir, exist_ok=True)
        
        # Directorios por número de dedos
        for i in range(6):
            os.makedirs(os.path.join(self.dataset_dir, f"fingers_{i}"), exist_ok=True)
        
        # Directorios por gestos
        for gesture in GestureType:
            os.makedirs(os.path.join(self.dataset_dir, "gestures", gesture.value.lower().replace(" ", "_")), exist_ok=True)
        
        # Directorio para calibración
        os.makedirs(os.path.join(self.dataset_dir, "calibration"), exist_ok=True)
    
    @staticmethod
    def calculate_angle(a: Tuple[float, float], 
                       b: Tuple[float, float], 
                       c: Tuple[float, float]) -> float:
        """
        Calcular ángulo en el punto b formado por los puntos a-b-c.
        
        Args:
            a, b, c: Puntos como tuplas (x, y)
            
        Returns:
            Ángulo en grados
        """
        # Vectores ba y bc
        ba = np.array([a[0] - b[0], a[1] - b[1]])
        bc = np.array([c[0] - b[0], c[1] - b[1]])
        
        # Calcular ángulo usando producto punto
        dot_product = np.dot(ba, bc)
        norms = np.linalg.norm(ba) * np.linalg.norm(bc)
        
        if norms == 0:
            return 0.0
            
        cos_angle = np.clip(dot_product / norms, -1.0, 1.0)
        angle_rad = np.arccos(cos_angle)
        
        return np.degrees(angle_rad)
    
    def get_landmark_coords(self, landmark, width: int, height: int) -> Tuple[float, float]:
        """Convertir landmark a coordenadas."""
        return (landmark.x * width, landmark.y * height)
    
    def calculate_finger_angles(self, landmarks, width: int, height: int) -> FingerAngles:
        """
        Calcular ángulos para todos los dedos.
        
        Args:
            landmarks: Landmarks de MediaPipe
            width, height: Dimensiones de la imagen
            
        Returns:
            FingerAngles con todos los ángulos calculados
        """
        # Definir puntos para cada dedo (base-articulación-punta)
        finger_points = {
            'thumb': (1, 2, 4),      # CMC-MCP-TIP
            'index': (5, 6, 8),      # MCP-PIP-TIP
            'middle': (9, 10, 12),   # MCP-PIP-TIP
            'ring': (13, 14, 16),    # MCP-PIP-TIP
            'pinky': (17, 18, 20)    # MCP-PIP-TIP
        }
        
        angles = {}
        
        for finger, (base_idx, joint_idx, tip_idx) in finger_points.items():
            base = self.get_landmark_coords(landmarks[base_idx], width, height)
            joint = self.get_landmark_coords(landmarks[joint_idx], width, height)
            tip = self.get_landmark_coords(landmarks[tip_idx], width, height)
            
            angle = self.calculate_angle(base, joint, tip)
            angles[finger] = angle
        
        return FingerAngles(
            thumb=angles['thumb'],
            index=angles['index'],
            middle=angles['middle'],
            ring=angles['ring'],
            pinky=angles['pinky']
        )
    
    def is_finger_extended(self, angle: float, finger_type: str = 'fingers') -> bool:
        """
        Determinar si un dedo está extendido basado en el ángulo.
        
        Args:
            angle: Ángulo del dedo
            finger_type: Tipo de dedo ('thumb' o 'fingers')
            
        Returns:
            True si está extendido
        """
        threshold = self.angle_thresholds.get(finger_type, self.angle_thresholds['fingers'])
        return angle > threshold
    
    def detect_gesture(self, finger_states: List[bool], angles: FingerAngles) -> GestureType:
        """
        Detectar gesto específico basado en estados de dedos y ángulos.
        
        Args:
            finger_states: Estados de los 5 dedos [thumb, index, middle, ring, pinky]
            angles: Ángulos de todos los dedos
            
        Returns:
            Tipo de gesto detectado
        """
        count = sum(finger_states)
        thumb, index, middle, ring, pinky = finger_states
        
        # Patrones específicos
        if count == 0:
            return GestureType.FIST
        elif count == 5:
            return GestureType.OPEN_HAND
        elif count == 1 and thumb:
            return GestureType.THUMBS_UP
        elif count == 1 and index:
            return GestureType.POINTING
        elif count == 2 and index and middle:
            return GestureType.PEACE
        elif count == 2 and index and pinky:
            return GestureType.ROCK
        elif count == 3 and thumb and index and middle:
            # Verificar si forma un círculo (gesto OK)
            if angles.thumb < 120 and angles.index < 140:
                return GestureType.OK
        
        return GestureType.CUSTOM
    
    def get_hand_bounding_box(self, landmarks, width: int, height: int, 
                             padding: int = 20) -> Tuple[int, int, int, int]:
        """
        Calcular bounding box de la mano.
        
        Args:
            landmarks: Landmarks de la mano
            width, height: Dimensiones de la imagen
            padding: Padding alrededor de la mano
            
        Returns:
            Tupla (x_min, y_min, x_max, y_max)
        """
        x_coords = [lm.x * width for lm in landmarks]
        y_coords = [lm.y * height for lm in landmarks]
        
        x_min = max(int(min(x_coords) - padding), 0)
        x_max = min(int(max(x_coords) + padding), width)
        y_min = max(int(min(y_coords) - padding), 0)
        y_max = min(int(max(y_coords) + padding), height)
        
        return (x_min, y_min, x_max, y_max)
    
    def smooth_detection(self, current_count: int) -> int:
        """
        Suavizar el conteo usando ventana móvil.
        
        Args:
            current_count: Conteo actual
            
        Returns:
            Conteo suavizado
        """
        self.count_history.append(current_count)
        
        if len(self.count_history) < 3:
            return current_count
        
        try:
            # Usar moda si hay suficientes datos
            return mode(self.count_history)
        except:
            # Si hay empate, usar mediana
            return int(median(self.count_history))
    
    def update_stats(self, detection: Optional[HandDetection]):
        """Actualizar estadísticas de detección."""
        self.stats['total_frames'] += 1
        
        if detection:
            self.stats['hands_detected'] += 1
            self.stats['gesture_counts'][detection.gesture.value] += 1
    
    def draw_debug_info(self, frame: np.ndarray, detection: Optional[HandDetection], 
                       angles: Optional[FingerAngles]) -> np.ndarray:
        """
        Dibujar información de debug en el frame.
        
        Args:
            frame: Frame de video
            detection: Información de detección
            angles: Ángulos de los dedos
            
        Returns:
            Frame con información dibujada
        """
        height, width = frame.shape[:2]
        
        # Fondo semitransparente para información
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 150), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
        
        if detection and angles:
            # Información principal
            cv2.putText(frame, f'Mano: {detection.hand_type.value}', 
                       (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f'Dedos: {detection.finger_count}', 
                       (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, f'Gesto: {detection.gesture.value}', 
                       (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Ángulos detallados
            angles_text = [
                f'Pulgar: {angles.thumb:.0f}°',
                f'Índice: {angles.index:.0f}°',
                f'Medio: {angles.middle:.0f}°',
                f'Anular: {angles.ring:.0f}°',
                f'Meñique: {angles.pinky:.0f}°'
            ]
            
            for i, text in enumerate(angles_text):
                color = (0, 255, 0) if i == 0 else (200, 200, 0)
                cv2.putText(frame, text, (20, 110 + i * 15), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            # Dibujar bounding box
            x_min, y_min, x_max, y_max = detection.bounding_box
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            
            # Indicadores de dedos extendidos
            finger_names = ['T', 'I', 'M', 'A', 'Me']
            for i, (name, is_up) in enumerate(zip(finger_names, detection.finger_states)):
                color = (0, 255, 0) if is_up else (0, 0, 255)
                cv2.circle(frame, (width - 200 + i * 35, 50), 15, color, -1)
                cv2.putText(frame, name, (width - 205 + i * 35, 55), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # FPS
        fps = self.update_fps()
        cv2.putText(frame, f'FPS: {fps}', (width - 100, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Modo calibración
        if self.calibration_mode:
            cv2.putText(frame, 'MODO CALIBRACIÓN', (width//2 - 100, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame
    
    def update_fps(self) -> int:
        """Actualizar contador de FPS."""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_start_time = current_time
        
        return self.current_fps
    
    def save_sample(self, frame: np.ndarray, detection: HandDetection, 
                   sample_type: str = "manual"):
        """
        Guardar muestra para dataset.
        
        Args:
            frame: Frame actual
            detection: Información de detección
            sample_type: Tipo de muestra ('manual', 'auto', 'calibration')
        """
        timestamp = int(time.time() * 1000)
        
        # Extraer región de la mano
        x_min, y_min, x_max, y_max = detection.bounding_box
        hand_roi = frame[y_min:y_max, x_min:x_max]
        
        # Determinar directorio de destino
        if sample_type == "calibration":
            dest_dir = os.path.join(self.dataset_dir, "calibration")
            filename = f"cal_{timestamp}.jpg"
        else:
            dest_dir = os.path.join(self.dataset_dir, f"fingers_{detection.finger_count}")
            filename = f"{detection.finger_count}_{timestamp}.jpg"
        
        # Guardar imagen y metadata
        img_path = os.path.join(dest_dir, filename)
        cv2.imwrite(img_path, hand_roi)
        
        # Guardar metadata en JSON
        metadata = {
            'finger_count': detection.finger_count,
            'finger_states': detection.finger_states,
            'angles': {
                'thumb': detection.angles.thumb,
                'index': detection.angles.index,
                'middle': detection.angles.middle,
                'ring': detection.angles.ring,
                'pinky': detection.angles.pinky
            },
            'gesture': detection.gesture.value,
            'hand_type': detection.hand_type.value,
            'timestamp': timestamp,
            'sample_type': sample_type
        }
        
        json_path = os.path.join(dest_dir, filename.replace('.jpg', '.json'))
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f'Muestra guardada: {img_path}')
    
    def process_frame(self, frame: np.ndarray, debug: bool = True) -> Tuple[np.ndarray, Optional[HandDetection]]:
        """
        Procesar un frame completo.
        
        Args:
            frame: Frame de entrada
            debug: Si mostrar información de debug
            
        Returns:
            Tupla (frame_procesado, detección)
        """
        height, width = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = self.hands.process(rgb_frame)
        detection = None
        angles = None
        
        if results.multi_hand_landmarks and results.multi_handedness:
            # Procesar primera mano detectada
            hand_landmarks = results.multi_hand_landmarks[0]
            handedness = results.multi_handedness[0]
            
            # Dibujar landmarks
            if debug:
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
            
            # Calcular ángulos
            angles = self.calculate_finger_angles(hand_landmarks.landmark, width, height)
            
            # Determinar estados de dedos
            finger_states = [
                self.is_finger_extended(angles.thumb, 'thumb'),
                self.is_finger_extended(angles.index),
                self.is_finger_extended(angles.middle),
                self.is_finger_extended(angles.ring),
                self.is_finger_extended(angles.pinky)
            ]
            
            finger_count = sum(finger_states)
            smooth_count = self.smooth_detection(finger_count)
            
            # Detectar gesto
            gesture = self.detect_gesture(finger_states, angles)
            
            # Obtener información adicional
            hand_type = HandType(handedness.classification[0].label)
            confidence = handedness.classification[0].score
            bounding_box = self.get_hand_bounding_box(hand_landmarks.landmark, width, height)
            
            # Crear objeto de detección
            detection = HandDetection(
                finger_count=smooth_count,
                finger_states=finger_states,
                angles=angles,
                hand_type=hand_type,
                gesture=gesture,
                confidence=confidence,
                bounding_box=bounding_box
            )
        
        # Actualizar estadísticas
        self.update_stats(detection)
        
        # Dibujar información de debug
        if debug:
            frame = self.draw_debug_info(frame, detection, angles)
        
        return frame, detection
    
    def print_stats(self):
        """Imprimir estadísticas de detección."""
        print("\n=== ESTADÍSTICAS DE DETECCIÓN ===")
        print(f"Frames procesados: {self.stats['total_frames']}")
        print(f"Manos detectadas: {self.stats['hands_detected']}")
        if self.stats['total_frames'] > 0:
            detection_rate = (self.stats['hands_detected'] / self.stats['total_frames']) * 100
            print(f"Tasa de detección: {detection_rate:.1f}%")
        
        print("\nGestos detectados:")
        for gesture, count in self.stats['gesture_counts'].items():
            if count > 0:
                print(f"  {gesture}: {count}")

def main():
    """Función principal."""
    print("=== DETECTOR DE DEDOS BASADO EN ÁNGULOS ===")
    print("Controles:")
    print("  ESC/q: Salir")
    print("  0-5: Guardar muestra con N dedos")
    print("  c: Activar/desactivar modo calibración")
    print("  r: Reiniciar historial de suavizado")
    print("  s: Mostrar estadísticas")
    print("  h: Mostrar ayuda")
    
    # Crear detector
    detector = AngleBasedFingerDetector(
        max_num_hands=1,
        detection_confidence=0.7,
        tracking_confidence=0.6,
        smooth_window=7
    )
    
    # Configurar cámara
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        return
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error leyendo frame")
                break
            
            # Procesar frame
            frame, detection = detector.process_frame(frame, debug=True)
            
            # Mostrar frame
            cv2.imshow('Detector de Dedos Avanzado (Ángulos)', frame)
            
            # Manejar teclas
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27 or key == ord('q'):  # ESC o 'q'
                break
            elif key in [ord(str(i)) for i in range(6)]:  # 0-5
                if detection:
                    label = int(chr(key))
                    detector.save_sample(frame, detection, "manual")
                else:
                    print("No hay mano detectada para guardar")
            elif key == ord('c'):  # Calibración
                detector.calibration_mode = not detector.calibration_mode
                status = "activado" if detector.calibration_mode else "desactivado"
                print(f"Modo calibración {status}")
            elif key == ord('r'):  # Reset historial
                detector.count_history.clear()
                detector.gesture_history.clear()
                print("Historial reiniciado")
            elif key == ord('s'):  # Estadísticas
                detector.print_stats()
            elif key == ord('h'):  # Ayuda
                print("\nControles disponibles:")
                print("  ESC/q: Salir")
                print("  0-5: Guardar muestra")
                print("  c: Modo calibración")
                print("  r: Reiniciar historial")
                print("  s: Estadísticas")
    
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
    
    finally:
        # Mostrar estadísticas finales
        detector.print_stats()
        
        # Limpiar recursos
        cap.release()
        cv2.destroyAllWindows()
        detector.hands.close()
        print("Recursos liberados correctamente")

if __name__ == "__main__":
    main()