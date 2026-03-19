/**
 * Test helpers for LitigationOS Desktop.
 *
 * Mock WebSocket, mock Electron IPC, event replay utilities.
 */
import { vi } from 'vitest';
import { EVENTS, validateEventPayload } from '../../shared/events';

// ---------------------------------------------------------------------------
// Mock Socket.io Client
// ---------------------------------------------------------------------------

/**
 * Create a mock Socket.io socket for testing hooks and components.
 * @returns {{ socket: object, emitFromServer: Function, getHandlers: Function }}
 */
export function createMockSocket() {
  const handlers = new Map();

  const socket = {
    id: 'mock-socket-001',
    connected: true,
    on(event, handler) {
      if (!handlers.has(event)) handlers.set(event, []);
      handlers.get(event).push(handler);
    },
    off(event, handler) {
      if (!handlers.has(event)) return;
      if (handler) {
        handlers.set(event, handlers.get(event).filter((h) => h !== handler));
      } else {
        handlers.delete(event);
      }
    },
    emit: vi.fn(),
    disconnect: vi.fn(),
    connect: vi.fn(),
  };

  /**
   * Simulate a server-sent event (triggers registered handlers).
   * @param {string} event
   * @param {*} payload
   */
  function emitFromServer(event, payload) {
    const fns = handlers.get(event) || [];
    fns.forEach((fn) => fn(payload));
  }

  /** Get all registered handlers for an event */
  function getHandlers(event) {
    return handlers.get(event) || [];
  }

  /** Clear all handlers */
  function clearHandlers() {
    handlers.clear();
  }

  return { socket, emitFromServer, getHandlers, clearHandlers };
}

// ---------------------------------------------------------------------------
// Mock Electron IPC (window.litigos)
// ---------------------------------------------------------------------------

/**
 * Create a complete mock of the Electron IPC bridge.
 * @param {object} [overrides] - Override specific methods
 */
export function createMockIPC(overrides = {}) {
  return {
    db: {
      query: vi.fn().mockResolvedValue({ ok: true, data: [] }),
      stats: vi.fn().mockResolvedValue({
        ok: true,
        data: { tables: 691, sizeBytes: 10_653_532_160, path: 'C:\\mock\\db.db' },
      }),
      ...overrides.db,
    },
    app: {
      info: vi.fn().mockResolvedValue({
        version: '1.0.0', platform: 'win32', arch: 'x64',
        electron: '29.0.0', node: '20.11.1',
      }),
      ...overrides.app,
    },
    case: {
      separationDays: vi.fn().mockResolvedValue({ days: 209, since: '2025-08-08' }),
      ...overrides.case,
    },
    socket: {
      getToken: vi.fn().mockResolvedValue('test-token-0000'),
      ...overrides.socket,
    },
  };
}

// ---------------------------------------------------------------------------
// Event Replay
// ---------------------------------------------------------------------------

/**
 * Replay a sequence of events onto a mock socket with optional delays.
 * @param {Function} emitFn - The emitFromServer function from createMockSocket
 * @param {Array<{event: string, payload: object}>} events
 * @param {number} [delayMs=0] - Delay between events (0 = synchronous)
 */
export async function replayEvents(emitFn, events, delayMs = 0) {
  for (const { event, payload } of events) {
    emitFn(event, payload);
    if (delayMs > 0) {
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
}

// ---------------------------------------------------------------------------
// Event Validation Helper
// ---------------------------------------------------------------------------

/**
 * Assert that a payload passes the event schema validation.
 * Throws with details on failure.
 * @param {string} eventName
 * @param {*} payload
 */
export function assertValidPayload(eventName, payload) {
  const result = validateEventPayload(eventName, payload);
  if (!result.valid) {
    throw new Error(
      `Payload validation failed for ${eventName}:\n  ${result.errors.join('\n  ')}\n` +
      `Payload: ${JSON.stringify(payload, null, 2)}`
    );
  }
  return result;
}

/**
 * Validate an array of factory-produced payloads against their event schemas.
 * Returns { valid: number, invalid: number, errors: string[] }
 */
export function validateFactoryOutputs(entries) {
  const results = { valid: 0, invalid: 0, errors: [] };
  for (const { event, payload } of entries) {
    const r = validateEventPayload(event, payload);
    if (r.valid) {
      results.valid++;
    } else {
      results.invalid++;
      results.errors.push(`${event}: ${r.errors.join('; ')}`);
    }
  }
  return results;
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

export { EVENTS };
