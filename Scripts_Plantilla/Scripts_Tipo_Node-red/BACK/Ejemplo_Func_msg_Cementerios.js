//EJEMPLO DE ENVÍO DE DATOS


//Constantes y variables aleatorias


//Coordenadas Churriana de la Vega, Granada
const LONGITUD = -3.64595;

const LATITUD = 37.14777;




//Generación de parámetros random de un inversor
const fechaObservada = (new Date()).toISOString();

const potenciaActiva = Math.floor(2000 + Math.random() * 8000);

const energiaGenerada = Number((potenciaActiva).toFixed(1));

const energiaExportadaBruta = energiaGenerada * (0.8 + Math.random() * 0.15);

const energiaExportada = Number(Math.min(energiaExportadaBruta, energiaGenerada).toFixed(1));

const energiaConsumida = Number((energiaGenerada * (0.02 + Math.random() * 0.05)).toFixed(1));

const energiaReactivaConsumida = Number((Math.random() * 20).toFixed(1));

const energiaReactivaConsumidaRed = Number((Math.random() * 10).toFixed(1));

const potenciaReactiva = Number((Math.random() * 50).toFixed(1));

const intensidadR = Number((20 + Math.random() * 15).toFixed(1));

const intensidadS = Number((20 + Math.random() * 15).toFixed(1));

const intensidadT = Number((20 + Math.random() * 15).toFixed(1));

const tensionR = Number((215 + Math.random() * 10).toFixed(1));

const tensionS = Number((215 + Math.random() * 10).toFixed(1));

const tensionT = Number((215 + Math.random() * 10).toFixed(1));


//Variable de dirección 
const direccion = "Churriana de la Vega, Granada, Spain";


// Construir el payload
msg.payload = {
    dateObserved: fechaObservada,
    energyGenerated: energiaGenerada,
    energyExported: energiaExportada,
    energyConsumed: energiaConsumida,
    reactiveEnergyConsumed: energiaReactivaConsumida,
    energyConsumedGrid: 0.0,
    reactiveEnergyConsumedGrid: energiaReactivaConsumidaRed,
    activePower: potenciaActiva,
    reactivePower: potenciaReactiva,
    intensityR: intensidadR,
    intensityS: intensidadS,
    intensityT: intensidadT,
    voltageR: tensionR,
    voltageS: tensionS,
    voltageT: tensionT,
    location: { type: "Point", coordinates: [LONGITUD, LATITUD] },
    address: direccion
};


//Cabeceras HTTP
msg.headers = {
    "Content-Type": "application/json",
    "Connection": "keep-alive"
};

return msg;


