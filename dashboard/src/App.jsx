import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Activity, AlertTriangle, CheckCircle, ChevronDown, MapPin } from 'lucide-react';
import './App.css';

const API_URL = "http://localhost:8000";

function App() {
  const [bridges, setBridges] = useState([]);
  const [selectedBridge, setSelectedBridge] = useState('');
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(false);

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
      <header className="dashboard-header">
        <div className="header-title">
          <div className="logo-icon">
            <Activity color="#60A5FA" size={28} />
          </div>
          <div>
            <h1>Structural Intelligence Platform</h1>
            <p>Behavioral Shift Analysis & Dynamics Monitoring</p>
          </div>
        </div>
        
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
      </header>

      {loading ? (
        <div className="loader-container">
           <div className="loader"></div>
           <p>Analyzing structural data...</p>
        </div>
      ) : (
        <main className="dashboard-content">
          
          {/* Top Metrics Cards */}
          <div className="metrics-grid">
            <div className="metric-card glass-panel">
              <div className="metric-header">Behavioral Shift Index</div>
              <div className="metric-value highlight-blue">
                {latestMetrics ? latestMetrics.Behavioral_Shift_Index?.toFixed(4) : "—"}
              </div>
              <div className="metric-footer">Normalized Log-Likelihood Deviation</div>
            </div>

            <div className="metric-card glass-panel">
              <div className="metric-header">Structural Dynamics Score</div>
              <div className="metric-value highlight-orange">
                {latestMetrics ? latestMetrics.Structural_Dynamics_Score?.toFixed(4) : "—"}
              </div>
              <div className="metric-footer">Isolation Forest Anomaly Ranking</div>
            </div>

            <div className="metric-card glass-panel">
              <div className="metric-header">Current Behavioral State</div>
              <div className="metric-value state-value">
                {latestMetrics ? getStateBadge(latestMetrics.Behavioral_State_Cluster) : "—"}
              </div>
              <div className="metric-footer">Gaussian Mixture Mode</div>
            </div>

            <div className="metric-card glass-panel">
              <div className="metric-header">Forecast Degradation (30d)</div>
              <div className="metric-value highlight-red">
                {latestMetrics?.forecast_score_next_30d ? (latestMetrics.forecast_score_next_30d * 100).toFixed(1) + "%" : "—"}
              </div>
              <div className="metric-footer">Predicted from historical behavior</div>
            </div>
          </div>

          {/* Charts Area */}
          <div className="charts-grid">
            
            <div className="chart-panel glass-panel">
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
                    <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" vertical={false} />
                    <XAxis dataKey="time_step" stroke="#A0AEC0" tick={{fill: '#A0AEC0', fontSize: 12}} />
                    <YAxis stroke="#A0AEC0" tick={{fill: '#A0AEC0', fontSize: 12}} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1A202C', borderColor: '#2D3748', borderRadius: '8px', color: '#E2E8F0' }}
                      itemStyle={{ color: '#60A5FA' }}
                    />
                    <Area type="monotone" dataKey="Behavioral_Shift_Index" stroke="#3B82F6" strokeWidth={3} fillOpacity={1} fill="url(#colorShift)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="chart-panel glass-panel">
              <div className="panel-header">
                <h2>Structural Dynamics Isolation Score</h2>
                <div className="panel-badge warning">Anomaly Detection</div>
              </div>
              <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={metrics} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" vertical={false} />
                    <XAxis dataKey="time_step" stroke="#A0AEC0" tick={{fill: '#A0AEC0', fontSize: 12}} />
                    <YAxis stroke="#A0AEC0" tick={{fill: '#A0AEC0', fontSize: 12}} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1A202C', borderColor: '#2D3748', borderRadius: '8px', color: '#E2E8F0' }}
                      itemStyle={{ color: '#F6AD55' }}
                    />
                    <Line type="monotone" dataKey="Structural_Dynamics_Score" stroke="#F6AD55" strokeWidth={3} dot={false} activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        </main>
      )}
    </div>
  );
}

export default App;
