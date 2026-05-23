let electron = null;
try {
  electron = require('electron');
} catch (error) {
  electron = {};
}

const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const app = electron.app;
const BrowserWindow = electron.BrowserWindow;
const ipcMain = electron.ipcMain;

let backendProcess = null;

function getBackendWorkingDirectory() {
  return path.resolve(__dirname, '..', '..');
}

function getBackendArgs() {
  return ['-m', 'backend.server'];
}

function getPythonExecutable() {
  if (process.env.XHS_PYTHON) {
    return process.env.XHS_PYTHON;
  }
  const bundledPython = path.join(
    process.env.USERPROFILE || '',
    '.cache',
    'codex-runtimes',
    'codex-primary-runtime',
    'dependencies',
    'python',
    'python.exe'
  );
  if (fs.existsSync(bundledPython)) {
    return bundledPython;
  }
  return 'python';
}

function startBackend() {
  if (backendProcess) {
    return backendProcess;
  }
  backendProcess = spawn(getPythonExecutable(), getBackendArgs(), {
    cwd: getBackendWorkingDirectory(),
    windowsHide: true,
    stdio: 'ignore'
  });
  backendProcess.on('exit', () => {
    backendProcess = null;
  });
  return backendProcess;
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 1000,
    minHeight: 680,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  });
  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

if (require.main === module && app) {
  app.whenReady().then(() => {
    startBackend();
    createWindow();

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });

  app.on('before-quit', stopBackend);
  ipcMain.handle('backend:base-url', () => 'http://127.0.0.1:8787');
}

module.exports = {
  getBackendArgs,
  getBackendWorkingDirectory,
  getPythonExecutable,
  startBackend,
  stopBackend
};
