/**
 * PipelineFactory — 16-phase pipeline test data.
 *
 * Creates payloads for: phase-start, phase-progress, phase-complete, phase-error, full-complete
 */
import { faker } from '@faker-js/faker';
import { sequence } from './sequence';

const PIPELINE_PHASES = [
  { id: '0',  name: 'Safety Snapshot' },
  { id: '1',  name: 'Inventory' },
  { id: '2',  name: 'Deduplication' },
  { id: '3',  name: 'Classification' },
  { id: '4a', name: 'PDF Extraction' },
  { id: '4b', name: 'DOCX Extraction' },
  { id: '4c', name: 'Structured Extraction' },
  { id: '4d', name: 'Atomization' },
  { id: '4e', name: 'Archive Extraction' },
  { id: '5',  name: 'LEXOS Brain Feed' },
  { id: '6',  name: 'Gap Analysis' },
  { id: '7a', name: 'Graph Delta' },
  { id: '7b', name: 'Synthesis Merge' },
  { id: '7c', name: 'Knowledge Merge' },
  { id: '8',  name: 'Litigation Refresh' },
  { id: '9',  name: 'MCP Ingest' },
];

export class PipelineFactory {
  constructor() {
    this.data = {};
    this._phaseIndex = null;
  }

  static phaseStart(overrides) {
    return new PipelineFactory().with(overrides).buildPhaseStart();
  }

  static phaseProgress(overrides) {
    return new PipelineFactory().with(overrides).buildPhaseProgress();
  }

  static phaseComplete(overrides) {
    return new PipelineFactory().with(overrides).buildPhaseComplete();
  }

  static phaseError(overrides) {
    return new PipelineFactory().with(overrides).buildPhaseError();
  }

  static fullComplete(overrides) {
    return new PipelineFactory().with(overrides).buildFullComplete();
  }

  with(overrides) {
    if (overrides) this.data = { ...this.data, ...overrides };
    return this;
  }

  forPhase(phaseIndex) {
    this._phaseIndex = phaseIndex;
    return this;
  }

  _getPhase() {
    const idx = this._phaseIndex ?? faker.number.int({ min: 0, max: PIPELINE_PHASES.length - 1 });
    return PIPELINE_PHASES[idx];
  }

  buildPhaseStart() {
    const phase = this._getPhase();
    return {
      phaseId: this.data.phaseId ?? phase.id,
      phaseName: this.data.phaseName ?? phase.name,
      totalItems: this.data.totalItems ?? faker.number.int({ min: 100, max: 50000 }),
    };
  }

  buildPhaseProgress() {
    const phase = this._getPhase();
    const total = this.data.total ?? faker.number.int({ min: 100, max: 50000 });
    const processed = this.data.processed ?? faker.number.int({ min: 0, max: total });
    return {
      phaseId: this.data.phaseId ?? phase.id,
      processed,
      total,
      percent: this.data.percent ?? (total > 0 ? Math.round((processed / total) * 100) : 0),
    };
  }

  buildPhaseComplete() {
    const phase = this._getPhase();
    return {
      phaseId: this.data.phaseId ?? phase.id,
      phaseName: this.data.phaseName ?? phase.name,
      duration: this.data.duration ?? faker.number.int({ min: 500, max: 300000 }),
      stats: this.data.stats ?? {
        itemsProcessed: faker.number.int({ min: 100, max: 50000 }),
        errors: faker.number.int({ min: 0, max: 10 }),
        skipped: faker.number.int({ min: 0, max: 50 }),
      },
    };
  }

  buildPhaseError() {
    const phase = this._getPhase();
    return {
      phaseId: this.data.phaseId ?? phase.id,
      error: this.data.error ?? faker.lorem.sentence(),
      recoverable: this.data.recoverable ?? faker.datatype.boolean(),
    };
  }

  buildFullComplete() {
    return {
      duration: this.data.duration ?? faker.number.int({ min: 60000, max: 3600000 }),
      phasesRun: this.data.phasesRun ?? faker.number.int({ min: 1, max: 16 }),
      summary: this.data.summary ?? {
        totalItems: faker.number.int({ min: 10000, max: 200000 }),
        totalErrors: faker.number.int({ min: 0, max: 50 }),
        lanes: { A: 'ok', B: 'ok', C: 'ok', D: 'ok', E: 'ok', F: 'ok' },
      },
    };
  }
}

/** Available pipeline phase definitions for reference */
PipelineFactory.PHASES = PIPELINE_PHASES;

export default PipelineFactory;
