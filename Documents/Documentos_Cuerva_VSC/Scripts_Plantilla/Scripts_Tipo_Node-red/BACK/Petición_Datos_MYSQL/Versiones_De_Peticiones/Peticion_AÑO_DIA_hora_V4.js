// Nodo: SQL Gen (polling revisado)
// Entrada: 
//   • msg.trigger (bool)   ← Inject configurado para poner sólo esta propiedad
//   • msg.payload, msg.period ← Date-picker
// Salida: msg.topic con la consulta SQL + msg.selected_period, msg.startDate, msg.endDate

// 1) Recuperar settings previos
let settings = flow.get('lastSettings');

// 2) ¿Viene del date-picker?
if (msg.period !== undefined) {
  // Guardamos la nueva selección
  settings = { period: msg.period, payload: msg.payload };
  flow.set('lastSettings', settings);
}
// 3) ¿Viene del inject de polling?
else if (msg.trigger === true) {
  if (!settings) {
    // Aún no hay selección: no hacemos nada
    node.warn("Polling ignorado: no hay fecha seleccionada aún");
    return null;
  }
}
// 4) Otro tipo de mensaje, lo descartamos
else {
  return null;
}

// 5) Preparamos msg con la selección
const { period, payload } = settings;
msg.period  = period;
msg.payload = payload;

// 6) Generación de SQL (igual que antes)
const SQL_BY_MONTH = "DATE_FORMAT(fecha, '%Y-%m')";
const SQL_BY_DAY   = "DATE_FORMAT(fecha, '%Y-%m-%d')";
const SQL_BY_HOUR  = "DATE_FORMAT(fecha, '%Y-%m-%d %H:00:00')";

function fmt(d) {
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth()+1).padStart(2,'0')}-${String(d.getUTCDate()).padStart(2,'0')}`;
}

try {
  let startDate, endDate, groupBy;

  switch (period) {
    case 'year': {
      const y = parseInt(payload, 10);
      startDate = new Date(Date.UTC(y, 0, 1));
      endDate   = new Date(Date.UTC(y, 11, 31));
      groupBy   = SQL_BY_MONTH;
      break;
    }
    case 'month': {
      const d = new Date(payload);
      const y = d.getFullYear(), m = d.getMonth();
      startDate = new Date(Date.UTC(y, m, 1));
      endDate   = new Date(Date.UTC(y, m+1, 0, 23,59,59));
      groupBy   = SQL_BY_DAY;
      break;
    }
    case 'week': {
      const d = new Date(payload);
      const base = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
      const dow  = base.getUTCDay();
      const diff = (dow === 0 ? -6 : 1 - dow);
      startDate = new Date(base); startDate.setUTCDate(base.getUTCDate() + diff);
      endDate   = new Date(startDate); endDate.setUTCDate(startDate.getUTCDate() + 6);
      groupBy   = SQL_BY_DAY;
      break;
    }
    case 'day': {
      const d = new Date(payload);
      const Y = d.getFullYear(), M = String(d.getMonth()+1).padStart(2,'0'), D = String(d.getDate()).padStart(2,'0');
      const dayStr = `${Y}-${M}-${D}`;
      msg.topic           = `
        SELECT
          ${SQL_BY_HOUR} AS periodo,
          SUM(Radiacion_Solar) AS Radiacion_Solar,
          SUM(Temperatura)     AS Temperatura
        FROM Mediciones_Sensores
        WHERE fecha BETWEEN '${dayStr} 00:00:00' AND '${dayStr} 23:59:59'
        GROUP BY 1 ORDER BY 1
      `.replace(/\s+/g,' ').trim();
      msg.selected_period = 'day';
      msg.startDate       = dayStr;
      msg.endDate         = dayStr;
      delete msg.payload;
      return msg;
    }
    default:
      throw new Error(`Unknown period: ${period}`);
  }

  // Para year/month/week
  const selectCol = `${groupBy} AS periodo`;
  msg.topic = `
    SELECT
      ${selectCol},
      SUM(Radiacion_Solar) AS Radiacion_Solar,
      SUM(Temperatura)     AS Temperatura
    FROM Mediciones_Sensores
    WHERE fecha BETWEEN '${fmt(startDate)} 00:00:00' AND '${fmt(endDate)} 23:59:59'
    GROUP BY 1 ORDER BY 1
  `.replace(/\s+/g,' ').trim();

  msg.selected_period = period;
  msg.startDate       = fmt(startDate);
  msg.endDate         = fmt(endDate);
  delete msg.payload;
  return msg;

} catch (err) {
  node.error(`SQL Gen Error: ${err.message}`, msg);
  return null;
}
