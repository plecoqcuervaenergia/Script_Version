
// Si msg.payload tiene valor lo usa, de lo contrario toma la fecha actual
var selectedDate = msg.payload ? new Date(msg.payload) : new Date();

// Formatea la fecha seleccionada para obtener el inicio del día (00:00:00)
var startDate = selectedDate.toISOString().split('T')[0] + ' 00:00:00';

// Formatea la fecha seleccionada para obtener el final del día (23:59:59)
var endDate = selectedDate.toISOString().split('T')[0] + ' 23:59:59';

// Construye la consulta SQL para obtener la fecha, temperatura y radiación solar 
// de la tabla 'Mediciones_Sensores' dentro del rango del día seleccionado
msg.topic = `SELECT fecha, Temperatura, Radiacion_Solar
             FROM Mediciones_Sensores 
             WHERE fecha >= '${startDate}' AND fecha <= '${endDate}'`;

// Retorna el mensaje con la consulta SQL lista para ser ejecutada
return msg;

