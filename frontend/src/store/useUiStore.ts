import { create } from 'zustand';

interface UiState {
  isSidebarCollapsed: boolean;
  isMobileMenuOpen: boolean;
  activeTab: string;
  
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleMobileMenu: () => void;
  setMobileMenuOpen: (isOpen: boolean) => void;
  setActiveTab: (tab: string) => void;
}

export const useUiStore = create<UiState>((set) => ({
  isSidebarCollapsed: false,
  isMobileMenuOpen: false,
  activeTab: 'chat',
  
  toggleSidebar: () => set((state) => ({
    isSidebarCollapsed: !state.isSidebarCollapsed
  })),
  
  setSidebarCollapsed: (collapsed) => set({ isSidebarCollapsed: collapsed }),
  
  toggleMobileMenu: () => set((state) => ({
    isMobileMenuOpen: !state.isMobileMenuOpen
  })),
  
  setMobileMenuOpen: (isOpen) => set({ isMobileMenuOpen: isOpen }),
  
  setActiveTab: (tab) => set({ activeTab: tab }),
}));