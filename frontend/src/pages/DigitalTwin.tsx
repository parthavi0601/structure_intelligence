import { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { Cpu, AlertTriangle, Wind, Thermometer, Car, ToggleLeft } from 'lucide-react';
import AIConclusionPanel from '../components/AIConclusionPanel';

// ── Bridge 3D Model ──────────────────────────────────────────────────────────
function BridgeModel({ traffic, temp, wind, damaged }: { traffic: number; temp: number; wind: number; damaged: string }) {
  const groupRef = useRef<THREE.Group>(null);
  const deckRef  = useRef<THREE.Mesh>(null);

  const stress = Math.min(1, traffic * 0.006 + Math.abs(temp - 20) * 0.01 + wind * 0.004);
  const stressColor = new THREE.Color().lerpColors(
    new THREE.Color('#00EA77'), new THREE.Color('#FF355E'), stress
  );
  const deflection = traffic * 0.003 + wind * 0.001;

  useFrame((s) => {
    if (deckRef.current) {
      deckRef.current.position.y = -deflection + Math.sin(s.clock.elapsedTime * (8 + wind * 0.05)) * wind * 0.0003;
    }
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(s.clock.elapsedTime * 0.1) * 0.03;
    }
  });

  const pillarColor = (id: string) => damaged === id ? '#FF355E' : '#334155';

  // Pillar positions along the bridge
  const pillars: [number, string][] = [[-4.5, 'P1'], [-1.5, 'P2'], [1.5, 'P3'], [4.5, 'P4']];

  return (
    <group ref={groupRef}>
      {/* Deck */}
      <mesh ref={deckRef} position={[0, 0, 0]}>
        <boxGeometry args={[12, 0.3, 2]} />
        <meshStandardMaterial color="#1e293b" roughness={0.6} metalness={0.3} />
      </mesh>

      {/* Road surface */}
      <mesh position={[0, 0.17, 0]}>
        <boxGeometry args={[12, 0.05, 1.4]} />
        <meshStandardMaterial color="#374151" roughness={0.9} />
      </mesh>

      {/* Lane markings */}
      {[-2.5, 0, 2.5, -2.5, 2.5].map((x, i) => (
        <mesh key={i} position={[x, 0.22, 0]}>
          <boxGeometry args={[1, 0.02, 0.1]} />
          <meshBasicMaterial color="#FFDF00" opacity={0.6} transparent />
        </mesh>
      ))}

      {/* Pillars */}
      {pillars.map(([x, id]) => (
        <mesh key={id} position={[x as number, -2.5, 0]}>
          <boxGeometry args={[0.6, 5, 0.6]} />
          <meshStandardMaterial color={pillarColor(id)} roughness={0.7} emissive={damaged === id ? '#FF355E' : '#000000'} emissiveIntensity={damaged === id ? 0.3 : 0} />
        </mesh>
      ))}

      {/* Towers */}
      {[-3, 3].map((x, i) => (
        <mesh key={i} position={[x, 2.5, 0]}>
          <boxGeometry args={[0.4, 5, 0.4]} />
          <meshStandardMaterial color={stressColor} roughness={0.5} metalness={0.4} />
        </mesh>
      ))}

      {/* Cables */}
      {[-5, -2.5, 0, 2.5, 5].map((x, i) => (
        <group key={i}>
          <mesh position={[x / 2 - 1.5, 1.2, 0]} rotation={[0, 0, Math.atan2(2.5, Math.abs(x - (-3)) * 0.5)]}>
            <cylinderGeometry args={[0.04, 0.04, 3.5, 6]} />
            <meshStandardMaterial color={stressColor} metalness={0.8} roughness={0.2} />
          </mesh>
          <mesh position={[x / 2 + 1.5, 1.2, 0]} rotation={[0, 0, -Math.atan2(2.5, Math.abs(x - 3) * 0.5)]}>
            <cylinderGeometry args={[0.04, 0.04, 3.5, 6]} />
            <meshStandardMaterial color={stressColor} metalness={0.8} roughness={0.2} />
          </mesh>
        </group>
      ))}

      {/* Ground plane */}
      <mesh position={[0, -5.05, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[30, 20]} />
        <meshStandardMaterial color="#0a0f1a" roughness={1} />
      </mesh>
      <gridHelper args={[30, 30, '#0d1a2e', '#0d1a2e']} position={[0, -5, 0]} />
    </group>
  );
}

// ── Mini sparkline ──────────────────────────────────────────────────────────
function Spark({ data, color }: { data: { v: number }[]; color: string }) {
  return (
    <ResponsiveContainer width="100%" height={40}>
      <LineChart data={data}>
        <Line type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────
const SCENARIOS = ['Normal', 'Peak Traffic', 'Storm', 'Extreme Heat', 'Overload', 'Pillar Failure'];

export default function DigitalTwin() {
  const [traffic, setTraffic] = useState(40);
  const [temp, setTemp]       = useState(22);
  const [wind, setWind]       = useState(20);
  const [scenario, setScenario]  = useState('Normal');
  const [damaged, setDamaged]    = useState('none');

  const [deflHistory, setDeflHistory] = useState(() => Array.from({ length: 30 }, (_, i) => ({ v: 1.2 + i * 0.01 })));
  const [riskHistory, setRiskHistory] = useState(() => Array.from({ length: 30 }, (_, i) => ({ v: 18 + i * 0.3 })));

  const stress = Math.min(100, traffic * 0.6 + Math.abs(temp - 20) * 1.0 + wind * 0.4 + (damaged !== 'none' ? 30 : 0));
  const deflection = (traffic * 0.3 + wind * 0.1).toFixed(2);
  const safetyFactor = Math.max(1.05, (4.0 - stress * 0.025)).toFixed(2);
  const stressLabel = stress < 30 ? 'LOW' : stress < 55 ? 'MODERATE' : stress < 75 ? 'HIGH' : 'CRITICAL';
  const stressColor = stress < 30 ? '#00EA77' : stress < 55 ? '#FFDF00' : stress < 75 ? '#FF6B35' : '#FF355E';

  const alerts: string[] = [];
  if (traffic > 80) alerts.push('Overload detected — traffic load exceeds safe threshold');
  if (Math.abs(temp - 20) > 20) alerts.push('Thermal expansion risk — temperature differential extreme');
  if (wind > 80) alerts.push('Wind flutter risk — aerodynamic instability threshold reached');
  if (stress > 70) alerts.push('Structural strain threshold exceeded — immediate inspection required');
  if (damaged !== 'none') alerts.push(`Pillar ${damaged} compromised — load redistributed to adjacent pillars`);

  useEffect(() => {
    const id = setInterval(() => {
      setDeflHistory(d => [...d.slice(1), { v: +(parseFloat(deflection) + (Math.random() - 0.5) * 0.2) }]);
      setRiskHistory(r => [...r.slice(1), { v: +(stress * 0.5 + (Math.random() - 0.5) * 3) }]);
    }, 1500);
    return () => clearInterval(id);
  }, [deflection, stress]);

  const applyScenario = (s: string) => {
    setScenario(s);
    if (s === 'Normal')        { setTraffic(40);  setTemp(22);  setWind(20);  setDamaged('none'); }
    if (s === 'Peak Traffic')  { setTraffic(90);  setTemp(24);  setWind(25);  setDamaged('none'); }
    if (s === 'Storm')         { setTraffic(30);  setTemp(12);  setWind(100); setDamaged('none'); }
    if (s === 'Extreme Heat')  { setTraffic(50);  setTemp(48);  setWind(15);  setDamaged('none'); }
    if (s === 'Overload')      { setTraffic(100); setTemp(28);  setWind(30);  setDamaged('none'); }
    if (s === 'Pillar Failure'){ setTraffic(60);  setTemp(25);  setWind(35);  setDamaged('P2');   }
  };

  const Slider = ({ label, icon: Icon, value, min, max, step, onChange, color, unit }: { label: string; icon: typeof Car; value: number; min: number; max: number; step: number; onChange: (v: number) => void; color: string; unit: string }) => (
    <div>
      <div className="flex justify-between items-center mb-1.5">
        <div className="flex items-center gap-2 text-xs text-gray-400 font-semibold">
          <Icon className="w-3.5 h-3.5" style={{ color }} /> {label}
        </div>
        <span className="text-sm font-black font-mono" style={{ color }}>{value}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full cursor-pointer"
        style={{ accentColor: color }} />
      <div className="flex justify-between text-[10px] text-gray-700 font-mono mt-0.5">
        <span>{min}</span><span>{max}</span>
      </div>
    </div>
  );

  return (
    <div className="p-4 flex flex-col gap-4 grid-bg overflow-y-auto" style={{ minHeight: 'calc(100vh - 64px)' }}>
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(255,223,0,0.1)', border: '1px solid rgba(255,223,0,0.3)' }}>
            <Cpu className="w-4 h-4 text-neon-yellow" />
          </div>
          <div>
            <h1 className="text-lg font-black text-white">Digital Twin Simulation</h1>
            <p className="text-xs text-gray-600">Physics-based structural model · Euler-Bernoulli beam theory</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border text-neon-yellow text-xs font-bold"
          style={{ background: 'rgba(255,223,0,0.07)', borderColor: 'rgba(255,223,0,0.25)' }}>
          <span className="w-1.5 h-1.5 rounded-full bg-neon-yellow animate-pulse" />
          TWIN ACTIVE
        </div>
      </div>

      <div className="flex gap-4 flex-1 min-h-0">
        {/* Left Controls */}
        <div className="w-64 shrink-0 space-y-4 overflow-y-auto">
          {/* Controls */}
          <div className="rounded-2xl border border-white/6 p-4 space-y-4" style={{ background: 'rgba(13,20,40,0.7)' }}>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 border-b border-white/5 pb-2">Simulation Controls</p>
            <Slider label="Traffic Load" icon={Car} value={traffic} min={0} max={100} step={1} onChange={setTraffic} color="#00D1FF" unit="%" />
            <Slider label="Temperature"  icon={Thermometer} value={temp} min={-30} max={65} step={1} onChange={setTemp}    color="#FFDF00" unit="°C" />
            <Slider label="Wind Speed"   icon={Wind} value={wind} min={0} max={150} step={1} onChange={setWind}    color="#00EA77" unit=" km/h" />
          </div>

          {/* Scenarios */}
          <div className="rounded-2xl border border-white/6 p-4" style={{ background: 'rgba(13,20,40,0.7)' }}>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-3">Scenarios</p>
            <div className="space-y-1.5">
              {SCENARIOS.map((s) => (
                <button key={s} onClick={() => applyScenario(s)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold transition-all ${scenario === s ? 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/30' : 'text-gray-400 hover:bg-white/5 border border-transparent'}`}>
                  ▶ {s}
                </button>
              ))}
            </div>
          </div>

          {/* Damaged pillar toggle */}
          <div className="rounded-2xl border border-white/6 p-4" style={{ background: 'rgba(13,20,40,0.7)' }}>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-3">Damage Node</p>
            <div className="grid grid-cols-4 gap-1.5">
              {['none', 'P1', 'P2', 'P3', 'P4'].map((p) => (
                <button key={p} onClick={() => setDamaged(p)}
                  className={`py-1.5 px-2 rounded-lg text-[10px] font-black border transition-all ${damaged === p ? 'bg-neon-red/10 text-neon-red border-neon-red/30' : 'text-gray-500 border-transparent hover:bg-white/5'}`}>
                  {p === 'none' ? '—' : p}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 3D Viewport */}
        <div className="flex-1 rounded-2xl border border-white/6 overflow-hidden relative" style={{ background: '#060b18' }}>
          <Canvas camera={{ position: [10, 5, 14], fov: 45 }} shadows>
            <color attach="background" args={['#060b18']} />
            <fog attach="fog" args={['#060b18', 25, 60]} />
            <ambientLight intensity={0.4} />
            <directionalLight position={[10, 20, 10]} intensity={1.5} color="#ffffff" castShadow />
            <pointLight position={[0, 5, 0]} intensity={0.8} color="#00D1FF" />
            <BridgeModel traffic={traffic} temp={temp} wind={wind} damaged={damaged} />
            <OrbitControls autoRotate={wind > 60} autoRotateSpeed={wind * 0.05} maxPolarAngle={Math.PI / 2} />
          </Canvas>

          {/* Stress legend overlay */}
          <div className="absolute top-3 left-3 rounded-lg border border-white/10 p-3 text-[10px]"
            style={{ background: 'rgba(6,11,24,0.85)', backdropFilter: 'blur(8px)' }}>
            <p className="font-bold text-gray-500 uppercase tracking-widest mb-2">Stress Level</p>
            {[['#00EA77','Low'], ['#FFDF00','Moderate'], ['#FF6B35','High'], ['#FF355E','Critical']].map(([c, l]) => (
              <div key={l} className="flex items-center gap-2 mb-1">
                <div className="w-3 h-2 rounded" style={{ background: c }} />
                <span className="text-gray-400">{l}</span>
              </div>
            ))}
          </div>

          {/* Stress indicator */}
          <div className="absolute top-3 right-3 rounded-lg border p-3 text-center"
            style={{ background: 'rgba(6,11,24,0.85)', backdropFilter: 'blur(8px)', borderColor: `${stressColor}40` }}>
            <div className="text-3xl font-black font-mono" style={{ color: stressColor }}>{stress.toFixed(0)}</div>
            <div className="text-[10px] font-bold uppercase tracking-widest" style={{ color: stressColor }}>{stressLabel}</div>
            <div className="text-[10px] text-gray-600 mt-1">Stress Index</div>
          </div>
        </div>

        {/* Right Panel */}
        <div className="w-56 shrink-0 space-y-4 overflow-y-auto">
          {/* Metrics */}
          <div className="rounded-2xl border border-white/6 p-4" style={{ background: 'rgba(13,20,40,0.7)' }}>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-3">Structural Metrics</p>
            <div className="space-y-3">
              {[
                ['Max Deflection', `${deflection} mm`, stress > 60 ? stressColor : '#fff'],
                ['Safety Factor', safetyFactor, parseFloat(safetyFactor) < 1.5 ? '#FF355E' : '#00EA77'],
                ['Bending Stress', `${(stress * 1.8).toFixed(1)} kPa`, stressColor],
                ['Temperature', `${temp}°C`, '#FFDF00'],
                ['Wind Speed', `${wind} km/h`, '#00EA77'],
                ['Damage Nodes', damaged === 'none' ? '0' : '1', damaged !== 'none' ? '#FF355E' : '#fff'],
              ].map(([k, v, c]) => (
                <div key={k} className="flex justify-between items-end border-b border-white/4 pb-2">
                  <span className="text-[10px] text-gray-500 font-semibold">{k}</span>
                  <span className="text-xs font-black font-mono" style={{ color: c }}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Sparklines */}
          <div className="rounded-2xl border border-white/6 p-4" style={{ background: 'rgba(13,20,40,0.7)' }}>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-1">Deflection History</p>
            <Spark data={deflHistory} color="#00D1FF" />
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mt-3 mb-1">Risk Index History</p>
            <Spark data={riskHistory} color="#FF355E" />
          </div>

          {/* Alerts */}
          <div className="rounded-2xl border border-white/6 p-4" style={{ background: 'rgba(13,20,40,0.7)' }}>
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-3.5 h-3.5 text-neon-red" />
              <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Active Alerts</p>
            </div>
            {alerts.length === 0 ? (
              <p className="text-[10px] text-neon-green font-mono">✓ All systems nominal</p>
            ) : (
              <div className="space-y-2">
                {alerts.map((a, i) => (
                  <div key={i} className="text-[10px] text-neon-red leading-relaxed border-l-2 border-neon-red pl-2">{a}</div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI Conclusion */}
      <AIConclusionPanel
        postBody={{ traffic, temp, wind, stress, damaged, scenario }}
        pageLabel="Digital Twin Simulation"
        deps={[traffic, temp, wind, damaged, scenario]}
      />
    </div>
  );
}
