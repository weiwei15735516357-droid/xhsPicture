const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('xhsApp', {
  getBackendBaseUrl: () => ipcRenderer.invoke('backend:base-url'),
  selectProjectDirectory: () => ipcRenderer.invoke('dialog:select-project-directory'),
  selectImportFiles: () => ipcRenderer.invoke('dialog:select-import-files'),
  selectImportFolder: () => ipcRenderer.invoke('dialog:select-import-folder'),
  selectDocumentFile: () => ipcRenderer.invoke('dialog:select-document-file')
});
