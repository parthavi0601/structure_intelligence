import { useState, useEffect } from 'react';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { Activity, RefreshCw } from 'lucide-react';
import AIConclusionPanel from '../components/AIConclusionPanel';

const API = 'http://localhost:8000';
const BRIDGE_ID = 'test1';
const BRIDGE_NAME = 'Bridge B001';

interface Summary {
  behavioral_shift_index: number;
  structural_dynamics_score: number;
  behavioral_state_cluster: number;
  anomaly_score: number;
  risk_score: number;
  alert_count: number;
}

export default function BehaviorAnalysis() {
  const [data, setData] = useState<Record<string, number>[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/api/behaviour/${BRIDGE_ID}`)
      .then(r => r.json())
      .then(d => {
        setData(d.data || []);
        setSummary(d.summary || null);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const clusterLabel: Record<number, string> = { 0: 'Normal Baseline', 1: 'Active Load', 2: 'Altered Dynamics' };

  const metricCards = summary ? [
    { label: 'Behavioral Shift Index', value: summary.behavioral_shift_index.toFixed(4), warn: summary.behavioral_shift_index > 0.35 },
    { label: 'Structural Dynamics Score', value: summary.structural_dynamics_score.toFixed(4), warn: summary.structural_dynamics_score > 0.6 },
    { label: 'Behavioral State', value: clusterLabel[summary.behavioral_state_cluster] ?? 'Unknown', warn: summary.behavioral_state_cluster === 2 },
    { label: 'Risk Score', value: `${(summary.risk_score * 100).toFixed(1)}%`, warn: summary.risk_score > 0.4 },
  ] : [];



  return (
    <div className="p-6 space-y-6 grid-bg min-h-full">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(0,234,119,0.1)', border: '1px solid rgba(0,234,119,0.3)' }}>
              <Activity className="w-4 h-4 text-neon-green" />
            </div>
            <h1 className="text-xl font-black text-white">Structural Behavior Analysis</h1>
          </div>
          <p className="text-sm text-gray-500 ml-10">Real parquet data · Behavioral shift index · Structural dynamics score</p>
        </div>

        {/* Bridge selector */}
        <div className="flex items-center gap-2">
          {loading && <RefreshCw className="w-4 h-4 text-neon-cyan animate-spin" />}
          <span className="text-xs font-bold px-3 py-1.5 rounded-lg border text-neon-green border-neon-green/40 bg-neon-green/10">
            {BRIDGE_NAME}
          </span>
        </div>
      </div>

      {/* Metric cards from real data */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((m) => (
          <div key={m.label} className="rounded-2xl border border-white/6 p-4" style={{ background: 'rgba(13,20,40,0.6)' }}>
            <div className="text-xs text-gray-500 uppercase tracking-wider font-bold mb-2">{m.label}</div>
            <div className={`text-2xl font-black font-mono ${m.warn ? 'text-neon-yellow' : 'text-white'}`}>{m.value}</div>
            <div className={`text-[10px] mt-1 font-bold ${m.warn ? 'text-neon-yellow' : 'text-neon-green'}`}>
              {m.warn ? '⚠ Elevated' : '✓ Normal'}
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Behavioral Shift Index over time */}
        <div className="rounded-2xl border border-white/6 p-5" style={{ background: 'rgba(13,20,40,0.6)' }}>
          <h3 className="text-sm font-bold text-white mb-1">Behavioral Shift Index</h3>
          <p className="text-xs text-gray-600 font-mono mb-4">How far structure deviates from baseline · {BRIDGE_NAME}</p>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data}>
              <defs>
                <linearGradient id="bsig" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00EA77" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#00EA77" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="time_start_s" tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={v => `${v}s`} />
              <YAxis tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} domain={[0, 1]} />
              <Tooltip contentStyle={{ background: '#0D1428', border: '1px solid rgba(0,234,119,0.2)', borderRadius: 8 }} />
              <ReferenceLine y={0.35} stroke="#FFDF00" strokeDasharray="4 2" strokeWidth={1} />
              <Area type="monotone" dataKey="Behavioral_Shift_Index" stroke="#00EA77" strokeWidth={2} fill="url(#bsig)" dot={false} name="Shift Index" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Structural Dynamics Score */}
        <div className="rounded-2xl border border-white/6 p-5" style={{ background: 'rgba(13,20,40,0.6)' }}>
          <h3 className="text-sm font-bold text-white mb-1">Structural Dynamics Score</h3>
          <p className="text-xs text-gray-600 font-mono mb-4">Vibration damping pattern analysis · {BRIDGE_NAME}</p>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="time_start_s" tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={v => `${v}s`} />
              <YAxis tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} domain={[0, 1]} />
              <Tooltip contentStyle={{ background: '#0D1428', border: '1px solid rgba(0,209,255,0.2)', borderRadius: 8 }} />
              <ReferenceLine y={0.6} stroke="#FF355E" strokeDasharray="4 2" strokeWidth={1} />
              <Line type="monotone" dataKey="Structural_Dynamics_Score" stroke="#00D1FF" strokeWidth={2} dot={false} name="Dynamics Score" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Predicted Risk Score */}
        <div className="rounded-2xl border border-white/6 p-5 lg:col-span-2" style={{ background: 'rgba(13,20,40,0.6)' }}>
          <h3 className="text-sm font-bold text-white mb-1">Predicted Risk Score Over Time</h3>
          <p className="text-xs text-gray-600 font-mono mb-4">AI-predicted failure probability from behavior analysis · {BRIDGE_NAME}</p>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={data.filter((_, i) => i % 3 === 0)}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="time_start_s" tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={v => `${v}s`} />
              <YAxis tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} domain={[0, 1]} />
              <Tooltip contentStyle={{ background: '#0D1428', border: '1px solid rgba(255,53,94,0.2)', borderRadius: 8 }} />
              <ReferenceLine y={0.4} stroke="#FF355E" strokeDasharray="4 2" strokeWidth={1.5} label={{ value: 'Risk Threshold', fill: '#FF355E', fontSize: 9 }} />
              <Bar dataKey="Predicted_Risk_Score" fill="#FF355E" radius={[2, 2, 0, 0]} opacity={0.7} name="Risk Score" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <AIConclusionPanel
        url={`${API}/api/ai-conclusion/behaviour/${BRIDGE_ID}`}
        pageLabel="Structural Behavior Analysis"
      />

    </div>
  );
}

