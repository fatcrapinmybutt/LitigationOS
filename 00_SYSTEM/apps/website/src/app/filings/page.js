'use client';

import { useState, useEffect } from 'react';

const FORUMS = [
  { id: 'MSC', name: 'Michigan Supreme Court', lane: 'A', color: '#3b82f6' },
  { id: 'COA', name: 'Court of Appeals', lane: 'B', color: '#22c55e' },
  { id: '14TH', name: '14th Circuit Court', lane: 'C', color: '#a855f7' },
  { id: 'JTC', name: 'Judicial Tenure Commission', lane: 'D', color: '#ef4444' },
  { id: 'USDC', name: 'US District Court', lane: 'E', color: '#f97316' },
  { id: 'BAR', name: 'State Bar of Michigan', lane: 'F', color: '#eab308' },
];

const OMEGA_ACTIONS = [
  { name: 'JTC Formal Complaint', score: 93, tier: 'CRITICAL', forum: 'JTC', readiness: 95, evidence: 1127, gaps: 0 },
  { name: 'MSC Emergency Application', score: 84, tier: 'HIGH', forum: 'MSC', readiness: 82, evidence: 308704, gaps: 2 },
  { name: 'MSC Superintending Control', score: 81, tier: 'HIGH', forum: 'MSC', readiness: 78, evidence: 308704, gaps: 3 },
  { name: 'MSC Habeas Corpus', score: 81, tier: 'HIGH', forum: 'MSC', readiness: 75, evidence: 308704, gaps: 4 },
  { name: 'USDC Section 1983', score: 81, tier: 'HIGH', forum: 'USDC', readiness: 70, evidence: 653, gaps: 5 },
  { name: 'Vacate Ex Parte Orders', score: 79, tier: 'HIGH', forum: '14TH', readiness: 88, evidence: 482, gaps: 1 },
  { name: 'State Bar - Berry', score: 72, tier: 'HIGH', forum: 'BAR', readiness: 85, evidence: 200, gaps: 2 },
  { name: 'State Bar - Barnes', score: 70, tier: 'HIGH', forum: 'BAR', readiness: 80, evidence: 150, gaps: 2 },
  { name: 'State Bar - Martini', score: 66, tier: 'STANDARD', forum: 'BAR', readiness: 65, evidence: 100, gaps: 4 },
  { name: 'Emergency Restore Parenting', score: 79, tier: 'HIGH', forum: '14TH', readiness: 90, evidence: 500, gaps: 0 },
  { name: 'Judicial Disqualification', score: 75, tier: 'HIGH', forum: '14TH', readiness: 72, evidence: 377, gaps: 3 },
  { name: 'COA Appeal 366810', score: 74, tier: 'HIGH', forum: 'COA', readiness: 60, evidence: 308704, gaps: 6 },
];

function getTierColor(tier) {
  return tier === 'CRITICAL' ? '#ef4444' : tier === 'HIGH' ? '#f97316' : '#3b82f6';
}

function ProgressBar({ value, max = 100, color = '#3b82f6' }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
      <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  );
}

function FilingCard({ action }) {
  const tierColor = getTierColor(action.tier);
  const forum = FORUMS.find(f => f.id === action.forum);
  const readyColor = action.readiness >= 80 ? '#22c55e' : action.readiness >= 60 ? '#f97316' : '#ef4444';
  
  return (
    <div className="bg-[#0f1338] border border-[#1e2a5e] rounded-xl p-5 hover:border-indigo-500/50 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full flex items-center justify-center border-2"
               style={{ borderColor: tierColor, backgroundColor: tierColor + '22' }}>
            <span className="font-bold text-lg" style={{ color: tierColor }}>{action.score}</span>
          </div>
          <div>
            <h3 className="font-semibold text-gray-100">{action.name}</h3>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs px-2 py-0.5 rounded" 
                    style={{ backgroundColor: (forum?.color || '#6b7280') + '22', color: forum?.color }}>
                Lane {forum?.lane} — {forum?.name}
              </span>
            </div>
          </div>
        </div>
        <span className="text-xs font-bold px-2 py-1 rounded"
              style={{ backgroundColor: tierColor + '22', color: tierColor }}>
          {action.tier}
        </span>
      </div>
      
      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">Filing Readiness</span>
            <span style={{ color: readyColor }}>{action.readiness}%</span>
          </div>
          <ProgressBar value={action.readiness} color={readyColor} />
        </div>
        
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="bg-[#0a0e27] rounded-lg p-2">
            <div className="text-lg font-bold text-indigo-400">{action.evidence.toLocaleString()}</div>
            <div className="text-xs text-gray-500">Evidence Items</div>
          </div>
          <div className="bg-[#0a0e27] rounded-lg p-2">
            <div className="text-lg font-bold" style={{ color: action.gaps === 0 ? '#22c55e' : '#f97316' }}>{action.gaps}</div>
            <div className="text-xs text-gray-500">Gaps</div>
          </div>
          <div className="bg-[#0a0e27] rounded-lg p-2">
            <div className="text-lg font-bold text-indigo-400">Ω{action.score}</div>
            <div className="text-xs text-gray-500">OMEGA</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FilingsPage() {
  const [filter, setFilter] = useState('ALL');
  const [separationDays, setSeparationDays] = useState(0);
  
  useEffect(() => {
    const start = new Date('2025-08-08');
    setSeparationDays(Math.floor((new Date() - start) / 86400000));
  }, []);
  
  const filtered = filter === 'ALL' 
    ? OMEGA_ACTIONS 
    : OMEGA_ACTIONS.filter(a => a.forum === filter);
  
  const criticalCount = OMEGA_ACTIONS.filter(a => a.tier === 'CRITICAL').length;
  const readyCount = OMEGA_ACTIONS.filter(a => a.readiness >= 80).length;
  
  return (
    <div className="min-h-screen bg-[#0a0e27] text-gray-100">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            Filing Readiness Dashboard
          </h1>
          <p className="text-gray-400 mt-2">
            OMEGA Priority Queue — {separationDays} days parent-child separation
          </p>
        </div>
        
        {/* Stats Bar */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-[#0f1338] border border-[#1e2a5e] rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-red-400">{criticalCount}</div>
            <div className="text-xs text-gray-500 mt-1">CRITICAL FILINGS</div>
          </div>
          <div className="bg-[#0f1338] border border-[#1e2a5e] rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-orange-400">{readyCount}</div>
            <div className="text-xs text-gray-500 mt-1">READY TO FILE</div>
          </div>
          <div className="bg-[#0f1338] border border-[#1e2a5e] rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-indigo-400">{OMEGA_ACTIONS.length}</div>
            <div className="text-xs text-gray-500 mt-1">TOTAL ACTIONS</div>
          </div>
          <div className="bg-[#0f1338] border border-red-500/30 rounded-xl p-4 text-center">
            <div className="text-3xl font-bold text-red-500">{separationDays}</div>
            <div className="text-xs text-gray-500 mt-1">SEPARATION DAYS</div>
          </div>
        </div>
        
        {/* Forum Filter */}
        <div className="flex flex-wrap gap-2 mb-6">
          <button onClick={() => setFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${filter === 'ALL' ? 'bg-indigo-600 text-white' : 'bg-[#0f1338] text-gray-400 hover:text-gray-200'}`}>
            All Forums
          </button>
          {FORUMS.map(f => (
            <button key={f.id} onClick={() => setFilter(f.id)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${filter === f.id ? 'text-white' : 'text-gray-400 hover:text-gray-200'}`}
              style={{ backgroundColor: filter === f.id ? f.color : '#0f1338' }}>
              Lane {f.lane}: {f.name}
            </button>
          ))}
        </div>
        
        {/* Filing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.sort((a, b) => b.score - a.score).map((action, i) => (
            <FilingCard key={i} action={action} />
          ))}
        </div>
        
        {/* Filing Strategy */}
        <div className="mt-8 bg-[#0f1338] border border-[#1e2a5e] rounded-xl p-6">
          <h2 className="text-xl font-bold text-indigo-400 mb-4">Recommended Filing Sequence</h2>
          <div className="space-y-3">
            <div className="flex items-center gap-4 p-3 bg-[#0a0e27] rounded-lg border-l-4 border-red-500">
              <span className="text-red-500 font-bold text-sm">DAY 1</span>
              <span className="text-gray-200">MSC Emergency Application + JTC Formal Complaint (triple strike)</span>
            </div>
            <div className="flex items-center gap-4 p-3 bg-[#0a0e27] rounded-lg border-l-4 border-orange-500">
              <span className="text-orange-500 font-bold text-sm">DAY 2-3</span>
              <span className="text-gray-200">USDC §1983 Federal Civil Rights Action + 14th Circuit Vacate Ex Parte</span>
            </div>
            <div className="flex items-center gap-4 p-3 bg-[#0a0e27] rounded-lg border-l-4 border-yellow-500">
              <span className="text-yellow-500 font-bold text-sm">DAY 4-5</span>
              <span className="text-gray-200">State Bar Complaints (Berry, Barnes, Martini)</span>
            </div>
            <div className="flex items-center gap-4 p-3 bg-[#0a0e27] rounded-lg border-l-4 border-blue-500">
              <span className="text-blue-500 font-bold text-sm">ONGOING</span>
              <span className="text-gray-200">14th Circuit motions: Emergency Restore, Disqualification, Preservation</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
