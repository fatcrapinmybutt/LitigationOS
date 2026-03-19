/**
 * LitigationOS Test Data Factory — Comprehensive Test Suite
 *
 * Validates that all factories produce data conforming to the
 * WebSocket event payload schemas defined in shared/events.js
 */
import { describe, it, expect, beforeEach } from 'vitest';
import {
  TestData,
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
} from '../factories/index';
import { PipelineRunBuilder } from '../builders/PipelineRunBuilder';
import { FilingScenarioBuilder } from '../builders/FilingScenarioBuilder';
import {
  assertValidPayload,
  validateFactoryOutputs,
  createMockSocket,
  createMockIPC,
  replayEvents,
} from '../helpers/test-helpers';
import { EVENTS, validateEventPayload } from '../../shared/events';

// Reset sequences between tests for determinism
beforeEach(() => {
  sequence.reset();
});

// -------------------------------------------------------------------------
// Sequence Generator
// -------------------------------------------------------------------------

describe('Sequence', () => {
  it('increments deterministically', () => {
    expect(sequence.next('test')).toBe(1);
    expect(sequence.next('test')).toBe(2);
    expect(sequence.next('test')).toBe(3);
  });

  it('maintains separate counters per key', () => {
    expect(sequence.next('a')).toBe(1);
    expect(sequence.next('b')).toBe(1);
    expect(sequence.next('a')).toBe(2);
    expect(sequence.next('b')).toBe(2);
  });

  it('resets a single key', () => {
    sequence.next('x');
    sequence.next('y');
    sequence.reset('x');
    expect(sequence.next('x')).toBe(1);
    expect(sequence.next('y')).toBe(2);
  });

  it('resets all keys', () => {
    sequence.next('a');
    sequence.next('b');
    sequence.reset();
    expect(sequence.next('a')).toBe(1);
    expect(sequence.next('b')).toBe(1);
  });
});

// -------------------------------------------------------------------------
// DeadlineFactory
// -------------------------------------------------------------------------

describe('DeadlineFactory', () => {
  it('creates a valid deadline', () => {
    const d = DeadlineFactory.create();
    expect(d).toHaveProperty('id');
    expect(d).toHaveProperty('title');
    expect(d).toHaveProperty('dueDate');
    expect(d).toHaveProperty('daysRemaining');
    expect(d).toHaveProperty('severity');
    assertValidPayload(EVENTS.DEADLINE.ALERT, d);
  });

  it('creates critical deadlines (≤7 days)', () => {
    const d = new DeadlineFactory().asCritical().build();
    expect(d.severity).toBe('critical');
    expect(d.daysRemaining).toBeLessThanOrEqual(7);
    assertValidPayload(EVENTS.DEADLINE.ALERT, d);
  });

  it('creates urgent deadlines (8-14 days)', () => {
    const d = new DeadlineFactory().asUrgent().build();
    expect(d.severity).toBe('urgent');
    expect(d.daysRemaining).toBeGreaterThanOrEqual(8);
    expect(d.daysRemaining).toBeLessThanOrEqual(14);
  });

  it('creates past-due deadlines', () => {
    const d = new DeadlineFactory().asPastDue().build();
    expect(d.daysRemaining).toBeLessThan(0);
    expect(d.severity).toBe('critical');
  });

  it('creates appeal deadline trait', () => {
    const d = new DeadlineFactory().asAppealDeadline().build();
    expect(d.title).toContain('MCR 7.204');
    expect(d.severity).toBe('critical');
  });

  it('accepts overrides', () => {
    const d = DeadlineFactory.create({ title: 'Custom Title', daysRemaining: 42 });
    expect(d.title).toBe('Custom Title');
    expect(d.daysRemaining).toBe(42);
  });

  it('creates many deadlines', () => {
    const list = DeadlineFactory.createMany(10);
    expect(list).toHaveLength(10);
    list.forEach((d) => assertValidPayload(EVENTS.DEADLINE.ALERT, d));
  });

  it('generates deterministic IDs', () => {
    const d1 = DeadlineFactory.create();
    const d2 = DeadlineFactory.create();
    expect(d1.id).toBe('deadline-1');
    expect(d2.id).toBe('deadline-2');
  });
});

// -------------------------------------------------------------------------
// PipelineFactory
// -------------------------------------------------------------------------

describe('PipelineFactory', () => {
  it('creates valid phase-start payload', () => {
    const p = PipelineFactory.phaseStart();
    assertValidPayload(EVENTS.PIPELINE.PHASE_START, p);
    expect(p).toHaveProperty('phaseId');
    expect(p).toHaveProperty('phaseName');
    expect(p).toHaveProperty('totalItems');
  });

  it('creates valid phase-progress payload', () => {
    const p = PipelineFactory.phaseProgress();
    assertValidPayload(EVENTS.PIPELINE.PHASE_PROGRESS, p);
    expect(p.percent).toBeGreaterThanOrEqual(0);
    expect(p.percent).toBeLessThanOrEqual(100);
  });

  it('creates valid phase-complete payload', () => {
    const p = PipelineFactory.phaseComplete();
    assertValidPayload(EVENTS.PIPELINE.PHASE_COMPLETE, p);
    expect(p.stats).toBeDefined();
  });

  it('creates valid phase-error payload', () => {
    const p = PipelineFactory.phaseError();
    assertValidPayload(EVENTS.PIPELINE.PHASE_ERROR, p);
    expect(typeof p.recoverable).toBe('boolean');
  });

  it('creates valid full-complete payload', () => {
    const p = PipelineFactory.fullComplete();
    assertValidPayload(EVENTS.PIPELINE.FULL_COMPLETE, p);
    expect(p.phasesRun).toBeGreaterThanOrEqual(1);
  });

  it('targets specific phase by index', () => {
    const p = new PipelineFactory().forPhase(0).buildPhaseStart();
    expect(p.phaseId).toBe('0');
    expect(p.phaseName).toBe('Safety Snapshot');
  });

  it('exposes all 16 phase definitions', () => {
    expect(PipelineFactory.PHASES).toHaveLength(16);
  });
});

// -------------------------------------------------------------------------
// AgentFactory
// -------------------------------------------------------------------------

describe('AgentFactory', () => {
  it('creates a valid agent status', () => {
    const a = AgentFactory.create();
    assertValidPayload(EVENTS.PIPELINE.AGENT_STATUS, a);
    expect(AgentFactory.STATUS_VALUES).toContain(a.status);
  });

  it('creates running agent', () => {
    const a = new AgentFactory().asRunning().build();
    expect(a.status).toBe('running');
  });

  it('creates fatal agent with error details', () => {
    const a = new AgentFactory().asFatal().build();
    expect(a.status).toBe('fatal');
    expect(a.stats.lastError).toBeDefined();
    expect(a.stats.errorStack).toBeDefined();
  });

  it('creates crash agent', () => {
    const a = new AgentFactory().asCrash().build();
    expect(a.status).toBe('crash');
  });

  it('creates infrastructure agent (A-tier)', () => {
    const a = new AgentFactory().asInfrastructure().build();
    expect(a.agentId).toMatch(/^A\d+$/);
  });

  it('creates intelligence agent (J/K/L-tier)', () => {
    const a = new AgentFactory().asIntelligence().build();
    expect(a.agentId).toMatch(/^[JKL]\d+$/);
  });

  it('creates convergence agent (F-tier)', () => {
    const a = new AgentFactory().asConvergence().build();
    expect(a.agentId).toMatch(/^F\d+$/);
  });

  it('creates full 56-agent fleet', () => {
    const fleet = AgentFactory.createFleet();
    expect(fleet).toHaveLength(AgentFactory.AGENT_IDS.length);
    fleet.forEach((a) => expect(a.status).toBe('success'));
  });
});

// -------------------------------------------------------------------------
// EvidenceFactory
// -------------------------------------------------------------------------

describe('EvidenceFactory', () => {
  it('creates valid evidence payload', () => {
    const e = EvidenceFactory.create();
    assertValidPayload(EVENTS.EVIDENCE.INGESTED, e);
    expect(e).toHaveProperty('documentId');
    expect(e).toHaveProperty('filename');
    expect(e).toHaveProperty('type');
    expect(e).toHaveProperty('quotesExtracted');
  });

  it('creates high-value evidence', () => {
    const e = new EvidenceFactory().asHighValue().build();
    expect(e.quotesExtracted).toBeGreaterThanOrEqual(50);
  });

  it('creates court order', () => {
    const e = new EvidenceFactory().asCourtOrder().build();
    expect(e.type).toBe('pdf');
    expect(e.filename).toContain('Court_Order');
  });

  it('creates Watson-sourced evidence', () => {
    const e = new EvidenceFactory().fromWatson().build();
    expect(e.filename).toContain('Watson');
    expect(e.lane).toBe('A');
  });

  it('creates judicial violation evidence', () => {
    const e = new EvidenceFactory().asJudicialViolation().build();
    expect(e.filename).toContain('McNeill_Violation');
    expect(e.lane).toBe('E');
  });

  it('creates valid batch progress', () => {
    const bp = EvidenceFactory.batchProgress();
    assertValidPayload(EVENTS.EVIDENCE.BATCH_PROGRESS, bp);
    expect(bp.percent).toBeGreaterThanOrEqual(0);
    expect(bp.percent).toBeLessThanOrEqual(100);
  });

  it('creates many evidence docs', () => {
    const list = EvidenceFactory.createMany(20);
    expect(list).toHaveLength(20);
    list.forEach((e) => assertValidPayload(EVENTS.EVIDENCE.INGESTED, e));
  });
});

// -------------------------------------------------------------------------
// FilingFactory
// -------------------------------------------------------------------------

describe('FilingFactory', () => {
  it('creates valid status change', () => {
    const f = FilingFactory.statusChange();
    assertValidPayload(EVENTS.FILING.STATUS_CHANGE, f);
    expect(f).toHaveProperty('filingId');
    expect(f).toHaveProperty('oldStatus');
    expect(f).toHaveProperty('newStatus');
  });

  it('creates valid readiness update', () => {
    const f = FilingFactory.readinessUpdate();
    assertValidPayload(EVENTS.FILING.READINESS_UPDATE, f);
    expect(f.newScore).toBeGreaterThanOrEqual(f.oldScore);
  });

  it('creates court-ready filing', () => {
    const f = new FilingFactory().asCourtReady().buildReadinessUpdate();
    expect(f.newScore).toBeGreaterThanOrEqual(85);
  });

  it('creates draft filing', () => {
    const f = new FilingFactory().asDraft().buildStatusChange();
    expect(f.newStatus).toBe('drafting');
  });

  it('creates filed status', () => {
    const f = new FilingFactory().asFiled().buildStatusChange();
    expect(f.oldStatus).toBe('final');
    expect(f.newStatus).toBe('filed');
  });

  it('exposes all 12 vehicles', () => {
    expect(FilingFactory.VEHICLES).toHaveLength(12);
  });
});

// -------------------------------------------------------------------------
// NotificationFactory
// -------------------------------------------------------------------------

describe('NotificationFactory', () => {
  it('creates valid notification', () => {
    const n = NotificationFactory.create();
    assertValidPayload(EVENTS.SYSTEM.NOTIFICATION, n);
    expect(n).toHaveProperty('id');
    expect(n).toHaveProperty('type');
    expect(n).toHaveProperty('title');
    expect(n).toHaveProperty('message');
    expect(n).toHaveProperty('createdAt');
  });

  it('creates deadline alert notification', () => {
    const n = new NotificationFactory().asDeadlineAlert().build();
    expect(n.type).toBe('deadline');
    expect(n.title).toBe('Deadline Approaching');
  });

  it('creates error notification', () => {
    const n = new NotificationFactory().asError().build();
    expect(n.type).toBe('error');
  });

  it('creates read notification', () => {
    const n = new NotificationFactory().asRead().build();
    expect(n.read).toBe(true);
  });

  it('creates many notifications', () => {
    const list = NotificationFactory.createMany(50);
    expect(list).toHaveLength(50);
    list.forEach((n) => assertValidPayload(EVENTS.SYSTEM.NOTIFICATION, n));
  });
});

// -------------------------------------------------------------------------
// SystemHealthFactory
// -------------------------------------------------------------------------

describe('SystemHealthFactory', () => {
  it('creates valid health payload', () => {
    const h = SystemHealthFactory.create();
    assertValidPayload(EVENTS.SYSTEM.HEALTH, h);
    expect(h).toHaveProperty('db');
    expect(h).toHaveProperty('pipeline');
    expect(h).toHaveProperty('engine');
    expect(h).toHaveProperty('memory');
    expect(h).toHaveProperty('uptime');
  });

  it('creates healthy system', () => {
    const h = new SystemHealthFactory().asHealthy().build();
    expect(h.db).toBe(true);
    expect(h.pipeline).toBe('idle');
    expect(h.engine).toBe('ready');
  });

  it('creates degraded system', () => {
    const h = new SystemHealthFactory().asDegraded().build();
    expect(h.db).toBe(false);
    expect(h.pipeline).toBe('error');
  });

  it('creates high memory scenario', () => {
    const h = new SystemHealthFactory().asHighMemory().build();
    expect(h.memory.heapUsedMB).toBeGreaterThanOrEqual(900);
  });

  it('creates valid error payload', () => {
    const e = SystemHealthFactory.error();
    assertValidPayload(EVENTS.SYSTEM.ERROR, e);
    expect(e).toHaveProperty('source');
    expect(e).toHaveProperty('message');
    expect(e).toHaveProperty('severity');
  });
});

// -------------------------------------------------------------------------
// ForumFactory & DbStatsFactory
// -------------------------------------------------------------------------

describe('ForumFactory', () => {
  it('creates a forum card', () => {
    const f = ForumFactory.create('A');
    expect(f.lane).toBe('A');
    expect(f.label).toBe('Michigan Supreme Court');
    expect(f.actions).toBeGreaterThanOrEqual(4);
    expect(f.score).toBeGreaterThanOrEqual(80);
  });

  it('creates all 6 forums', () => {
    const all = ForumFactory.createAll();
    expect(all).toHaveLength(6);
    expect(all.map((f) => f.lane)).toEqual(['A', 'B', 'C', 'D', 'E', 'F']);
  });
});

describe('DbStatsFactory', () => {
  it('creates production-size stats', () => {
    const s = new DbStatsFactory().asProduction().build();
    expect(s.tables).toBe(691);
    expect(s.sizeBytes).toBe(10_653_532_160);
  });

  it('creates empty stats', () => {
    const s = new DbStatsFactory().asEmpty().build();
    expect(s.tables).toBe(0);
    expect(s.sizeBytes).toBe(0);
  });
});

// -------------------------------------------------------------------------
// TestData Registry
// -------------------------------------------------------------------------

describe('TestData (Registry)', () => {
  it('creates data by name', () => {
    expect(TestData.create('deadline')).toHaveProperty('id');
    expect(TestData.create('agent')).toHaveProperty('agentId');
    expect(TestData.create('evidence')).toHaveProperty('documentId');
    expect(TestData.create('notification')).toHaveProperty('title');
    expect(TestData.create('health')).toHaveProperty('db');
    expect(TestData.create('error')).toHaveProperty('source');
  });

  it('throws on unknown factory', () => {
    expect(() => TestData.create('nonexistent')).toThrow('Factory not found');
  });

  it('passes overrides through', () => {
    const d = TestData.create('deadline', { title: 'Override' });
    expect(d.title).toBe('Override');
  });

  it('provides shorthand accessors', () => {
    expect(TestData.deadline()).toHaveProperty('id');
    expect(TestData.agent()).toHaveProperty('agentId');
    expect(TestData.evidence()).toHaveProperty('documentId');
    expect(TestData.notification()).toHaveProperty('title');
    expect(TestData.health()).toHaveProperty('db');
    expect(TestData.error()).toHaveProperty('source');
    expect(TestData.pipeline.phaseStart()).toHaveProperty('phaseId');
    expect(TestData.filing.statusChange()).toHaveProperty('filingId');
    expect(TestData.filing.readinessUpdate()).toHaveProperty('vehicleName');
  });
});

// -------------------------------------------------------------------------
// Composite Scenarios
// -------------------------------------------------------------------------

describe('Scenarios', () => {
  it('pipelineRun produces a full event sequence', () => {
    const events = TestData.scenarios.pipelineRun();
    expect(events.length).toBeGreaterThan(60); // 16 phases × (1 start + 3 progress + 1 complete) + 1 final = 81
    expect(events[0].type).toBe('phase-start');
    expect(events[events.length - 1].type).toBe('full-complete');
  });

  it('deadlineUrgency covers all severity levels', () => {
    const s = TestData.scenarios.deadlineUrgency();
    expect(s.critical.length).toBeGreaterThan(0);
    expect(s.urgent.length).toBeGreaterThan(0);
    expect(s.warning.length).toBeGreaterThan(0);
    expect(s.info.length).toBeGreaterThan(0);
    s.all().forEach((d) => assertValidPayload(EVENTS.DEADLINE.ALERT, d));
  });

  it('filingReadiness covers all vehicles', () => {
    const filings = TestData.scenarios.filingReadiness();
    expect(filings).toHaveLength(FilingFactory.VEHICLES.length);
    filings.forEach((f) => assertValidPayload(EVENTS.FILING.READINESS_UPDATE, f));
  });

  it('evidenceIngestion produces docs and progress', () => {
    const { docs, progress } = TestData.scenarios.evidenceIngestion(50);
    expect(docs).toHaveLength(50);
    expect(progress.length).toBeGreaterThan(1);
    docs.forEach((d) => assertValidPayload(EVENTS.EVIDENCE.INGESTED, d));
    progress.forEach((p) => assertValidPayload(EVENTS.EVIDENCE.BATCH_PROGRESS, p));
  });

  it('agentFleet produces mixed statuses', () => {
    const fleet = TestData.scenarios.agentFleet();
    const statuses = new Set(fleet.map((a) => a.status));
    expect(statuses.size).toBeGreaterThanOrEqual(2); // success + running/fatal/crash
  });

  it('dashboard produces all dashboard data', () => {
    const d = TestData.scenarios.dashboard();
    expect(d.separationDays).toBeGreaterThan(0);
    expect(d.dbStats.tables).toBe(691);
    expect(d.forums).toHaveLength(6);
    expect(d.deadlines.length).toBeGreaterThan(0);
    expect(d.notifications.length).toBeGreaterThan(0);
    expect(d.health.db).toBe(true);
  });
});

// -------------------------------------------------------------------------
// Builders
// -------------------------------------------------------------------------

describe('PipelineRunBuilder', () => {
  it('builds a full pipeline run', () => {
    const events = new PipelineRunBuilder().build();
    expect(events.length).toBeGreaterThan(80);
    expect(events[events.length - 1].type).toBe('full-complete');
  });

  it('builds with specific phases', () => {
    const events = new PipelineRunBuilder().withPhases(['0', '1', '2']).build();
    const starts = events.filter((e) => e.type === 'phase-start');
    expect(starts).toHaveLength(3);
  });

  it('injects errors', () => {
    const events = new PipelineRunBuilder()
      .withPhases(['0', '1'])
      .withErrorAt('1', true)
      .build();
    const errors = events.filter((e) => e.type === 'phase-error');
    expect(errors).toHaveLength(1);
    expect(errors[0].payload.recoverable).toBe(true);
  });

  it('stops on fatal error', () => {
    const events = new PipelineRunBuilder()
      .withPhases(['0', '1', '2'])
      .withErrorAt('1', false)
      .build();
    // Should not have phase-start for phase 2
    const starts = events.filter((e) => e.type === 'phase-start');
    expect(starts).toHaveLength(2); // phases 0 and 1 only
  });

  it('includes agent fleet', () => {
    const events = new PipelineRunBuilder().withAgents(5).build();
    const agentEvents = events.filter((e) => e.type === 'agent-status');
    expect(agentEvents).toHaveLength(5);
  });

  it('skips final complete', () => {
    const events = new PipelineRunBuilder().withoutFinalComplete().build();
    expect(events[events.length - 1].type).not.toBe('full-complete');
  });
});

describe('FilingScenarioBuilder', () => {
  it('builds MSC emergency scenario', () => {
    const s = new FilingScenarioBuilder().asMscEmergency().build();
    expect(s.forum).toBe('MSC');
    expect(s.targetScore).toBe(95);
    expect(s.evidence).toHaveLength(20);
    expect(s.deadline).not.toBeNull();
    expect(s.deadline.daysRemaining).toBe(3);
    expect(s.notifications.length).toBeGreaterThan(0);
    expect(s.readinessHistory.length).toBeGreaterThan(0);
  });

  it('builds COA brief scenario', () => {
    const s = new FilingScenarioBuilder().asCoaBrief().build();
    expect(s.forum).toBe('COA');
    expect(s.targetScore).toBe(75);
  });

  it('builds JTC complaint scenario', () => {
    const s = new FilingScenarioBuilder().asJtcComplaint().build();
    expect(s.forum).toBe('JTC');
    expect(s.evidence).toHaveLength(25);
  });

  it('builds without deadline', () => {
    const s = new FilingScenarioBuilder().withoutDeadline().build();
    expect(s.deadline).toBeNull();
  });

  it('builds without notifications', () => {
    const s = new FilingScenarioBuilder().withoutNotifications().build();
    expect(s.notifications).toHaveLength(0);
  });

  it('readiness history shows progressive improvement', () => {
    const s = new FilingScenarioBuilder().withTargetScore(90).build();
    for (let i = 1; i < s.readinessHistory.length; i++) {
      expect(s.readinessHistory[i].oldScore).toBeLessThanOrEqual(s.readinessHistory[i].newScore);
    }
  });
});

// -------------------------------------------------------------------------
// Test Helpers
// -------------------------------------------------------------------------

describe('Test Helpers', () => {
  describe('createMockSocket', () => {
    it('captures emitted events', () => {
      const { socket } = createMockSocket();
      socket.emit('test', { data: 1 });
      expect(socket.emit).toHaveBeenCalledWith('test', { data: 1 });
    });

    it('delivers server events to handlers', () => {
      const { socket, emitFromServer } = createMockSocket();
      const handler = vi.fn();
      socket.on('my-event', handler);
      emitFromServer('my-event', { value: 42 });
      expect(handler).toHaveBeenCalledWith({ value: 42 });
    });

    it('removes handlers with off()', () => {
      const { socket, emitFromServer } = createMockSocket();
      const handler = vi.fn();
      socket.on('x', handler);
      socket.off('x', handler);
      emitFromServer('x', {});
      expect(handler).not.toHaveBeenCalled();
    });
  });

  describe('createMockIPC', () => {
    it('provides default mock responses', async () => {
      const ipc = createMockIPC();
      const stats = await ipc.db.stats();
      expect(stats.ok).toBe(true);
      expect(stats.data.tables).toBe(691);
    });

    it('accepts overrides', async () => {
      const ipc = createMockIPC({
        db: { query: vi.fn().mockResolvedValue({ ok: true, data: [{ count: 42 }] }) },
      });
      const result = await ipc.db.query();
      expect(result.data[0].count).toBe(42);
    });
  });

  describe('replayEvents', () => {
    it('replays events onto mock socket', async () => {
      const { emitFromServer, getHandlers, socket } = createMockSocket();
      const received = [];
      socket.on('pipeline:phase-start', (p) => received.push(p));

      const events = [
        { event: 'pipeline:phase-start', payload: PipelineFactory.phaseStart() },
        { event: 'pipeline:phase-start', payload: PipelineFactory.phaseStart() },
      ];
      await replayEvents(emitFromServer, events);
      expect(received).toHaveLength(2);
    });
  });

  describe('assertValidPayload', () => {
    it('passes for valid payloads', () => {
      expect(() => assertValidPayload(EVENTS.DEADLINE.ALERT, DeadlineFactory.create())).not.toThrow();
    });

    it('throws for invalid payloads', () => {
      expect(() => assertValidPayload(EVENTS.DEADLINE.ALERT, {})).toThrow('Missing required field');
    });
  });

  describe('validateFactoryOutputs', () => {
    it('validates bulk factory outputs', () => {
      const entries = [
        { event: EVENTS.DEADLINE.ALERT, payload: DeadlineFactory.create() },
        { event: EVENTS.PIPELINE.PHASE_START, payload: PipelineFactory.phaseStart() },
        { event: EVENTS.EVIDENCE.INGESTED, payload: EvidenceFactory.create() },
        { event: EVENTS.SYSTEM.HEALTH, payload: SystemHealthFactory.create() },
        { event: EVENTS.SYSTEM.NOTIFICATION, payload: NotificationFactory.create() },
      ];
      const result = validateFactoryOutputs(entries);
      expect(result.valid).toBe(5);
      expect(result.invalid).toBe(0);
    });
  });
});

// -------------------------------------------------------------------------
// Cross-Validation: All factories vs event schemas
// -------------------------------------------------------------------------

describe('Schema Cross-Validation', () => {
  const factoryEventPairs = [
    ['DeadlineFactory', EVENTS.DEADLINE.ALERT, () => DeadlineFactory.create()],
    ['PipelineFactory.phaseStart', EVENTS.PIPELINE.PHASE_START, () => PipelineFactory.phaseStart()],
    ['PipelineFactory.phaseProgress', EVENTS.PIPELINE.PHASE_PROGRESS, () => PipelineFactory.phaseProgress()],
    ['PipelineFactory.phaseComplete', EVENTS.PIPELINE.PHASE_COMPLETE, () => PipelineFactory.phaseComplete()],
    ['PipelineFactory.phaseError', EVENTS.PIPELINE.PHASE_ERROR, () => PipelineFactory.phaseError()],
    ['PipelineFactory.fullComplete', EVENTS.PIPELINE.FULL_COMPLETE, () => PipelineFactory.fullComplete()],
    ['AgentFactory', EVENTS.PIPELINE.AGENT_STATUS, () => AgentFactory.create()],
    ['EvidenceFactory', EVENTS.EVIDENCE.INGESTED, () => EvidenceFactory.create()],
    ['EvidenceFactory.batch', EVENTS.EVIDENCE.BATCH_PROGRESS, () => EvidenceFactory.batchProgress()],
    ['FilingFactory.status', EVENTS.FILING.STATUS_CHANGE, () => FilingFactory.statusChange()],
    ['FilingFactory.readiness', EVENTS.FILING.READINESS_UPDATE, () => FilingFactory.readinessUpdate()],
    ['NotificationFactory', EVENTS.SYSTEM.NOTIFICATION, () => NotificationFactory.create()],
    ['SystemHealthFactory', EVENTS.SYSTEM.HEALTH, () => SystemHealthFactory.create()],
    ['SystemHealthFactory.error', EVENTS.SYSTEM.ERROR, () => SystemHealthFactory.error()],
  ];

  it.each(factoryEventPairs)('%s produces valid %s payload', (name, event, factory) => {
    // Run 10 times to catch edge cases
    for (let i = 0; i < 10; i++) {
      const payload = factory();
      const result = validateEventPayload(event, payload);
      expect(result.valid, `${name} iteration ${i}: ${result.errors.join(', ')}`).toBe(true);
    }
  });
});
