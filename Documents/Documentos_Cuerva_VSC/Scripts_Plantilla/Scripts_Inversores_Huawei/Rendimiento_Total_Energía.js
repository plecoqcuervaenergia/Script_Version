// Verificamos que msg.payload es un array con al menos dos registros (parte alta y parte baja)
if (Array.isArray(msg.payload) && msg.payload.length >= 2) {
    // Obtenemos la parte alta (primer registro) y la parte baja (segundo registro)
    const high = msg.payload[0];  // Primeros 16 bits
    const low = msg.payload[1];   // Siguientes 16 bits

    // Combinamos ambos registros para obtener un valor de 32 bits.
    // Se desplaza la parte alta 16 bits a la izquierda y se suma la parte baja.
    const activePowerW = (high << 16) + low;  // Potencia activa en vatios (W)

    // Convertimos a kilovatios (kW) dividiendo entre 1000.
    // Ajusta este factor de escala según la documentación de tu inversor si fuera distinto.
    const activePowerKW = activePowerW / 100;

    // Asignamos el resultado a msg.payload
    msg.payload = activePowerKW;

    // Retornamos el mensaje con la potencia activa en kW
    return msg;
} else {
    // Si no se reciben los dos registros, mostramos un error en la consola
    node.error("Payload no contiene los dos registros esperados", msg);
    return null;
}
