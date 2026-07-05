import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Provider {
  id: string;
  name: string;
  type: string;
  apiKey: string;
  isActive: boolean;
}

interface ProvidersState {
  providers: Provider[];
  activeProvider: string | null;
  addProvider: (provider: Provider) => void;
  removeProvider: (id: string) => void;
  setActiveProvider: (id: string) => void;
}

export const useProvidersStore = create<ProvidersState>()(
  persist(
    (set) => ({
      providers: [],
      activeProvider: null,
      addProvider: (p) => set((s) => ({ providers: [...s.providers, p] })),
      removeProvider: (id) => set((s) => ({ providers: s.providers.filter(p => p.id !== id) })),
      setActiveProvider: (id) => set({ activeProvider: id }),
    }),
    { name: 'providers-store' }
  )
);
