const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('xhsApp', {
  getBackendBaseUrl: () => ipcRenderer.invoke('backend:base-url')
});
