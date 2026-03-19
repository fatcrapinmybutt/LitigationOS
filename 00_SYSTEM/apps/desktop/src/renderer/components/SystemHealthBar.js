import { useState, useEffect } from 'react';
import useSystemHealth from '../hooks/useSystemHealth';

function formatUptime(seconds) {
  if (!seconds && seconds !== 0) return '—';
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

function getMemoryColor(percent) {
  if (percent >= 90) return 'text-omega-critical';
  if (percent >= 80) return 'text-amber-400';
  return 'text-omega-success';
}

export default function SystemHealthBar() {
  const { health, lastUpdate, isConnected } = useSystemHealth();
  const [secondsAgo, setSecondsAgo] = useState(null);

  useEffect(() => {
    if (!lastUpdate) {
      setSecondsAgo(null);
      return;
    }
    setSecondsAgo(Math.floor((Date.now() - lastUpdate) / 1000));
    const interval = setInterval(() => {
      setSecondsAgo(Math.floor((Date.now() - lastUpdate) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [lastUpdate]);

  if (!isConnected || !health) {
    return (
      <div className="flex items-center gap-4 px-3 py-1.5 bg-omega-surface rounded-lg text-xs">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-omega-critical" />
          <span className="text-omega-muted">System health unavailable</span>
        </div>
      </div>
    );
  }

  const memoryPercent = health.memoryUsage ?? health.memoryPercent ?? 0;
  const dbConnected = health.dbStatus === 'connected' || health.dbConnected === true;
  const uptime = health.uptime ?? health.uptimeSeconds ?? null;

  return (
    <div className="flex items-center gap-4 px-3 py-1.5 bg-omega-surface rounded-lg text-xs flex-wrap">
      {/* DB status */}
      <div className="flex items-center gap-1.5">
        <span className={`w-1.5 h-1.5 rounded-full ${dbConnected ? 'bg-omega-success' : 'bg-omega-critical'}`} />
        <span className="text-omega-muted">DB</span>
        <span className={dbConnected ? 'text-omega-success' : 'text-omega-critical'}>
          {dbConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      <span className="text-omega-border">|</span>

      {/* Memory */}
      <div className="flex items-center gap-1.5">
        <span className="text-omega-muted">Memory</span>
        <span className={`font-mono font-medium ${getMemoryColor(memoryPercent)}`}>
          {memoryPercent}%
        </span>
      </div>

      <span className="text-omega-border">|</span>

      {/* Uptime */}
      <div className="flex items-center gap-1.5">
        <span className="text-omega-muted">Uptime</span>
        <span className="font-mono">{formatUptime(uptime)}</span>
      </div>

      {/* Last update */}
      {secondsAgo !== null && (
        <>
          <span className="text-omega-border">|</span>
          <span className="text-omega-muted">
            Last update: {secondsAgo}s ago
          </span>
        </>
      )}
    </div>
  );
}
