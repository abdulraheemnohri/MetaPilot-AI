import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Provider {
  id: string;
  name: string;
  type: string;
  apiKey?: string;
  isActive: boolean;
  baseUrl?: string;
  models?: string[];
}

interface ProvidersState {
  providers: Provider[];
  activeProvider: string;
  isLoading: boolean;
  
  addProvider: (provider: Provider) => void;
  removeProvider: (id: string) => void;
  updateProvider: (id: string, updates: Partial<Provider>) => void;
  setActiveProvider: (id: string) => void;
  setProviders: (providers: Provider[]) => void;
  setLoading: (isLoading: boolean) => void;
}

export const useProvidersStore = create<ProvidersState>()(
  persist(
    (set) => ({
      providers: [],
      activeProvider: '',
      isLoading: false,
      
      addProvider: (provider) => set((state) => ({
        providers: [...state.providers, provider],
        activeProvider: state.activeProvider || provider.id
      })),
      
      removeProvider: (id) => set((state) => ({
        providers: state.providers.filter(p => p.id !== id),
        activeProvider: state.activeProvider === id ? '' : state.activeProvider
      })),
      
      updateProvider: (id, updates) => set((state) => ({
        providers: state.providers.map(p => 
          p.id === id ? { ...p, ...updates } : p
        )
      })),
      
      setActiveProvider: (id) => set({ activeProvider: id }),
      
      setProviders: (providers) => set({ providers }),
      
      setLoading: (isLoading) => set({ isLoading }),
    }),
    {
      name: 'providers-storage',
      partialize: (state) => ({
        providers: state.providers,
        activeProvider: state.activeProvider
      })
    }
  )
);