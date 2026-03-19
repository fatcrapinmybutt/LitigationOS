/**
 * LitigationOS Test Data Factory Registry
 *
 * Central entry point for all test data generation.
 * Composable builders and composite scenario creators.
 */
import { sequence } from './sequence';
import { DeadlineFactory } from './DeadlineFactory';
import { PipelineFactory } from './PipelineFactory';
import { AgentFactory } from './AgentFactory';
import { EvidenceFactory } from './EvidenceFactory';
import { FilingFactory } from './FilingFactory';
import { NotificationFactory } from './NotificationFactory';
import { SystemHealthFactory } from './SystemHealthFactory';
import { ForumFactory, DbStatsFactory } from './ForumFactory';

// ---------------------------------------------------------------------------
// Factory Registry
// ---------------------------------------------------------------------------

const registry = new Map();

registry.set('deadline', (o) => DeadlineFactory.create(o));
registry.set('pipeline-start', (o) => PipelineFactory.phaseStart(o));
registry.set('pipeline-progress', (o) => PipelineFactory.phaseProgress(o));
registry.set('pipeline-complete', (o) => PipelineFactory.phaseComplete(o));
registry.set('pipeline-error', (o) => PipelineFactory.phaseError(o));
registry.set('agent', (o) => AgentFactory.create(o));
registry.set('evidence', (o) => EvidenceFactory.create(o));
registry.set('filing-status', (o) => FilingFactory.statusChange(o));
registry.set('filing-readiness', (o) => FilingFactory.readinessUpdate(o));
registry.set('notification', (o) => NotificationFactory.create(o));
registry.set('health', (o) => SystemHealthFactory.create(o));
registry.set('error', (o) => SystemHealthFactory.error(o));
registry.set('forum', (o) => ForumFactory.create(o?.lane, o));
registry.set('db-stats', (o) => DbStatsFactory.create(o));

/**
 * Create test data by registry name.
 * @param {string} name - Factory name
 * @param {object} [overrides] - Optional overrides
 */
function create(name, overrides) {
  const factory = registry.get(name);
  if (!factory) throw new Error(`Factory not found: "${name}". Available: ${[...registry.keys()].join(', ')}`);
  return factory(overrides);
}

// ---------------------------------------------------------------------------
// Composite Scenarios
// ---------------------------------------------------------------------------

/**
 * Full 16-phase pipeline run: start → progress → complete for each phase.
 */
function pipelineRunScenario() {
  const events = [];
  for (let i = 0; i < PipelineFactory.PHASES.length; i++) {
    const phase = PipelineFactory.PHASES[i];
    const totalItems = 1000 + i * 500;
    events.push({
      type: 'phase-start',
      payload: PipelineFactory.phaseStart({ phaseId: phase.id, phaseName: phase.name, totalItems }),
    });
    // 3 progress ticks per phase
    for (const pct of [25, 50, 75]) {
      const processed = Math.round(totalItems * pct / 100);
      events.push({
        type: 'phase-progress',
        payload: PipelineFactory.phaseProgress({
          phaseId: phase.id, processed, total: totalItems, percent: pct,
        }),
      });
    }
    events.push({
      type: 'phase-complete',
      payload: PipelineFactory.phaseComplete({
        phaseId: phase.id, phaseName: phase.name, duration: 5000 + i * 1000,
        stats: { itemsProcessed: totalItems, errors: 0, skipped: i },
      }),
    });
  }
  events.push({
    type: 'full-complete',
    payload: PipelineFactory.fullComplete({ phasesRun: 16, duration: 120000 }),
  });
  return events;
}

/**
 * Deadline urgency scenario — deadlines at various severities.
 */
function deadlineUrgencyScenario() {
  return {
    critical: [
      new DeadlineFactory().asCritical().with({ title: 'Disqualification Motion — McNeill' }).build(),
      new DeadlineFactory().asCritical().with({ title: '21-Day Claim of Appeal' }).build(),
    ],
    urgent: [
      new DeadlineFactory().asUrgent().with({ title: 'MSC Emergency Application' }).build(),
    ],
    warning: [
      new DeadlineFactory().asWarning().with({ title: 'COA Brief 366810' }).build(),
      new DeadlineFactory().asWarning().with({ title: 'JTC Formal Complaint' }).build(),
    ],
    info: [
      new DeadlineFactory().asInfo().with({ title: 'USDC §1983 Complaint' }).build(),
    ],
    all() {
      return [...this.critical, ...this.urgent, ...this.warning, ...this.info];
    },
  };
}

/**
 * Filing readiness scenario — multiple filings across forums.
 */
function filingReadinessScenario() {
  return FilingFactory.VEHICLES.map((v) => ({
    vehicleName: v.name,
    forum: v.forum,
    oldScore: 0,
    newScore: 50 + Math.floor(Math.random() * 50),
  }));
}

/**
 * Evidence ingestion batch scenario.
 */
function evidenceIngestionScenario(batchSize = 100) {
  const docs = EvidenceFactory.createMany(batchSize);
  const progress = [];
  for (let i = 0; i <= batchSize; i += Math.ceil(batchSize / 5)) {
    progress.push(EvidenceFactory.batchProgress({
      batchId: 'batch-scenario',
      processed: Math.min(i, batchSize),
      total: batchSize,
    }));
  }
  return { docs, progress };
}

/**
 * Agent fleet mixed-status scenario.
 */
function agentFleetScenario() {
  const fleet = AgentFactory.AGENT_IDS.map((agentId, i) => {
    if (i < 40) return AgentFactory.create({ agentId, status: 'success' });
    if (i < 50) return AgentFactory.create({ agentId, status: 'running' });
    if (i < 54) return new AgentFactory().with({ agentId }).asFatal().build();
    return new AgentFactory().with({ agentId }).asCrash().build();
  });
  return fleet;
}

/**
 * Full dashboard scenario — everything needed to render a complete dashboard.
 */
function dashboardScenario() {
  return {
    separationDays: Math.floor((Date.now() - new Date('2025-08-08').getTime()) / 86400000),
    dbStats: new DbStatsFactory().asProduction().build(),
    forums: ForumFactory.createAll(),
    deadlines: deadlineUrgencyScenario().all(),
    notifications: NotificationFactory.createMany(5),
    health: new SystemHealthFactory().asHealthy().build(),
    agents: agentFleetScenario().slice(0, 10),
  };
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

export const TestData = {
  // Direct factory access
  deadline: (o) => DeadlineFactory.create(o),
  pipeline: {
    phaseStart: (o) => PipelineFactory.phaseStart(o),
    phaseProgress: (o) => PipelineFactory.phaseProgress(o),
    phaseComplete: (o) => PipelineFactory.phaseComplete(o),
    phaseError: (o) => PipelineFactory.phaseError(o),
    fullComplete: (o) => PipelineFactory.fullComplete(o),
  },
  agent: (o) => AgentFactory.create(o),
  evidence: (o) => EvidenceFactory.create(o),
  filing: {
    statusChange: (o) => FilingFactory.statusChange(o),
    readinessUpdate: (o) => FilingFactory.readinessUpdate(o),
  },
  notification: (o) => NotificationFactory.create(o),
  health: (o) => SystemHealthFactory.create(o),
  error: (o) => SystemHealthFactory.error(o),
  forum: (lane, o) => ForumFactory.create(lane, o),
  dbStats: (o) => DbStatsFactory.create(o),

  // Composite scenarios
  scenarios: {
    pipelineRun: pipelineRunScenario,
    deadlineUrgency: deadlineUrgencyScenario,
    filingReadiness: filingReadinessScenario,
    evidenceIngestion: evidenceIngestionScenario,
    agentFleet: agentFleetScenario,
    dashboard: dashboardScenario,
  },

  // Registry
  create,

  // Sequence control
  resetSequences: () => sequence.reset(),
};

// Re-export individual factories for direct access
export {
  DeadlineFactory,
  PipelineFactory,
  AgentFactory,
  EvidenceFactory,
  FilingFactory,
  NotificationFactory,
  SystemHealthFactory,
  ForumFactory,
  DbStatsFactory,
  sequence,
};

export default TestData;
