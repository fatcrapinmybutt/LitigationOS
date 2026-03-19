/**
 * Vitest global setup for LitigationOS Desktop tests.
 *
 * - Stubs Electron IPC (window.litigos)
 * - Seeds faker for deterministic output
 * - Provides afterEach cleanup
 */
import { afterEach, vi } from 'vitest';
import '@testing-library/jest-dom';

// Stub window.litigos (Electron preload bridge)
if (typeof window !== 'undefined') {
  window.litigos = {
    db: {
      query: vi.fn().mockResolvedValue({ ok: true, data: [] }),
      stats: vi.fn().mockResolvedValue({
        ok: true,
        data: { tables: 691, sizeBytes: 10_653_532_160, path: 'C:\\mock\\litigation_context.db' },
      }),
    },
    app: {
      info: vi.fn().mockResolvedValue({
        version: '1.0.0',
        platform: 'win32',
        arch: 'x64',
        electron: '29.0.0',
        node: '20.11.1',
      }),
    },
    case: {
      separationDays: vi.fn().mockResolvedValue({ days: 209, since: '2025-08-08' }),
    },
    socket: {
      getToken: vi.fn().mockResolvedValue('test-token-0000'),
    },
  };
}

// Clean up after each test
afterEach(() => {
  vi.restoreAllMocks();
});
