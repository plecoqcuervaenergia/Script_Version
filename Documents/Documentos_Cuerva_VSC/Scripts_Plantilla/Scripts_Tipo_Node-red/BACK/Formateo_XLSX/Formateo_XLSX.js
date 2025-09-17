//NODO FUCTION A LA SALIDA DE MYSQL

// msg.payload: array de objetos con { fecha, Radiacion_Solar, Temperatura }
let data = msg.payload;

let excelData = data.map(row => {
    // parsear la fecha ISO a objeto Date
    const d = new Date(row.fecha);
    // formatear a “dd/mm/yyyy hh:MM:ss”
    const fechaHora = d.toLocaleString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
    return {
        FechaHora: fechaHora,
        Temperatura: row.Temperatura,
        Radiacion_Solar: row.Radiacion_Solar
    };
});

msg.payload = excelData;
msg.topic = "Datos sensores Meteo Cuerva";
msg.filename = "Datos_FOTOV_UNI_MADRID.xlsx";
return msg;



//NODO FUCTION A LA SALIDA DEL NODO EXCEL


// Obtener fechas desde los parámetros
const fechaInicio = msg.req.query.inicio.split('T')[0]; // Ej: "2025-04-22"
const fechaFin = msg.req.query.fin.split('T')[0];

// Configurar headers para forzar la descarga como .xlsx
msg.headers = {
  "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // MIME type correcto
  "Content-Disposition": `attachment; filename="Datos_Fotov_UNI_MADRID_${fechaInicio}_a_${fechaFin}.xlsx"` // Extensión explícita
};

return msg;