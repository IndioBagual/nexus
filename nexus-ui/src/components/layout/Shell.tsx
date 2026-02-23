import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { CommandBar } from './CommandBar';
import { LayoutDashboard, CheckSquare, Wallet, Shield, BookOpen, Inbox, Search, Bot } from 'lucide-react';
import { CortexDrawer } from './CortexDrawer';



const navItems = [
  { path: '/dashboard', label: 'Cockpit', icon: LayoutDashboard },
  { path: '/chronos', label: 'Chronos', icon: CheckSquare },
  { path: '/treasury', label: 'Treasury', icon: Wallet },
  { path: '/rpg', label: 'RPG', icon: Shield },
  { path: '/library', label: 'Library', icon: BookOpen },
  { path: '/inbox', label: 'Inbox', icon: Inbox },
];

export function Shell() {
  // Função para disparar o evento manualmente caso clique no botão visual
  const [isCortexOpen, setIsCortexOpen] = useState(false);
  
  const triggerCommandBar = () => {
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }));
  };
  return (
    <div className="flex h-screen w-full bg-zinc-950 text-zinc-50 font-sans">
      <CommandBar />
      <CortexDrawer isOpen={isCortexOpen} onClose={() => setIsCortexOpen(false)} />

      {/* Sidebar */}
      <aside className="w-64 border-r border-zinc-800 bg-zinc-900/50 flex flex-col">
        <div className="h-14 flex items-center px-6 border-b border-zinc-800">
          <span className="font-bold tracking-widest text-zinc-100">NEXUS</span>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                  isActive ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50'
                }`
              }
            >
              <item.icon className="w-4 h-4" />
              <span className="text-sm font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="h-14 border-b border-zinc-800 bg-zinc-950/50 flex items-center justify-between px-6">
          <div className="text-sm text-zinc-500">System / Workspace</div>
          <div className="flex items-center gap-4">
            {/* O onClick agora simula o Cmd+K */}
            <button 
              onClick={triggerCommandBar}
              className="flex items-center gap-2 px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-md text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
            >
              <Search className="w-3 h-3" />
              <span>Cmd + K</span>
            </button>

            <button 
              onClick={() => setIsCortexOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-md text-xs text-emerald-400 hover:bg-emerald-500/20 transition-colors font-medium"
            >
              <Bot className="w-3 h-3" />
              <span>Córtex</span>
            </button>

            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" title="API Online" />
          </div>
        </header>

        {/* Outlet */}
        <main className="flex-1 overflow-auto p-6 relative">
          <Outlet />
        </main>
      </div>
    </div>
  );
}