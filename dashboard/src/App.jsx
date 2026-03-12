import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Activity, AlertTriangle, CheckCircle, ChevronDown, MapPin, Moon, Sun, ShieldAlert } from 'lucide-react';
import { motion } from 'framer-motion';
import './App.css';

const API_URL = "http://localhost:8000";

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

function App() {
  const [bridges, setBridges] = useState([]);
  const [selectedBridge, setSelectedBridge] = useState('');
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Theme state
  const [theme, setTheme] = useState('dark');

  // Initialize theme
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  };

  useEffect(() => {
    // Fetch available bridges
    fetch(`${API_URL}/api/bridges`)
      .then(res => res.json())
      .then(data => {
        if (data.bridges && data.bridges.length > 0) {
          setBridges(data.bridges);
          setSelectedBridge(data.bridges[0]);
        }
      })
      .catch(err => console.error("Failed to load bridges:", err));
  }, []);

  useEffect(() => {
    if (!selectedBridge) return;
    
    setLoading(true);
    fetch(`${API_URL}/api/behavioral-metrics/${selectedBridge}`)
      .then(res => res.json())
      .then(data => {
        if (data.data) {
          setMetrics(data.data);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load metrics:", err);
        setLoading(false);
      });
  }, [selectedBridge]);

  const latestMetrics = metrics.length > 0 ? metrics[metrics.length - 1] : null;

  const getStateBadge = (cluster) => {
    if (cluster === 0) return <span className="badge state-normal"><CheckCircle size={14}/> Normal Baseline</span>;
    if (cluster === 1) return <span className="badge state-warning"><Activity size={14}/> Active Load State</span>;
    if (cluster === 2) return <span className="badge state-danger"><AlertTriangle size={14}/> Altered Dynamics</span>;
    return <span className="badge state-unknown">Unknown State</span>;
  };

  return (
    <div className="dashboard-container">
      <motion.header 
        className="dashboard-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <div className="header-title">
          <div className="logo-icon">
            <Activity color="#3B82F6" size={28} />
          </div>
          <div>
            <h1>Structural Intelligence Platform</h1>
            <p>Behavioral Shift Analysis & Dynamics Monitoring</p>
          </div>
        </div>
        
        <div className="header-controls">
          <div className="bridge-selector">
            <MapPin size={18} className="selector-icon" />
            <select 
              value={selectedBridge} 
              onChange={(e) => setSelectedBridge(e.target.value)}
              className="styled-select"
            >
              {bridges.map(b => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
            <ChevronDown size={18} className="selector-chevron" />
          </div>
          
          <button onClick={toggleTheme} className="theme-toggle" aria-label="Toggle theme">
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
        </div>
      </motion.header>

      {loading ? (
        <div className="loader-container">
           <div className="loader"></div>
           <p>Analyzing structural data...</p>
        </div>
      ) : (
        <main className="dashboard-content">
          
          {/* Top Metrics Cards */}
          <motion.div 
            className="metrics-grid"
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
          >
            <motion.div variants={fadeInUp} className="metric-card glass-panel">
              <div className="metric-header">Behavioral Shift Index</div>
              <div className="metric-value highlight-blue">
                {latestMetrics ? latestMetrics.Behavioral_Shift_Index?.toFixed(4) : "—"}
              </div>
              <div className="metric-footer">Normalized Log-Likelihood Deviation</div>
            </motion.div>

            <motion.div variants={fadeInUp} className="metric-card glass-panel">
              <div className="metric-header">Structural Dynamics Score</div>
              <div className="metric-value highlight-orange">
                {latestMetrics ? latestMetrics.Structural_Dynamics_Score?.toFixed(4) : "—"}
              </div>
              <div className="metric-footer">Isolation Forest Anomaly Ranking</div>
            </motion.div>

            <motion.div variants={fadeInUp} className="metric-card glass-panel">
              <div className="metric-header">Failure Risk Prediction</div>
              <div className="metric-value highlight-red" style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                {latestMetrics?.Predicted_Risk_Score !== undefined ? 
                  (latestMetrics.Predicted_Risk_Score * 100).toFixed(1) + "%" : 
                  (latestMetrics?.forecast_score_next_30d ? (latestMetrics.forecast_score_next_30d * 100).toFixed(1) + "%" : "—")
                }
              </div>
              <div className="metric-footer"><ShieldAlert size={14}/> AI Dynamics Regressor Model</div>
            </motion.div>

            <motion.div variants={fadeInUp} className="metric-card glass-panel">
              <div className="metric-header">Current Behavioral State</div>
              <div className="metric-value state-value">
                {latestMetrics ? getStateBadge(latestMetrics.Behavioral_State_Cluster) : "—"}
              </div>
              <div className="metric-footer">Gaussian Mixture Mode</div>
            </motion.div>

            <motion.div variants={fadeInUp} className="metric-card glass-panel">
              <div className="metric-header">Autoencoder Anomaly Score</div>
              <div className="metric-value highlight-purple">
                {latestMetrics?.Autoencoder_Anomaly_Score !== undefined ? latestMetrics.Autoencoder_Anomaly_Score.toFixed(4) : "—"}
              </div>
              <div className="metric-footer">Neural Net Reconstruction Error</div>
            </motion.div>

            <motion.div variants={fadeInUp} className="metric-card glass-panel">
              <div className="metric-header">System Alert Status</div>
              <div className="metric-value state-value">
                {latestMetrics?.Anomaly_Alert_Flag ? 
                  <span className="badge state-danger"><AlertTriangle size={14}/> ANOMALY DETECTED</span> : 
                  <span className="badge state-normal"><CheckCircle size={14}/> SYSTEM CLEAR</span>}
              </div>
              <div className="metric-footer">Based on 95th Percentile Threshold</div>
            </motion.div>
          </motion.div>

          {/* Charts Area */}
          <motion.div 
            className="charts-grid"
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
          >
            
            <motion.div variants={fadeInUp} className="chart-panel glass-panel">
              <div className="panel-header">
                <h2>Behavioral Shift Over Time</h2>
                <div className="panel-badge">Monitoring Drift</div>
              </div>
              <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={metrics} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorShift" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
                    <XAxis dataKey="time_step" stroke="var(--chart-axis)" tick={{fill: 'var(--chart-axis)', fontSize: 12}} />
                    <YAxis stroke="var(--chart-axis)" tick={{fill: 'var(--chart-axis)', fontSize: 12}} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'var(--chart-tooltip-bg)', borderColor: 'var(--chart-tooltip-border)', borderRadius: '8px', color: 'var(--text-primary)' }}
                      itemStyle={{ color: '#60A5FA' }}
                    />
                    <Area type="monotone" dataKey="Behavioral_Shift_Index" stroke="#3B82F6" strokeWidth={3} fillOpacity={1} fill="url(#colorShift)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </motion.div>

            <motion.div variants={fadeInUp} className="chart-panel glass-panel">
              <div className="panel-header">
                <h2>Structural Dynamics Isolation Score</h2>
                <div className="panel-badge warning">Anomaly Detection</div>
              </div>
              <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={metrics} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
                    <XAxis dataKey="time_step" stroke="var(--chart-axis)" tick={{fill: 'var(--chart-axis)', fontSize: 12}} />
                    <YAxis stroke="var(--chart-axis)" tick={{fill: 'var(--chart-axis)', fontSize: 12}} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'var(--chart-tooltip-bg)', borderColor: 'var(--chart-tooltip-border)', borderRadius: '8px', color: 'var(--text-primary)' }}
                      itemStyle={{ color: '#F6AD55' }}
                    />
                    <Line type="monotone" dataKey="Structural_Dynamics_Score" stroke="#F6AD55" strokeWidth={3} dot={false} activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </motion.div>

            <motion.div variants={fadeInUp} className="chart-panel glass-panel" style={{ gridColumn: '1 / -1' }}>
              <div className="panel-header">
                <h2>Infrastructure Failure Risk Forecast & Autoencoder Error</h2>
                <div className="panel-badge danger">AI Alerting</div>
              </div>
              <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={metrics} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#EF4444" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorAnomaly" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#9333EA" stopOpacity={0.5}/>
                        <stop offset="95%" stopColor="#9333EA" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
                    <XAxis dataKey="time_step" stroke="var(--chart-axis)" tick={{fill: 'var(--chart-axis)', fontSize: 12}} />
                    <YAxis stroke="var(--chart-axis)" tick={{fill: 'var(--chart-axis)', fontSize: 12}} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'var(--chart-tooltip-bg)', borderColor: 'var(--chart-tooltip-border)', borderRadius: '8px', color: 'var(--text-primary)' }}
                    />
                    <Area type="monotone" name="Predicted Failure Risk" dataKey={metrics.length && metrics[0].Predicted_Risk_Score !== undefined ? "Predicted_Risk_Score" : "forecast_score_next_30d"} stroke="#EF4444" strokeWidth={3} fillOpacity={1} fill="url(#colorRisk)" />
                    <Area type="monotone" name="Autoencoder Anomaly" dataKey="Autoencoder_Anomaly_Score" stroke="#9333EA" strokeWidth={2} fillOpacity={1} fill="url(#colorAnomaly)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </motion.div>

          </motion.div>
        </main>
      )}
    </div>
  );
}

export default App;
