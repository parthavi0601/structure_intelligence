import { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { ShieldAlert, RefreshCw, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import AIConclusionPanel from '../components/AIConclusionPanel';

const API = 'http://localhost:8000';
const BRIDGE_ID = 'test1';
const BRIDGE_NAME = 'Bridge B001';

// Only show columns that exist in failure_prediction_behavior.parquet for B001
const COMP_LABELS = [
  { key: 'Autoencoder_Anomaly_Score', label: 'Anomaly Score' },
  { key: 'Predicted_Risk_Score',      label: 'Predicted Risk' },
];


function riskColor(v: number) {
  if (v < 0.2) return '#00EA77';
  if (v < 0.4) return '#FFDF00';
  if (v < 0.6) return '#FF6B35';
  return '#FF355E';
}
function riskLabel(v: number) {
  if (v < 0.2) return 'LOW';
  if (v < 0.4) return 'MODERATE';
  if (v < 0.6) return 'HIGH';
  return 'CRITICAL';
}

export default function RiskPrediction() {
  const [data, setData] = useState<Record<string, number>[]>([]);
  const [summary, setSummary] = useState<Record<string, number | string>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/api/risk/${BRIDGE_ID}`).then(r => r.json()).then(d => {
      setData(d.data || []);
      setSummary(d.summary || {});
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);


  const riskMean = (summary.risk_mean as number) || 0;
  const riskMax  = (summary.risk_max as number)  || 0;
  const riskPct  = (summary.risk_pct as number)  || 0;
  const level    = (summary.risk_level as string) || 'LOW';
  const bsi      = (summary.behavioral_shift as number) || 0;

  // Compute trend from data (first third vs last third)
  let trend = 0;
  if (data.length > 9) {
    const n = Math.floor(data.length / 3);
    const first = data.slice(0, n).reduce((s, d) => s + (d.Predicted_Risk_Score || 0), 0) / n;
    const last  = data.slice(-n).reduce((s, d) => s + (d.Predicted_Risk_Score || 0), 0) / n;
    trend = last - first;
  }

  // Per-component bar data from summary
  const componentData = COMP_LABELS.map(c => ({
    name: c.label,
    value: Number(data.length > 0 ? data.reduce((s, d) => s + (d[c.key] || 0), 0) / data.length : 0),
  }));

  return (
    <div className="p-6 space-y-6 grid-bg min-h-full">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(255,53,94,0.1)', border: '1px solid rgba(255,53,94,0.3)' }}>
              <ShieldAlert className="w-4 h-4 text-neon-red" />
            </div>
            <h1 className="text-xl font-black text-white">Infrastructure Failure Risk Prediction</h1>
          </div>
          <p className="text-sm text-gray-500 ml-10">AI regression model · real parquet data · failure probability assessment</p>
        </div>
        <div className="flex items-center gap-2">
          {loading && <RefreshCw className="w-4 h-4 text-neon-cyan animate-spin" />}
          <span className="text-xs font-bold px-3 py-1.5 rounded-lg border text-neon-red border-neon-red/40 bg-neon-red/10">
            {BRIDGE_NAME}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Risk score dial */}
        <div className="rounded-2xl border border-white/6 p-6 flex flex-col items-center" style={{ background: 'rgba(13,20,40,0.6)' }}>
          <h3 className="text-sm font-bold text-white mb-4 self-start">Failure Risk Index</h3>
          {/* Simple circular progress */}
          <div className="relative w-40 h-40 flex items-center justify-center">
            <svg className="w-40 h-40 -rotate-90" viewBox="0 0 160 160">
              <circle cx="80" cy="80" r="60" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="14" />
              <circle cx="80" cy="80" r="60" fill="none" stroke={riskColor(riskMean)} strokeWidth="14"
                strokeDasharray={`${2 * Math.PI * 60 * riskMean} ${2 * Math.PI * 60 * (1 - riskMean)}`}
                strokeLinecap="round"
                style={{ filter: `drop-shadow(0 0 8px ${riskColor(riskMean)})`, transition: 'stroke-dasharray 0.5s ease' }} />
            </svg>
            <div className="absolute flex flex-col items-center">
              <div className="text-4xl font-black font-mono" style={{ color: riskColor(riskMean) }}>{riskPct.toFixed(0)}%</div>
              <div className="text-xs font-bold tracking-widest mt-1" style={{ color: riskColor(riskMean) }}>{level}</div>
            </div>
          </div>
          <div className="mt-4 w-full space-y-1.5">
            {[
              ['Mean Risk', `${(riskMean * 100).toFixed(1)}%`],
              ['Peak Risk', `${(riskMax * 100).toFixed(1)}%`],
              ['Behav. Shift', bsi.toFixed(4)],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between text-xs font-mono px-1">
                <span className="text-gray-600">{k}</span>
                <span className="text-gray-300 font-bold">{v}</span>
              </div>
            ))}
          </div>
          {/* Trend */}
          <div className="mt-3 flex items-center gap-2 px-3 py-2 rounded-xl w-full justify-center border"
            style={{ borderColor: trend > 0.05 ? 'rgba(255,53,94,0.3)' : trend < -0.05 ? 'rgba(0,234,119,0.3)' : 'rgba(255,255,255,0.07)' }}>
            {trend > 0.05 ? <TrendingUp className="w-4 h-4 text-neon-red" /> : trend < -0.05 ? <TrendingDown className="w-4 h-4 text-neon-green" /> : <Minus className="w-4 h-4 text-gray-500" />}
            <span className="text-xs font-bold" style={{ color: trend > 0.05 ? '#FF355E' : trend < -0.05 ? '#00EA77' : '#6b7280' }}>
              {trend > 0.05 ? 'RISING' : trend < -0.05 ? 'IMPROVING' : 'STABLE'}
            </span>
          </div>
        </div>

        {/* Component risk bars */}
        <div className="rounded-2xl border border-white/6 p-5 lg:col-span-2" style={{ background: 'rgba(13,20,40,0.6)' }}>
          <h3 className="text-sm font-bold text-white mb-4">Risk by Component — Real Parquet Data</h3>
          <div className="space-y-3">
            {componentData.map(c => (
              <div key={c.name} className="flex items-center gap-3">
                <div className="text-xs text-gray-400 font-semibold w-40 shrink-0">{c.name}</div>
                <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{ width: `${c.value * 100}%`, background: riskColor(c.value) }} />
                </div>
                <div className="text-xs font-black font-mono w-10 text-right" style={{ color: riskColor(c.value) }}>
                  {(c.value * 100).toFixed(0)}%
                </div>
                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border w-20 text-center"
                  style={{ color: riskColor(c.value), borderColor: `${riskColor(c.value)}40`, background: `${riskColor(c.value)}10` }}>
                  {riskLabel(c.value)}
                </span>
              </div>
            ))}
          </div>

          {/* Stacked bar chart */}
          <div className="mt-5">
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={componentData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
                <XAxis type="number" domain={[0, 1]} tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} width={120} />
                <Tooltip contentStyle={{ background: '#0D1428', border: '1px solid rgba(255,53,94,0.2)', borderRadius: 8 }} formatter={(v) => [(Number(v) * 100).toFixed(1) + '%', 'Score']} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {componentData.map((entry, index) => (
                    <rect key={index} fill={riskColor(entry.value)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Risk over time */}
      <div className="rounded-2xl border border-white/6 p-5" style={{ background: 'rgba(13,20,40,0.6)' }}>
        <h3 className="text-sm font-bold text-white mb-1">Risk Score Over Time — {BRIDGE_NAME}</h3>
        <p className="text-xs text-gray-600 font-mono mb-4">Real failure prediction from parquet data</p>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis dataKey="time_start_s" tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={v => `${Number(v).toFixed(0)}s`} />
            <YAxis tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} domain={[0, 1]} />
            <Tooltip contentStyle={{ background: '#0D1428', border: '1px solid rgba(255,53,94,0.2)', borderRadius: 8 }} formatter={(v) => [(Number(v) * 100).toFixed(1) + '%', 'Risk']} />
            <ReferenceLine y={0.4} stroke="#FFDF00" strokeDasharray="4 2" strokeWidth={1.5} label={{ value: 'Moderate', fill: '#FFDF00', fontSize: 9 }} />
            <ReferenceLine y={0.6} stroke="#FF355E" strokeDasharray="4 2" strokeWidth={1.5} label={{ value: 'High', fill: '#FF355E', fontSize: 9 }} />
            <Line type="monotone" dataKey="Predicted_Risk_Score" stroke="#FF355E" strokeWidth={2.5} dot={false} name="Risk Score" />
            <Line type="monotone" dataKey="Autoencoder_Anomaly_Score" stroke="#00D1FF" strokeWidth={1.5} dot={false} strokeDasharray="4 2" name="Anomaly Score" />

          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* AI Conclusion */}
      <AIConclusionPanel
        url={`${API}/api/ai-conclusion/risk/${BRIDGE_ID}`}
        pageLabel="Infrastructure Failure Risk Prediction"
      />
    </div>
  );
}
