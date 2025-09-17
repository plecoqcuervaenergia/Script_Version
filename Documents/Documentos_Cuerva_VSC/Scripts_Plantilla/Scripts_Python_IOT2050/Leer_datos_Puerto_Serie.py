#!/usr/bin/env python3

import serial
import time
import sys

# --- Configuración del puerto serial ---
#
# ¡¡¡MUY IMPORTANTE!!!
# ¡AJUSTA ESTOS VALORES PARA QUE COINCIDAN EXACTAMENTE CON LA CONFIGURACIÓN DE TU SENSOR!
# Consulta la documentación de tus sensores para obtener estos parámetros.
#
SERIAL_PORT = '/dev/ttyS2' # Nombre del archivo de dispositivo para el puerto X30
BAUD_RATE = 9600          # Velocidad en baudios (la más común, ajusta si es necesario)
PARITY = serial.PARITY_NONE # Paridad (serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD)
STOP_BITS = serial.STOPBITS_ONE # Bits de parada (serial.STOPBITS_ONE, serial.STOPBITS_TWO)
BYTE_SIZE = 8             # Bits de datos (serial.EIGHTBITS)
READ_TIMEOUT = 0.1        # Tiempo máximo de espera para leer datos (en segundos)
READ_SIZE = 100           # Número máximo de bytes a intentar leer en cada ciclo

# --- Script para leer datos seriales ---

print(f"Script de lectura serial iniciado.")
print(f"Intentando abrir puerto serial {SERIAL_PORT} con configuración:")
print(f"  Baudrate: {BAUD_RATE}")
print(f"  Paridad: {PARITY}")
print(f"  Bits de parada: {STOP_BITS}")
print(f"  Bits de datos: {BYTE_SIZE}")
print(f"  Tiempo de espera de lectura: {READ_TIMEOUT}s")

ser = None # Inicializamos la variable para la instancia del puerto serial

try:
    # Abrir el puerto serial con la configuración especificada
    ser = serial.Serial(
        port=SERIAL_PORT,
        baudrate=BAUD_RATE,
        parity=PARITY,
        stopbits=STOP_BITS,
        bytesize=BYTE_SIZE,
        timeout=READ_TIMEOUT
    )

    if ser.isOpen():
        print(f"\nPuerto serial {SERIAL_PORT} abierto exitosamente.")
        print("Escuchando datos... Presiona Ctrl+C para detener.")

        # Limpiar buffers de entrada y salida por si hay datos pendientes o basura
        ser.flushInput()
        ser.flushOutput()

        # --- Loop principal para leer datos continuamente ---
        while True:
            # Lee datos del puerto. read(size) intentará leer hasta `size` bytes.
            # Si no llegan datos en el tiempo definido por `timeout`, read() retornará una cadena vacía.
            data_read = ser.read(READ_SIZE)

            if data_read:
                # Si se recibieron datos (data_read no está vacío)
                print("-" * 30) # Imprime un separador

                # Intentar decodificar los datos como texto (UTF-8 es común)
                try:
                    # 'errors="ignore"' para evitar fallar si hay bytes no válidos en la secuencia de texto
                    text_data = data_read.decode('utf-8', errors='ignore')
                    # .strip() elimina espacios en blanco y saltos de línea al inicio y final si es texto
                    print(f"Datos recibidos (Texto posible): {text_data.strip()}")
                except Exception as e:
                    # Si falla la decodificación a texto (probablemente son datos binarios)
                    print(f"No se pudo decodificar como texto. Error: {e}")
                    # Muestra los datos en formato hexadecimal para ver los bytes exactos
                    print(f"Datos recibidos (Hex): {data_read.hex()}")

                # Opcional: puedes añadir un pequeño retardo si es necesario, pero con timeout suele bastar
                # time.sleep(0.01)
            else:
                # Si read() retorna una cadena vacía, significa que no llegaron datos en el tiempo de espera
                # Puedes añadir un print de depuración aquí si quieres ver cuando no llega nada
                # print("No data within timeout.")
                pass # No hacer nada si no hay datos para evitar llenar la terminal

except serial.SerialException as e:
    # Captura errores específicos de la librería serial (ej: puerto no encontrado, permisos)
    print(f"\nError de puerto serial al intentar abrir o usar {SERIAL_PORT}: {e}", file=sys.stderr)
    print("Verifica el nombre del puerto, los permisos de usuario (grupo dialout) y si otro proceso lo está usando.", file=sys.stderr)
except KeyboardInterrupt:
    # Captura la interrupción por teclado (cuando presionas Ctrl+C)
    print("\nScript detenido por el usuario (Ctrl+C).", file=sys.stderr)
except Exception as e:
    # Captura cualquier otro error inesperado
    print(f"\nOcurrió un error inesperado: {e}", file=sys.stderr)
    print("Detalles:", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)


finally:
    # Este bloque se ejecuta siempre, tanto si hay errores como si sales con Ctrl+C
    # Asegura que el puerto serial se cierre limpiamente si se abrió
    if ser is not None and ser.isOpen():
        ser.close()
        print(f"Puerto serial {SERIAL_PORT} cerrado.")
    else:
        print(f"Puerto serial {SERIAL_PORT} no estaba abierto o ya estaba cerrado.")

print("Fin del script.")