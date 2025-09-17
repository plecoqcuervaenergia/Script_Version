// Nodo: Conversión a Chart (Actualizado para Mediciones_Sensores - Radiacion_Solar)
// Entrada esperada en msg:
//   payload: array de filas [{ periodo, Radiacion_Solar }, …]
//   selected_period: 'year' | 'month' | 'week' | 'day'
//   startDate, endDate: strings "YYYY-MM-DD" que definen el rango
// Salida:
//   msg.payload = [ { series: [...], data: [...], labels: [...] } ]

// Validar y extraer datos de entrada
const rows = Array.isArray(msg.payload) ? msg.payload : [];
const periodType = msg.selected_period;
const startDate = msg.startDate;
const endDate = msg.endDate;

if (!periodType || !startDate || !endDate) {
    node.error("Faltan datos para generar el chart (selected_period, startDate, endDate).", msg);
    return null;
}

// Función para generar la lista completa de periodos entre startDate y endDate
function genPeriods(start, end, type) {
    const list = [];
    let current, startDt, endDt;

    try {
        startDt = new Date(start + 'T00:00:00Z');
        endDt = new Date(end + 'T00:00:00Z');
        if (isNaN(startDt) || isNaN(endDt)) throw new Error("Fechas inválidas");
        current = new Date(startDt);
    } catch (err) {
        node.error(`Error al parsear fechas en genPeriods: ${err.message}`, msg);
        return list;
    }

    if (type === 'year') {
        // 12 meses del año: YYYY-MM
        const year = startDt.getUTCFullYear();
        for (let m = 1; m <= 12; m++) {
            list.push(`${year}-${String(m).padStart(2, '0')}`);
        }

    } else if (type === 'month' || type === 'week') {
        // Cada día entre start y end: YYYY-MM-DD
        while (current <= endDt) {
            const y = current.getUTCFullYear();
            const mo = String(current.getUTCMonth() + 1).padStart(2, '0');
            const da = String(current.getUTCDate()).padStart(2, '0');
            list.push(`${y}-${mo}-${da}`);
            current.setUTCDate(current.getUTCDate() + 1);
            if (list.length > 366) { // Prevenir bucles infinitos o muy largos
                node.warn("genPeriods: rango demasiado largo, se interrumpe bucle.");
                break;
            }
        }

    } else if (type === 'day') {
        // Cada hora del día: "YYYY-MM-DD HH:00:00"
        for (let h = 0; h < 24; h++) {
            const hh = String(h).padStart(2, '0');
            list.push(`${start} ${hh}:00:00`);
        }
    }

    return list;
}

// Crear un map para acceso rápido a los datos por periodo
const dataMap = {};
rows.forEach(row => {
    if (row && row.periodo != null && row.Radiacion_Solar !== undefined) { // Verificar Radiacion_Solar
        dataMap[row.periodo] = {
            radiacion_solar: Number(row.Radiacion_Solar) || 0
        };
    } else {
        node.warn(`Fila ignorada por periodo inválido o falta Radiacion_Solar: ${JSON.stringify(row)}`);
    }
});

// Generar todas las etiquetas de periodo
const fullPeriods = genPeriods(startDate, endDate, periodType);

// Construir el objeto para ui_chart
const chart = {
    series: ["Radiacion_Solar"], // Solo una serie
    data: [[]],                 // Solo un array de datos para la serie
    labels: []
};

// Llenar labels y datos (0 si no hay entrada en dataMap)
fullPeriods.forEach(period => {
    let label = period;

    if (periodType === 'day') {
        // Formatear horas a "HH:MM"
        try {
            const dt = new Date(period.replace(' ', 'T') + 'Z'); // Asegurar parseo UTC
            if (!isNaN(dt)) {
                label = dt.toLocaleTimeString('es-ES', {
                    hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'UTC'
                });
                // No es necesario .replace(/:\d{2}$/, match => match); si el formato ya es HH:MM
            }
        } catch (e) {
            // fallback: usar la cadena original si hay error en formateo
            node.warn(`Error al formatear etiqueta de hora para el chart: ${period}. Error: ${e.message}`);
        }
    }

    chart.labels.push(label);
    const entry = dataMap[period] || { radiacion_solar: 0 }; // Valor por defecto para la nueva estructura
    chart.data[0].push(entry.radiacion_solar); // Añadir a la única serie de datos
});

// Preparar salida para ui_chart y limpiar props auxiliares
msg.payload = [chart];
delete msg.selected_period;
delete msg.startDate;
delete msg.endDate;
delete msg.topic; // msg.topic se usa para la query SQL, ya no es necesario aquí

return msg;