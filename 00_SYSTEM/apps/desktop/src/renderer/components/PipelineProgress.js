import usePipelineStatus from '../hooks/usePipelineStatus';

const AGENT_STATUS_COLORS = {
  running: 'bg-omega-success animate-pulse',
  success: 'bg-blue-400',
  fatal: 'bg-omega-critical',
  crash: 'bg-omega-critical',
};

export default function PipelineProgress() {
  const { isRunning, currentPhase, progress, agents, phases, errors, isConnected } = usePipelineStatus();

  if (!isConnected) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 text-omega-muted text-sm">
          <span className="w-2 h-2 rounded-full bg-omega-critical" />
          Pipeline — Disconnected
        </div>
      </div>
    );
  }

  if (!isRunning && phases.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-1">
          <span className="w-2 h-2 rounded-full bg-omega-hold" />
          <h3 className="font-semibold text-sm">Pipeline</h3>
        </div>
        <p className="text-omega-muted text-sm">Idle — No pipeline running</p>
      </div>
    );
  }

  const agentEntries = Object.entries(agents);

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-omega-success animate-pulse' : 'bg-omega-hold'}`} />
          <h3 className="font-semibold text-sm">Pipeline</h3>
        </div>
        <span className="text-xs text-omega-muted">
          {phases.length} phase{phases.length !== 1 ? 's' : ''} completed
        </span>
      </div>

      {/* Current phase */}
      {currentPhase && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">{currentPhase.phaseName || currentPhase.phaseId}</span>
            <span className="text-xs font-mono text-omega-accent">{progress.percent}%</span>
          </div>

          {/* Progress bar */}
          <div className="w-full h-2 bg-omega-surface rounded-full overflow-hidden">
            <div
              className="h-full bg-omega-accent rounded-full transition-all duration-500 ease-out"
              style={{ width: `${Math.min(progress.percent, 100)}%` }}
            />
          </div>

          {progress.total > 0 && (
            <div className="text-xs text-omega-muted mt-1">
              {progress.processed.toLocaleString()} / {progress.total.toLocaleString()} items
            </div>
          )}
        </div>
      )}

      {/* Agent indicators */}
      {agentEntries.length > 0 && (
        <div className="mb-4">
          <div className="text-xs text-omega-muted mb-2">Agents</div>
          <div className="flex flex-wrap gap-2">
            {agentEntries.map(([agentId, agent]) => (
              <div
                key={agentId}
                className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-omega-surface text-xs"
                title={`${agentId}: ${agent.status}`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${AGENT_STATUS_COLORS[agent.status] || 'bg-omega-hold'}`} />
                <span className="text-omega-muted">{agentId}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Errors */}
      {errors.length > 0 && (
        <div>
          <div className="text-xs text-omega-critical mb-1">Errors ({errors.length})</div>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {errors.map((err, i) => (
              <div key={`${err.phaseId}-${err.timestamp}-${i}`} className="text-xs px-2 py-1.5 rounded bg-omega-critical/10 text-omega-critical border border-omega-critical/20">
                <span className="font-mono">{err.phaseId}</span>: {err.error}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
