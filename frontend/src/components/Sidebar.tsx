import { useNavigate, useLocation } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import {
  LayoutDashboard,
  MessageSquare,
  Database,
  Cpu,
  Settings,
  Activity,
  Layers,
  Search
} from 'lucide-react';

export function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isSidebarOpen } = useAppStore();

  const menuItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: MessageSquare, label: 'Chat', path: '/chat' },
    { icon: Layers, label: 'Tasks', path: '/tasks' },
    { icon: Database, label: 'Knowledge', path: '/knowledge' },
    { icon: Cpu, label: 'Providers', path: '/providers' },
    { icon: Search, label: 'Plugins', path: '/plugins' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ];

  if (!isSidebarOpen) return null;

  return (
    <aside className="w-64 bg-card border-r border-border h-[calc(100vh-4rem)] sticky top-16 hidden md:block animate-fade-in">
      <nav className="p-4 space-y-2">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                isActive
                  ? 'bg-primary text-white shadow-lg shadow-primary/20 scale-[1.02]'
                  : 'hover:bg-muted text-muted-foreground hover:text-foreground'
              }`}
            >
              <item.icon size={20} className={isActive ? 'text-white' : 'text-primary'} />
              <span className="font-semibold">{item.label}</span>
            </button>
          );
        })}
      </nav>
      <div className="absolute bottom-8 left-4 right-4 p-4 rounded-2xl bg-gradient-to-br from-primary/5 to-primary/10 border border-primary/10">
        <div className="flex items-center gap-2 mb-2 text-primary">
          <Activity size={16} />
          <span className="text-xs font-bold uppercase tracking-wider">System Status</span>
        </div>
        <div className="text-[10px] text-muted-foreground font-mono">
          CPU: 12% | RAM: 4.2GB
        </div>
      </div>
    </aside>
  );
}
