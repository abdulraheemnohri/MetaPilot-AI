import { create } from 'zustand';

interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  enabled: boolean;
  config?: Record<string, unknown>;
}

interface PluginsState {
  plugins: Plugin[];
  isLoading: boolean;
  
  addPlugin: (plugin: Plugin) => void;
  removePlugin: (id: string) => void;
  updatePlugin: (plugin: Plugin) => void;
  enablePlugin: (id: string) => void;
  disablePlugin: (id: string) => void;
  setPlugins: (plugins: Plugin[]) => void;
  setLoading: (isLoading: boolean) => void;
}

export const usePluginsStore = create<PluginsState>((set) => ({
  plugins: [],
  isLoading: false,
  
  addPlugin: (plugin) => set((state) => ({
    plugins: [...state.plugins, plugin]
  })),
  
  removePlugin: (id) => set((state) => ({
    plugins: state.plugins.filter(p => p.id !== id)
  })),
  
  updatePlugin: (plugin) => set((state) => ({
    plugins: state.plugins.map(p => p.id === plugin.id ? plugin : p)
  })),
  
  enablePlugin: (id) => set((state) => ({
    plugins: state.plugins.map(p => 
      p.id === id ? { ...p, enabled: true } : p
    )
  })),
  
  disablePlugin: (id) => set((state) => ({
    plugins: state.plugins.map(p => 
      p.id === id ? { ...p, enabled: false } : p
    )
  })),
  
  setPlugins: (plugins) => set({ plugins }),
  
  setLoading: (isLoading) => set({ isLoading }),
}));