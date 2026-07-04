import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Settings {
  maxTokens: number;
  temperature: number;
  theme: 'light' | 'dark' | 'system';
  language: string;
  autoSave: boolean;
}

interface SettingsState {
  settings: Settings;
  
  updateSettings: (updates: Partial<Settings>) => void;
  resetSettings: () => void;
}

const defaultSettings: Settings = {
  maxTokens: 4096,
  temperature: 0.7,
  theme: 'system',
  language: 'en',
  autoSave: true
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      settings: defaultSettings,
      
      updateSettings: (updates) => set((state) => ({
        settings: { ...state.settings, ...updates }
      })),
      
      resetSettings: () => set({ settings: defaultSettings }),
    }),
    {
      name: 'settings-storage',
      partialize: (state) => ({ settings: state.settings })
    }
  )
);