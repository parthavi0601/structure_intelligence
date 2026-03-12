import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, ComposedChart, Bar } from 'recharts';
import { Activity, AlertTriangle, CheckCircle, ChevronDown, MapPin, Moon, Sun, ShieldAlert, Cpu, Zap } from 'lucide-react';
import { motion } from 'framer-motion';
import BridgeDigitalTwin from './BridgeDigitalTwin';
import './App.css';

const API_URL = "http://localhost:8000";

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

  // live clock tick for header
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

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

  useEffect(() => {
    fetch(`${API_URL}/api/bridges`)
      .then(r => r.json())
      .then(d => {
        if (d.bridges?.length) { setBridges(d.bridges); setSelectedBridge(d.bridges[0]); }
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedBridge) return;
    setLoading(true);
    fetch(`${API_URL}/api/behavioral-metrics/${selectedBridge}`)
      .then(r => r.json())
      .then(d => { if (d.data) setMetrics(d.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [selectedBridge]);

  const latest = metrics.length ? metrics[metrics.length - 1] : null;

  const getAIInsight = (tab) => {
    if (!latest) return "Collecting structural data...";
    
    switch (tab) {
      case 'behavior':
        const condition = latest.structural_condition || 0;
        const shift = latest.Behavioral_Shift_Index || 0;
        if (condition > 0.9 && shift < 0.05) return "Structural behavior is exceptionally stable. The bridge is perfectly adapting to current traffic loads with minimal drift.";
        if (shift > 0.1) return "A minor behavioral shift is detected. This usually indicates seasonal thermal expansion or regular maintenance needs. No structural integrity risks.";
        return "Stable structural dynamics. The baseline signature remains consistent with historical patterns.";
      
      case 'anomaly':
        const alert = latest.Anomaly_Alert_Flag;
        const score = latest.Autoencoder_Anomaly_Score || 0;
        if (!alert && score < 0.1) return "Anomaly detection systems show no irregularities. All neural network reconstruction errors are within the 'Healthy' threshold.";
        if (alert) return "The system has flagged a secondary dynamic anomaly. While structural health is good, this may indicate sensor noise or a heavy-load vehicle passage.";
        return "Data patterns are clean and consistent. The structural condition remains within normal operating parameters.";
        
      case 'risk':
        const risk = latest.Predicted_Risk_Score || latest.forecast_score_next_30d || 0;
        const degradation = latest.degradation_score || 0;
        // Simple linear extrapolation for "years to survive":
        // Assume failure at risk = 100%. Current risk is 'risk'. 
        // Deg per year is roughly (degradation * 12) if degradation is monthly?
        // Let's assume a healthy bridge survives 50+ years.
        const yearsRemaining = Math.max(5, Math.floor((1 - risk) / (degradation > 0 ? degradation * 0.1 : 0.005)));
        
        if (risk < 0.1) return `High structural reliability. At the current degradation rate of ${(degradation * 100).toFixed(2)}%, the bridge is projected to remain fully operational for over ${yearsRemaining} years.`;
        if (risk < 0.3) return `Moderate health status. Predicted service life is approximately ${yearsRemaining} years. Continued monitoring is recommended for non-critical repairs.`;
        return `Elevated risk profile detected. Projected remaining life is ${yearsRemaining} years. We recommend a physical inspection within the next budget cycle.`;
        
      default: return "Select a tab to view AI-driven structural insights.";
    }
  };

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

  return (
    <div className="dashboard-container">

      {/* ── Header ─────────────────────────────────────────── */}
      <motion.header
        className="dashboard-header"
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="header-title">
          <div className="logo-icon">
            <Activity color="#00ffff" size={26} />
          </div>
          <div>
            <div className="header-sysline">AUGENBLICK SYSTEMS · PS-02</div>
            <h1>STRUCTURAL <span>INTELLIGENCE</span> PLATFORM</h1>
            <p>BEHAVIORAL SHIFT ANALYSIS &amp; DYNAMICS MONITORING · T+{String(tick).padStart(5, '0')}s</p>
          </div>
        </div>

        <div className="header-controls">
          <div className="bridge-selector">
            <MapPin size={15} className="selector-icon" />
            <select
              value={selectedBridge}
              onChange={e => setSelectedBridge(e.target.value)}
              className="styled-select"
            >
              {bridges.map(b => <option key={b} value={b}>{b}</option>)}
            </select>
            <ChevronDown size={14} className="selector-chevron" />
          </div>

          <button onClick={toggleTheme} className="theme-toggle" aria-label="Toggle theme">
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </motion.header>

      {/* ── Tabs ────────────────────────────────────────────── */}
      <div className="tabs-container">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* ── Content ─────────────────────────────────────────── */}
      <div className="main-layout-grid">
        <div className="analysis-column">
          {loading && activeTab !== 'twin' ? (
            <div className="loader-container">
              <div className="loader" />
              <p>ANALYZING STRUCTURAL DATA...</p>
            </div>
          ) : activeTab === 'behavior' ? (
            <main className="dashboard-content">
              <motion.div className="metrics-grid" variants={staggerContainer} initial="hidden" animate="visible">
                <motion.div variants={fadeInUp} className="metric-card glass-panel">
                  <div className="metric-header">Behavioral Shift Index</div>
                  <div className="metric-value highlight-blue">
                    {latest?.Behavioral_Shift_Index?.toFixed(4) ?? "—"}
                  </div>
                  <div className="metric-footer">NORMALIZED LOG-LIKELIHOOD DEVIATION</div>
                </motion.div>
                <motion.div variants={fadeInUp} className="metric-card glass-panel">
                  <div className="metric-header">Current Behavioral State</div>
                  <div className="metric-value state-value">
                    {latest ? getStateBadge(latest.Behavioral_State_Cluster) : "—"}
                  </div>
                  <div className="metric-footer">GAUSSIAN MIXTURE MODE</div>
                </motion.div>
                <motion.div variants={fadeInUp} className="metric-card glass-panel">
                  <div className="metric-header">Structural Condition Score</div>
                  <div className="metric-value highlight-blue">
                    {latest?.structural_condition !== undefined ? latest.structural_condition.toFixed(3) : "—"}
                  </div>
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
                  <div className="metric-value highlight-purple">
                    {latest?.Autoencoder_Anomaly_Score !== undefined ? latest.Autoencoder_Anomaly_Score.toFixed(4) : "—"}
                  </div>
                  <div className="metric-footer">NEURAL NET RECONSTRUCTION ERROR</div>
                </motion.div>
                <motion.div variants={fadeInUp} className="metric-card glass-panel">
                  <div className="metric-header">Structural Dynamics Score</div>
                  <div className="metric-value highlight-orange">
                    {latest?.Structural_Dynamics_Score?.toFixed(4) ?? "—"}
                  </div>
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
                  <div className="metric-value highlight-orange">
                    {latest?.forecast_score_next_30d !== undefined ? latest.forecast_score_next_30d.toFixed(3) : "—"}
                  </div>
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

        {activeTab !== 'twin' && (
          <motion.aside 
            className="insights-panel"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <div className="insight-card glass-panel">
              <div className="insight-header">
                <Zap size={18} color="#00ffff" />
                <h3>AI CONCLUSION</h3>
              </div>
              <p className="insight-text">
                {getAIInsight(activeTab)}
              </p>
              <div className="insight-footer">
                Dynamic Structural Intelligence Report
              </div>
            </div>

            <div className="quick-actions glass-panel">
              <h3>SYSTEM STATS</h3>
              <div className="status-grid">
                <div className="status-item">
                  <span className="label">Uptime</span>
                  <span className="value success">99.9%</span>
                </div>
                <div className="status-item">
                  <span className="label">Sync</span>
                  <span className="value">Active</span>
                </div>
              </div>
            </div>
          </motion.aside>
        )}
      </div>
    </div>
  );
}

export default App;