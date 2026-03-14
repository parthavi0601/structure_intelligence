import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Bot, User, Cpu, FileDown } from 'lucide-react';


interface Msg { id: string; role: 'user' | 'ai'; text: string; ts: string; }

const presets = [
  "What is the current structural health of Bridge B-07?",
  "Why is the risk index increasing over the last 3 months?",
  "Explain the anomaly detected at Node N-12.",
  "What maintenance actions do you recommend for the East deck?",
  "Predict the failure time given current degradation rate.",
];

const aiReply = (q: string): string => {
  const ql = q.toLowerCase();
  if (ql.includes('health') || ql.includes('b-07')) return "🔍 **Bridge B-07 Structural Health Report (Live)**\n\nOverall Health Index: **72/100** (Moderate)\n\n• **Vibration**: Normal — peak 2.3 mm/s at Node VIB-03\n• **Strain**: Elevated — STR-02 reading 0.42 mε (Warning threshold: 0.40)\n• **Temperature**: 24.1°C — within safe range\n• **Acoustic AE**: No recent high-energy events detected\n\n⚠️ Recommend visual inspection of Pier P-3 expansion joint within 14 days.";
  if (ql.includes('risk index') || ql.includes('increasing')) return "📈 **Risk Index Trend Analysis**\n\nThe risk index has increased from 18% (Jan) to 38% (current) — a **+20 point rise** over 12 months.\n\n**Primary drivers:**\n1. Cumulative fatigue at Deck Plate East (contributing ~12%)\n2. Gradual corrosion of expansion joint #4 (~8%)\n3. Increased peak traffic frequency post-road-diversion (~6%)\n\nAt current rate, **High Risk** threshold (60%) will be reached in ~7 months. Preventive repair of expansion joint is strongly recommended.";
  if (ql.includes('anomaly') || ql.includes('n-12')) return "⚡ **Anomaly Report — Node N-12**\n\nDetected at 02:14 UTC. Autoencoder reconstruction error: **0.31** (threshold: 0.25)\n\n**Pattern Analysis:**\nUnusual 12 Hz harmonic detected in vibration signal — consistent with **loose bearing pad** or **resonance with traffic rhythm**.\n\n**Confidence**: 87.3%\n**Recommended action**: Torque check on bearing assembly at Node N-12. If vibration persists post-inspection, consider structural damper installation.";
  if (ql.includes('maintenance') || ql.includes('east deck')) return "🔧 **Maintenance Recommendations — East Deck**\n\nBased on current sensor data and risk model outputs:\n\n**Immediate (< 30 days):**\n• Replace Expansion Joint #4 (critical wear detected)\n• Reseal micro-cracks at positions D-14 through D-17\n\n**Short-term (< 90 days):**\n• Apply epoxy corrosion inhibitor to exposed rebar at midspan\n• Recalibrate strain gauges STR-03 and STR-07\n\n**Long-term (< 12 months):**\n• Full bearing pad replacement for Piers P-2 through P-4\n• Scheduled load test to verify post-repair stiffness recovery";
  if (ql.includes('predict') || ql.includes('failure time')) return "🧮 **Failure Prediction Model Output**\n\nUsing LSTM time-series regression with 36-month training data:\n\n| Scenario | P50 Estimate | P90 Estimate |\n|---|---|---|\n| No maintenance | **14 months** | 8 months |\n| Minor repair | **28 months** | 19 months |\n| Major rehabilitation | **9+ years** | 6 years |\n\n⚠️ Model confidence: **82%** (high). Key uncertainty: traffic load growth rate.\n\n**Recommendation**: Prioritize expansion joint replacement + pier inspection to extend service life by 2-3x.";
  return `🤖 **AI Engineering Assistant**\n\nAnalyzing your query: *"${q}"*\n\nI have access to real-time sensor streams, anomaly detection outputs, and 36 months of historical structural data.\n\n**Available analyses I can provide:**\n• Structural health scores by component or bridge\n• Anomaly explanations with root-cause hypotheses\n• Maintenance prioritization recommendations\n• Failure probability and lifetime forecasting\n• Digital twin scenario analysis\n\nPlease ask about a specific bridge, sensor, anomaly, or maintenance decision.`;
};

export default function AIAssistant() {
  const [messages, setMessages] = useState<Msg[]>([{
    id: '0', role: 'ai',
    text: "👋 **Welcome, Engineer.**\n\nI am your AI Structural Engineering Assistant, powered by real-time data from 24 active sensors across 8 monitored bridges.\n\nI can help you:\n• Interpret sensor anomalies and structural behavior\n• Assess risk indices and predict failure timelines\n• Recommend maintenance actions\n• Analyze digital twin simulation results\n\nWhat would you like to investigate today?",
    ts: new Date().toLocaleTimeString()
  }]);
  const [input, setInput]   = useState('');
  const [typing, setTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const send = (text: string) => {
    if (!text.trim()) return;
    const userMsg: Msg = { id: Date.now().toString(), role: 'user', text, ts: new Date().toLocaleTimeString() };
    setMessages(m => [...m, userMsg]);
    setInput('');
    setTyping(true);
    setTimeout(() => {
      const reply: Msg = { id: (Date.now() + 1).toString(), role: 'ai', text: aiReply(text), ts: new Date().toLocaleTimeString() };
      setMessages(m => [...m, reply]);
      setTyping(false);
    }, 800 + Math.random() * 700);
  };

  return (
    <div className="p-6 grid-bg min-h-full h-[calc(100vh-64px)] flex flex-col">
      <div className="flex items-center gap-3 mb-5 shrink-0">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(96,165,250,0.1)', border: '1px solid rgba(96,165,250,0.3)' }}>
          <MessageSquare className="w-4 h-4 text-blue-400" />
        </div>
        <div>
          <h1 className="text-xl font-black text-white">Agentic AI Engineering Assistant</h1>
          <p className="text-xs text-gray-500">Powered by structural intelligence · real parquet sensor data · Bridge B001</p>
        </div>
        <div className="ml-auto flex items-center gap-2 px-3 py-1.5 rounded-xl border border-blue-400/25 bg-blue-400/7 text-blue-400 text-xs font-bold">
          <Cpu className="w-3.5 h-3.5" /> AI ONLINE
        </div>
      </div>

      <div className="flex gap-5 flex-1 min-h-0">
        {/* Chat window */}
        <div className="flex-1 flex flex-col rounded-2xl border border-white/6 overflow-hidden" style={{ background: 'rgba(13,20,40,0.6)' }}>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.map((m) => (
              <div key={m.id} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center ${m.role === 'ai' ? 'bg-blue-500/20 border border-blue-500/30' : 'bg-neon-cyan/15 border border-neon-cyan/30'}`}>
                  {m.role === 'ai' ? <Bot className="w-4 h-4 text-blue-400" /> : <User className="w-4 h-4 text-neon-cyan" />}
                </div>
                <div className={`max-w-[80%] ${m.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                  <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-line ${m.role === 'ai'
                    ? 'text-gray-200 rounded-tl-none border border-white/6'
                    : 'text-white rounded-tr-none border border-neon-cyan/20'}`}
                    style={{ background: m.role === 'ai' ? 'rgba(0,0,0,0.3)' : 'rgba(0,209,255,0.08)' }}>
                    {m.text}
                  </div>
                  <span className="text-[10px] text-gray-700 font-mono px-1">{m.ts}</span>
                </div>
              </div>
            ))}
            {typing && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full shrink-0 flex items-center justify-center bg-blue-500/20 border border-blue-500/30">
                  <Bot className="w-4 h-4 text-blue-400" />
                </div>
                <div className="px-4 py-3 rounded-2xl rounded-tl-none border border-white/6 text-sm"
                  style={{ background: 'rgba(0,0,0,0.3)' }}>
                  <div className="flex items-center gap-1.5">
                    {[0, 0.2, 0.4].map((d) => (
                      <div key={d} className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: `${d}s` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-white/5">
            <div className="flex gap-3">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send(input)}
                placeholder="Ask about sensor data, anomalies, maintenance, or risk..."
                className="flex-1 px-4 py-3 rounded-xl text-sm text-white placeholder-gray-600 border border-white/8 focus:border-neon-cyan/30 focus:outline-none transition-colors"
                style={{ background: 'rgba(0,0,0,0.4)' }}
              />
              <button onClick={() => send(input)}
                className="px-5 py-3 rounded-xl text-black text-sm font-bold transition-all hover:-translate-y-0.5 flex items-center gap-2 shrink-0"
                style={{ background: '#00D1FF', boxShadow: '0 0 20px rgba(0,209,255,0.3)' }}>
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Preset queries sidebar */}
        <div className="w-60 shrink-0 space-y-4">
          <div className="rounded-2xl border border-white/6 p-4" style={{ background: 'rgba(13,20,40,0.6)' }}>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-3">Quick Queries</p>
            <div className="space-y-2">
              {presets.map((p, i) => (
                <button key={i} onClick={() => send(p)}
                  className="w-full text-left px-3 py-2.5 rounded-xl border border-white/5 text-xs text-gray-400 hover:text-white hover:border-neon-cyan/20 hover:bg-neon-cyan/5 transition-all leading-relaxed"
                  style={{ background: 'rgba(0,0,0,0.2)' }}>
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Context data cards */}
          <div className="rounded-2xl border border-white/6 p-4" style={{ background: 'rgba(13,20,40,0.6)' }}>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-3">Live Context</p>
            <div className="space-y-2 text-[10px] font-mono">
              {[
                ['Active Sensors', '24', '#00EA77'],
                ['Bridges', '8', '#00D1FF'],
                ['Open Alerts', '3', '#FF355E'],
                ['Avg Health', '74%', '#FFDF00'],
              ].map(([k, v, c]) => (
                <div key={k} className="flex justify-between items-center">
                  <span className="text-gray-600">{k}</span>
                  <span className="font-black" style={{ color: c }}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Download Report */}
          <div className="rounded-2xl border border-white/6 p-4" style={{ background: 'rgba(13,20,40,0.6)' }}>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-3">Health Report</p>
            <a
              href="http://localhost:8000/api/report/B001"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2.5 w-full px-3 py-3 rounded-xl border border-neon-cyan/20 bg-neon-cyan/5 hover:bg-neon-cyan/10 hover:border-neon-cyan/40 transition-all group"
            >
              <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0" style={{ background: 'rgba(0,209,255,0.15)', border: '1px solid rgba(0,209,255,0.3)' }}>
                <FileDown className="w-3.5 h-3.5 text-neon-cyan" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-neon-cyan leading-tight">Download PDF Report</div>
                <div className="text-[10px] text-gray-500 mt-0.5">Bridge B001 · Full Health Analysis</div>
              </div>
            </a>
            <p className="text-[9px] text-gray-600 mt-2 leading-relaxed">Includes metrics, risk trend, recommendations &amp; data sources</p>
          </div>
        </div>
      </div>
    </div>
  );
}
