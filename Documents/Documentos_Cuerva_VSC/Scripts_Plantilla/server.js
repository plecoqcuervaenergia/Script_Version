// ~/.node-red/server.js
const http    = require('http');
const express = require('express');
const RED     = require('node-red');

// Carga tu settings normal (el que acabas de dejar en settings.js)
const settings = require('./server.js');

// App y server para el editor
const adminApp    = express();
const adminServer = http.createServer(adminApp);
settings.httpAdminRoot = '/admin';
settings.httpNodeRoot  = false;
RED.init(adminServer, settings);
adminApp.use(settings.httpAdminRoot, RED.httpAdmin);

// App y server para el Dashboard
const nodeApp    = express();
const nodeServer = http.createServer(nodeApp);
const dashSettings = Object.assign({}, settings, {
  httpAdminRoot: false,
  httpNodeRoot : '/ui',
  ui: { path: '/ui' },
});
RED.init(nodeServer, dashSettings);
nodeApp.use(dashSettings.httpNodeRoot, RED.httpNode);

// Arranca ambos
adminServer.listen(40001, () => {
  console.log('Editor en http://localhost:40001/admin');
});
nodeServer.listen(1880, () => {
  console.log('Dashboard en http://localhost:1880/ui');
});
