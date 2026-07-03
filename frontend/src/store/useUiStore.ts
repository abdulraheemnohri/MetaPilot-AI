// UI store for MetaPilot AI
// Zustand store for UI state management

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UiState {
  // Sidebar
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  
  // Theme
  theme: 'light' | 'dark' | 'system';
  
  // Language
  language: string;
  
  // Modal states
  isModalOpen: boolean;
  modalContent: React.ReactNode | null;
  
  // Loading states
  isLoading: boolean;
  loadingMessage: string | null;
  
  // Search
  searchQuery: string;
  searchOpen: boolean;
  
  // Notifications
  notificationsOpen: boolean;
  
  // Settings drawer
  settingsOpen: boolean;
  
  // Current page title
  pageTitle: string;
}

interface UiActions {
  // Sidebar actions
  setSidebarOpen: (open: boolean) => void;
  toggleSidebarOpen: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebarCollapsed: () => void;
  
  // Theme actions
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  toggleTheme: () => void;
  
  // Language actions
  setLanguage: (language: string) => void;
  
  // Modal actions
  openModal: (content: React.ReactNode) => void;
  closeModal: () => void;
  
  // Loading actions
  setLoading: (isLoading: boolean, message?: string) => void;
  
  // Search actions
  setSearchQuery: (query: string) => void;
  setSearchOpen: (open: boolean) => void;
  toggleSearchOpen: () => void;
  
  // Notifications actions
  setNotificationsOpen: (open: boolean) => void;
  toggleNotificationsOpen: () => void;
  
  // Settings drawer actions
  setSettingsOpen: (open: boolean) => void;
  toggleSettingsOpen: () => void;
  
  // Page title actions
  setPageTitle: (title: string) => void;
  
  // Reset UI state
  reset: () => void;
}

type UiStore = UiState & UiActions;

// Initial state
const initialState: UiState = {
  sidebarOpen: false,
  sidebarCollapsed: false,
  theme: 'system',
  language: 'en',
  isModalOpen: false,
  modalContent: null,
  isLoading: false,
  loadingMessage: null,
  searchQuery: '',
  searchOpen: false,
  notificationsOpen: false,
  settingsOpen: false,
  pageTitle: 'MetaPilot AI',
};

export const useUiStore = create<UiStore>()(
  persist(
    (set, get) => ({
      // State
      ...initialState,

      // Sidebar actions
      setSidebarOpen: (open: boolean) => {
        set({ sidebarOpen: open });
      },
      
      toggleSidebarOpen: () => {
        set((state) => ({ sidebarOpen: !state.sidebarOpen }));
      },
      
      setSidebarCollapsed: (collapsed: boolean) => {
        set({ sidebarCollapsed: collapsed });
      },
      
      toggleSidebarCollapsed: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
      },

      // Theme actions
      setTheme: (theme: 'light' | 'dark' | 'system') => {
        set({ theme });
        // Update document class for theme
        document.documentElement.classList.remove('light', 'dark');
        if (theme !== 'system') {
          document.documentElement.classList.add(theme);
        }
      },
      
      toggleTheme: () => {
        const currentTheme = get().theme;
        const themes: ('light' | 'dark' | 'system')[] = ['light', 'dark', 'system'];
        const nextIndex = (themes.indexOf(currentTheme) + 1) % themes.length;
        get().setTheme(themes[nextIndex]);
      },

      // Language actions
      setLanguage: (language: string) => {
        set({ language });
      },

      // Modal actions
      openModal: (content: React.ReactNode) => {
        set({
          isModalOpen: true,
          modalContent: content,
        });
      },
      
      closeModal: () => {
        set({
          isModalOpen: false,
          modalContent: null,
        });
      },

      // Loading actions
      setLoading: (isLoading: boolean, message?: string) => {
        set({
          isLoading,
          loadingMessage: message || null,
        });
      },

      // Search actions
      setSearchQuery: (query: string) => {
        set({ searchQuery: query });
      },
      
      setSearchOpen: (open: boolean) => {
        set({ searchOpen: open });
      },
      
      toggleSearchOpen: () => {
        set((state) => ({ searchOpen: !state.searchOpen }));
      },

      // Notifications actions
      setNotificationsOpen: (open: boolean) => {
        set({ notificationsOpen: open });
      },
      
      toggleNotificationsOpen: () => {
        set((state) => ({ notificationsOpen: !state.notificationsOpen }));
      },

      // Settings drawer actions
      setSettingsOpen: (open: boolean) => {
        set({ settingsOpen: open });
      },
      
      toggleSettingsOpen: () => {
        set((state) => ({ settingsOpen: !state.settingsOpen }));
      },

      // Page title actions
      setPageTitle: (title: string) => {
        set({ pageTitle: title });
        document.title = title;
      },

      // Reset UI state
      reset: () => {
        set(initialState);
      },
    }),
    {
      name: 'metapilot-ui-storage',
      partialize: (state) => ({
        // Only persist these settings
        theme: state.theme,
        language: state.language,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);

export default useUiStore;
