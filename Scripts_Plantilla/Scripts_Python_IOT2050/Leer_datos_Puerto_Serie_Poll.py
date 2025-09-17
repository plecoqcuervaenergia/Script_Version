import serial
from serial.rs485 import RS485Settings

# Abre el puerto en 8N1, 9600 baud
ser = serial.Serial('/dev/ttyS2', 9600, bytesize=8, parity='N', stopbits=1, timeout=1)

# Activa modo RS485: pySerial levantará RTS en TX y lo bajará en RX
ser.rs485_mode = RS485Settings()

# Petición RTU: 02 03 00 00 00 0A C5 FE
req = bytes.fromhex('02 03 00 00 00 0A C5 FE')
ser.write(req)

# Lee ID + FC + count + 20 bytes de datos + CRC = 1+1+1+20+2 = 25 bytes
resp = ser.read(25)
print("Respuesta (hex):", resp.hex(' '))
