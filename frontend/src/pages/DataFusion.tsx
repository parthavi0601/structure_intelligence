import { useState, useEffect } from 'react';
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Wifi, RefreshCw } from 'lucide-react';

const API = 'http://localhost:8000';
interface Bridge { id: string; name: string; }

const CHANNELS = [
  { key: 'ch1_g_rms', label: 'CH1 RMS', color: '#00D1FF' },
  { key: 'ch2_g_rms', label: 'CH2 RMS', color: '#00EA77' },
  { key: 'ch3_g_rms', label: 'CH3 RMS', color: '#FFDF00' },
  { key: 'ch4_g_rms', label: 'CH4 RMS', color: '#FF355E' },
  { key: 'ch5_g_rms', label: 'CH5 RMS', color: '#A855F7' },
];

const FREQ_CHANNELS = [
  { key: 'ch1_g_dom_freq_hz', label: 'CH1 Freq', color: '#00D1FF' },
  { key: 'ch3_g_dom_freq_hz', label: 'CH3 Freq', color: '#FFDF00' },
  { key: 'ch5_g_dom_freq_hz', label: 'CH5 Freq', color: '#A855F7' },
];

export default function DataFusion() {
  const [bridges, setBridges] = useState<Bridge[]>([]);
  const [selected, setSelected] = useState('');
  const [data, setData] = useState<Record<string, number>[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/bridges`).then(r => r.json()).then(d => {
      const list: Bridge[] = (d.bridges || []).slice(0, 3);
      setBridges(list);
      if (list.length) setSelected(list[0].id);
    }).catch(() => setSelected('all'));
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    fetch(`${API}/api/sensor/${selected}`).then(r => r.json()).then(d => {
      setData(d.data || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [selected]);

  // Summary stats
  const stats = CHANNELS.map(c => {
    const vals = data.map(d => d[c.key] || 0).filter(v => v > 0);
    const mean = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
    const max  = vals.length ? Math.max(...vals) : 0;
    const status = max > 1.5 ? 'critical' : max > 1.0 ? 'warning' : 'normal';
    return { ...c, mean: mean.toFixed(3), max: max.toFixed(3), status };
  });

  const statusStyle: Record<string, { badge: string; dot: string }> = {
    normal:   { badge: 'text-neon-green bg-neon-green/10 border-neon-green/30',   dot: 'bg-neon-green' },
    warning:  { badge: 'text-neon-yellow bg-neon-yellow/10 border-neon-yellow/30', dot: 'bg-neon-yellow' },
    critical: { badge: 'text-neon-red bg-neon-red/10 border-neon-red/30',          dot: 'bg-neon-red animate-pulse' },
  };

  return (
    <div className="p-6 space-y-6 grid-bg min-h-full">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(0,209,255,0.1)', border: '1px solid rgba(0,209,255,0.3)' }}>
              <Activity className="w-4 h-4 text-neon-cyan" />
            </div>
            <h1 className="text-xl font-black text-white">Multi-Sensor Structural Data Fusion</h1>
          </div>
          <p className="text-sm text-gray-500 ml-10">Real sensor fusion parquet · 5 accelerometer channels · RMS & dominant frequency</p>
        </div>
        <div className="flex items-center gap-2">
          {loading && <RefreshCw className="w-4 h-4 text-neon-cyan animate-spin" />}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-neon-green text-xs font-bold"
            style={{ background: 'rgba(0,234,119,0.07)', borderColor: 'rgba(0,234,119,0.25)' }}>
            <Wifi className="w-3.5 h-3.5" /> LIVE DATA
          </div>
        </div>
      </div>

      {/* Bridge selector */}
      <div className="flex gap-1.5">
        {bridges.map(b => (
          <button key={b.id} onClick={() => setSelected(b.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all ${selected === b.id ? 'text-neon-cyan border-neon-cyan/40 bg-neon-cyan/10' : 'text-gray-500 border-white/8 hover:text-gray-300 hover:bg-white/5'}`}>
            {b.name}
          </button>
        ))}
      </div>

      {/* Channel stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        {stats.map((s) => {
          const st = statusStyle[s.status];
          return (
            <div key={s.key} className="rounded-xl p-3 border border-white/6" style={{ background: 'rgba(13,20,40,0.6)' }}>
              <div className="flex items-center justify-between mb-2">
                <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold border ${st.badge}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${st.dot}`} />
                  {s.status.toUpperCase()}
                </span>
              </div>
              <div className="text-lg font-black text-white font-mono">{s.mean}g</div>
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mt-1">{s.label}</div>
              <div className="text-[10px] font-mono text-gray-600">peak {s.max}g</div>
            </div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Multi-channel RMS */}
        <div className="rounded-2xl border border-white/6 p-5" style={{ background: 'rgba(13,20,40,0.6)' }}>
          <h3 className="text-sm font-bold text-white mb-1">RMS Vibration — All Channels</h3>
          <p className="text-xs text-gray-600 font-mono mb-4">Accelerometer RMS values per time window · g units</p>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="time_start_s" tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={v => `${Number(v).toFixed(0)}s`} />
              <YAxis tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: '#0D1428', border: '1px solid rgba(0,209,255,0.2)', borderRadius: 8 }} />
              {CHANNELS.map(c => (
                <Line key={c.key} type="monotone" dataKey={c.key} stroke={c.color} strokeWidth={1.5} dot={false} name={c.label} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Dominant Frequency */}
        <div className="rounded-2xl border border-white/6 p-5" style={{ background: 'rgba(13,20,40,0.6)' }}>
          <h3 className="text-sm font-bold text-white mb-1">Dominant Frequency — Channels 1/3/5</h3>
          <p className="text-xs text-gray-600 font-mono mb-4">Modal frequency Hz · structural resonance tracking</p>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data}>
              <defs>
                {FREQ_CHANNELS.map(c => (
                  <linearGradient key={c.key} id={c.key + 'g'} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={c.color} stopOpacity={0.3} />
                    <stop offset="100%" stopColor={c.color} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="time_start_s" tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} tickFormatter={v => `${Number(v).toFixed(0)}s`} />
              <YAxis tick={{ fill: '#4b5563', fontSize: 9 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: '#0D1428', border: '1px solid rgba(0,209,255,0.2)', borderRadius: 8 }} />
              {FREQ_CHANNELS.map(c => (
                <Area key={c.key} type="monotone" dataKey={c.key} stroke={c.color} strokeWidth={2} fill={`url(#${c.key}g)`} dot={false} name={c.label} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
