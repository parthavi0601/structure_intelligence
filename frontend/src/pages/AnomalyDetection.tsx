import { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { BrainCircuit, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import AIConclusionPanel from '../components/AIConclusionPanel';

const API = 'http://localhost:8000';
const BRIDGE_ID = 'test1';
const BRIDGE_NAME = 'Bridge B001';

export default function AnomalyDetection() {
  const [data, setData] = useState<Record<string, number>[]>([]);
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/api/anomaly/${BRIDGE_ID}`).then(r => r.json()).then(d => {
      setData(d.data || []);
      setSummary(d.summary || {});
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const isAnomaly = (summary.anomaly_mean || 0) > 0.3;
  const alertCount = summary.alert_count || 0;
  const anomalyMean = summary.anomaly_mean || 0;
  const anomalyMax = summary.anomaly_max || 0;
  const threshold = summary.threshold || 0.5;

  // Alerts from real data
  const alerts: { level: string; msg: string; loc: string }[] = [];
  if (alertCount > 0) {
    alerts.push({ level: 'warning', msg: `${alertCount} anomaly readings exceeded the AI threshold (B001 dataset)`, loc: BRIDGE_NAME });
  }
  if (anomalyMax > 0.7) {
    alerts.push({ level: 'critical', msg: `Peak anomaly score ${(anomalyMax * 100).toFixed(1)}% exceeds critical threshold`, loc: 'Peak Reading' });
  }
  if ((summary.anomaly_mean || 0) > 0.25 && alertCount === 0) {
    alerts.push({ level: 'warning', msg: `Elevated baseline anomaly score (${(anomalyMean * 100).toFixed(1)}%) — watchlist`, loc: 'Baseline' });
  }

  return (
    <div className="p-6 space-y-6 grid-bg min-h-full">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(168,85,247,0.1)', border: '1px solid rgba(168,85,247,0.3)' }}>
              <BrainCircuit className="w-4 h-4 text-neon-purple" />
            </div>
            <h1 className="text-xl font-black text-white">Structural Anomaly Detection</h1>
          </div>
          <p className="text-sm text-gray-500 ml-10">Autoencoder model · B001 failure prediction dataset · real sensor anomaly scores</p>
        </div>

        <div className="flex items-center gap-2">
          {loading && <RefreshCw className="w-4 h-4 text-neon-cyan animate-spin" />}
          <span className="text-xs font-bold px-3 py-1.5 rounded-lg border text-neon-purple border-neon-purple/40 bg-neon-purple/10">
            {BRIDGE_NAME}
          </span>
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-semibold ${isAnomaly ? 'text-neon-red border-neon-red/30 bg-neon-red/10 animate-pulse' : 'text-neon-green border-neon-green/30 bg-neon-green/10'}`}>
            {isAnomaly ? <AlertTriangle className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
            {isAnomaly ? 'ANOMALY DETECTED' : 'NORMAL OPERATION'}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Mean Anomaly Score', value: (anomalyMean * 100).toFixed(1) + '%', alert: anomalyMean > 0.3 },
          { label: 'Peak Anomaly Score', value: (anomalyMax * 100).toFixed(1) + '%', alert: anomalyMax > 0.5 },
          { label: 'AI Threshold', value: (threshold * 100).toFixed(0) + '%', alert: false },
          { label: 'Alert Events', value: String(alertCount), alert: alertCount > 0 },
        ].map(s => (
          <div key={s.label} className="rounded-2xl border border-white/6 p-4" style={{ background: 'rgba(13,20,40,0.6)' }}>
            <div className="text-xs text-gray-500 uppercase tracking-wider font-bold mb-2">{s.label}</div>
            <div className={`text-2xl font-black font-mono ${s.alert ? 'text-neon-red' : 'text-white'}`}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Alert list */}
      {alerts.length > 0 && (
        <div className="rounded-2xl border p-5" style={{ background: 'rgba(255,53,94,0.05)', borderColor: 'rgba(255,53,94,0.2)' }}>
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-4 h-4 text-neon-red" />
            <h3 className="text-sm font-bold text-white">Active Anomaly Alerts — {BRIDGE_NAME}</h3>
          </div>
          <div className="space-y-3">
            {alerts.map((a, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl border border-white/5" style={{ background: 'rgba(0,0,0,0.3)' }}>
                <div className={`w-1 rounded-full self-stretch ${a.level === 'critical' ? 'bg-neon-red' : 'bg-neon-yellow'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${a.level === 'critical' ? 'text-neon-red bg-neon-red/10 border-neon-red/30' : 'text-neon-yellow bg-neon-yellow/10 border-neon-yellow/30'}`}>
                      {a.level.toUpperCase()}
                    </span>
                    <span className="text-[10px] font-mono text-gray-600">{a.loc}</span>
                  </div>
                  <p className="text-sm text-gray-300">{a.msg}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="rounded-2xl border border-white/6 p-5" style={{ background: 'rgba(13,20,40,0.6)' }}>
          <h3 className="text-sm font-bold text-white mb-1">Anomaly Score — Real Data</h3>
          <p className="text-xs text-gray-600 font-mono mb-4">Autoencoder reconstruction score per time window</p>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data}>
              <defs>
                <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#A855F7" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#A855F7" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="time_start_s" tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={v => `${v}s`} />
              <YAxis tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} domain={[0, 1]} />
              <Tooltip contentStyle={{ background: '#0D1428', border: '1px solid rgba(168,85,247,0.2)', borderRadius: 8 }} />
              <ReferenceLine y={threshold} stroke="#FF355E" strokeDasharray="4 2" strokeWidth={1.5} label={{ value: 'Threshold', fill: '#FF355E', fontSize: 9 }} />
              <Area type="monotone" dataKey="Autoencoder_Anomaly_Score" stroke="#A855F7" strokeWidth={2} fill="url(#ag)" dot={false} name="Anomaly Score" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-2xl border border-white/6 p-5" style={{ background: 'rgba(13,20,40,0.6)' }}>
          <h3 className="text-sm font-bold text-white mb-1">Predicted Risk Score</h3>
          <p className="text-xs text-gray-600 font-mono mb-4">AI failure risk prediction over time</p>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data}>
              <defs>
                <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#FF355E" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#FF355E" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="time_start_s" tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={v => `${v}s`} />
              <YAxis tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} domain={[0, 1]} />
              <Tooltip contentStyle={{ background: '#0D1428', border: '1px solid rgba(255,53,94,0.2)', borderRadius: 8 }} />
              <ReferenceLine y={0.4} stroke="#FFDF00" strokeDasharray="4 2" strokeWidth={1.5} />
              <Area type="monotone" dataKey="Predicted_Risk_Score" stroke="#FF355E" strokeWidth={2} fill="url(#rg)" dot={false} name="Risk Score" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* AI Conclusion */}
      <AIConclusionPanel
        url={`${API}/api/ai-conclusion/anomaly/${BRIDGE_ID}`}
        pageLabel="Structural Anomaly Detection"
      />

    </div>
  );
}
