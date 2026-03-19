const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('litigos', {
  db: {
    query: (sql, params) => ipcRenderer.invoke('db:query', sql, params),
    stats: () => ipcRenderer.invoke('db:stats'),
  },
  app: {
    info: () => ipcRenderer.invoke('app:info'),
  },
  case: {
    separationDays: () => ipcRenderer.invoke('case:separation-days'),
  },
  socket: {
    getToken: () => ipcRenderer.invoke('socket:token'),
  },
});
