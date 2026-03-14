import { NavLink } from 'react-router-dom';
import { Activity, BrainCircuit, ShieldAlert, Cpu, MessageSquare, Layers } from 'lucide-react';

const items = [
  { to: '/dashboard', label: 'Data Fusion', icon: Layers, color: '#00D1FF' },
  { to: '/dashboard/behavior', label: 'Behavior Analysis', icon: Activity, color: '#00EA77' },
  { to: '/dashboard/anomaly', label: 'Anomaly Detection', icon: BrainCircuit, color: '#A855F7' },
  { to: '/dashboard/risk', label: 'Risk Prediction', icon: ShieldAlert, color: '#FF355E' },
  { to: '/twin', label: 'Digital Twin', icon: Cpu, color: '#FFDF00' },
  { to: '/assistant', label: 'AI Assistant', icon: MessageSquare, color: '#60A5FA' },
];

export default function Sidebar({ dark }: { dark: boolean }) {
  const bg = dark ? 'rgba(7,12,24,0.8)' : 'rgba(248,250,255,0.9)';
  const border = dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.07)';

  return (
    <aside className="fixed left-0 top-16 bottom-0 w-60 flex-col hidden lg:flex"
      style={{ background: bg, backdropFilter: 'blur(12px)', borderRight: `1px solid ${border}` }}>

      <div className="p-4" style={{ borderBottom: `1px solid ${border}` }}>
        <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 px-2">Modules</p>
      </div>

      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {items.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.to === '/dashboard'}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold tracking-wider transition-all ${
                isActive
                  ? dark ? 'bg-white/8 text-white border border-white/10' : 'bg-black/6 text-black border border-black/10'
                  : dark ? 'text-gray-500 hover:text-gray-200 hover:bg-white/5' : 'text-gray-500 hover:text-gray-800 hover:bg-black/5'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className="w-4 h-4" style={{ color: isActive ? item.color : undefined }} />
                <span>{item.label}</span>
                {isActive && <span className="ml-auto w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: item.color }} />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-4" style={{ borderTop: `1px solid ${border}` }}>
        <div className="rounded-xl p-3" style={{ background: dark ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.04)', border: `1px solid ${border}` }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">System</span>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-mono text-[#00EA77]">ONLINE</span>
              <span className="w-1.5 h-1.5 rounded-full bg-[#00EA77] animate-pulse" />
            </div>
          </div>
          <div className="space-y-1.5 text-[10px] font-mono">
            {[['API', 'port 8000'], ['Frontend', 'port 5173'], ['Latency', '< 15ms']].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span className="text-gray-600">{k}</span>
                <span className={dark ? 'text-gray-300' : 'text-gray-700'}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
