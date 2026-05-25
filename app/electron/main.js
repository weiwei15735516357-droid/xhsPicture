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
const dialog = electron.dialog;
const ipcMain = electron.ipcMain;
const shell = electron.shell;

let backendProcess = null;

function getBackendWorkingDirectory() {
  return path.resolve(__dirname, '..', '..');
}

function getBackendArgs() {
  return ['-m', 'backend.server'];
}

function getImageImportFilters() {
  return [
    { name: '图片文件', extensions: ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'tif', 'tiff', 'jfif'] },
    { name: '所有文件', extensions: ['*'] }
  ];
}

function getDocumentImportFilters() {
  return [
    { name: 'PPT 演示文稿', extensions: ['ppt', 'pptx'] },
    { name: 'Word 文档', extensions: ['doc', 'docx'] },
    { name: 'PDF 文件', extensions: ['pdf'] },
    { name: '所有支持文档', extensions: ['ppt', 'pptx', 'doc', 'docx', 'pdf'] },
    { name: '所有文件', extensions: ['*'] }
  ];
}

function getSpreadsheetImportFilters() {
  return [
    { name: 'Excel 或 CSV 表格', extensions: ['xlsx', 'xlsm', 'csv'] },
    { name: '所有文件', extensions: ['*'] }
  ];
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

if (app) {
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
  ipcMain.handle('dialog:select-project-directory', async () => {
    const result = await dialog.showOpenDialog({ properties: ['openDirectory', 'createDirectory'] });
    return result.canceled ? null : result.filePaths[0];
  });
  ipcMain.handle('dialog:select-import-files', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openFile', 'multiSelections'],
      filters: getImageImportFilters()
    });
    return result.canceled ? [] : result.filePaths;
  });
  ipcMain.handle('dialog:select-import-folder', async () => {
    const result = await dialog.showOpenDialog({ properties: ['openDirectory'] });
    return result.canceled ? null : result.filePaths[0];
  });
  ipcMain.handle('dialog:select-background-image', async () => {
    const result = await dialog.showOpenDialog({ properties: ['openFile'], filters: getImageImportFilters() });
    return result.canceled ? null : result.filePaths[0];
  });
  ipcMain.handle('dialog:select-document-file', async () => {
    const result = await dialog.showOpenDialog({ properties: ['openFile'], filters: getDocumentImportFilters() });
    return result.canceled ? null : result.filePaths[0];
  });
  ipcMain.handle('dialog:select-perspective-scene-image', async () => {
    const result = await dialog.showOpenDialog({ properties: ['openFile'], filters: getImageImportFilters() });
    return result.canceled ? null : result.filePaths[0];
  });
  ipcMain.handle('dialog:select-perspective-overlay-files', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openFile', 'multiSelections'],
      filters: getImageImportFilters()
    });
    return result.canceled ? [] : result.filePaths;
  });
  ipcMain.handle('dialog:select-perspective-overlay-folder', async () => {
    const result = await dialog.showOpenDialog({ properties: ['openDirectory'] });
    if (result.canceled) {
      return [];
    }
    const extensions = new Set(getImageImportFilters()[0].extensions.map((extension) => `.${extension}`));
    return fs
      .readdirSync(result.filePaths[0])
      .filter((filename) => extensions.has(path.extname(filename).toLowerCase()))
      .map((filename) => path.join(result.filePaths[0], filename));
  });
  ipcMain.handle('dialog:select-perspective-excel-file', async () => {
    const result = await dialog.showOpenDialog({ properties: ['openFile'], filters: getSpreadsheetImportFilters() });
    return result.canceled ? null : result.filePaths[0];
  });
  ipcMain.handle('shell:show-item-in-folder', (_event, filePath) => {
    shell.showItemInFolder(filePath);
    return true;
  });
}

module.exports = {
  getBackendArgs,
  getBackendWorkingDirectory,
  getDocumentImportFilters,
  getImageImportFilters,
  getSpreadsheetImportFilters,
  getPythonExecutable,
  startBackend,
  stopBackend
};
