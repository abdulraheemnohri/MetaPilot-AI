import { useState } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { useTheme } from '../hooks/useTheme';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';

export function Header() {
  const { user, logout } = useAuthStore();
  const { theme, toggleTheme } = useTheme();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold">MetaPilot AI</h1>
          <Badge variant="secondary">
            {import.meta.env.MODE === 'development' ? 'Dev' : 'Prod'}
          </Badge>
        </div>
        
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? '🌙' : '☀️'}
          </Button>
          
          {user ? (
            <>
              <span className="text-sm font-medium">{user.username}</span>
              <Button variant="outline" onClick={logout}>
                Logout
              </Button>
            </>
          ) : (
            <Button variant="outline">Login</Button>
          )}
        </div>
      </div>
    </header>
  );
}