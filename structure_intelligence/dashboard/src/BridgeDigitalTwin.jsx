import { useState, useEffect, useRef, useCallback } from "react";

const BRIDGE_SEGMENTS = 12;
const SUPPORTS = [0, 3, 6, 9, 12];

function computeDeflection(x, L, load, EI = 1e9) {
  // Simply supported beam with UDL: y = (w*x/(24EI))*(L^3 - 2L*x^2 + x^3)
  const w = load * 1000;
  return (w * x * (Math.pow(L, 3) - 2 * L * x * x + Math.pow(x, 3))) / (24 * EI);
}

function computeStrain(x, L, load) {
  // Bending moment at x: M = w*x*(L-x)/2
  const w = load * 1000;
  const M = (w * x * (L - x)) / 2;
  return M / 1e8; // normalized strain
}

function getRiskColor(risk) {
  if (risk < 30) return "#00ff9d";
  if (risk < 60) return "#ffd700";
  if (risk < 80) return "#ff8c00";
  return "#ff2d55";
}

function getRiskLabel(risk) {
  if (risk < 30) return "NOMINAL";
  if (risk < 60) return "ELEVATED";
  if (risk < 80) return "HIGH";
  return "CRITICAL";
}

function SensorGauge({ label, value, unit, max, color }) {
  const pct = Math.min(value / max, 1);
  const angle = -135 + pct * 270;
  const r = 36;
  const cx = 50, cy = 55;
  const startAngle = -135 * (Math.PI / 180);
  const endAngle = (angle) * (Math.PI / 180);
  const x1 = cx + r * Math.cos(startAngle);
  const y1 = cy + r * Math.sin(startAngle);
  const x2 = cx + r * Math.cos(endAngle);
  const y2 = cy + r * Math.sin(endAngle);
  const largeArc = pct > (270 / 360) ? 1 : 0;

  return (
    <div style={{ textAlign: "center", flex: 1 }}>
      <svg width="100" height="80" viewBox="0 0 100 80">
        <path d={`M ${cx + r * Math.cos(-135 * Math.PI / 180)} ${cy + r * Math.sin(-135 * Math.PI / 180)} A ${r} ${r} 0 1 1 ${cx + r * Math.cos(135 * Math.PI / 180)} ${cy + r * Math.sin(135 * Math.PI / 180)}`}
          fill="none" stroke="#1a1a2e" strokeWidth="6" />
        {pct > 0 && (
          <path d={`M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`}
            fill="none" stroke={color} strokeWidth="6" strokeLinecap="round" />
        )}
        <circle cx={cx} cy={cy} r="4" fill={color} />
        <text x={cx} y={cy - 8} textAnchor="middle" fill={color} fontSize="10" fontFamily="'Courier New', monospace" fontWeight="bold">
          {typeof value === 'number' ? value.toFixed(1) : value}
        </text>
        <text x={cx} y={cy + 2} textAnchor="middle" fill="#666" fontSize="7" fontFamily="'Courier New', monospace">
          {unit}
        </text>
      </svg>
      <div style={{ fontSize: "10px", color: "#888", fontFamily: "'Courier New', monospace", marginTop: "-8px", letterSpacing: "1px" }}>{label}</div>
    </div>
  );
}

function BridgeViz({ deflections, strains, loadMultiplier, selectedNode, setSelectedNode, time }) {
  const L = BRIDGE_SEGMENTS;
  const W = 700, H = 200;
  const pad = 40;
  const nodeSpacing = (W - pad * 2) / BRIDGE_SEGMENTS;

  const maxDeflect = Math.max(...deflections.map(Math.abs), 1e-6);
  const scale = 55;

  const points = deflections.map((d, i) => ({
    x: pad + i * nodeSpacing,
    y: 90 + (d / maxDeflect) * scale * loadMultiplier,
    strain: strains[i],
    index: i
  }));

  const roadPath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const fillPath = roadPath + ` L ${points[points.length - 1].x} 160 L ${points[0].x} 160 Z`;

  return (
    <div style={{ position: "relative" }}>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ overflow: "visible" }}>
        <defs>
          <linearGradient id="bridgeFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0ff" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#0ff" stopOpacity="0.01" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="redglow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Ground */}
        <rect x={0} y={158} width={W} height={4} fill="#1a1a2e" rx="2" />

        {/* Support pillars */}
        {SUPPORTS.map(s => {
          const p = points[s];
          if (!p) return null;
          return (
            <g key={s}>
              <rect x={p.x - 5} y={p.y} width={10} height={162 - p.y} fill="#0a0a1a" stroke="#00ff9d" strokeWidth="1" />
              <rect x={p.x - 12} y={155} width={24} height={8} fill="#00ff9d" rx="2" />
            </g>
          );
        })}

        {/* Bridge deck fill */}
        <path d={fillPath} fill="url(#bridgeFill)" />

        {/* Strain heatmap on deck */}
        {points.slice(0, -1).map((p, i) => {
          const next = points[i + 1];
          const s = strains[i];
          const intensity = Math.min(s / 0.005, 1);
          const hue = 120 - intensity * 120;
          return (
            <rect key={i}
              x={p.x} y={p.y - 6}
              width={next.x - p.x} height={12}
              fill={`hsla(${hue}, 100%, 50%, ${0.3 + intensity * 0.5})`}
            />
          );
        })}

        {/* Bridge deck line */}
        <path d={roadPath} fill="none" stroke="#00ffff" strokeWidth="3" filter="url(#glow)" />

        {/* Cables / suspenders */}
        {[2, 5, 8, 11].map(i => {
          const p = points[i];
          const top = { x: p.x, y: 20 };
          return (
            <g key={i}>
              <line x1={p.x} y1={p.y} x2={top.x} y2={top.y} stroke="#334" strokeWidth="1.5" strokeDasharray="4,3" />
              <circle cx={top.x} cy={top.y} r="3" fill="#556" />
            </g>
          );
        })}

        {/* Main cable */}
        <path d={`M ${pad} 25 Q ${W / 2} 5 ${W - pad} 25`} fill="none" stroke="#445" strokeWidth="2.5" />

        {/* Nodes */}
        {points.map((p, i) => {
          const s = strains[i];
          const intensity = Math.min(s / 0.005, 1);
          const hue = 120 - intensity * 120;
          const isSelected = selectedNode === i;
          const isSupport = SUPPORTS.includes(i);
          return (
            <g key={i} onClick={() => setSelectedNode(i)} style={{ cursor: "pointer" }}>
              {isSelected && <circle cx={p.x} cy={p.y} r="12" fill="none" stroke="#fff" strokeWidth="1" strokeDasharray="4,3" opacity="0.5">
                <animateTransform attributeName="transform" type="rotate" from={`0 ${p.x} ${p.y}`} to={`360 ${p.x} ${p.y}`} dur="3s" repeatCount="indefinite" />
              </circle>}
              <circle cx={p.x} cy={p.y} r={isSupport ? 7 : 5}
                fill={isSelected ? "#fff" : `hsl(${hue}, 100%, 55%)`}
                stroke={isSelected ? "#fff" : "transparent"}
                strokeWidth="2"
                filter={intensity > 0.6 ? "url(#redglow)" : "url(#glow)"}
              />
            </g>
          );
        })}

        {/* Deflection arrows */}
        {points.filter((_, i) => !SUPPORTS.includes(i)).map((p, idx) => {
          const deflect = deflections[p.index] * loadMultiplier;
          const arrowLen = Math.abs(deflect / maxDeflect) * 20;
          if (arrowLen < 3) return null;
          return (
            <g key={idx}>
              <line x1={p.x} y1={p.y - arrowLen - 5} x2={p.x} y2={p.y - 5}
                stroke="#ff6b6b" strokeWidth="1.5" markerEnd="url(#arrow)" opacity="0.6" />
            </g>
          );
        })}

        <defs>
          <marker id="arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill="#ff6b6b" />
          </marker>
        </defs>

        {/* Load indicator */}
        {loadMultiplier > 1.2 && (
          <text x={W / 2} y={15} textAnchor="middle" fill="#ffd700" fontSize="11"
            fontFamily="'Courier New', monospace" opacity="0.8">
            ▼ LOAD: {loadMultiplier.toFixed(1)}x ▼
          </text>
        )}
      </svg>
    </div>
  );
}

function WaveChart({ data, color, label, height = 60 }) {
  const W = 300, H = height;
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * W},${H - ((v - min) / range) * (H - 10) - 5}`).join(' ');
  return (
    <div>
      <div style={{ fontSize: "10px", color: "#666", fontFamily: "'Courier New', monospace", marginBottom: "4px", letterSpacing: "1px" }}>{label}</div>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`}>
        <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" />
        <line x1={W - 1} y1={0} x2={W - 1} y2={H} stroke={color} strokeWidth="1" opacity="0.5" />
      </svg>
    </div>
  );
}

export default function BridgeDigitalTwin() {
  const [loadMultiplier, setLoadMultiplier] = useState(1.0);
  const [temperature, setTemperature] = useState(25);
  const [damageNode, setDamageNode] = useState(null);
  const [selectedNode, setSelectedNode] = useState(6);
  const [isRunning, setIsRunning] = useState(true);
  const [time, setTime] = useState(0);
  const [history, setHistory] = useState({ deflection: [], strain: [], risk: [] });
  const animRef = useRef();

  const L = BRIDGE_SEGMENTS;
  const xs = Array.from({ length: L + 1 }, (_, i) => i);

  const deflections = xs.map(x => {
    let d = computeDeflection(x, L, loadMultiplier);
    if (damageNode !== null) {
      const dist = Math.abs(x - damageNode);
      if (dist < 2) d *= (1 + (2 - dist) * 0.4);
    }
    const thermalEffect = (temperature - 20) * 0.0001;
    return d + thermalEffect * x * (L - x);
  });

  const strains = xs.map(x => {
    let s = computeStrain(x, L, loadMultiplier);
    if (damageNode !== null) {
      const dist = Math.abs(x - damageNode);
      if (dist < 2) s *= (1 + (2 - dist) * 0.6);
    }
    return Math.abs(s);
  });

  const maxStrain = Math.max(...strains);
  const maxDeflect = Math.max(...deflections.map(Math.abs));
  const riskScore = Math.min(
    (loadMultiplier - 1) * 30 +
    (maxStrain / 0.005) * 40 +
    (temperature > 40 ? (temperature - 40) * 1.5 : 0) +
    (damageNode !== null ? 25 : 0),
    100
  );

  const nodeData = selectedNode !== null ? {
    deflection: (deflections[selectedNode] * 1000).toFixed(3),
    strain: (strains[selectedNode] * 1000).toFixed(4),
    stress: (strains[selectedNode] * 2.1e5).toFixed(1),
    safety: Math.max(0, (100 - riskScore)).toFixed(0)
  } : null;

  useEffect(() => {
    if (!isRunning) return;
    const id = setInterval(() => {
      setTime(t => t + 1);
      setHistory(h => {
        const noise = () => (Math.random() - 0.5) * 0.02;
        return {
          deflection: [...h.deflection.slice(-59), maxDeflect * 1000 + noise()],
          strain: [...h.strain.slice(-59), maxStrain * 1000 + noise()],
          risk: [...h.risk.slice(-59), riskScore + (Math.random() - 0.5) * 2]
        };
      });
    }, 500);
    return () => clearInterval(id);
  }, [isRunning, maxDeflect, maxStrain, riskScore]);

  const riskColor = getRiskColor(riskScore);
  const riskLabel = getRiskLabel(riskScore);

  return (
    <div style={{
      background: "#05050f",
      minHeight: "100vh",
      color: "#ccc",
      fontFamily: "'Courier New', monospace",
      padding: "24px",
      boxSizing: "border-box",
      borderRadius: "16px",
      overflow: "hidden"
    }}>
      {/* Scanline overlay */}
      <div style={{
        position: "absolute", inset: 0, pointerEvents: "none", zIndex: 100,
        backgroundImage: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)"
      }} />

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
        <div>
          <div style={{ fontSize: "10px", color: "#444", letterSpacing: "4px", marginBottom: "4px" }}>AUGENBLICK SYSTEMS · PS-02</div>
          <h1 style={{ margin: 0, fontSize: "22px", color: "#fff", letterSpacing: "2px", fontWeight: 400 }}>
            BRIDGE <span style={{ color: "#00ffff" }}>DIGITAL TWIN</span>
          </h1>
          <div style={{ fontSize: "10px", color: "#555", marginTop: "4px", letterSpacing: "2px" }}>
            STRUCTURAL SIMULATION ENGINE v2.1 · T+{String(time).padStart(4, '0')}s
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: "10px", color: "#555", letterSpacing: "2px", marginBottom: "6px" }}>RISK INDEX</div>
          <div style={{ fontSize: "42px", fontWeight: "bold", color: riskColor, lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>
            {riskScore.toFixed(0)}
          </div>
          <div style={{ fontSize: "11px", color: riskColor, letterSpacing: "4px", marginTop: "2px" }}>{riskLabel}</div>
        </div>
      </div>

      {/* Main bridge viz */}
      <div style={{
        background: "#080820",
        border: `1px solid ${riskColor}22`,
        borderRadius: "4px",
        padding: "20px",
        marginBottom: "16px",
        position: "relative",
        overflow: "hidden"
      }}>
        <div style={{ position: "absolute", top: "12px", left: "16px", fontSize: "9px", color: "#444", letterSpacing: "3px" }}>
          STRUCTURAL DEFORMATION · {loadMultiplier.toFixed(1)}x LOAD · {temperature}°C
        </div>
        <div style={{ marginTop: "16px" }}>
          <BridgeViz
            deflections={deflections}
            strains={strains}
            loadMultiplier={loadMultiplier}
            selectedNode={selectedNode}
            setSelectedNode={setSelectedNode}
            time={time}
          />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: "8px", fontSize: "9px", color: "#444", letterSpacing: "2px" }}>
          <span>■ SUPPORT NODE</span>
          <span style={{ color: "#00ff9d" }}>▬ LOW STRAIN</span>
          <span style={{ color: "#ffd700" }}>▬ MED STRAIN</span>
          <span style={{ color: "#ff2d55" }}>▬ HIGH STRAIN</span>
          <span>CLICK NODE TO INSPECT</span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "16px" }}>
        {/* Controls */}
        <div style={{ background: "#080820", border: "1px solid #1a1a3a", borderRadius: "4px", padding: "16px" }}>
          <div style={{ fontSize: "9px", color: "#444", letterSpacing: "3px", marginBottom: "16px" }}>SIMULATION CONTROLS</div>

          <div style={{ marginBottom: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
              <span style={{ fontSize: "10px", color: "#888" }}>TRAFFIC LOAD</span>
              <span style={{ fontSize: "10px", color: "#00ffff" }}>{loadMultiplier.toFixed(2)}x</span>
            </div>
            <input type="range" min="0.1" max="3.0" step="0.05"
              value={loadMultiplier}
              onChange={e => setLoadMultiplier(parseFloat(e.target.value))}
              style={{ width: "100%", accentColor: "#00ffff", cursor: "pointer" }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "8px", color: "#444", marginTop: "2px" }}>
              <span>0.1x</span><span>NORMAL</span><span>3.0x</span>
            </div>
          </div>

          <div style={{ marginBottom: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
              <span style={{ fontSize: "10px", color: "#888" }}>TEMPERATURE</span>
              <span style={{ fontSize: "10px", color: "#ffd700" }}>{temperature}°C</span>
            </div>
            <input type="range" min="-20" max="60" step="1"
              value={temperature}
              onChange={e => setTemperature(parseInt(e.target.value))}
              style={{ width: "100%", accentColor: "#ffd700", cursor: "pointer" }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "8px", color: "#444", marginTop: "2px" }}>
              <span>-20°C</span><span>NOMINAL</span><span>60°C</span>
            </div>
          </div>

          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "10px", color: "#888", marginBottom: "8px" }}>DAMAGE NODE</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
              {[null, 3, 4, 5, 6, 7, 8, 9].map(n => (
                <button key={n ?? 'none'}
                  onClick={() => setDamageNode(n)}
                  style={{
                    padding: "4px 8px", fontSize: "9px", cursor: "pointer",
                    background: damageNode === n ? (n === null ? "#001a00" : "#1a0000") : "#0a0a1a",
                    border: `1px solid ${damageNode === n ? (n === null ? "#00ff9d" : "#ff2d55") : "#1a1a3a"}`,
                    color: damageNode === n ? (n === null ? "#00ff9d" : "#ff2d55") : "#666",
                    borderRadius: "2px", fontFamily: "'Courier New', monospace"
                  }}>
                  {n === null ? "NONE" : `N${n}`}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={() => setIsRunning(r => !r)}
            style={{
              width: "100%", padding: "8px", cursor: "pointer", fontSize: "10px",
              background: isRunning ? "#001a00" : "#0a0a1a",
              border: `1px solid ${isRunning ? "#00ff9d" : "#1a1a3a"}`,
              color: isRunning ? "#00ff9d" : "#666",
              fontFamily: "'Courier New', monospace", letterSpacing: "2px", borderRadius: "2px"
            }}>
            {isRunning ? "◼ PAUSE SIMULATION" : "▶ RESUME SIMULATION"}
          </button>
        </div>

        {/* Node inspector */}
        <div style={{ background: "#080820", border: "1px solid #1a1a3a", borderRadius: "4px", padding: "16px" }}>
          <div style={{ fontSize: "9px", color: "#444", letterSpacing: "3px", marginBottom: "16px" }}>
            NODE INSPECTOR · {selectedNode !== null ? `N${selectedNode}` : "NONE"}
          </div>
          {nodeData && (
            <>
              <div style={{ display: "flex", justifyContent: "space-around", marginBottom: "16px" }}>
                <SensorGauge label="DEFLECT" value={parseFloat(nodeData.deflection)} unit="mm" max={5} color="#00ffff" />
                <SensorGauge label="STRAIN" value={parseFloat(nodeData.strain)} unit="mε" max={5} color={maxStrain > 0.003 ? "#ff2d55" : "#ffd700"} />
              </div>
              <div style={{ borderTop: "1px solid #1a1a3a", paddingTop: "12px" }}>
                {[
                  ["BENDING STRESS", `${nodeData.stress} kPa`, "#00ffff"],
                  ["SAFETY MARGIN", `${nodeData.safety}%`, nodeData.safety > 40 ? "#00ff9d" : "#ff2d55"],
                  ["LOAD STATE", `${loadMultiplier.toFixed(2)}x NOMINAL`, "#ffd700"],
                  ["SUPPORT", SUPPORTS.includes(selectedNode) ? "YES — FIXED" : "NO — FREE", "#aaa"],
                  ["DAMAGE", damageNode === selectedNode ? "⚠ DEGRADED" : "NOMINAL", damageNode === selectedNode ? "#ff2d55" : "#00ff9d"],
                ].map(([k, v, c]) => (
                  <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                    <span style={{ fontSize: "9px", color: "#555", letterSpacing: "1px" }}>{k}</span>
                    <span style={{ fontSize: "10px", color: c, fontWeight: "bold" }}>{v}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Scenario presets + alerts */}
        <div style={{ background: "#080820", border: "1px solid #1a1a3a", borderRadius: "4px", padding: "16px" }}>
          <div style={{ fontSize: "9px", color: "#444", letterSpacing: "3px", marginBottom: "16px" }}>SCENARIO PRESETS</div>
          {[
            { label: "NOMINAL OPERATION", load: 1.0, temp: 25, dmg: null, color: "#00ff9d" },
            { label: "PEAK TRAFFIC", load: 2.0, temp: 30, dmg: null, color: "#ffd700" },
            { label: "EXTREME HEAT", load: 1.2, temp: 55, dmg: null, color: "#ff8c00" },
            { label: "OVERLOAD EVENT", load: 2.8, temp: 35, dmg: null, color: "#ff2d55" },
            { label: "STRUCTURAL DAMAGE", load: 1.5, temp: 28, dmg: 6, color: "#ff2d55" },
            { label: "WORST CASE", load: 2.5, temp: 50, dmg: 5, color: "#ff0040" },
          ].map(s => (
            <button key={s.label}
              onClick={() => { setLoadMultiplier(s.load); setTemperature(s.temp); setDamageNode(s.dmg); }}
              style={{
                display: "block", width: "100%", textAlign: "left", padding: "8px 10px",
                marginBottom: "6px", cursor: "pointer", fontSize: "9px",
                background: "#0a0a1a", border: `1px solid ${s.color}33`,
                color: s.color, fontFamily: "'Courier New', monospace",
                letterSpacing: "1px", borderRadius: "2px"
              }}>
              ▶ {s.label}
            </button>
          ))}

          {/* Active alerts */}
          <div style={{ borderTop: "1px solid #1a1a3a", marginTop: "12px", paddingTop: "12px" }}>
            <div style={{ fontSize: "9px", color: "#444", letterSpacing: "3px", marginBottom: "8px" }}>ACTIVE ALERTS</div>
            {riskScore < 30 && <div style={{ fontSize: "9px", color: "#00ff9d" }}>✓ All systems nominal</div>}
            {loadMultiplier > 2.0 && <div style={{ fontSize: "9px", color: "#ff2d55", marginBottom: "4px" }}>⚠ OVERLOAD: {loadMultiplier.toFixed(1)}x limit exceeded</div>}
            {temperature > 40 && <div style={{ fontSize: "9px", color: "#ff8c00", marginBottoM: "4px" }}>⚠ THERMAL: expansion risk at {temperature}°C</div>}
            {damageNode !== null && <div style={{ fontSize: "9px", color: "#ff2d55", marginBottom: "4px" }}>⚠ DAMAGE: Node N{damageNode} integrity compromised</div>}
            {maxStrain > 0.003 && <div style={{ fontSize: "9px", color: "#ff8c00", marginBottom: "4px" }}>⚠ STRAIN: Critical level at {(maxStrain * 1000).toFixed(2)}mε</div>}
          </div>
        </div>
      </div>

      {/* Time series charts */}
      <div style={{ background: "#080820", border: "1px solid #1a1a3a", borderRadius: "4px", padding: "16px" }}>
        <div style={{ fontSize: "9px", color: "#444", letterSpacing: "3px", marginBottom: "16px" }}>REAL-TIME SENSOR HISTORY · LAST 30s</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "16px" }}>
          <WaveChart data={history.deflection} color="#00ffff" label="MAX DEFLECTION (mm)" />
          <WaveChart data={history.strain} color="#ffd700" label="MAX STRAIN (mε)" />
          <WaveChart data={history.risk} color={riskColor} label="RISK INDEX" />
        </div>
      </div>

      <div style={{ marginTop: "12px", display: "flex", justifyContent: "space-between", fontSize: "8px", color: "#333", letterSpacing: "2px" }}>
        <span>MODEL: EULER-BERNOULLI BEAM · SIMPLY SUPPORTED · EI=1×10⁹ N·m²</span>
        <span>FEM NODES: {BRIDGE_SEGMENTS + 1} · ΔT: 500ms · SYNTHETIC DATA</span>
      </div>
    </div>
  );
}
