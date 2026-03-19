/**
 * PipelineRunBuilder — Builds complex pipeline execution scenarios.
 *
 * Produces a sequence of events simulating a full or partial pipeline run
 * with configurable phase selection, error injection, and agent fleet state.
 */
import { PipelineFactory } from '../factories/PipelineFactory';
import { AgentFactory } from '../factories/AgentFactory';
import { faker } from '@faker-js/faker';

export class PipelineRunBuilder {
  constructor() {
    this._phases = [...PipelineFactory.PHASES];
    this._errorPhases = new Set();
    this._agents = [];
    this._includeFinalComplete = true;
    this._baseItemCount = 1000;
  }

  /** Only include specific phases (by index or id) */
  withPhases(phaseIds) {
    this._phases = PipelineFactory.PHASES.filter(
      (p, i) => phaseIds.includes(p.id) || phaseIds.includes(i)
    );
    return this;
  }

  /** Skip specific phases */
  skipPhases(phaseIds) {
    this._phases = this._phases.filter((p) => !phaseIds.includes(p.id));
    return this;
  }

  /** Inject a recoverable error at the given phase */
  withErrorAt(phaseId, recoverable = true) {
    this._errorPhases.add(JSON.stringify({ phaseId, recoverable }));
    return this;
  }

  /** Include agent status events */
  withAgents(count = 10) {
    this._agents = AgentFactory.createMany(count);
    return this;
  }

  /** Include a full fleet with mixed statuses */
  withFleetStatus() {
    this._agents = AgentFactory.AGENT_IDS.slice(0, 20).map((agentId, i) => {
      const status = i < 15 ? 'success' : i < 18 ? 'running' : 'fatal';
      return AgentFactory.create({ agentId, status });
    });
    return this;
  }

  /** Set base item count per phase */
  withItemCount(count) {
    this._baseItemCount = count;
    return this;
  }

  /** Don't emit full-complete event */
  withoutFinalComplete() {
    this._includeFinalComplete = false;
    return this;
  }

  /**
   * Build the event sequence.
   * @returns {Array<{type: string, event: string, payload: object, timestamp: number}>}
   */
  build() {
    const events = [];
    let ts = Date.now();
    const phaseDuration = () => faker.number.int({ min: 2000, max: 30000 });

    // Emit agent status events first
    for (const agent of this._agents) {
      events.push({
        type: 'agent-status',
        event: 'pipeline:agent-status',
        payload: agent,
        timestamp: ts++,
      });
    }

    // Phase events
    for (const phase of this._phases) {
      const totalItems = this._baseItemCount + events.length * 100;

      // Phase start
      events.push({
        type: 'phase-start',
        event: 'pipeline:phase-start',
        payload: PipelineFactory.phaseStart({ phaseId: phase.id, phaseName: phase.name, totalItems }),
        timestamp: ts++,
      });

      // Progress ticks (25%, 50%, 75%, 100%)
      for (const pct of [25, 50, 75, 100]) {
        events.push({
          type: 'phase-progress',
          event: 'pipeline:phase-progress',
          payload: PipelineFactory.phaseProgress({
            phaseId: phase.id,
            processed: Math.round(totalItems * pct / 100),
            total: totalItems,
            percent: pct,
          }),
          timestamp: ts++,
        });
      }

      // Check for error injection
      const errorEntry = [...this._errorPhases].find((e) => JSON.parse(e).phaseId === phase.id);
      if (errorEntry) {
        const { recoverable } = JSON.parse(errorEntry);
        events.push({
          type: 'phase-error',
          event: 'pipeline:phase-error',
          payload: PipelineFactory.phaseError({ phaseId: phase.id, recoverable }),
          timestamp: ts++,
        });
        if (!recoverable) break; // Fatal error stops pipeline
      }

      // Phase complete
      const duration = phaseDuration();
      events.push({
        type: 'phase-complete',
        event: 'pipeline:phase-complete',
        payload: PipelineFactory.phaseComplete({
          phaseId: phase.id,
          phaseName: phase.name,
          duration,
          stats: { itemsProcessed: totalItems, errors: 0, skipped: 0 },
        }),
        timestamp: ts++,
      });
    }

    // Full complete
    if (this._includeFinalComplete) {
      events.push({
        type: 'full-complete',
        event: 'pipeline:full-complete',
        payload: PipelineFactory.fullComplete({
          phasesRun: this._phases.length,
          duration: ts - events[0]?.timestamp || 0,
        }),
        timestamp: ts++,
      });
    }

    return events;
  }
}

export default PipelineRunBuilder;
