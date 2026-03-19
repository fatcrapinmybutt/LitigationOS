/**
 * LitigationOS Socket.IO WebSocket Server
 *
 * Runs inside the Electron main process on port 3001.
 * Provides real-time events for pipeline progress, deadline alerts,
 * system health, evidence ingestion, and filing updates.
 *
 * Namespaces:
 *   /pipeline   – Pipeline execution events
 *   /deadlines  – Court deadline alerts
 *   /           – System health, notifications, evidence, filings
 */

const { createServer } = require('http');
const { Server } = require('socket.io');
const { EVENTS } = require('../shared/events');
const crypto = require('crypto');

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let httpServer = null;
let io = null;
let pipelineNs = null;
let deadlinesNs = null;
let healthInterval = null;
let authToken = null;
const startTime = Date.now();

/** Per-socket rate limiting: socketId → { count, resetAt } */
const rateLimits = new Map();
const RATE_LIMIT_MAX = 100;
const RATE_LIMIT_WINDOW_MS = 1000;

// ---------------------------------------------------------------------------
// Auth Token
// ---------------------------------------------------------------------------

/**
 * Return the shared secret token (generated once on first call).
 * Pass this to the renderer via Electron IPC so it can authenticate.
 */
function getAuthToken() {
  if (!authToken) {
    authToken = crypto.randomBytes(32).toString('hex');
  }
  return authToken;
}

// ---------------------------------------------------------------------------
// Rate Limiting
// ---------------------------------------------------------------------------

function checkRateLimit(socketId) {
  const now = Date.now();
  let bucket = rateLimits.get(socketId);
  if (!bucket || now >= bucket.resetAt) {
    bucket = { count: 0, resetAt: now + RATE_LIMIT_WINDOW_MS };
    rateLimits.set(socketId, bucket);
  }
  bucket.count++;
  return bucket.count <= RATE_LIMIT_MAX;
}

function clearRateLimit(socketId) {
  rateLimits.delete(socketId);
}

// ---------------------------------------------------------------------------
// Auth Middleware
// ---------------------------------------------------------------------------

function authMiddleware(socket, next) {
  const token = socket.handshake.auth?.token;
  if (token && token === getAuthToken()) {
    return next();
  }
  console.warn(`[WS] Auth rejected: ${socket.id} from ${socket.handshake.address}`);
  return next(new Error('Authentication failed: invalid token'));
}

// ---------------------------------------------------------------------------
// Rate Limit Middleware (applied per-event via socket.use)
// ---------------------------------------------------------------------------

function rateLimitMiddleware(socket, next) {
  if (!checkRateLimit(socket.id)) {
    console.warn(`[WS] Rate limit exceeded: ${socket.id}`);
    socket.emit(EVENTS.SYSTEM.ERROR, {
      source: 'socket-server',
      message: 'Rate limit exceeded (100 events/sec)',
      severity: 'warning',
    });
    return next(new Error('Rate limit exceeded'));
  }
  return next();
}

// ---------------------------------------------------------------------------
// Connection Handlers
// ---------------------------------------------------------------------------

function setupDefaultNamespace() {
  io.on('connection', (socket) => {
    console.log(`[WS] Client connected: ${socket.id} (default namespace)`);

    // Rate limit per-event
    socket.use((packet, next) => rateLimitMiddleware(socket, next));

    // Auto-join system room
    socket.join('system');

    // Allow clients to join/leave lane rooms
    socket.on('join:lane', (lane) => {
      const valid = /^[A-F]$/.test(lane);
      if (valid) {
        socket.join(`lane:${lane}`);
        console.log(`[WS] ${socket.id} joined lane:${lane}`);
      }
    });

    socket.on('leave:lane', (lane) => {
      socket.leave(`lane:${lane}`);
    });

    socket.on('disconnect', (reason) => {
      clearRateLimit(socket.id);
      console.log(`[WS] Client disconnected: ${socket.id} (${reason})`);
    });
  });
}

function setupPipelineNamespace() {
  pipelineNs = io.of('/pipeline');
  pipelineNs.use(authMiddleware);

  pipelineNs.on('connection', (socket) => {
    console.log(`[WS] Client connected: ${socket.id} (/pipeline)`);

    socket.use((packet, next) => rateLimitMiddleware(socket, next));

    // Auto-join active pipeline watchers room
    socket.join('pipeline:active');

    socket.on('disconnect', (reason) => {
      clearRateLimit(socket.id);
      console.log(`[WS] Pipeline client disconnected: ${socket.id} (${reason})`);
    });
  });
}

function setupDeadlinesNamespace() {
  deadlinesNs = io.of('/deadlines');
  deadlinesNs.use(authMiddleware);

  deadlinesNs.on('connection', (socket) => {
    console.log(`[WS] Client connected: ${socket.id} (/deadlines)`);

    socket.use((packet, next) => rateLimitMiddleware(socket, next));

    socket.on('disconnect', (reason) => {
      clearRateLimit(socket.id);
      console.log(`[WS] Deadlines client disconnected: ${socket.id} (${reason})`);
    });
  });
}

// ---------------------------------------------------------------------------
// Periodic Health Broadcast
// ---------------------------------------------------------------------------

function startHealthBroadcast() {
  healthInterval = setInterval(() => {
    if (!io) return;
    const mem = process.memoryUsage();
    const health = {
      db: true, // main.js opens DB on startup; overridable via emitSystemHealth
      pipeline: 'idle',
      engine: 'ready',
      memory: {
        heapUsedMB: Math.round(mem.heapUsed / 1024 / 1024),
        heapTotalMB: Math.round(mem.heapTotal / 1024 / 1024),
        rssMB: Math.round(mem.rss / 1024 / 1024),
      },
      uptime: Math.floor((Date.now() - startTime) / 1000),
    };
    io.to('system').emit(EVENTS.SYSTEM.HEALTH, health);
  }, 30_000);
}

// ---------------------------------------------------------------------------
// Server Lifecycle
// ---------------------------------------------------------------------------

/**
 * Create and start the Socket.IO server on the given port.
 * @param {number} [port=3001]
 * @returns {Promise<{ io: Server, httpServer: import('http').Server }>}
 */
function createSocketServer(port = 3001) {
  return new Promise((resolve, reject) => {
    httpServer = createServer();

    io = new Server(httpServer, {
      cors: {
        origin: ['http://localhost:3000', 'http://127.0.0.1:3000'],
        methods: ['GET', 'POST'],
        credentials: true,
      },
      pingInterval: 25000,
      pingTimeout: 20000,
      maxHttpBufferSize: 1e6, // 1 MB
    });

    // Auth middleware on default namespace
    io.use(authMiddleware);

    // Setup all namespaces
    setupDefaultNamespace();
    setupPipelineNamespace();
    setupDeadlinesNamespace();

    // Start periodic health
    startHealthBroadcast();

    httpServer.listen(port, '127.0.0.1', () => {
      console.log(`[WS] Socket.IO server listening on 127.0.0.1:${port}`);
      resolve({ io, httpServer });
    });

    httpServer.on('error', (err) => {
      console.error(`[WS] Server error: ${err.message}`);
      reject(err);
    });
  });
}

// ---------------------------------------------------------------------------
// Event Emitters — called by other main-process code
// ---------------------------------------------------------------------------

function emitPipelineProgress(phaseId, processed, total) {
  if (!pipelineNs) return;
  const percent = total > 0 ? Math.round((processed / total) * 100) : 0;
  pipelineNs.to('pipeline:active').emit(EVENTS.PIPELINE.PHASE_PROGRESS, {
    phaseId,
    processed,
    total,
    percent,
  });
}

function emitPipelinePhaseStart(phaseId, phaseName, totalItems) {
  if (!pipelineNs) return;
  pipelineNs.to('pipeline:active').emit(EVENTS.PIPELINE.PHASE_START, {
    phaseId,
    phaseName,
    totalItems,
  });
}

function emitPipelinePhaseComplete(phaseId, phaseName, duration, stats) {
  if (!pipelineNs) return;
  pipelineNs.to('pipeline:active').emit(EVENTS.PIPELINE.PHASE_COMPLETE, {
    phaseId,
    phaseName,
    duration,
    stats: stats || {},
  });
}

function emitDeadlineAlert(deadline) {
  if (!deadlinesNs) return;
  deadlinesNs.emit(EVENTS.DEADLINE.ALERT, deadline);
}

function emitSystemHealth(healthData) {
  if (!io) return;
  io.to('system').emit(EVENTS.SYSTEM.HEALTH, healthData);
}

function emitNotification(notification) {
  if (!io) return;
  io.to('system').emit(EVENTS.SYSTEM.NOTIFICATION, {
    ...notification,
    createdAt: notification.createdAt || new Date().toISOString(),
  });
}

function emitEvidenceIngested(docInfo) {
  if (!io) return;
  io.to('system').emit(EVENTS.EVIDENCE.INGESTED, docInfo);
}

function emitFilingUpdate(filingInfo) {
  if (!io) return;
  io.to('system').emit(EVENTS.FILING.STATUS_CHANGE, filingInfo);
}

// ---------------------------------------------------------------------------
// Clean Shutdown
// ---------------------------------------------------------------------------

/**
 * Gracefully close all Socket.IO connections and the HTTP server.
 * @returns {Promise<void>}
 */
function shutdown() {
  return new Promise((resolve) => {
    console.log('[WS] Shutting down socket server...');

    if (healthInterval) {
      clearInterval(healthInterval);
      healthInterval = null;
    }

    rateLimits.clear();

    if (io) {
      io.disconnectSockets(true);
      io.close(() => {
        console.log('[WS] Socket.IO closed');
        io = null;
        pipelineNs = null;
        deadlinesNs = null;
        if (httpServer) {
          httpServer.close(() => {
            console.log('[WS] HTTP server closed');
            httpServer = null;
            resolve();
          });
        } else {
          resolve();
        }
      });
    } else if (httpServer) {
      httpServer.close(() => {
        httpServer = null;
        resolve();
      });
    } else {
      resolve();
    }
  });
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

module.exports = {
  createSocketServer,
  emitPipelineProgress,
  emitPipelinePhaseStart,
  emitPipelinePhaseComplete,
  emitDeadlineAlert,
  emitSystemHealth,
  emitNotification,
  emitEvidenceIngested,
  emitFilingUpdate,
  shutdown,
  getAuthToken,
};
