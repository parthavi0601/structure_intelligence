import { useState, useEffect, useRef } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area, ComposedChart, Bar
} from 'recharts';
import {
  Activity, AlertTriangle, CheckCircle, ChevronDown, MapPin,
  Moon, Sun, ShieldAlert, Cpu, Zap, Send, Bot, User, FileDown
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import BridgeDigitalTwin from './BridgeDigitalTwin';
import './App.css';

const API_URL = "http://localhost:8000";

const EXAMPLE_QUERIES = [
  "Summarize the structural health of monitored assets.",
  "What maintenance action should be prioritized this month?",
  "Show the latest anomaly events.",
  "Which structures show abnormal vibration patterns?",
  "Why was a structure flagged as high risk?",
];

const fadeInUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } }
};
const staggerContainer = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } }
};

function App() {
  const [bridges, setBridges] = useState([]);
  const [selectedBridge, setSelectedBridge] = useState('');
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('behavior');
  const [theme, setTheme] = useState('dark');
  const [tick, setTick] = useState(0);

  const [aiConclusion, setAiConclusion] = useState('');
  const [conclusionLoading, setConclusionLoading] = useState(false);

  const [chatMessages, setChatMessages] = useState([{
    role: 'assistant',
    content: 'Hello, Engineer. I am your AI Structural Intelligence Assistant. Ask me anything about the monitored infrastructure — anomalies, risk scores, maintenance priorities, or behavioral patterns.',
    timestamp: new Date().toLocaleTimeString(),
  }]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Live clock
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  // Theme
  useEffect(() => {
    const saved = localStorage.getItem('theme') || 'dark';
    setTheme(saved);
    document.documentElement.setAttribute('data-theme', saved);
  }, []);

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  };

  // Load bridges
  useEffect(() => {
    fetch(`${API_URL}/api/bridges`)
      .then(r => r.json())
      .then(d => {
        if (d.bridges?.length) { setBridges(d.bridges); setSelectedBridge(d.bridges[0]); }
      })
      .catch(console.error);
  }, []);

  // Load metrics for selected bridge
  useEffect(() => {
    if (!selectedBridge) return;
    setLoading(true);
    fetch(`${API_URL}/api/behavioral-metrics/${selectedBridge}`)
      .then(r => r.json())
      .then(d => { if (d.data) setMetrics(d.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [selectedBridge]);

  // Fetch AI conclusion on tab / bridge change
  useEffect(() => {
    if (!selectedBridge || activeTab === 'twin') return;
    setConclusionLoading(true);
    setAiConclusion('');
    fetch(`${API_URL}/api/agent-conclusion/${activeTab}/${selectedBridge}`)
      .then(r => r.json())
      .then(d => { setAiConclusion(d.conclusion || 'Analysis complete.'); setConclusionLoading(false); })
      .catch(() => { setAiConclusion('Could not retrieve AI analysis.'); setConclusionLoading(false); });
  }, [activeTab, selectedBridge]);

  // Auto-scroll chat
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [chatMessages]);

  const sendChat = async (overrideMsg) => {
    const text = (overrideMsg || chatInput).trim();
    if (!text || chatLoading) return;
    setChatInput('');
    const userMsg = { role: 'user', content: text, timestamp: new Date().toLocaleTimeString() };
    setChatMessages(prev => [...prev, userMsg]);
    setChatLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response || 'No response received.',
        timestamp: new Date().toLocaleTimeString(),
      }]);
    } catch {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Connection error. Ensure the FastAPI server is running on port 8000.',
        timestamp: new Date().toLocaleTimeString(),
      }]);
    }
    setChatLoading(false);
  };

  const latest = metrics.length ? metrics[metrics.length - 1] : null;

  const getStateBadge = (cluster) => {
    if (cluster === 0) return <span className="badge state-normal"><CheckCircle size={12} /> NORMAL BASELINE</span>;
    if (cluster === 1) return <span className="badge state-warning"><Activity size={12} /> ACTIVE LOAD STATE</span>;
    if (cluster === 2) return <span className="badge state-danger"><AlertTriangle size={12} /> ALTERED DYNAMICS</span>;
    return <span className="badge state-unknown">UNKNOWN STATE</span>;
  };

  const TABS = [
    { id: 'behavior', label: 'STRUCTURE BEHAVIOR', icon: <Activity size={14} /> },
    { id: 'anomaly', label: 'ANOMALY DETECTION', icon: <Zap size={14} /> },
    { id: 'risk', label: 'RISK PREDICTION', icon: <ShieldAlert size={14} /> },
    { id: 'twin', label: 'DIGITAL TWIN', icon: <Cpu size={14} /> },
  ];

  // ─── JSX ────────────────────────────────────────────────────────────────────
  return (
    <div className="dashboard-container">

      {/* Header */}
      <motion.header className="dashboard-header"
        initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
        <div className="header-title">
          <div className="logo-icon"><Activity color="#00ffff" size={26} /></div>
          <div>
            <div className="header-sysline">AUGENBLICK SYSTEMS · PS-02</div>
            <h1>STRUCTURAL <span>INTELLIGENCE</span> PLATFORM</h1>
            <p>BEHAVIORAL SHIFT ANALYSIS &amp; DYNAMICS MONITORING · T+{String(tick).padStart(5, '0')}s</p>
          </div>
        </div>
        <div className="header-controls">
          <div className="bridge-selector">
            <MapPin size={15} className="selector-icon" />
            <select value={selectedBridge} onChange={e => setSelectedBridge(e.target.value)} className="styled-select">
              {bridges.map(b => <option key={b} value={b}>{b}</option>)}
            </select>
            <ChevronDown size={14} className="selector-chevron" />
          </div>
          <button onClick={toggleTheme} className="theme-toggle" aria-label="Toggle theme">
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </motion.header>

      {/* Tabs */}
      <div className="tabs-container">
        {TABS.map(t => (
          <button key={t.id} className={`tab-btn ${activeTab === t.id ? 'active' : ''}`} onClick={() => setActiveTab(t.id)}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* 3-column grid: main content | AI conclusion | chat */}
      <div className={`main-layout-grid ${activeTab === 'twin' ? 'twin-layout' : ''}`}>

        {/* ── Main content column ─────────────────────────── */}
        <div className="analysis-column">
          {loading && activeTab !== 'twin' ? (
            <div className="loader-container">
              <div className="loader" /><p>ANALYZING STRUCTURAL DATA...</p>
            </div>

          ) : activeTab === 'behavior' ? (
            <main className="dashboard-content">
              <motion.div className="metrics-grid" variants={staggerContainer} initial="hidden" animate="visible">
                <motion.div variants={fadeInUp} className="metric-card glass-panel">
                  <div className="metric-header">Behavioral Shift Index</div>
                  <div className="metric-value highlight-blue">{latest?.Behavioral_Shift_Index?.toFixed(4) ?? "—"}</div>
                  <div className="metric-footer">NORMALIZED LOG-LIKELIHOOD DEVIATION</div>
                </motion.div>
                <motion.div variants={fadeInUp} className="metric-card glass-panel">
                  <div className="metric-header">Current Behavioral State</div>
                  <div className="metric-value state-value">{latest ? getStateBadge(latest.Behavioral_State_Cluster) : "—"}</div>
                  <div className="metric-footer">GAUSSIAN MIXTURE MODE</div>
                </motion.div>
                <motion.div variants={fadeInUp} className="metric-card glass-panel">
                  <div className="metric-header">Structural Condition Score</div>
                  <div className="metric-value highlight-blue">{latest?.structural_condition !== undefined ? latest.structural_condition.toFixed(3) : "—"}</div>
                  <div className="metric-footer">CONDITION STATE</div>
                </motion.div>
              </motion.div>
              <motion.div className="charts-grid" variants={staggerContainer} initial="hidden" animate="visible">
                <motion.div variants={fadeInUp} className="chart-panel glass-panel" style={{ gridColumn: '1 / -1' }}>
                  <div className="panel-header">
                    <h2>Behavioral Shift &amp; Degradation Over Time</h2>
                    <div className="panel-badge">MONITORING DRIFT</div>
                  </div>
                  <div className="chart-wrapper">
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={metrics} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <defs>
                          <linearGradient id="gradShift" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#00ffff" stopOpacity={0.35} />
                            <stop offset="95%" stopColor="#00ffff" stopOpacity={0} />
                          </linearGradient>
                          <linearGradient id="gradDeg" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#00ff9d" stopOpacity={0.25} />
                            <stop offset="95%" stopColor="#00ff9d" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
                        <XAxis dataKey="time_step" stroke="var(--chart-axis)" tick={{ fill: 'var(--chart-axis)', fontSize: 10, fontFamily: 'Share Tech Mono' }} />
                        <YAxis stroke="var(--chart-axis)" tick={{ fill: 'var(--chart-axis)', fontSize: 10, fontFamily: 'Share Tech Mono' }} />
                        <Tooltip contentStyle={{ background: 'var(--chart-tooltip-bg)', border: '1px solid var(--chart-tooltip-border)', borderRadius: '2px', fontFamily: 'Share Tech Mono', fontSize: 11, color: 'var(--text-primary)' }} />
                        <Area type="monotone" dataKey="Behavioral_Shift_Index" stroke="#00ffff" strokeWidth={2} fillOpacity={1} fill="url(#gradShift)" name="Behavioral Shift" />
                        <Area type="monotone" dataKey="degradation_score" stroke="#00ff9d" strokeWidth={1.5} fillOpacity={1} fill="url(#gradDeg)" name="Degradation Score" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </motion.div>
              </motion.div>
            </main>

          ) : activeTab === 'anomaly' ? (
            <main className="dashboard-content">
              <motion.div className="metrics-grid" variants={staggerContainer} initial="hidden" animate="visible">
                <motion.div variants={fadeInUp} className="metric-card glass-panel">
                  <div className="metric-header">System Alert Status</div>
                  <div className="metric-value state-value">
                    {latest?.Anomaly_Alert_Flag
                      ? <span className="badge state-danger"><AlertTriangle size={12} /> ANOMALY DETECTED</span>
                      : <span className="badge state-normal"><CheckCircle size={12} /> SYSTEM CLEAR</span>}
                  </div>
                  <div className="metric-footer">BASED ON 95TH PERCENTILE THRESHOLD</div>
                </motion.div>
                <motion.div variants={fadeInUp} className="metric-card glass-panel">
                  <div className="metric-header">Autoencoder Anomaly Score</div>
                  <div className="metric-value highlight-purple">{latest?.Autoencoder_Anomaly_Score !== undefined ? latest.Autoencoder_Anomaly_Score.toFixed(4) : "—"}</div>
                  <div className="metric-footer">NEURAL NET RECONSTRUCTION ERROR</div>
                </motion.div>
                <motion.div variants={fadeInUp} className="metric-card glass-panel">
                  <div className="metric-header">Structural Dynamics Score</div>
                  <div className="metric-value highlight-orange">{latest?.Structural_Dynamics_Score?.toFixed(4) ?? "—"}</div>
                  <div className="metric-footer">ISOLATION FOREST ANOMALY RANKING</div>
                </motion.div>
              </motion.div>
              <motion.div className="charts-grid" variants={staggerContainer} initial="hidden" animate="visible">
                <motion.div variants={fadeInUp} className="chart-panel glass-panel" style={{ gridColumn: '1 / -1' }}>
                  <div className="panel-header">
                    <h2>Structural Dynamics Isolation Score</h2>
                    <div className="panel-badge warning">ANOMALY DETECTION</div>
                  </div>
                  <div className="chart-wrapper">
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={metrics} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
                        <XAxis dataKey="time_step" stroke="var(--chart-axis)" tick={{ fill: 'var(--chart-axis)', fontSize: 10, fontFamily: 'Share Tech Mono' }} />
                        <YAxis stroke="var(--chart-axis)" tick={{ fill: 'var(--chart-axis)', fontSize: 10, fontFamily: 'Share Tech Mono' }} />
                        <Tooltip contentStyle={{ background: 'var(--chart-tooltip-bg)', border: '1px solid var(--chart-tooltip-border)', borderRadius: '2px', fontFamily: 'Share Tech Mono', fontSize: 11, color: 'var(--text-primary)' }} />
                        <Line type="monotone" dataKey="Structural_Dynamics_Score" stroke="#ffd700" strokeWidth={2} dot={false} name="Isolation Forest Score" />
                        <Line type="monotone" dataKey="Autoencoder_Anomaly_Score" stroke="#bf5fff" strokeWidth={1.5} dot={false} name="Autoencoder Error" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </motion.div>
              </motion.div>
            </main>

          ) : activeTab === 'risk' ? (
            <main className="dashboard-content">
              <motion.div className="metrics-grid" variants={staggerContainer} initial="hidden" animate="visible">
                <motion.div variants={fadeInUp} className="metric-card glass-panel" style={{ gridColumn: '1 / span 2' }}>
                  <div className="metric-header">Failure Risk Prediction</div>
                  <div className="metric-value highlight-red">
                    {latest?.Predicted_Risk_Score !== undefined
                      ? (latest.Predicted_Risk_Score * 100).toFixed(1) + "%"
                      : latest?.forecast_score_next_30d
                        ? (latest.forecast_score_next_30d * 100).toFixed(1) + "%"
                        : "—"}
                  </div>
                  <div className="metric-footer"><ShieldAlert size={12} /> AI DYNAMICS REGRESSOR MODEL</div>
                </motion.div>
                <motion.div variants={fadeInUp} className="metric-card glass-panel">
                  <div className="metric-header">30-Day Forecast Delta</div>
                  <div className="metric-value highlight-orange">{latest?.forecast_score_next_30d !== undefined ? latest.forecast_score_next_30d.toFixed(3) : "—"}</div>
                  <div className="metric-footer">TIME SERIES FORECASTING BASELINE</div>
                </motion.div>
              </motion.div>
              <motion.div className="charts-grid" variants={staggerContainer} initial="hidden" animate="visible">
                <motion.div variants={fadeInUp} className="chart-panel glass-panel" style={{ gridColumn: '1 / -1' }}>
                  <div className="panel-header">
                    <h2>Infrastructure Failure Risk Forecast &amp; Confidence Bounds</h2>
                    <div className="panel-badge danger">AI ALERTING</div>
                  </div>
                  <div className="chart-wrapper">
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={metrics} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <defs>
                          <linearGradient id="gradRisk" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ff2d55" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#ff2d55" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
                        <XAxis dataKey="time_step" stroke="var(--chart-axis)" tick={{ fill: 'var(--chart-axis)', fontSize: 10, fontFamily: 'Share Tech Mono' }} />
                        <YAxis stroke="var(--chart-axis)" tick={{ fill: 'var(--chart-axis)', fontSize: 10, fontFamily: 'Share Tech Mono' }} />
                        <Tooltip contentStyle={{ background: 'var(--chart-tooltip-bg)', border: '1px solid var(--chart-tooltip-border)', borderRadius: '2px', fontFamily: 'Share Tech Mono', fontSize: 11, color: 'var(--text-primary)' }} />
                        <Area type="monotone" name="Predicted Failure Risk"
                          dataKey={metrics.length && metrics[0].Predicted_Risk_Score !== undefined ? "Predicted_Risk_Score" : "forecast_score_next_30d"}
                          stroke="#ff2d55" strokeWidth={2} fillOpacity={1} fill="url(#gradRisk)" />
                        <Line type="monotone" name="Baseline Forecast" dataKey="forecast_score_next_30d"
                          stroke="#ffd700" strokeWidth={1.5} strokeDasharray="5 4" dot={false} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </motion.div>
                <motion.div variants={fadeInUp} className="chart-panel glass-panel" style={{ gridColumn: '1 / -1' }}>
                  <div className="panel-header">
                    <h2>Degradation Impact Analysis</h2>
                    <div className="panel-badge warning">CONDITION CORRELATE</div>
                  </div>
                  <div className="chart-wrapper">
                    <ResponsiveContainer width="100%" height={300}>
                      <ComposedChart data={metrics} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
                        <XAxis dataKey="time_step" stroke="var(--chart-axis)" tick={{ fill: 'var(--chart-axis)', fontSize: 10, fontFamily: 'Share Tech Mono' }} />
                        <YAxis yAxisId="left" stroke="var(--chart-axis)" tick={{ fill: 'var(--chart-axis)', fontSize: 10, fontFamily: 'Share Tech Mono' }} />
                        <YAxis yAxisId="right" orientation="right" stroke="var(--chart-axis)" tick={{ fill: 'var(--chart-axis)', fontSize: 10, fontFamily: 'Share Tech Mono' }} />
                        <Tooltip contentStyle={{ background: 'var(--chart-tooltip-bg)', border: '1px solid var(--chart-tooltip-border)', borderRadius: '2px', fontFamily: 'Share Tech Mono', fontSize: 11, color: 'var(--text-primary)' }} />
                        <Bar yAxisId="left" dataKey="degradation_score" barSize={16} fill="#00ffff" fillOpacity={0.5} name="Degradation Magnitude" />
                        <Line yAxisId="right" dataKey="structural_condition" stroke="#ffd700" strokeWidth={2} dot={false} name="Condition" />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </motion.div>
              </motion.div>
            </main>

          ) : (
            <main className="dashboard-content digital-twin-container">
              <BridgeDigitalTwin />
            </main>
          )}
        </div>

        {/* ── AI Conclusion column (middle) ───────────────────── */}
        {activeTab !== 'twin' && (
          <motion.aside className="insights-panel"
            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}>
            <div className="insight-card glass-panel">
              <div className="insight-header">
                <Zap size={18} color="#00ffff" />
                <h3>AI CONCLUSION</h3>
                {conclusionLoading && <div className="conclusion-spinner" />}
              </div>
              <AnimatePresence mode="wait">
                <motion.p
                  key={`${activeTab}-${selectedBridge}`}
                  className="insight-text"
                  initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.4 }}
                >
                  {conclusionLoading
                    ? 'Generating AI analysis...'
                    : aiConclusion || 'Select a bridge and tab to view AI-driven insights.'}
                </motion.p>
              </AnimatePresence>
              <div className="insight-footer">
                {selectedBridge} · {activeTab.toUpperCase()} · Dynamic Structural Intelligence Report
              </div>
            </div>
          </motion.aside>
        )}

        {/* ── Chat Panel column (right) ───────────────────────── */}
        {activeTab !== 'twin' && (
          <motion.aside className="chat-panel-col"
            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.55 }}>
            <div className="chat-panel glass-panel">
              <div className="chat-header">
                <Bot size={18} color="#00ffff" />
                <h3>AI ENGINEERING ASSISTANT</h3>
              </div>

              {/* Example Queries */}
              <div className="example-queries">
                <div className="example-queries-label">EXAMPLE QUERIES</div>
                {EXAMPLE_QUERIES.map((q, i) => (
                  <button key={i} className="example-query-btn" onClick={() => sendChat(q)} disabled={chatLoading}>
                    {q}
                  </button>
                ))}
              </div>

              {/* Download Report Button */}
              <a
                href={`${API_URL}/api/report/${selectedBridge}`}
                target="_blank"
                rel="noreferrer"
                className="report-download-btn"
              >
                <FileDown size={15} />
                Download PDF Health Report — {selectedBridge}
              </a>

              {/* Messages */}
              <div className="chat-messages">
                {chatMessages.map((msg, i) => (
                  <motion.div key={i} className={`chat-message ${msg.role}`}
                    initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
                    <div className="chat-message-avatar">
                      {msg.role === 'assistant'
                        ? <Bot size={14} color="#00ffff" />
                        : <User size={14} color="#94A3B8" />}
                    </div>
                    <div className="chat-message-content">
                      <pre className="chat-message-text">{msg.content}</pre>
                      {/* Auto-render download button if message contains a report URL */}
                      {msg.role === 'assistant' && msg.content.includes('/api/report/') && (() => {
                        const m = msg.content.match(/http:\/\/[^\s]+\/api\/report\/([^\s]+)/);
                        return m ? (
                          <a href={m[0]} target="_blank" rel="noreferrer" className="report-download-btn inline">
                            <FileDown size={13} /> Download PDF Report
                          </a>
                        ) : null;
                      })()}
                      <div className="chat-message-time">{msg.timestamp}</div>
                    </div>
                  </motion.div>
                ))}
                {chatLoading && (
                  <div className="chat-message assistant">
                    <div className="chat-message-avatar"><Bot size={14} color="#00ffff" /></div>
                    <div className="chat-message-content">
                      <div className="chat-typing"><span /><span /><span /></div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Input */}
              <div className="chat-input-row">
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Ask the AI assistant..."
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendChat()}
                  disabled={chatLoading}
                />
                <button className="chat-send-btn" onClick={() => sendChat()}
                  disabled={chatLoading || !chatInput.trim()} aria-label="Send">
                  <Send size={16} />
                </button>
              </div>
            </div>
          </motion.aside>
        )}

      </div>
    </div>
  );
}

export default App;