import { NavLink } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';

export function Sidebar() {
  const { user } = useAuthStore();

  const navItems = [
    { to: '/', label: 'Chat', icon: '💬' },
    { to: '/knowledge', label: 'Knowledge', icon: '📚' },
    { to: '/providers', label: 'Providers', icon: '⚙️' },
    { to: '/plugins', label: 'Plugins', icon: '🔌' },
    { to: '/tasks', label: 'Tasks', icon: '📋' },
    { to: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <aside className="w-64 h-screen border-r border-border bg-background p-4">
      <div className="flex flex-col h-full">
        <div className="mb-8">
          <h2 className="text-xl font-bold">MetaPilot AI</h2>
          {user && <p className="text-sm text-muted-foreground">{user.email}</p>}
        </div>
        
        <nav className="flex-1 space-y-2">
          {navItems.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${
                  isActive 
                    ? 'bg-accent text-accent-foreground font-medium'                     : 'hover:bg-muted text-foreground'
                }`
              }
            >
              <span>{icon}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-2">
          <p className="text-xs text-muted-foreground text-center">
            v1.0.0
          </p>
        </div>
      </div>
    </aside>
  );
}