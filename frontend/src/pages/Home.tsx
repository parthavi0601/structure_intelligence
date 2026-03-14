import { useRef, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { Activity, BrainCircuit, ShieldAlert, Cpu, MessageSquare, Layers, ArrowRight, Github, ExternalLink } from 'lucide-react';

// ─── 3D Globe ────────────────────────────────────────────────────────────────
const NODE_POSITIONS: [number, number, number][] = [
  [1.8, 0.6, 0.8], [-1.5, 0.3, 1.4], [0.3, 1.8, 0.6], [1.2, -1.1, 1.2],
  [-0.9, 1.5, 0.9], [1.6, -0.5, 1.1], [-1.8, -0.7, 0.8], [0.5, -1.9, 0.6],
  [1.0, 1.5, 0.9], [-1.2, -1.4, 1.1], [0.8, 0.2, 1.9], [-0.4, 1.0, 1.8],
  [1.7, 0.8, -0.6], [-0.6, -1.8, 1.0], [1.3, -1.5, -0.6],
];
const NODE_COLORS = ['#00EA77', '#00EA77', '#00EA77', '#FFDF00', '#00EA77', '#FF355E', '#00EA77', '#FFDF00', '#00EA77', '#00EA77', '#FF355E', '#00EA77', '#FFDF00', '#00EA77', '#00EA77'];

function GlobeNode({ pos, color, delay }: { pos: [number, number, number]; color: string; delay: number }) {
  const meshRef = useRef<THREE.Mesh>(null);
  useFrame((s) => {
    if (meshRef.current) {
      meshRef.current.scale.setScalar(1 + Math.sin(s.clock.elapsedTime * 2 + delay) * 0.2);
    }
  });
  const norm = pos.map(v => {
    const l = Math.sqrt(pos[0] ** 2 + pos[1] ** 2 + pos[2] ** 2);
    return v / l * 2.05;
  }) as [number, number, number];
  return (
    <mesh ref={meshRef} position={norm}>
      <sphereGeometry args={[0.05, 8, 8]} />
      <meshBasicMaterial color={color} />
    </mesh>
  );
}

function Globe() {
  const groupRef = useRef<THREE.Group>(null);
  const wireRef = useRef<THREE.Mesh>(null);
  useFrame((s) => {
    if (groupRef.current) groupRef.current.rotation.y = s.clock.elapsedTime * 0.08;
    if (wireRef.current) wireRef.current.rotation.y = -s.clock.elapsedTime * 0.03;
  });

  const linesMat = useMemo(() => new THREE.LineBasicMaterial({ color: '#00D1FF', opacity: 0.08, transparent: true }), []);
  const linesGeo = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const pts: number[] = [];
    for (let i = 0; i < NODE_POSITIONS.length; i++) {
      for (let j = i + 1; j < NODE_POSITIONS.length; j++) {
        const a = NODE_POSITIONS[i], b = NODE_POSITIONS[j];
        const la = Math.sqrt(a[0]**2+a[1]**2+a[2]**2), lb = Math.sqrt(b[0]**2+b[1]**2+b[2]**2);
        const dist = Math.sqrt((a[0]/la*2.05-b[0]/lb*2.05)**2+(a[1]/la*2.05-b[1]/lb*2.05)**2+(a[2]/la*2.05-b[2]/lb*2.05)**2);
        if (dist < 2.0) {
          pts.push(a[0]/la*2.05, a[1]/la*2.05, a[2]/la*2.05, b[0]/lb*2.05, b[1]/lb*2.05, b[2]/lb*2.05);
        }
      }
    }
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    return geo;
  }, []);

  return (
    <group ref={groupRef}>
      {/* Core sphere */}
      <mesh>
        <sphereGeometry args={[2, 64, 64]} />
        <meshStandardMaterial color="#020812" emissive="#001020" roughness={0.8} metalness={0.2} />
      </mesh>
      {/* Wireframe */}
      <mesh ref={wireRef}>
        <sphereGeometry args={[2.01, 32, 32]} />
        <meshBasicMaterial color="#00D1FF" wireframe opacity={0.06} transparent />
      </mesh>
      {/* Connection lines */}
      <lineSegments geometry={linesGeo} material={linesMat} />
      {/* Nodes */}
      {NODE_POSITIONS.map((pos, i) => (
        <GlobeNode key={i} pos={pos} color={NODE_COLORS[i]} delay={i * 0.5} />
      ))}
    </group>
  );
}

// ─── Feature Cards ────────────────────────────────────────────────────────────
const features = [
  {
    icon: Layers, title: 'Multi-Sensor Data Fusion', path: '/dashboard',
    color: '#00D1FF', desc: 'Combine vibration, temperature, strain, and acoustic sensors into a unified health profile.',
  },
  {
    icon: Activity, title: 'Structural Behavior Analysis', path: '/dashboard/behavior',
    color: '#00EA77', desc: 'Analyze structural response patterns over time using frequency-domain techniques.',
  },
  {
    icon: BrainCircuit, title: 'Structural Anomaly Detection', path: '/dashboard/anomaly',
    color: '#A855F7', desc: 'AI models detect abnormal structural patterns like stress concentration and sudden displacement.',
  },
  {
    icon: ShieldAlert, title: 'Failure Risk Prediction', path: '/dashboard/risk',
    color: '#FF355E', desc: 'Predict infrastructure failure probability using historical and real-time response data.',
  },
  {
    icon: Cpu, title: 'Digital Twin Simulation', path: '/twin',
    color: '#FFDF00', desc: 'Interactive 3D simulation of bridges under variable stress, wind, and traffic loads.',
  },
  {
    icon: MessageSquare, title: 'AI Engineering Assistant', path: '/assistant',
    color: '#60A5FA', desc: 'Agentic AI that autonomously interprets structural data and generates engineer insights.',
  },
];

// ─── Home Component ───────────────────────────────────────────────────────────
export default function Home() {
  const nav = useNavigate();
  return (
    <div className="w-full" style={{ background: '#070C18' }}>

      {/* ── Hero ── */}
      <section className="relative w-full" style={{ minHeight: '90vh' }}>
        {/* Background grid */}
        <div className="absolute inset-0 grid-bg opacity-40" />

        {/* Gradient overlays */}
        <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse 80% 60% at 70% 50%, rgba(0,209,255,0.06) 0%, transparent 70%)' }} />
        <div className="absolute bottom-0 left-0 right-0 h-32" style={{ background: 'linear-gradient(to bottom, transparent, #070C18)' }} />

        {/* 3D Canvas */}
        <div className="absolute inset-0" style={{ right: 0, left: '45%' }}>
          <Canvas camera={{ position: [0, 0, 5.5], fov: 50 }}>
            <ambientLight intensity={0.3} />
            <pointLight position={[5, 5, 5]} intensity={1.5} color="#00D1FF" />
            <pointLight position={[-5, -5, 5]} intensity={0.8} color="#00EA77" />
            <Globe />
            <OrbitControls enableZoom={false} enablePan={false} rotateSpeed={0.3} />
          </Canvas>
          {/* Canvas gradient overlay */}
          <div className="absolute inset-0 pointer-events-none"
            style={{ background: 'linear-gradient(to right, #070C18 0%, transparent 30%, transparent 70%, #070C18 100%)' }} />
        </div>

        {/* Hero text */}
        <div className="relative z-10 max-w-7xl mx-auto px-6 flex flex-col justify-center h-full pt-24 pb-20" style={{ minHeight: '90vh' }}>
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-neon-cyan/20 mb-8"
              style={{ background: 'rgba(0,209,255,0.05)' }}>
              <span className="w-2 h-2 rounded-full bg-neon-cyan animate-pulse" />
              <span className="text-neon-cyan text-xs font-mono tracking-widest uppercase">System Online · 24 Sensors Active</span>
            </div>

            <h1 className="text-5xl lg:text-6xl font-black text-white leading-tight tracking-tight mb-2">
              AI Structural
            </h1>
            <h1 className="text-5xl lg:text-6xl font-black leading-tight tracking-tight mb-6"
              style={{ color: 'transparent', backgroundClip: 'text', WebkitBackgroundClip: 'text', backgroundImage: 'linear-gradient(135deg, #00D1FF, #00EA77)' }}>
              Monitoring Platform
            </h1>
            <p className="text-gray-400 text-lg leading-relaxed mb-8 max-w-md">
              Real-Time Infrastructure Intelligence. AI-powered monitoring, predictive maintenance, and digital twin simulation for bridges and critical infrastructure.
            </p>

            <div className="flex flex-wrap gap-4">
              <button onClick={() => nav('/dashboard')}
                className="flex items-center gap-2 px-7 py-3.5 rounded-xl text-sm font-bold tracking-wider text-black transition-all hover:-translate-y-0.5"
                style={{ background: '#00D1FF', boxShadow: '0 0 30px rgba(0,209,255,0.4)' }}>
                Explore Dashboard <ArrowRight className="w-4 h-4" />
              </button>
              <button onClick={() => nav('/twin')}
                className="flex items-center gap-2 px-7 py-3.5 rounded-xl text-sm font-bold tracking-wider text-white border border-white/20 hover:border-white/40 hover:bg-white/5 transition-all">
                View Digital Twin <Cpu className="w-4 h-4" />
              </button>
            </div>

            {/* Stats row */}
            <div className="flex gap-8 mt-12">
              {[['1,200+', 'Bridges Monitored'], ['99.9%', 'Uptime'], ['< 50ms', 'Latency']].map(([v, l]) => (
                <div key={l}>
                  <div className="text-2xl font-black text-white">{v}</div>
                  <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mt-1">{l}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Features Section ── */}
      <section className="py-24 px-6" style={{ background: '#070C18' }}>
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/10 mb-4"
              style={{ background: 'rgba(255,255,255,0.03)' }}>
              <span className="text-xs font-mono text-gray-400 uppercase tracking-widest">Platform Capabilities</span>
            </div>
            <h2 className="text-4xl font-black text-white mb-4">Six Core Modules</h2>
            <p className="text-gray-500 max-w-lg mx-auto">Each module is purpose-built for a specific domain of structural intelligence and predictive infrastructure management.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((f) => (
              <div key={f.path} onClick={() => nav(f.path)}
                className="group cursor-pointer rounded-2xl border border-white/6 p-6 transition-all duration-300 hover:-translate-y-1 relative overflow-hidden"
                style={{ background: 'rgba(13,20,40,0.5)' }}>
                {/* Hover glow */}
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl"
                  style={{ boxShadow: `inset 0 0 40px ${f.color}10` }} />
                <div className="absolute top-0 left-0 right-0 h-px opacity-0 group-hover:opacity-100 transition-opacity"
                  style={{ background: `linear-gradient(to right, transparent, ${f.color}, transparent)` }} />

                <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-5 transition-transform group-hover:scale-110"
                  style={{ background: `${f.color}15`, border: `1px solid ${f.color}30` }}>
                  <f.icon className="w-5 h-5" style={{ color: f.color }} />
                </div>

                <h3 className="text-white font-bold text-base mb-3 group-hover:text-opacity-90">{f.title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed mb-5">{f.desc}</p>

                <div className="flex items-center gap-1 text-xs font-bold tracking-wider"
                  style={{ color: f.color }}>
                  Open Module <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/5 py-12 px-6" style={{ background: 'rgba(0,0,0,0.4)' }}>
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-start gap-8">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-5 h-5 text-neon-cyan" />
                <span className="text-white font-bold text-sm tracking-widest uppercase">AI Structural Monitoring</span>
              </div>
              <p className="text-sm text-gray-600 max-w-xs">Real-time infrastructure intelligence for bridges and critical assets.</p>
            </div>
            <div className="flex flex-wrap gap-12">
              {[
                ['Platform', ['About', 'Documentation', 'API Reference']],
                ['Legal', ['Terms & Privacy', 'License']],
                ['Contact', ['GitHub', 'Support', 'Contact']]
              ].map(([heading, links]) => (
                <div key={String(heading)}>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-gray-600 mb-3">{String(heading)}</p>
                  <div className="space-y-2">
                    {(links as string[]).map((l) => (
                      <a key={l} href="#" className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-200 transition-colors">
                        {l === 'GitHub' && <Github className="w-3.5 h-3.5" />}
                        {l}
                      </a>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="border-t border-white/5 mt-8 pt-6 text-center">
            <p className="text-xs text-gray-700 font-mono">© 2026 AI Structural Monitoring Platform · Built for Engineers</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
