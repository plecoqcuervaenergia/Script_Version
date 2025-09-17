// Verificamos si msg.payload es un array y tiene al menos 2 elementos (parte alta y baja)
if (Array.isArray(msg.payload) && msg.payload.length >= 2) {
    // Si msg.payload es un array con al menos 2 elementos (parte alta y parte baja):
    
    // Asignamos la parte alta (primer valor) del array a la variable "high"
    // Cuando el valor llegue a 65.535 kWh la parte alta empezará a recibir valores
    const high = msg.payload[0];  // Parte alta (primer valor de 16 bits)
    
    // Asignamos la parte baja (segundo valor) del array a la variable "low"
    const low = msg.payload[1];   // Parte baja (segundo valor de 16 bits)
    
    // Sumamos los dos valores (parte alta y parte baja) para obtener la suma
    msg.payload = high + low; // El valor final es la suma de los dos registros Modbus

    // Retornamos el objeto msg con el resultado de la suma como nuevo msg.payload
    return msg;
} else {
    // Si msg.payload no contiene al menos 2 elementos (es decir, no es un array válido o no tiene 2 registros Modbus):
    
    // Mostramos un mensaje de error en la consola de Node-RED
    node.error("Payload no contiene dos registros Modbus", msg);
    
    // No devolvemos nada, retornamos null para indicar que la ejecución no fue exitosa
    return null;
}
