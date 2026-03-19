'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

function useLiveDays(startDate) {
  const [days, setDays] = useState(() => Math.floor((Date.now() - new Date(startDate).getTime()) / 86400000));
  useEffect(() => {
    const id = setInterval(() => setDays(Math.floor((Date.now() - new Date(startDate).getTime()) / 86400000)), 60000);
    return () => clearInterval(id);
  }, [startDate]);
  return days;
}

function StatCard({ value, label, color = 'text-omega-accent', border = 'border-omega-border' }) {
  return (
    <div className={`bg-omega-card border ${border} rounded-xl p-5 text-center`}>
      <div className={`text-4xl md:text-5xl font-black ${color}`}>{typeof value === 'number' ? value.toLocaleString() : value}</div>
      <div className="text-xs text-omega-muted mt-2 uppercase tracking-wider">{label}</div>
    </div>
  );
}

function TierBadge({ tier }) {
  const styles = {
    CRITICAL: 'bg-omega-critical/20 text-omega-critical border-omega-critical/30',
    HIGH: 'bg-orange-500/20 text-orange-500 border-orange-500/30',
    MEDIUM: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
    LOW: 'bg-green-500/20 text-green-500 border-green-500/30',
  };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[tier] || styles.MEDIUM}`}>
      {tier}
    </span>
  );
}

function ViolationBar({ items, total }) {
  const colors = { critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e' };
  return (
    <div>
      <div className="flex rounded-full overflow-hidden h-5 bg-omega-surface">
        {items.map((v) => (
          <div key={v.severity} style={{ width: `${(v.count / total) * 100}%`, backgroundColor: colors[v.severity] || '#6b7280' }}
            title={`${v.severity}: ${v.count}`} />
        ))}
      </div>
      <div className="flex flex-wrap gap-4 mt-3">
        {items.map((v) => (
          <div key={v.severity} className="flex items-center gap-2 text-sm">
            <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: colors[v.severity] }} />
            <span className="capitalize text-omega-muted">{v.severity}</span>
            <span className="font-semibold">{v.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ViolationTypeChart({ items }) {
  const max = items.length > 0 ? items[0].count : 1;
  return (
    <div className="space-y-2">
      {items.map((v, i) => (
        <div key={i}>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-omega-muted truncate mr-2">{v.category}</span>
            <span className="font-mono font-semibold shrink-0">{v.count}</span>
          </div>
          <div className="h-2 bg-omega-surface rounded-full overflow-hidden">
            <div className="h-full bg-omega-accent rounded-full" style={{ width: `${(v.count / max) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function ReadinessRing({ ready, nearReady, total }) {
  const pct = total > 0 ? Math.round((ready / total) * 100) : 0;
  const r = 40, c = 2 * Math.PI * r;
  return (
    <div className="flex items-center gap-6">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#2a3567" strokeWidth="8" />
        <circle cx="50" cy="50" r={r} fill="none" stroke="#22c55e" strokeWidth="8"
          strokeDasharray={c} strokeDashoffset={c - (c * pct) / 100}
          strokeLinecap="round" transform="rotate(-90 50 50)" />
        <text x="50" y="54" textAnchor="middle" className="fill-white text-lg font-bold">{pct}%</text>
      </svg>
      <div className="space-y-1 text-sm">
        <div><span className="text-omega-success font-bold">{ready}</span> <span className="text-omega-muted">Ready to File</span></div>
        <div><span className="text-yellow-500 font-bold">{nearReady}</span> <span className="text-omega-muted">Near Ready</span></div>
        <div><span className="text-omega-muted">{total} Total Actions</span></div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const liveDays = useLiveDays('2025-08-08');

  useEffect(() => {
    fetch('/api/v1/dashboard')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setData)
      .catch(e => setError(e.message));
  }, []);

  if (error) return (
    <div className="min-h-screen bg-omega-bg flex items-center justify-center p-6">
      <div className="bg-omega-card border border-omega-critical/30 rounded-xl p-8 max-w-md text-center">
        <div className="text-4xl mb-4">⚠️</div>
        <h2 className="text-xl font-bold text-omega-critical mb-2">Dashboard Error</h2>
        <p className="text-omega-muted">{error}</p>
      </div>
    </div>
  );

  if (!data) return (
    <div className="min-h-screen bg-omega-bg flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-omega-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-omega-muted">Loading OMEGA dashboard…</p>
      </div>
    </div>
  );

  const forums = [...new Set(data.topActions.map(a => a.forum))];

  return (
    <div className="min-h-screen bg-omega-bg">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-omega-border/50">
        <Link href="/" className="text-lg font-bold">
          <span className="text-omega-accent">⚖️ Litigation</span>OS
        </Link>
        <span className="text-sm text-omega-muted">OMEGA Dashboard</span>
      </nav>

      <div className="max-w-7xl mx-auto p-4 md:p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl md:text-3xl font-bold mb-1">Case Dashboard</h1>
          <p className="text-omega-muted">Pigors v. Watson — {forums.length} Forums Active</p>
        </div>

        {/* Top Stats */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <StatCard value={liveDays} label="Days Separated" color="text-omega-critical" border="border-omega-critical/30" />
          <StatCard value={data.totalViolations} label="Total Violations" color="text-omega-critical" border="border-omega-critical/30" />
          <StatCard value={data.criticalViolations} label="Critical" color="text-red-400" />
          <StatCard value={data.exParteViolations} label="Ex Parte" color="text-orange-400" />
          <StatCard value={data.totalClaims} label="Claims" color="text-omega-accent" />
          <StatCard value={data.totalEvidence} label="Evidence Items" color="text-omega-success" />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* OMEGA Priority Queue — spans 2 cols */}
          <div className="lg:col-span-2 bg-omega-card border border-omega-border rounded-xl p-5">
            <h2 className="text-lg font-semibold mb-4">⚡ OMEGA Priority Queue</h2>
            <div className="space-y-2">
              {data.topActions.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 rounded-lg bg-omega-surface/50 hover:bg-omega-surface transition-colors">
                  <div className="flex items-center gap-4 min-w-0">
                    <span className={`font-mono font-bold w-14 shrink-0 ${
                      item.omega_score >= 85 ? 'text-omega-critical' : item.omega_score >= 70 ? 'text-orange-500' : 'text-yellow-500'
                    }`}>
                      Ω{item.omega_score}
                    </span>
                    <div className="min-w-0">
                      <div className="font-medium truncate">{item.filing_name}</div>
                      <div className="text-xs text-omega-muted">{item.forum} · Evidence: {item.evidence_strength}%</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      item.readiness_label === 'READY TO FILE' ? 'bg-omega-success/20 text-omega-success' : 'bg-yellow-500/20 text-yellow-500'
                    }`}>
                      {item.readiness_label}
                    </span>
                    <TierBadge tier={item.omega_tier} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Filing Readiness */}
          <div className="bg-omega-card border border-omega-border rounded-xl p-5">
            <h2 className="text-lg font-semibold mb-4">📋 Filing Readiness</h2>
            <ReadinessRing ready={data.filingReadiness.ready} nearReady={data.filingReadiness.nearReady} total={data.filingReadiness.total} />
            <div className="mt-4 pt-4 border-t border-omega-border">
              <h3 className="text-sm font-semibold text-omega-muted uppercase mb-3">Success Predictions</h3>
              <div className="space-y-2">
                {data.predictions.slice(0, 5).map((p, i) => (
                  <div key={i} className="flex justify-between items-center text-sm">
                    <span className="truncate mr-2 text-omega-muted">{p.action_name}</span>
                    <span className="font-mono font-bold text-omega-success shrink-0">{Math.round(p.probability * 100)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Violations Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-omega-card border border-omega-border rounded-xl p-5">
            <h2 className="text-lg font-semibold mb-4">🔴 Violations by Severity</h2>
            <ViolationBar items={data.violationsBySeverity} total={data.totalViolations} />
          </div>
          <div className="bg-omega-card border border-omega-border rounded-xl p-5">
            <h2 className="text-lg font-semibold mb-4">📊 Violations by Type</h2>
            <ViolationTypeChart items={data.violationsByType} />
          </div>
        </div>

        {/* Deadlines */}
        <div className="bg-omega-card border border-omega-border rounded-xl p-5">
          <h2 className="text-lg font-semibold mb-4">📅 Upcoming Deadlines</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-omega-muted border-b border-omega-border">
                  <th className="pb-2 pr-4">Action</th>
                  <th className="pb-2 pr-4">Forum</th>
                  <th className="pb-2 pr-4">Deadline</th>
                  <th className="pb-2 pr-4">Days</th>
                  <th className="pb-2 pr-4">Priority</th>
                  <th className="pb-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-omega-border/50">
                {data.recentDeadlines.map((d, i) => (
                  <tr key={i} className="hover:bg-omega-surface/30">
                    <td className="py-2 pr-4 font-medium">{d.action}</td>
                    <td className="py-2 pr-4 text-omega-muted">{d.forum}</td>
                    <td className="py-2 pr-4 font-mono text-omega-muted">{d.deadline_date}</td>
                    <td className="py-2 pr-4">
                      <span className={`font-bold ${d.days_remaining <= 3 ? 'text-omega-critical' : d.days_remaining <= 7 ? 'text-orange-500' : 'text-omega-muted'}`}>
                        {d.days_remaining}d
                      </span>
                    </td>
                    <td className="py-2 pr-4"><TierBadge tier={d.priority === 'URGENT' ? 'CRITICAL' : d.tier} /></td>
                    <td className="py-2">
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        d.status === 'PENDING' ? 'bg-yellow-500/20 text-yellow-500' : 'bg-omega-success/20 text-omega-success'
                      }`}>{d.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer timestamp */}
        <div className="text-center text-xs text-omega-muted pb-4">
          Data as of {new Date(data.timestamp).toLocaleString()} · Separation since Aug 8, 2025
        </div>
      </div>
    </div>
  );
}
