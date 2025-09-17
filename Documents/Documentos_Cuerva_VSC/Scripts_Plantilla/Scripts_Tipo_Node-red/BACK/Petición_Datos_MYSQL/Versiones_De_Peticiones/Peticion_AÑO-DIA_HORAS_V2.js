// msg.payload: 
//   - number/string 'YYYY'    si period==='year'
//   - 'YYYY-MM'               si period==='month'
//   - 'YYYY-Www'              si period==='week'
//   - 'YYYY-MM-DD'            si period==='day'
// msg.period: 'year' | 'month' | 'week' | 'day'

let startDate, endDate;

if (msg.period === 'year') {
  // ---- AÑO COMPLETO ----
  let year = parseInt(msg.payload, 10);
  startDate = new Date(year, 0, 1);        // 1 Ene
  endDate = new Date(year + 1, 0, 0);    // 31 Dic (día 0 del año siguiente)

} else if (msg.period === 'week' && typeof msg.payload === 'string' && msg.payload.includes('-W')) {
  // ---- SEMANA ISO (lunes a domingo) ----
  let [yearStr, weekStr] = msg.payload.split('-W');
  let year = parseInt(yearStr, 10);
  let week = parseInt(weekStr, 10);

  let simple = new Date(year, 0, 1 + (week - 1) * 7);
  let dayOfWeek = simple.getDay();    // 0=Dom,1=Lun,...6=Sáb
  let diffToMonday = (dayOfWeek === 0 ? -6 : 1 - dayOfWeek);
  let monday = new Date(simple.setDate(simple.getDate() + diffToMonday));

  startDate = new Date(monday);
  endDate = new Date(monday);
  endDate.setDate(endDate.getDate() + 6);

} else if (msg.period === 'day' && typeof msg.payload === 'string') {
  // ---- DÍA CONCRETO ----
  let d = new Date(msg.payload);
  startDate = new Date(d);
  endDate = new Date(d);

} else {
  // ---- MES ENTERO ----
  let selected = msg.payload ? new Date(msg.payload) : new Date();
  let y = selected.getFullYear();
  let m = selected.getMonth();
  startDate = new Date(y, m, 1);
  endDate = new Date(y, m + 1, 0);
}

// Función de formateo a 'YYYY-MM-DD'
function formatDate(d) {
  return d.toISOString().split('T')[0];
}

let formattedStart = `${formatDate(startDate)} 00:00:00`;
let formattedEnd = `${formatDate(endDate)} 23:59:59`;

msg.topic = `
  SELECT fecha, Radiacion_Solar, Temperatura
    FROM Mediciones_Sensores
   WHERE fecha >= '${formattedStart}'
     AND fecha <= '${formattedEnd}'
   ORDER BY fecha
`.trim();

return msg;
