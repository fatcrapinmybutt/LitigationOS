/**
 * SystemHealthFactory — System health and error test data.
 *
 * Health payload: {db, pipeline, engine, memory: {heapUsedMB, heapTotalMB, rssMB}, uptime}
 * Error payload: {source, message, severity}
 */
import { faker } from '@faker-js/faker';

const PIPELINE_STATES = ['idle', 'running', 'paused', 'error'];
const ENGINE_STATES = ['ready', 'loading', 'error', 'unavailable'];
const ERROR_SOURCES = ['socket-server', 'pipeline', 'database', 'inference-engine', 'agent-fleet', 'mcp-server'];
const ERROR_SEVERITIES = ['info', 'warning', 'error', 'critical'];

export class SystemHealthFactory {
  constructor() {
    this.data = {};
    this.traits = [];
  }

  static create(overrides) {
    return new SystemHealthFactory().with(overrides).build();
  }

  static error(overrides) {
    return new SystemHealthFactory().with(overrides).buildError();
  }

  with(overrides) {
    if (overrides) this.data = { ...this.data, ...overrides };
    return this;
  }

  withTrait(trait) {
    this.traits.push(trait);
    return this;
  }

  /** Trait: healthy system — everything green */
  asHealthy() {
    this.data.db = true;
    this.data.pipeline = 'idle';
    this.data.engine = 'ready';
    return this;
  }

  /** Trait: degraded — DB disconnected */
  asDegraded() {
    this.data.db = false;
    this.data.pipeline = 'error';
    this.data.engine = 'ready';
    return this;
  }

  /** Trait: pipeline running */
  asPipelineRunning() {
    this.data.pipeline = 'running';
    return this;
  }

  /** Trait: high memory usage */
  asHighMemory() {
    this.data.memory = {
      heapUsedMB: faker.number.int({ min: 900, max: 1500 }),
      heapTotalMB: faker.number.int({ min: 1500, max: 2048 }),
      rssMB: faker.number.int({ min: 1500, max: 2500 }),
    };
    return this;
  }

  /** Trait: long uptime */
  asLongRunning() {
    this.data.uptime = faker.number.int({ min: 86400, max: 604800 }); // 1-7 days in seconds
    return this;
  }

  build() {
    return {
      db: this.data.db ?? true,
      pipeline: this.data.pipeline ?? faker.helpers.arrayElement(PIPELINE_STATES),
      engine: this.data.engine ?? faker.helpers.arrayElement(ENGINE_STATES),
      memory: this.data.memory ?? {
        heapUsedMB: faker.number.int({ min: 50, max: 500 }),
        heapTotalMB: faker.number.int({ min: 500, max: 1024 }),
        rssMB: faker.number.int({ min: 100, max: 800 }),
      },
      uptime: this.data.uptime ?? faker.number.int({ min: 0, max: 86400 }),
    };
  }

  buildError() {
    return {
      source: this.data.source ?? faker.helpers.arrayElement(ERROR_SOURCES),
      message: this.data.message ?? faker.lorem.sentence(),
      severity: this.data.severity ?? faker.helpers.arrayElement(ERROR_SEVERITIES),
    };
  }
}

SystemHealthFactory.PIPELINE_STATES = PIPELINE_STATES;
SystemHealthFactory.ENGINE_STATES = ENGINE_STATES;
SystemHealthFactory.ERROR_SOURCES = ERROR_SOURCES;

export default SystemHealthFactory;
