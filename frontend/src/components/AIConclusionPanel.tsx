import { useEffect, useState } from 'react';
import { BrainCircuit, RefreshCw, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

interface AIConclusionProps {
  /** Full API URL to fetch the conclusion from, e.g. http://localhost:8000/api/ai-conclusion/behaviour/test1 */
  url?: string;
  /** For POST requests (Digital Twin): pass the body instead of a URL param */
  postBody?: object;
  /** Override conclusion text directly (skips fetching) */
  staticConclusion?: string;
  /** Override status directly (skips fetching) */
  staticStatus?: 'normal' | 'warning' | 'critical';
  /** Page/section label shown in the header */
  pageLabel?: string;
  /** When deps change, re-fetch (for Digital Twin) */
  deps?: unknown[];
}

const STATUS_CONFIG = {
  normal: {
    color: '#00EA77',
    bg: 'rgba(0,234,119,0.06)',
    border: 'rgba(0,234,119,0.2)',
    Icon: CheckCircle,
    label: 'ALL SYSTEMS NOMINAL',
  },
  warning: {
    color: '#FFDF00',
    bg: 'rgba(255,223,0,0.06)',
    border: 'rgba(255,223,0,0.2)',
    Icon: AlertTriangle,
    label: 'REQUIRES MONITORING',
  },
  critical: {
    color: '#FF355E',
    bg: 'rgba(255,53,94,0.06)',
    border: 'rgba(255,53,94,0.2)',
    Icon: XCircle,
    label: 'ACTION REQUIRED',
  },
};

export default function AIConclusionPanel({
  url,
  postBody,
  staticConclusion,
  staticStatus,
  pageLabel = 'Page',
  deps = [],
}: AIConclusionProps) {
  const [conclusion, setConclusion] = useState('');
  const [status, setStatus] = useState<'normal' | 'warning' | 'critical'>('normal');
  const [loading, setLoading] = useState(false);
  const [dots, setDots] = useState('');

  // Animated dots while loading
  useEffect(() => {
    if (!loading) return;
    const id = setInterval(() => setDots(d => (d.length >= 3 ? '' : d + '.')), 450);
    return () => clearInterval(id);
  }, [loading]);

  // Fetch or apply static
  useEffect(() => {
    if (staticConclusion !== undefined) {
      setConclusion(staticConclusion);
      setStatus(staticStatus ?? 'normal');
      return;
    }
    if (!url && !postBody) return;

    setLoading(true);
    setConclusion('');

    const fetchData = postBody
      ? fetch(url ?? 'http://localhost:8000/api/ai-conclusion/digital-twin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(postBody),
        })
      : fetch(url!);

    fetchData
      .then(r => r.json())
      .then(d => {
        setConclusion(d.conclusion ?? '');
        setStatus(d.status ?? 'normal');
      })
      .catch(() => {
        setConclusion('AI conclusion service is currently unavailable. Please ensure the backend is running.');
        setStatus('normal');
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, staticConclusion, staticStatus, ...deps]);

  const cfg = STATUS_CONFIG[status];
  const StatusIcon = cfg.Icon;

  return (
    <div
      className="rounded-2xl border p-5 space-y-4"
      style={{ background: cfg.bg, borderColor: cfg.border }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: `${cfg.color}18`, border: `1px solid ${cfg.color}40` }}
          >
            <BrainCircuit className="w-4 h-4" style={{ color: cfg.color }} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-black uppercase tracking-widest" style={{ color: cfg.color }}>
                AI Conclusion
              </span>
              <span
                className="text-[9px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wide"
                style={{ color: cfg.color, borderColor: `${cfg.color}40`, background: `${cfg.color}12` }}
              >
                {cfg.label}
              </span>
            </div>
            <p className="text-[10px] text-gray-600 font-mono mt-0.5">{pageLabel} · Parquet data analysis · Real-time AI verdict</p>
          </div>
        </div>

        {loading && (
          <div className="flex items-center gap-1.5 text-xs text-gray-500 font-mono">
            <RefreshCw className="w-3 h-3 animate-spin" />
            Analyzing{dots}
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="h-px" style={{ background: `${cfg.color}20` }} />

      {/* Conclusion text */}
      <div className="space-y-3">
        {loading ? (
          <div className="space-y-2">
            {[100, 90, 75].map(w => (
              <div
                key={w}
                className="h-3 rounded animate-pulse"
                style={{ width: `${w}%`, background: 'rgba(255,255,255,0.05)' }}
              />
            ))}
          </div>
        ) : conclusion ? (
          <p className="text-sm text-gray-300 leading-relaxed font-mono">
            {conclusion.split('⚠').map((part, i) =>
              i === 0 ? (
                <span key={i}>{part}</span>
              ) : (
                <span key={i}>
                  <span style={{ color: cfg.color }}>⚠</span>
                  {part}
                </span>
              )
            )}
          </p>
        ) : (
          <p className="text-xs text-gray-600 italic">No conclusion available — data may still be loading.</p>
        )}
      </div>

      {/* Status footer */}
      {!loading && conclusion && (
        <div className="flex items-center gap-2 pt-1">
          <StatusIcon className="w-3.5 h-3.5 shrink-0" style={{ color: cfg.color }} />
          <span className="text-[10px] font-bold" style={{ color: cfg.color }}>
            AI analysis complete · Based on real parquet sensor data
          </span>
        </div>
      )}
    </div>
  );
}
