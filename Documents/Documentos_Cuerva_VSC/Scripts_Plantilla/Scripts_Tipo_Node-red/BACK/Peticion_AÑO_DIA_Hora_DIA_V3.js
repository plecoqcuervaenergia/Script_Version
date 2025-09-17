// msg.payload: 
//   - number/string 'YYYY'    si period==='year'
//   - 'YYYY-MM'               si period==='month'
//   - 'YYYY-Www'              si period==='week'
//   - 'YYYY-MM-DD'            si period==='day'
// msg.period: 'year' | 'month' | 'week' | 'day'

// 1) Calcula startDate y endDate
let startDate, endDate;

if (msg.period === 'year') {
  // ---- AÑO ----
  let year = parseInt(msg.payload, 10);
  startDate = new Date(year, 0, 1);        // 1 Ene
  endDate   = new Date(year + 1, 0, 0);    // 31 Dic

} else if (msg.period === 'week' && typeof msg.payload === 'string' && msg.payload.includes('-W')) {
  // ---- SEMANA ISO (Lun-Dom) ----
  let [yearStr, weekStr] = msg.payload.split('-W');
  let year = parseInt(yearStr, 10);
  let week = parseInt(weekStr, 10);
  let simple = new Date(year, 0, 1 + (week - 1) * 7);
  let dayOfWeek = simple.getDay();         // 0=Dom,1=Lun,...6=Sáb
  let diffToMonday = (dayOfWeek === 0 ? -6 : 1 - dayOfWeek);
  let monday = new Date(simple.setDate(simple.getDate() + diffToMonday));
  startDate = new Date(monday);
  endDate   = new Date(monday);
  endDate.setDate(endDate.getDate() + 6);

} else if (msg.period === 'day' && typeof msg.payload === 'string') {
  // ---- DÍA ----
  let d = new Date(msg.payload);
  startDate = new Date(d);
  endDate   = new Date(d);

} else {
  // ---- MES ----
  let selected = msg.payload ? new Date(msg.payload) : new Date();
  let y = selected.getFullYear();
  let m = selected.getMonth();
  startDate = new Date(y, m, 1);
  endDate   = new Date(y, m + 1, 0);
}

// 2) Ajusta horas y formatea a 'YYYY-MM-DD HH:MM:SS'
startDate.setHours(0,0,0);
endDate.setHours(23,59,59);

function formatDateTime(d) {
  let date = d.toISOString().split('T')[0];
  let time = d.toTimeString().split(' ')[0];
  return `${date} ${time}`;
}

let formattedStart = formatDateTime(startDate);
let formattedEnd   = formatDateTime(endDate);

// 3) Construye la consulta SQL según el periodo
if (msg.period === 'year') {
  // Año completo → agrupamos por mes
  // Usa DATE_FORMAT para extraer 'YYYY-MM'. Ajusta si tu SGBD es distinto.
  msg.topic = `
    SELECT 
      DATE_FORMAT(fecha, '%Y-%m')      AS fecha,
      SUM(Radiacion_Solar)             AS Radiacion_Solar,
      SUM(Temperatura)                 AS Temperatura
    FROM Mediciones_Sensores
    WHERE fecha >= '${formattedStart}'
      AND fecha <= '${formattedEnd}'
    GROUP BY YEAR(fecha), MONTH(fecha)
    ORDER BY YEAR(fecha), MONTH(fecha)
  `.trim();

} else if (msg.period === 'month' || msg.period === 'week') {
  // Mes o semana → agrupamos por día
  msg.topic = `
    SELECT 
      DATE(fecha)                      AS fecha,
      SUM(Radiacion_Solar)             AS Radiacion_Solar,
      SUM(Temperatura)                 AS Temperatura
    FROM Mediciones_Sensores
    WHERE fecha >= '${formattedStart}'
      AND fecha <= '${formattedEnd}'
    GROUP BY DATE(fecha)
    ORDER BY DATE(fecha)
  `.trim();

} else {
  // Día → todos los registros por hora
  msg.topic = `
    SELECT 
      fecha,
      Radiacion_Solar,
      Temperatura
    FROM Mediciones_Sensores
    WHERE fecha >= '${formattedStart}'
      AND fecha <= '${formattedEnd}'
    ORDER BY fecha
  `.trim();
}

return msg;
