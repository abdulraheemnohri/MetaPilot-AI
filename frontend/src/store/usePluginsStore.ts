"""
MetaPilot AI - Plugins Store

Plugin management state.
"""

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  isEnabled: boolean;
  isInstalled: boolean;
  isLoaded: boolean;
  path?: string;
  config?: Record<string, any>;
  permissions?: string[];
  metadata?: Record<string, any>;
}

interface PluginConfig {
  id: string;
  config: Record<string, any>;
  isEnabled: boolean;
}

interface PluginsState {
  // Plugins
  plugins: Plugin[];
  installedPluginIds: string[];
  loadedPluginIds: string[];
  
  // Configuration
  pluginConfigs: PluginConfig[];
  
  // Registry
  pluginRegistry: Record<string, any>;
  
  // State
  isLoading: boolean;
  isInstalling: boolean;
  installingPluginId: string | null;
  installError: string | null;
  isScanning: boolean;
  
  // Actions
  setPlugins: (plugins: Plugin[]) => void;
  addPlugin: (plugin: Plugin) => void;
  updatePlugin: (id: string, updates: Partial<Plugin>) => void;
  deletePlugin: (id: string) => void;
  setInstalledPluginIds: (ids: string[]) => void;
  addInstalledPluginId: (id: string) => void;
  removeInstalledPluginId: (id: string) => void;
  setLoadedPluginIds: (ids: string[]) => void;
  addLoadedPluginId: (id: string) => void;
  removeLoadedPluginId: (id: string) => void;
  
  setPluginConfigs: (configs: PluginConfig[]) => void;
  addPluginConfig: (config: PluginConfig) => void;
  updatePluginConfig: (id: string, updates: Partial<PluginConfig>) => void;
  deletePluginConfig: (id: string) => void;
  
  setPluginRegistry: (registry: Record<string, any>) => void;
  registerPlugin: (id: string, plugin: any) => void;
  unregisterPlugin: (id: string) => void;
  
  setIsLoading: (isLoading: boolean) => void;
  setIsInstalling: (isInstalling: boolean) => void;
  setInstallingPluginId: (id: string | null) => void;
  setInstallError: (error: string | null) => void;
  setIsScanning: (isScanning: boolean) => void;
  
  enablePlugin: (id: string) => void;
  disablePlugin: (id: string) => void;
  togglePlugin: (id: string) => void;
  
  reset: () => void;
}

const initialState = {
  plugins: [],
  installedPluginIds: [],
  loadedPluginIds: [],
  pluginConfigs: [],
  pluginRegistry: {},
  isLoading: false,
  isInstalling: false,
  installingPluginId: null,
  installError: null,
  isScanning: false,
};

export const usePluginsStore = create<PluginsState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,
        
        setPlugins: (plugins) => set({ plugins }),
        
        addPlugin: (plugin) =>
          set((state) => ({
            plugins: [...state.plugins, plugin],
          })),
        
        updatePlugin: (id, updates) =>
          set((state) => ({
            plugins: state.plugins.map((p) =>
              p.id === id ? { ...p, ...updates } : p
            ),
          })),
        
        deletePlugin: (id) =>
          set((state) => ({
            plugins: state.plugins.filter((p) => p.id !== id),
            installedPluginIds: state.installedPluginIds.filter((pid) => pid !== id),
            loadedPluginIds: state.loadedPluginIds.filter((pid) => pid !== id),
          })),
        
        setInstalledPluginIds: (ids) => set({ installedPluginIds: ids }),
        
        addInstalledPluginId: (id) =>
          set((state) => ({
            installedPluginIds: [...state.installedPluginIds, id],
          })),
        
        removeInstalledPluginId: (id) =>
          set((state) => ({
            installedPluginIds: state.installedPluginIds.filter((pid) => pid !== id),
          })),
        
        setLoadedPluginIds: (ids) => set({ loadedPluginIds: ids }),
        
        addLoadedPluginId: (id) =>
          set((state) => ({
            loadedPluginIds: [...state.loadedPluginIds, id],
          })),
        
        removeLoadedPluginId: (id) =>
          set((state) => ({
            loadedPluginIds: state.loadedPluginIds.filter((pid) => pid !== id),
          })),
        
        setPluginConfigs: (configs) => set({ pluginConfigs: configs }),
        
        addPluginConfig: (config) =>
          set((state) => ({
            pluginConfigs: [...state.pluginConfigs, config],
          })),
        
        updatePluginConfig: (id, updates) =>
          set((state) => ({
            pluginConfigs: state.pluginConfigs.map((c) =>
              c.id === id ? { ...c, ...updates } : c
            ),
          })),
        
        deletePluginConfig: (id) =>
          set((state) => ({
            pluginConfigs: state.pluginConfigs.filter((c) => c.id !== id),
          })),
        
        setPluginRegistry: (registry) => set({ pluginRegistry: registry }),
        
        registerPlugin: (id, plugin) =>
          set((state) => ({
            pluginRegistry: {
              ...state.pluginRegistry,
              [id]: plugin,
            },
          })),
        
        unregisterPlugin: (id) =>
          set((state) => {
            const newRegistry = { ...state.pluginRegistry };
            delete newRegistry[id];
            return { pluginRegistry: newRegistry };
          }),
        
        setIsLoading: (isLoading) => set({ isLoading }),
        setIsInstalling: (isInstalling) => set({ isInstalling }),
        setInstallingPluginId: (id) => set({ installingPluginId: id }),
        setInstallError: (error) => set({ installError: error }),
        setIsScanning: (isScanning) => set({ isScanning }),
        
        enablePlugin: (id) =>
          set((state) => ({
            plugins: state.plugins.map((p) =>
              p.id === id ? { ...p, isEnabled: true } : p
            ),
          })),
        
        disablePlugin: (id) =>
          set((state) => ({
            plugins: state.plugins.map((p) =>
              p.id === id ? { ...p, isEnabled: false } : p
            ),
          })),
        
        togglePlugin: (id) =>
          set((state) => ({
            plugins: state.plugins.map((p) =>
              p.id === id ? { ...p, isEnabled: !p.isEnabled } : p
            ),
          })),
        
        reset: () => set(initialState),
      }),
      {
        name: 'plugins-store',
        partialize: (state) => ({
          plugins: state.plugins,
          installedPluginIds: state.installedPluginIds,
          pluginConfigs: state.pluginConfigs,
        }),
      }
    ),
    { name: 'PluginsStore' }
  )
);

// Selector hooks
export const usePlugins = () => usePluginsStore((state) => state.plugins);
export const useInstalledPluginIds = () => usePluginsStore((state) => state.installedPluginIds);
export const useLoadedPluginIds = () => usePluginsStore((state) => state.loadedPluginIds);
export const usePluginConfigs = () => usePluginsStore((state) => state.pluginConfigs);
export const usePluginRegistry = () => usePluginsStore((state) => state.pluginRegistry);
export const useIsLoading = () => usePluginsStore((state) => state.isLoading);
export const useIsInstalling = () => usePluginsStore((state) => state.isInstalling);
export const useInstallingPluginId = () => usePluginsStore((state) => state.installingPluginId);
export const useInstallError = () => usePluginsStore((state) => state.installError);
export const useIsScanning = () => usePluginsStore((state) => state.isScanning);

// Helper hooks
export const useEnabledPlugins = () => 
  usePluginsStore((state) => 
    state.plugins.filter(p => p.isEnabled)
  );

export const useInstalledPlugins = () => 
  usePluginsStore((state) => 
    state.plugins.filter(p => state.installedPluginIds.includes(p.id))
  );

export const useLoadedPlugins = () => 
  usePluginsStore((state) => 
    state.plugins.filter(p => state.loadedPluginIds.includes(p.id))
  );

export const usePluginById = (id: string) => 
  usePluginsStore((state) => 
    state.plugins.find(p => p.id === id) || null
  );

export const usePluginConfig = (id: string) => 
  usePluginsStore((state) => 
    state.pluginConfigs.find(c => c.id === id) || null
  );

export const useRegistryPlugin = (id: string) => 
  usePluginsStore((state) => 
    state.pluginRegistry[id] || null
  );

export const useIsPluginEnabled = (id: string) => 
  usePluginsStore((state) => 
    state.plugins.find(p => p.id === id)?.isEnabled || false
  );

export const useIsPluginInstalled = (id: string) => 
  usePluginsStore((state) => 
    state.installedPluginIds.includes(id)
  );

export const useIsPluginLoaded = (id: string) => 
  usePluginsStore((state) => 
    state.loadedPluginIds.includes(id)
  );
