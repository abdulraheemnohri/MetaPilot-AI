import { create } from 'zustand';

interface AppState {
  isSidebarOpen: boolean;
  isLoading: boolean;
  error: string | null;
  
  setSidebarOpen: (isOpen: boolean) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  isSidebarOpen: true,
  isLoading: false,
  error: null,
  
  setSidebarOpen: (isOpen) => set({ isSidebarOpen: isOpen }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));