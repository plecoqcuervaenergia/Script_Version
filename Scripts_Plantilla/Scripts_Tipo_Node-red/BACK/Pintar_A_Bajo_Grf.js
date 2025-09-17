var limite = 2000;  // Valor en Y donde cambia el color
var colorPorDefecto = 'blue';  // Azul
var colorAlto = 'red';  // Rojo

// Configurar los datos del gráfico
msg.payload = [
    {
        "series": ["Dato"],
        "data": [[msg.payload]],
        "labels": [""]
    }
];

// Verifica si el valor Y supera el límite
msg.ui_control = {
    options: {
        elements: {
            line: {
                borderColor: msg.payload[0].data[0][1] > limite ? colorAlto : colorPorDefecto
                
            }
        }
    }
};

return msg;

