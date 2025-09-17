import cv2
import mediapipe as mp
import numpy as np
from typing import Tuple, Optional, List
import time

class FingerDetector:
    """
    Detector de dedos mejorado con múltiples funcionalidades y mejor precisión.
    """
    
    def __init__(self, max_num_hands: int = 2, detection_confidence: float = 0.7, 
                 tracking_confidence: float = 0.5):
        """
        Inicializar el detector de dedos.
        
        Args:
            max_num_hands: Número máximo de manos a detectar
            detection_confidence: Confianza mínima para detección inicial
            tracking_confidence: Confianza mínima para tracking
        """
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )
        
        # Índices de landmarks para cada dedo
        self.finger_tips = [4, 8, 12, 16, 20]  # Puntas de dedos
        self.finger_pips = [3, 6, 10, 14, 18]  # Articulaciones para comparar
        
        # Historial para suavizado
        self.finger_history = []
        self.history_size = 5
        
        # FPS Counter
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
    def get_hand_type(self, landmarks, handedness_label: str) -> str:
        """
        Determinar el tipo de mano usando la información de MediaPipe.
        
        Args:
            landmarks: Landmarks de la mano
            handedness_label: Etiqueta de handedness de MediaPipe
            
        Returns:
            'Right' o 'Left'
        """
        return handedness_label
    
    def count_fingers(self, landmarks, hand_type: str) -> Tuple[int, List[bool]]:
        """
        Contar dedos levantados con lógica mejorada.
        
        Args:
            landmarks: Landmarks de la mano
            hand_type: 'Right' o 'Left'
            
        Returns:
            Tupla con (número_dedos, lista_dedos_estado)
        """
        fingers_up = []
        
        # Pulgar - lógica mejorada basada en el tipo de mano
        if hand_type == "Right":
            # Mano derecha: pulgar extendido si tip está a la derecha del PIP
            fingers_up.append(landmarks[self.finger_tips[0]].x > landmarks[self.finger_pips[0]].x)
        else:
            # Mano izquierda: pulgar extendido si tip está a la izquierda del PIP
            fingers_up.append(landmarks[self.finger_tips[0]].x < landmarks[self.finger_pips[0]].x)
        
        # Otros dedos - comparación vertical mejorada
        for i in range(1, 5):
            tip = landmarks[self.finger_tips[i]]
            pip = landmarks[self.finger_pips[i]]
            mcp = landmarks[self.finger_tips[i] - 4]  # Metacarpo
            
            # Usar tanto PIP como MCP para mejor precisión
            fingers_up.append(tip.y < pip.y and tip.y < mcp.y)
        
        return sum(fingers_up), fingers_up
    
    def smooth_finger_count(self, current_count: int) -> int:
        """
        Suavizar el conteo de dedos usando historial.
        
        Args:
            current_count: Conteo actual de dedos
            
        Returns:
            Conteo suavizado
        """
        self.finger_history.append(current_count)
        
        if len(self.finger_history) > self.history_size:
            self.finger_history.pop(0)
        
        # Usar la moda (valor más frecuente) para suavizar
        return max(set(self.finger_history), key=self.finger_history.count)
    
    def draw_info(self, frame: np.ndarray, finger_count: int, fingers_up: List[bool], 
                  hand_type: str, position: Tuple[int, int]) -> np.ndarray:
        """
        Dibujar información en el frame.
        
        Args:
            frame: Frame de video
            finger_count: Número de dedos levantados
            fingers_up: Estado de cada dedo
            hand_type: Tipo de mano
            position: Posición para dibujar el texto
            
        Returns:
            Frame con información dibujada
        """
        x, y = position
        
        # Fondo semitransparente para mejor legibilidad
        overlay = frame.copy()
        cv2.rectangle(overlay, (x-10, y-40), (x+200, y+20), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
        
        # Texto principal
        cv2.putText(frame, f'Mano: {hand_type}', (x, y-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f'Dedos: {finger_count}', (x, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Indicadores individuales de dedos
        finger_names = ['Pulgar', 'Indice', 'Medio', 'Anular', 'Meñique']
        for i, (name, is_up) in enumerate(zip(finger_names, fingers_up)):
            color = (0, 255, 0) if is_up else (0, 0, 255)
            cv2.circle(frame, (x + i * 30, y + 30), 8, color, -1)
            cv2.putText(frame, name[:3], (x + i * 30 - 10, y + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        
        return frame
    
    def update_fps(self) -> float:
        """
        Actualizar contador de FPS.
        
        Returns:
            FPS actual
        """
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_start_time = current_time
            
        return self.current_fps
    
    def detect_gesture(self, finger_count: int, fingers_up: List[bool]) -> str:
        """
        Detectar gestos específicos basados en los dedos.
        
        Args:
            finger_count: Número de dedos levantados
            fingers_up: Estado de cada dedo
            
        Returns:
            Nombre del gesto detectado
        """
        if finger_count == 0:
            return "Puño cerrado"
        elif finger_count == 5:
            return "Mano abierta"
        elif finger_count == 1 and fingers_up[1]:  # Solo índice
            return "Señalar"
        elif finger_count == 2 and fingers_up[1] and fingers_up[2]:  # Índice y medio
            return "Victoria/Paz"
        elif finger_count == 1 and fingers_up[0]:  # Solo pulgar
            return "Pulgar arriba"
        elif finger_count == 3 and not fingers_up[3] and not fingers_up[4]:  # Pulgar, índice, medio
            return "OK (3 dedos)"
        else:
            return f"{finger_count} dedos"
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Procesar un frame completo.
        
        Args:
            frame: Frame de entrada
            
        Returns:
            Frame procesado con detecciones
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # Dibujar landmarks con mejor estilo
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
                
                # Obtener tipo de mano
                hand_type = handedness.classification[0].label
                
                # Contar dedos
                finger_count, fingers_up = self.count_fingers(hand_landmarks.landmark, hand_type)
                
                # Suavizar conteo
                smooth_count = self.smooth_finger_count(finger_count)
                
                # Detectar gesto
                gesture = self.detect_gesture(smooth_count, fingers_up)
                
                # Obtener posición de la mano para dibujar información
                h, w, _ = frame.shape
                cx = int(hand_landmarks.landmark[9].x * w)  # Centro de la mano
                cy = int(hand_landmarks.landmark[9].y * h)
                
                # Dibujar información
                frame = self.draw_info(frame, smooth_count, fingers_up, hand_type, (cx, cy))
                
                # Dibujar gesto detectado
                cv2.putText(frame, f'Gesto: {gesture}', (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Dibujar FPS
        fps = self.update_fps()
        cv2.putText(frame, f'FPS: {fps}', (frame.shape[1] - 100, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame

def main():
    """
    Función principal del programa.
    """
    # Crear detector
    detector = FingerDetector(max_num_hands=2, detection_confidence=0.8, tracking_confidence=0.7)
    
    # Configurar cámara
    cap = cv2.VideoCapture(0)
    
    # Configurar resolución para mejor rendimiento
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        return
    
    print("Presiona 'q' o ESC para salir")
    print("Presiona 'r' para reiniciar el historial de suavizado")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: No se pudo leer el frame")
                break
            
            # Voltear horizontalmente para efecto espejo
            frame = cv2.flip(frame, 1)
            
            # Procesar frame
            frame = detector.process_frame(frame)
            
            # Mostrar frame
            cv2.imshow('Detector de Dedos Avanzado', frame)
            
            # Manejar teclas
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q' o ESC
                break
            elif key == ord('r'):  # Reiniciar historial
                detector.finger_history.clear()
                print("Historial de suavizado reiniciado")
    
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
    
    finally:
        # Limpiar recursos
        cap.release()
        cv2.destroyAllWindows()
        print("Recursos liberados correctamente")

if __name__ == "__main__":
    main()