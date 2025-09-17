// Supongamos que tu array está en msg.payload.data
let data = msg.payload.data;

// Extraer los índices 1 y 3
let result = [data[1], data[3]];

// Retornar el resultado
msg.payload = result;
return msg;
