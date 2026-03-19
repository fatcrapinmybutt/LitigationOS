import Head from 'next/head';
import { useState, useEffect } from 'react';
import NotificationPanel from '../components/NotificationPanel';
import PipelineProgress from '../components/PipelineProgress';
import DeadlineAlert from '../components/DeadlineAlert';
import ConnectionStatus from '../components/ConnectionStatus';
import SystemHealthBar from '../components/SystemHealthBar';

const LANE_COLORS = {
  A: { label: 'MSC', color: 'lane-A', bg: 'bg-lane-A/20' },
  B: { label: 'COA', color: 'lane-B', bg: 'bg-lane-B/20' },
  C: { label: '14th Circuit', color: 'lane-C', bg: 'bg-lane-C/20' },
  D: { label: 'JTC', color: 'lane-D', bg: 'bg-lane-D/20' },
  E: { label: 'USDC §1983', color: 'lane-E', bg: 'bg-lane-E/20' },
  F: { label: 'State Bar', color: 'lane-F', bg: 'bg-lane-F/20' },
};

function SeparationCounter({ days }) {
  return (
    <div className="card border-omega-critical/50 text-center">
      <div className="text-6xl font-black text-omega-critical tracking-tighter animate-pulse-slow">
        {days}
      </div>
      <div className="stat-label text-omega-critical/80 mt-2">
        DAYS SEPARATED FROM LINCOLN
      </div>
      <div className="text-xs text-omega-muted mt-1">Since August 8, 2025</div>
    </div>
  );
}

function StatCard({ value, label, color = 'text-omega-accent', icon }) {
  return (
    <div className="card-hover">
      <div className="flex items-start justify-between">
        <div>
          <div className={`stat-value ${color}`}>{value}</div>
          <div className="stat-label">{label}</div>
        </div>
        {icon && <span className="text-2xl opacity-60">{icon}</span>}
      </div>
    </div>
  );
}

function ForumCard({ lane, label, actions, score }) {
  const laneStyle = {
    A: 'border-lane-A/50 hover:border-lane-A',
    B: 'border-lane-B/50 hover:border-lane-B',
    C: 'border-lane-C/50 hover:border-lane-C',
    D: 'border-lane-D/50 hover:border-lane-D',
    E: 'border-lane-E/50 hover:border-lane-E',
    F: 'border-lane-F/50 hover:border-lane-F',
  };
  const textStyle = {
    A: 'text-lane-A', B: 'text-lane-B', C: 'text-lane-C',
    D: 'text-lane-D', E: 'text-lane-E', F: 'text-lane-F',
  };

  return (
    <div className={`card-hover ${laneStyle[lane]}`}>
      <div className="flex items-center gap-2 mb-3">
        <span className={`w-3 h-3 rounded-full bg-lane-${lane}`} />
        <span className={`font-semibold ${textStyle[lane]}`}>Lane {lane}</span>
        <span className="text-omega-muted text-sm">— {label}</span>
      </div>
      <div className="flex justify-between items-end">
        <div>
          <div className="text-2xl font-bold">{actions}</div>
          <div className="text-xs text-omega-muted">Actions Identified</div>
        </div>
        <div className="text-right">
          <div className={`text-lg font-mono font-bold ${
            score >= 85 ? 'text-omega-critical' :
            score >= 70 ? 'text-omega-high' :
            score >= 55 ? 'text-omega-accent' : 'text-omega-standard'
          }`}>
            Ω {score}
          </div>
          <div className="text-xs text-omega-muted">Avg OMEGA</div>
        </div>
      </div>
    </div>
  );
}

function SystemStatus({ dbStats }) {
  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-omega-success animate-pulse" />
        System Status
      </h3>
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-omega-muted">Database</span>
          <span className={dbStats ? 'text-omega-success' : 'text-omega-critical'}>
            {dbStats ? '● Connected' : '○ Disconnected'}
          </span>
        </div>
        {dbStats && (
          <>
            <div className="flex justify-between">
              <span className="text-omega-muted">Tables</span>
              <span className="font-mono">{dbStats.tables}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-omega-muted">Size</span>
              <span className="font-mono">{(dbStats.sizeBytes / (1024**3)).toFixed(2)} GB</span>
            </div>
          </>
        )}
        <div className="flex justify-between">
          <span className="text-omega-muted">Pipeline</span>
          <span className="text-omega-success">● Ready</span>
        </div>
        <div className="flex justify-between">
          <span className="text-omega-muted">Neo4j</span>
          <span className="text-omega-muted">○ Pending</span>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [separationDays, setSeparationDays] = useState(0);
  const [dbStats, setDbStats] = useState(null);

  useEffect(() => {
    // Calculate separation days
    const start = new Date('2025-08-08');
    const now = new Date();
    setSeparationDays(Math.floor((now - start) / (1000 * 60 * 60 * 24)));

    // Try to get DB stats via Electron IPC
    if (typeof window !== 'undefined' && window.litigos) {
      window.litigos.db.stats().then(res => {
        if (res.ok) setDbStats(res.data);
      });
    }
  }, []);

  return (
    <>
      <Head>
        <title>LitigationOS — Command Center</title>
      </Head>

      <div className="min-h-screen bg-omega-bg">
        {/* Title Bar */}
        <div className="h-9 bg-omega-bg flex items-center px-4 border-b border-omega-border/50"
             style={{ WebkitAppRegion: 'drag' }}>
          <span className="text-sm font-semibold text-omega-accent tracking-wider">
            ⚖️ LITIGATION<span className="text-omega-text">OS</span>
          </span>
          <span className="text-xs text-omega-muted ml-3">v1.0.0 — OPERATION OMEGA</span>
          <ConnectionStatus />
        </div>

        {/* Main Content */}
        <div className="p-6 max-w-[1600px] mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold">
                Command Center
              </h1>
              <p className="text-omega-muted mt-1">
                Pigors v. Watson — All Forums Active
              </p>
            </div>
            <div className="flex gap-3 items-center">
              <NotificationPanel />
              <span className="badge-critical">⚡ OMEGA ACTIVE</span>
              <span className="badge-success">● Systems Online</span>
            </div>
          </div>

          <DeadlineAlert />

          {/* Top Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <SeparationCounter days={separationDays} />
            <StatCard value="6" label="Active Forums" icon="⚖️" />
            <StatCard value="48" label="Court-Ready Docs" icon="📄" color="text-omega-success" />
            <StatCard value="377" label="Judicial Violations" icon="🚨" color="text-omega-critical" />
          </div>

          {/* Forum Cards */}
          <h2 className="text-xl font-semibold mb-4">Case Lanes</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            <ForumCard lane="A" label="Michigan Supreme Court" actions={10} score={88} />
            <ForumCard lane="B" label="Court of Appeals" actions={1} score={75} />
            <ForumCard lane="C" label="14th Circuit Court" actions={6} score={72} />
            <ForumCard lane="D" label="Judicial Tenure Commission" actions={1} score={92} />
            <ForumCard lane="E" label="US District Court" actions={5} score={82} />
            <ForumCard lane="F" label="State Bar of Michigan" actions={3} score={78} />
          </div>

          {/* Bottom Row */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <div>
              <SystemStatus dbStats={dbStats} />
              <SystemHealthBar />
            </div>
            
            <PipelineProgress />

            {/* Recent Activity */}
            <div className="card lg:col-span-2">
              <h3 className="text-lg font-semibold mb-4">OMEGA Priority Queue</h3>
              <div className="space-y-2">
                {[
                  { action: 'JTC Formal Complaint (9-Count)', score: 92, tier: 'CRITICAL' },
                  { action: 'MSC Emergency Application', score: 88, tier: 'CRITICAL' },
                  { action: 'USDC §1983 (5 Counts)', score: 82, tier: 'HIGH' },
                  { action: 'MSC Superintending Control', score: 80, tier: 'HIGH' },
                  { action: 'State Bar — Berry', score: 78, tier: 'HIGH' },
                  { action: 'COA Appeal 366810 Brief', score: 75, tier: 'HIGH' },
                  { action: '14th Circuit — Vacate Ex Parte', score: 72, tier: 'HIGH' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg 
                                          bg-omega-surface/50 hover:bg-omega-surface transition-colors">
                    <div className="flex items-center gap-3">
                      <span className={`font-mono font-bold text-sm w-12 ${
                        item.score >= 85 ? 'text-omega-critical' :
                        item.score >= 70 ? 'text-omega-high' : 'text-omega-standard'
                      }`}>
                        Ω{item.score}
                      </span>
                      <span>{item.action}</span>
                    </div>
                    <span className={
                      item.tier === 'CRITICAL' ? 'badge-critical' : 'badge-high'
                    }>
                      {item.tier}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
