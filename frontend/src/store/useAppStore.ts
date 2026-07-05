import { create } from 'zustand';
import { User, AppStats } from '../types';

export interface AppState {
  user: User | null;
  stats: AppStats | null;
  isSidebarOpen: boolean;
  isLoading: boolean;
  error: string | null;
  
  setUser: (user: User | null) => void;
  setStats: (stats: AppStats | null) => void;
  setSidebarOpen: (isOpen: boolean) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: { id: '1', name: 'MetaPilot User', email: 'user@metapilot.ai' },
  stats: { totalChats: 12, totalDocuments: 5, activeProviders: 3, pendingTasks: 0 },
  isSidebarOpen: true,
  isLoading: false,
  error: null,
  
  setUser: (user) => set({ user }),
  setStats: (stats) => set({ stats }),
  setSidebarOpen: (isOpen) => set({ isSidebarOpen: isOpen }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));
export interface AuthState {}
export interface ChatState {
  messages: any[];
  addMessage: (msg: any) => void;
  clearMessages: () => void;
  isLoading: boolean;
}
export interface KnowledgeState {
  documents: any[];
}
export interface PluginsState {}
export interface ProvidersState {
  providers: any[];
  activeProvider: string | null;
  removeProvider: (id: string) => void;
}
export interface SettingsState {
  theme: string;
  setTheme: (theme: string) => void;
}
export interface TasksState {
  tasks: any[];
}
export interface UiState {}
