const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');

let win, nodeRed;

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      contextIsolation: true
    }
  });

  nodeRed = spawn('node-red', [], { shell: true });

  setTimeout(() => {
    win.loadURL('http://localhost:1880');
  }, 4000);

  nodeRed.stdout.on('data', (data) => {
    console.log(`Node-RED: ${data}`);
  });

  nodeRed.stderr.on('data', (data) => {
    console.error(`Error: ${data}`);
  });

  nodeRed.on('close', () => {
    console.log(`Node-RED cerrado`);
    app.quit();
  });

  win.on('closed', () => {
    win = null;
    if (nodeRed) nodeRed.kill();
  });
}

app.on('ready', createWindow);
app.on('window-all-closed', () => {
  app.quit();
});
