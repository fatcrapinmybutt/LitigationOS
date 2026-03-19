/**
 * LitigationOS WebSocket Event Definitions
 *
 * Shared event types used across server and client for the litigation
 * intelligence system: 16-phase pipeline, 56-agent fleet, deadline
 * tracking, evidence ingestion, and filing management.
 *
 * Namespaces:
 *   /pipeline   – Pipeline execution and agent status
 *   /deadlines  – Court deadline alerts and updates
 *   /           – System health, evidence, filing, notifications
 *   (presence)  – User presence tracking
 */

// ---------------------------------------------------------------------------
// Event Constants
// ---------------------------------------------------------------------------

const EVENTS = {
  // --- Pipeline Namespace (/pipeline) ---
  PIPELINE: {
    PHASE_START:    'pipeline:phase-start',
    PHASE_PROGRESS: 'pipeline:phase-progress',
    PHASE_COMPLETE: 'pipeline:phase-complete',
    PHASE_ERROR:    'pipeline:phase-error',
    AGENT_STATUS:   'pipeline:agent-status',
    FULL_COMPLETE:  'pipeline:full-complete',
  },

  // --- Deadlines Namespace (/deadlines) ---
  DEADLINE: {
    ALERT:       'deadline:alert',
    UPDATED:     'deadline:updated',
    APPROACHING: 'deadline:approaching',
  },

  // --- System Namespace (default /) ---
  SYSTEM: {
    HEALTH:       'system:health',
    ERROR:        'system:error',
    NOTIFICATION: 'system:notification',
  },

  // --- Evidence (default /) ---
  EVIDENCE: {
    INGESTED:       'evidence:ingested',
    BATCH_PROGRESS: 'evidence:batch-progress',
  },

  // --- Filing (default /) ---
  FILING: {
    READINESS_UPDATE: 'filing:readiness-update',
    STATUS_CHANGE:    'filing:status-change',
  },

  // --- Presence ---
  PRESENCE: {
    UPDATE: 'presence:update',
    LIST:   'presence:list',
  },
};

// ---------------------------------------------------------------------------
// Payload Schemas – lightweight required-field validation
// ---------------------------------------------------------------------------

const PAYLOAD_SCHEMAS = {
  [EVENTS.PIPELINE.PHASE_START]:    ['phaseId', 'phaseName', 'totalItems'],
  [EVENTS.PIPELINE.PHASE_PROGRESS]: ['phaseId', 'processed', 'total', 'percent'],
  [EVENTS.PIPELINE.PHASE_COMPLETE]: ['phaseId', 'phaseName', 'duration', 'stats'],
  [EVENTS.PIPELINE.PHASE_ERROR]:    ['phaseId', 'error', 'recoverable'],
  [EVENTS.PIPELINE.AGENT_STATUS]:   ['agentId', 'status', 'stats'],
  [EVENTS.PIPELINE.FULL_COMPLETE]:  ['duration', 'phasesRun', 'summary'],

  [EVENTS.DEADLINE.ALERT]:       ['id', 'title', 'dueDate', 'daysRemaining', 'severity'],
  [EVENTS.DEADLINE.UPDATED]:     ['id', 'changes'],
  [EVENTS.DEADLINE.APPROACHING]: ['deadlines'],

  [EVENTS.SYSTEM.HEALTH]:       ['db', 'pipeline', 'engine', 'memory', 'uptime'],
  [EVENTS.SYSTEM.ERROR]:        ['source', 'message', 'severity'],
  [EVENTS.SYSTEM.NOTIFICATION]: ['id', 'type', 'title', 'message', 'createdAt'],

  [EVENTS.EVIDENCE.INGESTED]:       ['documentId', 'filename', 'type', 'quotesExtracted'],
  [EVENTS.EVIDENCE.BATCH_PROGRESS]: ['batchId', 'processed', 'total', 'percent'],

  [EVENTS.FILING.READINESS_UPDATE]: ['vehicleName', 'oldScore', 'newScore', 'forum'],
  [EVENTS.FILING.STATUS_CHANGE]:    ['filingId', 'oldStatus', 'newStatus'],

  [EVENTS.PRESENCE.UPDATE]: ['userId', 'status'],
  [EVENTS.PRESENCE.LIST]:   null, // payload is an array, validated separately
};

// Allowed enum values for fields that have constrained sets
const ENUM_VALUES = {
  'pipeline:agent-status.status': ['running', 'success', 'fatal', 'crash'],
  'deadline:alert.severity':      ['critical', 'urgent', 'warning', 'info'],
  'presence:update.status':       ['online', 'away', 'offline'],
};

// ---------------------------------------------------------------------------
// Validation Helper
// ---------------------------------------------------------------------------

/**
 * Validate an event payload against its schema.
 *
 * @param {string} eventName  – One of the EVENTS.* string constants.
 * @param {*}      payload    – The payload object (or array for presence:list).
 * @returns {{ valid: boolean, errors: string[] }}
 */
function validateEventPayload(eventName, payload) {
  const errors = [];

  // Unknown event
  if (!(eventName in PAYLOAD_SCHEMAS)) {
    return { valid: false, errors: [`Unknown event: ${eventName}`] };
  }

  const schema = PAYLOAD_SCHEMAS[eventName];

  // Array-typed payloads (presence:list)
  if (schema === null) {
    if (!Array.isArray(payload)) {
      errors.push(`Expected array payload for ${eventName}`);
    }
    return { valid: errors.length === 0, errors };
  }

  // Object-typed payloads
  if (payload === null || typeof payload !== 'object' || Array.isArray(payload)) {
    return { valid: false, errors: [`Payload must be a non-null object for ${eventName}`] };
  }

  // Required fields
  for (const field of schema) {
    if (!(field in payload)) {
      errors.push(`Missing required field "${field}" for ${eventName}`);
    }
  }

  // Enum constraints
  for (const [key, allowed] of Object.entries(ENUM_VALUES)) {
    const [evt, field] = key.split('.');
    if (evt === eventName && field in payload) {
      if (!allowed.includes(payload[field])) {
        errors.push(
          `Invalid value "${payload[field]}" for ${field} in ${eventName}. ` +
          `Allowed: ${allowed.join(', ')}`
        );
      }
    }
  }

  return { valid: errors.length === 0, errors };
}

// ---------------------------------------------------------------------------
// Namespace Mapping – maps each event to its Socket.IO namespace
// ---------------------------------------------------------------------------

const NAMESPACE_MAP = {
  [EVENTS.PIPELINE.PHASE_START]:    '/pipeline',
  [EVENTS.PIPELINE.PHASE_PROGRESS]: '/pipeline',
  [EVENTS.PIPELINE.PHASE_COMPLETE]: '/pipeline',
  [EVENTS.PIPELINE.PHASE_ERROR]:    '/pipeline',
  [EVENTS.PIPELINE.AGENT_STATUS]:   '/pipeline',
  [EVENTS.PIPELINE.FULL_COMPLETE]:  '/pipeline',

  [EVENTS.DEADLINE.ALERT]:       '/deadlines',
  [EVENTS.DEADLINE.UPDATED]:     '/deadlines',
  [EVENTS.DEADLINE.APPROACHING]: '/deadlines',

  [EVENTS.SYSTEM.HEALTH]:       '/',
  [EVENTS.SYSTEM.ERROR]:        '/',
  [EVENTS.SYSTEM.NOTIFICATION]: '/',

  [EVENTS.EVIDENCE.INGESTED]:       '/',
  [EVENTS.EVIDENCE.BATCH_PROGRESS]: '/',

  [EVENTS.FILING.READINESS_UPDATE]: '/',
  [EVENTS.FILING.STATUS_CHANGE]:    '/',

  [EVENTS.PRESENCE.UPDATE]: '/',
  [EVENTS.PRESENCE.LIST]:   '/',
};

/**
 * Return the Socket.IO namespace for a given event name.
 * @param {string} eventName
 * @returns {string|undefined}
 */
function getNamespace(eventName) {
  return NAMESPACE_MAP[eventName];
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

module.exports = {
  EVENTS,
  PAYLOAD_SCHEMAS,
  ENUM_VALUES,
  NAMESPACE_MAP,
  validateEventPayload,
  getNamespace,
};
