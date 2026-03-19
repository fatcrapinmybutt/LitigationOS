const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const Database = require('better-sqlite3');
const { createSocketServer, shutdown: shutdownSocket, getAuthToken, emitSystemHealth } = require('./socket-server');

let mainWindow;
let db;

const DB_PATH = path.join(process.env.USERPROFILE || '', 'LitigationOS', 'litigation_context.db');

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'LitigationOS',
    backgroundColor: '#0a0e27',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#0a0e27',
      symbolColor: '#e2e8f0',
      height: 36,
    },
    show: false,
  });

  const isDev = !app.isPackaged;
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'out', 'index.html'));
  }

  mainWindow.once('ready-to-show', () => mainWindow.show());
  mainWindow.on('closed', () => { mainWindow = null; });
}

function initDB() {
  try {
    db = new Database(DB_PATH, { readonly: true, fileMustExist: true });
    db.pragma('journal_mode = WAL');
    db.pragma('cache_size = -64000'); // 64MB cache
    console.log(`[DB] Connected: ${DB_PATH}`);
    return true;
  } catch (err) {
    console.error(`[DB] Failed to connect: ${err.message}`);
    return false;
  }
}

// IPC Handlers
ipcMain.handle('db:query', async (event, sql, params = []) => {
  try {
    if (!db) throw new Error('Database not connected');
    const stmt = db.prepare(sql);
    return { ok: true, data: stmt.all(...params) };
  } catch (err) {
    return { ok: false, error: err.message };
  }
});

ipcMain.handle('db:stats', async () => {
  try {
    if (!db) throw new Error('Database not connected');
    const tables = db.prepare("SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table'").get();
    const size = require('fs').statSync(DB_PATH).size;
    return { ok: true, data: { tables: tables.cnt, sizeBytes: size, path: DB_PATH } };
  } catch (err) {
    return { ok: false, error: err.message };
  }
});

ipcMain.handle('app:info', async () => ({
  version: app.getVersion(),
  platform: process.platform,
  arch: process.arch,
  electron: process.versions.electron,
  node: process.versions.node,
}));

ipcMain.handle('socket:token', async () => getAuthToken());

ipcMain.handle('case:separation-days', async () => {
  const start = new Date('2025-08-08');
  const now = new Date();
  const days = Math.floor((now - start) / (1000 * 60 * 60 * 24));
  return { days, since: '2025-08-08' };
});

app.whenReady().then(() => {
  initDB();
  createWindow();
  // Start WebSocket server
  createSocketServer();
  console.log('[WS] Socket.io server started on port 3001');
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (db) db.close();
  shutdownSocket();
  if (process.platform !== 'darwin') app.quit();
});
