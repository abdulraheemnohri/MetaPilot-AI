"""
MetaPilot AI - Providers Store

AI provider configuration and status state management.
"""

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface ProviderConfig {
  id: string;
  name: string;
  type: string;
  baseUrl?: string;
  apiKey?: string;
  isEnabled: boolean;
  isConfigured: boolean;
  capabilities: string[];
  metadata?: Record<string, any>;
}

interface ProviderStatus {
  id: string;
  isAvailable: boolean;
  isHealthy: boolean;
  lastCheckedAt?: string;
  lastError?: string;
  latency?: number;
}

interface ProviderStats {
  totalCalls: number;
  successfulCalls: number;
  failedCalls: number;
  totalTokens: number;
  totalCost: number;
}

interface ProvidersState {
  // Providers
  providers: ProviderConfig[];
  providerStatuses: Record<string, ProviderStatus>;
  providerStats: Record<string, ProviderStats>;
  
  // Selection
  selectedProviderIds: string[];
  defaultProviderId: string | null;
  
  // State
  isLoading: boolean;
  isTesting: boolean;
  testResults: Record<string, boolean>;
  
  // Actions
  setProviders: (providers: ProviderConfig[]) => void;
  addProvider: (provider: ProviderConfig) => void;
  updateProvider: (id: string, updates: Partial<ProviderConfig>) => void;
  deleteProvider: (id: string) => void;
  setProviderStatus: (id: string, status: ProviderStatus) => void;
  setProviderStats: (id: string, stats: ProviderStats) => void;
  setSelectedProviderIds: (ids: string[]) => void;
  setDefaultProviderId: (id: string | null) => void;
  setIsLoading: (isLoading: boolean) => void;
  setIsTesting: (isTesting: boolean) => void;
  setTestResult: (id: string, result: boolean) => void;
  enableProvider: (id: string) => void;
  disableProvider: (id: string) => void;
  toggleProvider: (id: string) => void;
  reset: () => void;
}

const initialState = {
  providers: [],
  providerStatuses: {},
  providerStats: {},
  selectedProviderIds: [],
  defaultProviderId: null,
  isLoading: false,
  isTesting: false,
  testResults: {},
};

export const useProvidersStore = create<ProvidersState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,
        
        setProviders: (providers) => set({ providers }),
        
        addProvider: (provider) =>
          set((state) => ({
            providers: [...state.providers, provider],
          })),
        
        updateProvider: (id, updates) =>
          set((state) => ({
            providers: state.providers.map((p) =>
              p.id === id ? { ...p, ...updates } : p
            ),
          })),
        
        deleteProvider: (id) =>
          set((state) => ({
            providers: state.providers.filter((p) => p.id !== id),
            selectedProviderIds: state.selectedProviderIds.filter((id) => id !== id),
            defaultProviderId: state.defaultProviderId === id ? null : state.defaultProviderId,
          })),
        
        setProviderStatus: (id, status) =>
          set((state) => ({
            providerStatuses: {
              ...state.providerStatuses,
              [id]: status,
            },
          })),
        
        setProviderStats: (id, stats) =>
          set((state) => ({
            providerStats: {
              ...state.providerStats,
              [id]: stats,
            },
          })),
        
        setSelectedProviderIds: (ids) => set({ selectedProviderIds: ids }),
        
        setDefaultProviderId: (id) => set({ defaultProviderId: id }),
        
        setIsLoading: (isLoading) => set({ isLoading }),
        setIsTesting: (isTesting) => set({ isTesting }),
        setTestResult: (id, result) =>
          set((state) => ({
            testResults: {
              ...state.testResults,
              [id]: result,
            },
          })),
        
        enableProvider: (id) =>
          set((state) => ({
            providers: state.providers.map((p) =>
              p.id === id ? { ...p, isEnabled: true } : p
            ),
          })),
        
        disableProvider: (id) =>
          set((state) => ({
            providers: state.providers.map((p) =>
              p.id === id ? { ...p, isEnabled: false } : p
            ),
          })),
        
        toggleProvider: (id) =>
          set((state) => ({
            providers: state.providers.map((p) =>
              p.id === id ? { ...p, isEnabled: !p.isEnabled } : p
            ),
          })),
        
        reset: () => set(initialState),
      }),
      {
        name: 'providers-store',
        partialize: (state) => ({
          providers: state.providers,
          selectedProviderIds: state.selectedProviderIds,
          defaultProviderId: state.defaultProviderId,
        }),
      }
    ),
    { name: 'ProvidersStore' }
  )
);

// Selector hooks
export const useProviders = () => useProvidersStore((state) => state.providers);
export const useProviderStatuses = () => useProvidersStore((state) => state.providerStatuses);
export const useProviderStats = () => useProvidersStore((state) => state.providerStats);
export const useSelectedProviderIds = () => useProvidersStore((state) => state.selectedProviderIds);
export const useDefaultProviderId = () => useProvidersStore((state) => state.defaultProviderId);
export const useIsLoading = () => useProvidersStore((state) => state.isLoading);
export const useIsTesting = () => useProvidersStore((state) => state.isTesting);
export const useTestResults = () => useProvidersStore((state) => state.testResults);

// Helper hooks
export const useEnabledProviders = () => 
  useProvidersStore((state) => 
    state.providers.filter(p => p.isEnabled)
  );

export const useConfiguredProviders = () => 
  useProvidersStore((state) => 
    state.providers.filter(p => p.isConfigured)
  );

export const useSelectedProviders = () => 
  useProvidersStore((state) => 
    state.providers.filter(p => state.selectedProviderIds.includes(p.id))
  );

export const useDefaultProvider = () => 
  useProvidersStore((state) => 
    state.providers.find(p => p.id === state.defaultProviderId) || null
  );

export const useProviderById = (id: string) => 
  useProvidersStore((state) => 
    state.providers.find(p => p.id === id) || null
  );

export const useProviderStatus = (id: string) => 
  useProvidersStore((state) => 
    state.providerStatuses[id] || null
  );

export const useProviderStatsById = (id: string) => 
  useProvidersStore((state) => 
    state.providerStats[id] || null
  );
