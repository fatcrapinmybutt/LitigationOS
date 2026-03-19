/**
 * AgentFactory — 56-agent fleet test data.
 *
 * Matches payload schema: {agentId, status, stats}
 * Status enum: running | success | fatal | crash
 */
import { faker } from '@faker-js/faker';
import { sequence } from './sequence';

const AGENT_IDS = [
  // Lane 1 — Infrastructure (A01–A12)
  'A01', 'A02', 'A03', 'A04', 'A05', 'A06',
  'A07', 'A08', 'A09', 'A10', 'A11', 'A12',
  // Lane 2 — Intelligence (J01–L08)
  'J01', 'J02', 'J03', 'J04', 'J05', 'J06', 'J07', 'J08',
  'K01', 'K02', 'K03', 'K04', 'K05', 'K06', 'K07', 'K08',
  'L01', 'L02', 'L03', 'L04', 'L05', 'L06', 'L07', 'L08',
  // Convergence (F01–F06)
  'F01', 'F02', 'F03', 'F04', 'F05', 'F06',
];

const AGENT_STATUS_VALUES = ['running', 'success', 'fatal', 'crash'];

export class AgentFactory {
  constructor() {
    this.data = {};
    this.traits = [];
  }

  static create(overrides) {
    return new AgentFactory().with(overrides).build();
  }

  static createMany(count, overrides) {
    return Array.from({ length: count }, (_, i) =>
      AgentFactory.create({ agentId: AGENT_IDS[i % AGENT_IDS.length], ...overrides })
    );
  }

  /** Create a full fleet of 56 agents with given status */
  static createFleet(status = 'success') {
    return AGENT_IDS.map((agentId) =>
      AgentFactory.create({ agentId, status })
    );
  }

  with(overrides) {
    if (overrides) this.data = { ...this.data, ...overrides };
    return this;
  }

  withTrait(trait) {
    this.traits.push(trait);
    return this;
  }

  asRunning() {
    this.data.status = 'running';
    return this;
  }

  asSuccess() {
    this.data.status = 'success';
    return this;
  }

  asFatal() {
    this.data.status = 'fatal';
    this.traits.push('with_error');
    return this;
  }

  asCrash() {
    this.data.status = 'crash';
    this.traits.push('with_error');
    return this;
  }

  /** Trait: infrastructure agent (A-tier) */
  asInfrastructure() {
    this.data.agentId = faker.helpers.arrayElement(AGENT_IDS.filter((id) => id.startsWith('A')));
    return this;
  }

  /** Trait: intelligence agent (J/K/L-tier) */
  asIntelligence() {
    this.data.agentId = faker.helpers.arrayElement(AGENT_IDS.filter((id) => /^[JKL]/.test(id)));
    return this;
  }

  /** Trait: convergence agent (F-tier) */
  asConvergence() {
    this.data.agentId = faker.helpers.arrayElement(AGENT_IDS.filter((id) => id.startsWith('F')));
    return this;
  }

  build() {
    const n = sequence.next('agent');
    const status = this.data.status ?? faker.helpers.arrayElement(AGENT_STATUS_VALUES);

    const stats = this.data.stats ?? {
      itemsProcessed: faker.number.int({ min: 0, max: 10000 }),
      duration: faker.number.int({ min: 100, max: 60000 }),
      errors: status === 'success' ? 0 : faker.number.int({ min: 1, max: 20 }),
    };

    if (this.traits.includes('with_error')) {
      stats.lastError = faker.lorem.sentence();
      stats.errorStack = `Error: ${stats.lastError}\n    at Agent.run (agents/${this.data.agentId || 'A01'}.js:42:5)`;
    }

    return {
      agentId: this.data.agentId ?? AGENT_IDS[n % AGENT_IDS.length],
      status,
      stats,
    };
  }
}

AgentFactory.AGENT_IDS = AGENT_IDS;
AgentFactory.STATUS_VALUES = AGENT_STATUS_VALUES;

export default AgentFactory;
