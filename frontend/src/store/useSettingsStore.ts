"""
MetaPilot AI - Settings Store

Application settings and preferences state management.
"""

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface AppSettings {
  // Theme
  theme: 'light' | 'dark' | 'system';
  primaryColor: string;
  accentColor: string;
  
  // Language
  language: string;
  
  // Layout
  layoutMode: 'full' | 'compact' | 'minimal';
  sidebarCollapsed: boolean;
  sidebarWidth: number;
  
  // Editor
  editorFontSize: number;
  editorFontFamily: string;
  editorLineHeight: number;
  editorWordWrap: boolean;
  
  // Chat
  chatAutoScroll: boolean;
  chatShowTimestamps: boolean;
  chatShowProvider: boolean;
  chatMessageMaxWidth: number;
  
  // AI
  defaultModel: string;
  defaultProvider: string;
  temperature: number;
  maxTokens: number;
  topP: number;
  frequencyPenalty: number;
  presencePenalty: number;
  
  // Privacy
  enableAnalytics: boolean;
  enableErrorReporting: boolean;
  enableUsageStats: boolean;
  
  // Notifications
  notificationsEnabled: boolean;
  notificationSound: boolean;
  
  // Experimental
  experimentalFeatures: string[];
}

interface UiSettings {
  // Window
  windowWidth: number;
  windowHeight: number;
  
  // Panels
  chatPanelVisible: boolean;
  providersPanelVisible: boolean;
  knowledgePanelVisible: boolean;
  pluginsPanelVisible: boolean;
  tasksPanelVisible: boolean;
  settingsPanelVisible: boolean;
}

interface SettingsState {
  app: AppSettings;
  ui: UiSettings;
  
  // State
  isLoading: boolean;
  isSaving: boolean;
  lastSavedAt: string | null;
  error: string | null;
  
  // Actions
  setAppSettings: (settings: Partial<AppSettings>) => void;
  setUiSettings: (settings: Partial<UiSettings>) => void;
  setTheme: (theme: AppSettings['theme']) => void;
  setLanguage: (language: string) => void;
  toggleSidebar: () => void;
  setSidebarWidth: (width: number) => void;
  setWindowSize: (width: number, height: number) => void;
  togglePanel: (panel: keyof UiSettings) => void;
  setPanelVisible: (panel: keyof UiSettings, visible: boolean) => void;
  
  setIsLoading: (isLoading: boolean) => void;
  setIsSaving: (isSaving: boolean) => void;
  setLastSavedAt: (timestamp: string | null) => void;
  setError: (error: string | null) => void;
  
  saveSettings: () => Promise<boolean>;
  loadSettings: () => Promise<boolean>;
  resetSettings: () => void;
  reset: () => void;
}

const defaultAppSettings: AppSettings = {
  theme: 'system',
  primaryColor: '#6366f1',
  accentColor: '#8b5cf6',
  language: 'en',
  layoutMode: 'full',
  sidebarCollapsed: false,
  sidebarWidth: 280,
  editorFontSize: 14,
  editorFontFamily: 'Inter, system-ui, sans-serif',
  editorLineHeight: 1.6,
  editorWordWrap: true,
  chatAutoScroll: true,
  chatShowTimestamps: true,
  chatShowProvider: true,
  chatMessageMaxWidth: 800,
  defaultModel: '',
  defaultProvider: '',
  temperature: 0.7,
  maxTokens: 2000,
  topP: 1.0,
  frequencyPenalty: 0.0,
  presencePenalty: 0.0,
  enableAnalytics: true,
  enableErrorReporting: true,
  enableUsageStats: true,
  notificationsEnabled: true,
  notificationSound: true,
  experimentalFeatures: [],
};

const defaultUiSettings: UiSettings = {
  windowWidth: 1200,
  windowHeight: 800,
  chatPanelVisible: true,
  providersPanelVisible: true,
  knowledgePanelVisible: true,
  pluginsPanelVisible: true,
  tasksPanelVisible: true,
  settingsPanelVisible: true,
};

const initialState = {
  app: defaultAppSettings,
  ui: defaultUiSettings,
  isLoading: false,
  isSaving: false,
  lastSavedAt: null,
  error: null,
};

export const useSettingsStore = create<SettingsState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,
        
        setAppSettings: (settings) =>
          set((state) => ({
            app: { ...state.app, ...settings },
          })),
        
        setUiSettings: (settings) =>
          set((state) => ({
            ui: { ...state.ui, ...settings },
          })),
        
        setTheme: (theme) =>
          set((state) => ({
            app: { ...state.app, theme },
          })),
        
        setLanguage: (language) =>
          set((state) => ({
            app: { ...state.app, language },
          })),
        
        toggleSidebar: () =>
          set((state) => ({
            app: { 
              ...state.app, 
              sidebarCollapsed: !state.app.sidebarCollapsed 
            },
          })),
        
        setSidebarWidth: (width) =>
          set((state) => ({
            app: { ...state.app, sidebarWidth: width },
          })),
        
        setWindowSize: (width, height) =>
          set((state) => ({
            ui: { 
              ...state.ui, 
              windowWidth: width, 
              windowHeight: height 
            },
          })),
        
        togglePanel: (panel) =>
          set((state) => ({
            ui: { 
              ...state.ui, 
              [panel]: !state.ui[panel] 
            },
          })),
        
        setPanelVisible: (panel, visible) =>
          set((state) => ({
            ui: { ...state.ui, [panel]: visible },
          })),
        
        setIsLoading: (isLoading) => set({ isLoading }),
        setIsSaving: (isSaving) => set({ isSaving }),
        setLastSavedAt: (lastSavedAt) => set({ lastSavedAt }),
        setError: (error) => set({ error }),
        
        saveSettings: async () => {
          set({ isSaving: true, error: null });
          
          try {
            // In a real implementation, this would save to backend or localStorage
            // For now, we just mark as saved
            set({
              isSaving: false,
              lastSavedAt: new Date().toISOString(),
            });
            return true;
          } catch (err) {
            set({
              isSaving: false,
              error: err instanceof Error ? err.message : 'Failed to save settings',
            });
            return false;
          }
        },
        
        loadSettings: async () => {
          set({ isLoading: true, error: null });
          
          try {
            // In a real implementation, this would load from backend or localStorage
            set({ isLoading: false });
            return true;
          } catch (err) {
            set({
              isLoading: false,
              error: err instanceof Error ? err.message : 'Failed to load settings',
            });
            return false;
          }
        },
        
        resetSettings: () =>
          set({
            app: defaultAppSettings,
            ui: defaultUiSettings,
          }),
        
        reset: () => set(initialState),
      }),
      {
        name: 'settings-store',
        // Persist all settings
      }
    ),
    { name: 'SettingsStore' }
  )
);

// Selector hooks
export const useAppSettings = () => useSettingsStore((state) => state.app);
export const useUiSettings = () => useSettingsStore((state) => state.ui);
export const useTheme = () => useSettingsStore((state) => state.app.theme);
export const useLanguage = () => useSettingsStore((state) => state.app.language);
export const useSidebarCollapsed = () => useSettingsStore((state) => state.app.sidebarCollapsed);
export const useSidebarWidth = () => useSettingsStore((state) => state.app.sidebarWidth);
export const useWindowSize = () => useSettingsStore((state) => ({
  width: state.ui.windowWidth,
  height: state.ui.windowHeight,
}));
export const usePanelVisible = (panel: keyof UiSettings) => 
  useSettingsStore((state) => state.ui[panel]);
export const useIsLoading = () => useSettingsStore((state) => state.isLoading);
export const useIsSaving = () => useSettingsStore((state) => state.isSaving);
export const useLastSavedAt = () => useSettingsStore((state) => state.lastSavedAt);
export const useError = () => useSettingsStore((state) => state.error);

// Helper hooks
export const useIsDarkMode = () => 
  useSettingsStore((state) => {
    if (state.app.theme === 'system') {
      // Check system preference (simplified)
      if (typeof window !== 'undefined') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
      }
      return false;
    }
    return state.app.theme === 'dark';
  });

export const useAiSettings = () => 
  useSettingsStore((state) => ({
    temperature: state.app.temperature,
    maxTokens: state.app.maxTokens,
    topP: state.app.topP,
    frequencyPenalty: state.app.frequencyPenalty,
    presencePenalty: state.app.presencePenalty,
  }));

export const useChatSettings = () => 
  useSettingsStore((state) => ({
    autoScroll: state.app.chatAutoScroll,
    showTimestamps: state.app.chatShowTimestamps,
    showProvider: state.app.chatShowProvider,
    messageMaxWidth: state.app.chatMessageMaxWidth,
  }));
