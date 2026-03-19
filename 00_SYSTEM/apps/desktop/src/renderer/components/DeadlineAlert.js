import { useState } from 'react';
import useDeadlineAlerts from '../hooks/useDeadlineAlerts';

function getUrgencyStyle(daysRemaining) {
  if (daysRemaining <= 3) {
    return { badge: 'badge-critical', dot: 'bg-omega-critical animate-pulse', text: 'text-omega-critical' };
  }
  if (daysRemaining <= 7) {
    return { badge: 'bg-amber-500/20 text-amber-400 border border-amber-500/30', dot: 'bg-amber-400', text: 'text-amber-400' };
  }
  if (daysRemaining <= 14) {
    return { badge: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30', dot: 'bg-yellow-400', text: 'text-yellow-400' };
  }
  return { badge: 'badge-standard', dot: 'bg-omega-standard', text: 'text-omega-muted' };
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

export default function DeadlineAlert() {
  const { deadlines, criticalCount, isConnected } = useDeadlineAlerts();
  const [showAll, setShowAll] = useState(false);

  if (!isConnected) return null;

  if (deadlines.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 text-omega-muted text-sm">
          <span className="w-2 h-2 rounded-full bg-omega-hold" />
          No upcoming deadlines
        </div>
      </div>
    );
  }

  const visible = showAll ? deadlines : deadlines.slice(0, 3);

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm">⏰</span>
          <h3 className="font-semibold text-sm">Deadlines</h3>
          {criticalCount > 0 && (
            <span className="badge-critical text-[10px]">{criticalCount} critical</span>
          )}
        </div>
        {deadlines.length > 3 && (
          <button
            onClick={() => setShowAll((prev) => !prev)}
            className="text-xs text-omega-accent hover:text-omega-text transition-colors"
          >
            {showAll ? 'Show top 3' : `View all (${deadlines.length})`}
          </button>
        )}
      </div>

      {/* Deadline items */}
      <div className="space-y-2">
        {visible.map((d) => {
          const urgency = getUrgencyStyle(d.daysRemaining);
          return (
            <div
              key={d.id}
              className="flex items-center gap-3 px-3 py-2 rounded-lg bg-omega-surface/50"
            >
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${urgency.dot}`} />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{d.title || d.description || 'Deadline'}</div>
                <div className="text-[10px] text-omega-muted">{formatDate(d.dueDate)}</div>
              </div>
              <div className={`text-sm font-bold font-mono whitespace-nowrap ${urgency.text}`}>
                {d.daysRemaining <= 0 ? 'OVERDUE' : `${d.daysRemaining}d`}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
