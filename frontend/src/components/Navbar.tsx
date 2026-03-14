import { useState, useEffect, useRef } from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import { Activity, BrainCircuit, ShieldAlert, Cpu, MessageSquare, ChevronDown, Sun, Moon, Menu, X, Layers, Radio } from 'lucide-react';

interface Bridge { id: string; name: string; }

export default function Navbar({ dark, setDark }: { dark: boolean; setDark: (d: boolean) => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [bridgesOpen, setBridgesOpen] = useState(false);
  const [featuresOpen, setFeaturesOpen] = useState(false);
  const [bridges, setBridges] = useState<Bridge[]>([]);
  const navigate = useNavigate();
  const bridgeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/bridges')
      .then(r => r.json())
      .then(d => {
        if (d.bridges && d.bridges.length > 0) {
          setBridges(d.bridges.slice(0, 3)); // show first 3; map test_id → name
        }
      })
      .catch(() => {
        // Graceful fallback if backend not running
        setBridges([
          { id: 'B001', name: 'Bridge Alpha' },
          { id: 'B002', name: 'Bridge Beta' },
          { id: 'B003', name: 'Bridge Gamma' },
        ]);
      });
  }, []);

  const moduleLinks = [
    { to: '/dashboard', label: 'Data Fusion', icon: Layers },
    { to: '/dashboard/behavior', label: 'Behavior Analysis', icon: Activity },
    { to: '/dashboard/anomaly', label: 'Anomaly Detection', icon: BrainCircuit },
    { to: '/dashboard/risk', label: 'Risk Prediction', icon: ShieldAlert },
    { to: '/twin', label: 'Digital Twin', icon: Cpu },
    { to: '/assistant', label: 'AI Assistant', icon: MessageSquare },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-16 flex items-center px-6 border-b border-white/5"
      style={{ background: dark ? 'rgba(7,12,24,0.9)' : 'rgba(240,245,255,0.92)', backdropFilter: 'blur(20px)' }}>

      {/* Logo */}
      <Link to="/" className="flex items-center gap-2.5 mr-6 shrink-0">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center border border-[#00D1FF]/40"
          style={{ background: 'rgba(0,209,255,0.1)', boxShadow: '0 0 16px rgba(0,209,255,0.2)' }}>
          <Activity className="w-4 h-4 text-[#00D1FF]" />
        </div>
        <div className="leading-tight">
          <div className={`font-black text-xs tracking-widest uppercase ${dark ? 'text-white' : 'text-slate-800'}`}>AI Structural</div>
          <div className="text-[#00D1FF] text-[9px] font-mono tracking-widest uppercase">Monitoring System</div>
        </div>
      </Link>

      {/* Center Nav */}
      <div className="hidden md:flex items-center gap-0.5 flex-1">

        {/* Bridges dropdown */}
        <div className="relative" ref={bridgeRef}
          onMouseEnter={() => setBridgesOpen(true)}
          onMouseLeave={() => setBridgesOpen(false)}>
          <button className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-[11px] font-bold tracking-wider transition-all ${dark ? 'text-gray-400 hover:text-gray-200 hover:bg-white/5' : 'text-gray-600 hover:text-gray-900 hover:bg-black/5'}`}>
            <Radio className="w-3.5 h-3.5 text-[#00EA77]" />
            BRIDGES
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${bridgesOpen ? 'rotate-180' : ''}`} />
          </button>
          {bridgesOpen && (
            <div className="absolute top-full left-0 mt-1 w-52 rounded-xl border overflow-hidden z-50 shadow-2xl"
              style={{ background: dark ? 'rgba(7,12,24,0.98)' : 'rgba(255,255,255,0.98)', borderColor: dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)', backdropFilter: 'blur(20px)' }}>
              <div className="px-3 py-2 border-b text-[9px] font-bold uppercase tracking-widest text-gray-500" style={{ borderColor: dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)' }}>
                Active Monitoring
              </div>
              {bridges.map((b, i) => {
                const colors = ['#00EA77', '#00D1FF', '#FFDF00'];
                return (
                  <button key={b.id}
                    onClick={() => { navigate(`/dashboard?bridge=${b.id}`); setBridgesOpen(false); }}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 text-xs font-semibold tracking-wide transition-all ${dark ? 'text-gray-300 hover:bg-white/5 hover:text-white' : 'text-gray-700 hover:bg-black/5 hover:text-black'}`}>
                    <span className="w-2 h-2 rounded-full animate-pulse shrink-0" style={{ background: colors[i] }} />
                    <div className="text-left">
                      <div>{b.name}</div>
                      <div className="text-[10px] font-mono" style={{ color: colors[i], opacity: 0.8 }}>{b.id}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Features dropdown */}
        <div className="relative"
          onMouseEnter={() => setFeaturesOpen(true)}
          onMouseLeave={() => setFeaturesOpen(false)}>
          <button className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-[11px] font-bold tracking-wider transition-all ${dark ? 'text-gray-400 hover:text-gray-200 hover:bg-white/5' : 'text-gray-600 hover:text-gray-900 hover:bg-black/5'}`}>
            FEATURES <ChevronDown className={`w-3.5 h-3.5 transition-transform ${featuresOpen ? 'rotate-180' : ''}`} />
          </button>
          {featuresOpen && (
            <div className="absolute top-full left-0 mt-1 w-52 rounded-xl border overflow-hidden z-50 shadow-2xl"
              style={{ background: dark ? 'rgba(7,12,24,0.98)' : 'rgba(255,255,255,0.98)', borderColor: dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)', backdropFilter: 'blur(20px)' }}>
              {moduleLinks.map((item) => (
                <NavLink key={item.to} to={item.to}
                  className={({ isActive }) => `flex items-center gap-3 px-3 py-2.5 text-xs font-semibold tracking-wide transition-all ${isActive ? 'text-[#00D1FF] bg-[#00D1FF]/10' : dark ? 'text-gray-400 hover:bg-white/5 hover:text-white' : 'text-gray-600 hover:bg-black/5 hover:text-black'}`}>
                  <item.icon className="w-3.5 h-3.5" />
                  {item.label}
                </NavLink>
              ))}
            </div>
          )}
        </div>

        <NavLink to="/twin" className={({ isActive }) => `px-3.5 py-2 rounded-lg text-[11px] font-bold tracking-wider transition-all flex items-center gap-1.5 ${isActive ? (dark ? 'bg-white/10 text-white' : 'bg-black/8 text-black') : (dark ? 'text-gray-400 hover:text-gray-200 hover:bg-white/5' : 'text-gray-600 hover:text-gray-900 hover:bg-black/5')}`}>
          <Cpu className="w-3.5 h-3.5" /> DIGITAL TWIN
        </NavLink>
        <NavLink to="/assistant" className={({ isActive }) => `px-3.5 py-2 rounded-lg text-[11px] font-bold tracking-wider transition-all flex items-center gap-1.5 ${isActive ? (dark ? 'bg-white/10 text-white' : 'bg-black/8 text-black') : (dark ? 'text-gray-400 hover:text-gray-200 hover:bg-white/5' : 'text-gray-600 hover:text-gray-900 hover:bg-black/5')}`}>
          <MessageSquare className="w-3.5 h-3.5" /> AI ASSISTANT
        </NavLink>
        <NavLink to="/dashboard" className={({ isActive }) => `px-3.5 py-2 rounded-lg text-[11px] font-bold tracking-wider transition-all flex items-center gap-1.5 ${isActive ? (dark ? 'bg-white/10 text-white' : 'bg-black/8 text-black') : (dark ? 'text-gray-400 hover:text-gray-200 hover:bg-white/5' : 'text-gray-600 hover:text-gray-900 hover:bg-black/5')}`}>
          <ShieldAlert className="w-3.5 h-3.5" /> DASHBOARD
        </NavLink>
      </div>

      {/* Right — dark mode toggle only */}
      <div className="hidden md:flex items-center gap-3 ml-auto">
        <button onClick={() => setDark(!dark)}
          className={`p-2.5 rounded-lg transition-all border ${dark ? 'text-[#FFDF00] border-[#FFDF00]/25 bg-[#FFDF00]/8 hover:bg-[#FFDF00]/15' : 'text-slate-600 border-slate-300 bg-white hover:bg-slate-100'}`}
          title={dark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
          {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>

      {/* Mobile menu toggle */}
      <button className="md:hidden ml-auto" style={{ color: dark ? '#9ca3af' : '#475569' }} onClick={() => setMenuOpen(!menuOpen)}>
        {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {menuOpen && (
        <div className="absolute top-16 left-0 right-0 border-b py-4 px-6 flex flex-col gap-2 z-50"
          style={{ background: dark ? 'rgba(7,12,24,0.98)' : 'rgba(255,255,255,0.98)', borderColor: dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.08)' }}>
          <div className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-1">Bridges</div>
          {bridges.map((b) => (
            <button key={b.id} onClick={() => { navigate(`/dashboard?bridge=${b.id}`); setMenuOpen(false); }}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold tracking-wider ${dark ? 'text-gray-300 hover:bg-white/5' : 'text-gray-700 hover:bg-black/5'}`}>
              <span className="w-2 h-2 rounded-full bg-[#00EA77]" /> {b.name} <span className="text-gray-500 font-mono">({b.id})</span>
            </button>
          ))}
          <div className="border-t my-2" style={{ borderColor: dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)' }} />
          {moduleLinks.map((item) => (
            <NavLink key={item.to} to={item.to} onClick={() => setMenuOpen(false)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-semibold tracking-wider ${dark ? 'text-gray-300 hover:bg-white/5' : 'text-gray-700 hover:bg-black/5'}`}>
              <item.icon className="w-4 h-4" /> {item.label}
            </NavLink>
          ))}
          <div className="flex justify-end pt-2">
            <button onClick={() => setDark(!dark)} className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold border"
              style={{ borderColor: dark ? '#FFDF0040' : '#CBD5E1', color: dark ? '#FFDF00' : '#475569' }}>
              {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              {dark ? 'Light Mode' : 'Dark Mode'}
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
