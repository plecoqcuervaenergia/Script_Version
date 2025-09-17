/*// Obtener los datos del payload, que es el resultado de la consulta a la base de datos
const inp = msg.payload;


// Inicializar la estructura de los datos para el gráfico (chartData)
var chardatos_Rad_Solar = [{
    // La propiedad "series" define el nombre de la serie para el gráfico
    series: ["Radiacion_Solar"],
    // La propiedad "data" es un array de arrays
    // En este caso está inicializado con un array vacío dentro
    data: [[]],
    // La propiedad "labels" contendrá las etiquetas para el eje X del gráfico 
    labels: [""]
}]

// Iterar sobre cada elemento en el array "inp" que contiene los datos de la consulta
for (let item of inp) {
    // Agregar un punto de datos a la serie "Radiacion_Solar" en el gráfico
    // Se empuja un objeto que contiene "x" (fecha) y "y" (valor de la radiación solar)
    chardatos_Rad_Solar[0].data[0].push({
        // La propiedad "x" representa la fecha (se supone que "item.fecha" es una cadena de texto con la fecha)
        x: item.fecha,
        // La propiedad "y" representa el valor de la radiación solar
        y: item.Radiacion_Solar
    })
}

// Asignar el gráfico procesado al payload para que pueda ser usado por el siguiente nodo
msg.payload = chardatos_Rad_Solar;

// Retornar el mensaje con los datos del gráfico
return msg;


*/




/*// Obtener los datos de la consulta
const inp = msg.payload;

// Inicializar la estructura para Chart v2 JSON
let chartData = [{
    series: ["Radiacion_Solar"],
    data: [[]],
    labels: []
}];

for (let item of inp) {
    // Asegurarnos de tener un objeto Date
    let dateObj = item.fecha instanceof Date
        ? item.fecha
        : new Date(item.fecha);

    // Meter el valor numérico
    chartData[0].data[0].push(item.Radiacion_Solar);
    // Meter la etiqueta (Date directamente)
    chartData[0].labels.push(dateObj);
}

msg.payload = chartData;
return msg;*/

/*
// Obtener los datos de la consulta
const inp = msg.payload;

// Inicializar la estructura para Chart v2 JSON con DOS series
let chartData = [{
    series: ["Radiacion_Solar", "Temperatura"],
    data: [[], []],   // data[0] para Radiacion_Solar, data[1] para Temperatura
    labels: []          // mismísimas etiquetas para ambas series
}];

// Recorrer cada fila
for (let item of inp) {
    // Convertir a Date si viene string ISO
    let dateObj = item.fecha instanceof Date
        ? item.fecha
        : new Date(item.fecha);

    // Meter el dato de radiación en la serie 0
    chartData[0].data[0].push(item.Radiacion_Solar);
    // Meter el dato de temperatura en la serie 1
    chartData[0].data[1].push(item.Temperatura);
    // Meter la etiqueta (fecha) una sola vez
    chartData[0].labels.push(dateObj);
}

// Devolver el payload ya combinado
msg.payload = chartData;
return msg;
*/

/*
const inp = msg.payload;
let chartData = [{
    series: ["Radiacion_Solar", "Temperatura"],
    data: [[], []],     // dos arrays, uno por cada serie
    labels: []              // mismo array de fechas
}];

for (let item of inp) {
    let dateObj = item.fecha instanceof Date
        ? item.fecha
        : new Date(item.fecha);

    chartData[0].data[0].push(item.Radiacion_Solar);
    chartData[0].data[1].push(item.Temperatura);
    chartData[0].labels.push(dateObj);
}

msg.payload = chartData;
return msg;
*/


// msg.payload: array [{ periodo, Radiacion_Solar, Temperatura }, …]
// msg.selected_period: 'year'|'month'|'week'|'day'

// msg.payload: array de filas [{ periodo, Radiacion_Solar, Temperatura }, …]
// msg.selected_period: 'year'|'month'|'week'|'day'
// msg.startDate, msg.endDate: "YYYY-MM-DD"

const rows = Array.isArray(msg.payload) ? msg.payload : [];
const periodType = msg.selected_period;
const startDate = msg.startDate;
const endDate = msg.endDate;

// Genera array de periodos completos
function genPeriods(start, end, type) {
    let list = [];
    const s = new Date(start + 'T00:00:00');
    const e = new Date(end + 'T00:00:00');
    let cur = new Date(s);

    if (type === 'year') {
        // meses
        for (let m = 0; m < 12; m++) {
            const ym = `${s.getUTCFullYear()}-${String(m + 1).padStart(2, '0')}`;
            list.push(ym);
        }
    }
    else if (type === 'month' || type === 'week') {
        // días
        while (cur <= e) {
            const d = `${cur.getUTCFullYear()}-${String(cur.getUTCMonth() + 1).padStart(2, '0')}-${String(cur.getUTCDate()).padStart(2, '0')}`;
            list.push(d);
            cur.setUTCDate(cur.getUTCDate() + 1);
        }
    }
    else if (type === 'day') {
        // horas 00–23
        for (let h = 0; h < 24; h++) {
            const hh = String(h).padStart(2, '0');
            list.push(`${start} ${hh}:00:00`);
        }
    }
    return list;
}

// Creamos un mapa para buscar rápido
const dataMap = {};
rows.forEach(r => dataMap[r.periodo] = { rs: r.Radiacion_Solar, t: r.Temperatura });

// Generamos la lista completa de periodos
const fullPeriods = genPeriods(startDate, endDate, periodType);

// Construimos chartData
let chart = { series: ["Radiacion_Solar", "Temperatura"], data: [[], []], labels: [] };

fullPeriods.forEach(pv => {
    chart.labels.push(
        periodType === 'day'
            ? new Date(pv).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', hour12: false })
            : pv
    );
    const entry = dataMap[pv] || { rs: 0, t: 0 };
    chart.data[0].push(entry.rs || 0);
    chart.data[1].push(entry.t || 0);
});

msg.payload = [chart];
delete msg.selected_period;
delete msg.startDate;
delete msg.endDate;
return msg;
