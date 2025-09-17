// Convierte el contenido del payload a una cadena de texto en formato UTF-8
msg.payload = msg.payload.toString('utf8');

// Devuelve el mensaje modificado para que pueda ser procesado por los siguientes nodos en el flujo
return msg;
