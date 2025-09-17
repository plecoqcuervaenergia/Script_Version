// Function node: parseRegistersAndBuildPayload
// Entrada esperada: msg.payload = Array de 2 enteros [wordHigh, wordLow]
// Opcional: msg.scale (ej. 1000), msg.location, msg.address, msg.entityId, msg.apikey, msg.endpointBase

const words = msg.payload;
if (!Array.isArray(words) || words.length < 2) {
    node.error("Se esperaba msg.payload = [high16, low16]");
    return null;
}

const high = words[0] & 0xFFFF;
const low  = words[1] & 0xFFFF;

// Combinar en 32-bit sin signo:
const combinedUnsigned = high * 65536 + low;

// Interpretar como entero con signo de 32 bits si corresponde:
let combinedSigned = combinedUnsigned;
if (combinedUnsigned & 0x80000000) {
    combinedSigned = combinedUnsigned - 0x100000000;
}

// Intentar inferir valor real:
// Regla heurística:
//  - si high === 0 y low < 10000 => puede ser fixed-point en low (ej. 337 -> 0.337 con scale 1000)
//  - si high !== 0 => interpretar full 32-bit (y luego aplicar scale si se proporciona)
let value;
const providedScale = (typeof msg.scale === 'number') ? msg.scale : null;

if (providedScale !== null) {
    // si el usuario indica escala, úsala (ej. 1000)
    value = combinedSigned / providedScale;
} else if (high === 0 && low < 10000) {
    // heurística: si el high word es 0 y low es pequeño, asumimos fixed-point / milésimas
    value = low / 1000;
} else {
    // valor 32-bit sin signo o con signo
    value = combinedSigned; // puedes dividirlo después si sabes la escala real
}

// Construimos el JSON que pide la API (ejemplo con campo Potencia_Activa)
const payload = {
    dateObserved: (new Date()).toISOString(),
    activePower: Number(value.toFixed(6))  // ajustar decimales según convenga
};

// Añade location/address si vienen en msg (opcional)
if (msg.location) payload.location = msg.location;    // espera GeoJSON { type:"Point", coordinates:[lon,lat] }
if (msg.address)  payload.address  = msg.address;

// Preparamos headers para el HTTP node
msg.payload = payload;
msg.headers = msg.headers || {};
msg.headers['Content-Type'] = 'application/json';

// Si quieres configurar URL desde aquí:
const endpointBase = msg.endpointBase || "https://iota-json.vlci.valencia.es:18185/iot/json";
const apikey = msg.apikey || "vlcprognesm9oajr9rxwwdem";   // cambia por la key correcta
const entityId = msg.entityId || "ep_cemen_general_hourly"; // cambia según entidad
msg.url = `${endpointBase}?k=${encodeURIComponent(apikey)}&i=${encodeURIComponent(entityId)}&getCmd=0`;

// Devuelve msg para enviarlo al nodo HTTP request
return msg;
