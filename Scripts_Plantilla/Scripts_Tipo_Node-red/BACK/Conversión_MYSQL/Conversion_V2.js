// Nodo: Conversión a Chart
// Entrada: msg.payload = array de filas [{periodo, Radiacion_Solar, Temperatura}, …]
//          msg.selected_period ('year'|'month'|'week'|'day')
//          msg.startDate, msg.endDate ("YYYY-MM-DD")
// Salida: msg.payload = [ { series: [...], data: [...], labels: [...] } ]

const rows = Array.isArray(msg.payload) ? msg.payload : [];
const periodType = msg.selected_period;
const startDate = msg.startDate;
const endDate = msg.endDate;

// Genera array completo de periodos
function genPeriods(start, end, type) {
    let list = [];
    const s = new Date(start + 'T00:00:00');
    const e = new Date(end + 'T00:00:00');
    let cur = new Date(s);

    if (type === 'year') {
        // 12 meses del año
        for (let m = 0; m < 12; m++) {
            const ym = `${s.getUTCFullYear()}-${String(m+1).padStart(2,'0')}`;
            list.push(ym);
        }
    }
    else if (type === 'month' || type === 'week') {
        // días entre start y end
        while (cur <= e) {
            const d = `${cur.getUTCFullYear()}-${String(cur.getUTCMonth()+1).padStart(2,'0')}-${String(cur.getUTCDate()).padStart(2,'0')}`;
            list.push(d);
            cur.setUTCDate(cur.getUTCDate() + 1);
        }
    }
    else if (type === 'day') {
        // 24 horas del día
        for (let h = 0; h < 24; h++) {
            const hh = String(h).padStart(2,'0');
            list.push(`${start} ${hh}:00:00`);
        }
    }
    return list;
}

// Map de datos para lookup rápido
const dataMap = {};
rows.forEach(r => dataMap[r.periodo] = { rs: r.Radiacion_Solar, t: r.Temperatura });

// Lista completa de labels
const fullPeriods = genPeriods(startDate, endDate, periodType);

// Construir chart
let chart = { series: ["Radiacion_Solar","Temperatura"], data: [[],[]], labels: [] };

fullPeriods.forEach(pv => {
    // Formateo label
    chart.labels.push(
        periodType === 'day'
            ? new Date(pv).toLocaleTimeString('es-ES', { hour:'2-digit', minute:'2-digit', hour12:false })
            : pv
    );
    const entry = dataMap[pv] || { rs:0, t:0 };
    chart.data[0].push(entry.rs);
    chart.data[1].push(entry.t);
});

msg.payload = [chart];
// Limpiar propiedades extra
delete msg.selected_period;
delete msg.startDate;
delete msg.endDate;
return msg;
