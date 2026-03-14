import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

interface LayoutProps {
  home?: boolean;
}

export default function Layout({ home = false }: LayoutProps) {
  const [dark, setDark] = useState(true);

  return (
    <div className="min-h-screen transition-colors duration-300"
      style={{ background: dark ? '#070C18' : '#F0F4FF', color: dark ? '#e2e8f0' : '#1e293b' }}>
      <Navbar dark={dark} setDark={setDark} />
      <div className="pt-16 flex min-h-screen">
        {!home && <Sidebar dark={dark} />}
        <main className={`flex-1 ${!home ? 'lg:ml-60' : ''} overflow-auto`}>
          <Outlet context={{ dark }} />
        </main>
      </div>
    </div>
  );
}
