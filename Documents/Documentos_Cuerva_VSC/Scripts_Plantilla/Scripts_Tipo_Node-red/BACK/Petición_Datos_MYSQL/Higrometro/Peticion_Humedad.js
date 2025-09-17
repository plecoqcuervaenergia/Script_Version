// ─── Nodo: SQL Gen (polling revisado con parsing de fecha ISO para “year” | “month” | “week” | “day”) ───

try {
  // 1) Recuperar últimos settings del flujo
  let settings = flow.get('lastSettings');

  // 2) Si viene del date-picker: actualizamos settings
  if (msg.period !== undefined) {
    settings = { payload: msg.payload, period: msg.period };
    flow.set('lastSettings', settings);

  // 3) Si viene del polling (msg.trigger) sin settings previos: abortar
  } else if (msg.trigger === true) {
    if (!settings) {
      node.warn("Polling ignorado: sin selección previa");
      return null;
    }

  // 4) Caso contrario: no es date-picker ni polling → descartar
  } else {
    return null;
  }

  // 5) Extraer payload y period de settings
  let payload = settings.payload;
  const period = settings.period;
  msg.payload = payload;
  msg.period = period;

  // 6) Definiciones SQL para agrupar
  const SQL_BY_MONTH = "DATE_FORMAT(fecha, '%Y-%m')";
  const SQL_BY_DAY = "DATE_FORMAT(fecha, '%Y-%m-%d')";
  const SQL_BY_HOUR = "DATE_FORMAT(fecha, '%Y-%m-%d %H:00:00')";

  // Función auxiliar: formatea Date a "YYYY-MM-DD" en UTC
  function fmt(date) {
    return date.toISOString().slice(0, 10);
  }

  // 7) Manejo de payload si es un objeto Date
  if (payload instanceof Date) {
    const y = payload.getUTCFullYear();
    const m = payload.getUTCMonth() + 1;
    const d = payload.getUTCDate();

    if (period === 'month') {
      msg.payload = `${y}-${String(m).padStart(2, '0')}`;
    } else if (period === 'week' || period === 'day') {
      msg.payload = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    }
    payload = msg.payload;
  }

  let startDate, endDate, groupBy;

  // 8) Calcular rango y agrupación según el periodo
  switch (period) {
    case 'year': {
      const year = parseInt(payload.split('-')[0], 10);
      if (isNaN(year)) throw new Error(`Año inválido: ${payload}`);

      startDate = new Date(Date.UTC(year, 0, 1));
      endDate = new Date(Date.UTC(year, 11, 31, 23, 59, 59));
      groupBy = SQL_BY_MONTH;
      break;
    }

    case 'month': {
      // Payload "YYYY-MM" indica mes anterior; ajustamos un mes adelante
      const [yIn, mIn] = payload.split('-').map(n => parseInt(n, 10));
      if (isNaN(yIn) || isNaN(mIn)) throw new Error(`Mes inválido: ${payload}`);

      let yInt = yIn;
      let mInt = mIn + 1;
      if (mInt > 12) { mInt = 1; yInt++; }

      startDate = new Date(Date.UTC(yInt, mInt - 1, 1));
      endDate = new Date(Date.UTC(yInt, mInt, 0, 23, 59, 59));
      groupBy = SQL_BY_DAY;
      break;
    }

    case 'week': {
      // Payload "YYYY-MM-DD" como punto de referencia
      const [y, m, d] = payload.split('-').map(n => parseInt(n, 10));
      if ([y, m, d].some(v => isNaN(v))) throw new Error(`Fecha inválida: ${payload}`);

      const base = new Date(Date.UTC(y, m - 1, d));
      const dow = base.getUTCDay();          // 0=Dom, 1=Lun…6=Sáb
      const diff = (dow === 0 ? -6 : 1 - dow);    // Ajuste al lunes

      startDate = new Date(base);
      startDate.setUTCDate(base.getUTCDate() + diff);

      endDate = new Date(startDate);
      endDate.setUTCDate(startDate.getUTCDate() + 6); // Domingo de la misma semana
      groupBy = SQL_BY_DAY;
      break;
    }

    case 'day': {
      // Payload "YYYY-MM-DD" indica día anterior; ajustamos un día adelante
      const [Y, M, D] = payload.split('-').map(n => parseInt(n, 10));
      if ([Y, M, D].some(v => isNaN(v))) throw new Error(`Fecha inválida: ${payload}`);

      let date = new Date(Date.UTC(Y, M - 1, D));
      date.setUTCDate(date.getUTCDate() + 1);      // Día corregido
      const corrected = fmt(date);

      // Generar consulta SQL para el periodo "day"
      msg.topic = `
        SELECT
          ${SQL_BY_HOUR} AS periodo,
          SUM(Humedad) AS Humedad
        FROM Mediciones_Sensores
        WHERE fecha BETWEEN '${corrected} 00:00:00' AND '${corrected} 23:59:59'
        GROUP BY 1
        ORDER BY 1
      `.replace(/\s+/g, ' ').trim();

      msg.selected_period = 'day';
      msg.startDate = corrected;
      msg.endDate = corrected;
      delete msg.payload;
      return msg;
    }

    default:
      throw new Error(`Periodo desconocido: ${period}`);
  }

  // 9) Construir consulta SQL para 'year', 'month' y 'week'
  msg.topic = `
    SELECT
      ${groupBy} AS periodo,
      SUM(Humedad) AS Humedad
    FROM Mediciones_Sensores
    WHERE fecha BETWEEN '${fmt(startDate)} 00:00:00' AND '${fmt(endDate)} 23:59:59'
    GROUP BY 1
    ORDER BY 1
  `.replace(/\s+/g, ' ').trim();

  msg.selected_period = period;
  msg.startDate = fmt(startDate);
  msg.endDate = fmt(endDate);
  delete msg.payload;

  return msg;

} catch (err) {
  node.error(`SQL Gen Error: ${err.message}`, msg);
  return null;
}