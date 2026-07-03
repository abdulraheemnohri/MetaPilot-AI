"""
MetaPilot AI - Application Store

Global application state management.
"""

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface AppState {
  // Application status
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;
  
  // Connection status
  isConnected: boolean;
  isConnecting: boolean;
  connectionError: string | null;
  
  // Server info
  serverVersion: string | null;
  serverStatus: string | null;
  
  // Actions
  setLoading: (isLoading: boolean) => void;
  setInitialized: (isInitialized: boolean) => void;
  setError: (error: string | null) => void;
  setConnected: (isConnected: boolean) => void;
  setConnecting: (isConnecting: boolean) => void;
  setConnectionError: (error: string | null) => void;
  setServerInfo: (version: string, status: string) => void;
  reset: () => void;
}

const initialState = {
  isLoading: false,
  isInitialized: false,
  error: null,
  isConnected: false,
  isConnecting: false,
  connectionError: null,
  serverVersion: null,
  serverStatus: null,
};

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        ...initialState,
        
        setLoading: (isLoading) => set({ isLoading }),
        setInitialized: (isInitialized) => set({ isInitialized }),
        setError: (error) => set({ error }),
        setConnected: (isConnected) => set({ isConnected }),
        setConnecting: (isConnecting) => set({ isConnecting }),
        setConnectionError: (connectionError) => set({ connectionError }),
        setServerInfo: (serverVersion, serverStatus) => 
          set({ serverVersion, serverStatus }),
        reset: () => set(initialState),
      }),
      {
        name: 'app-store',
        partialize: (state) => ({
          // Only persist these fields
          isInitialized: state.isInitialized,
          serverVersion: state.serverVersion,
          serverStatus: state.serverStatus,
        }),
      }
    ),
    { name: 'AppStore' }
  )
);

// Selector hooks for better performance
export const useIsLoading = () => useAppStore((state) => state.isLoading);
export const useIsInitialized = () => useAppStore((state) => state.isInitialized);
export const useError = () => useAppStore((state) => state.error);
export const useIsConnected = () => useAppStore((state) => state.isConnected);
export const useIsConnecting = () => useAppStore((state) => state.isConnecting);
export const useConnectionError = () => useAppStore((state) => state.connectionError);
export const useServerVersion = () => useAppStore((state) => state.serverVersion);
export const useServerStatus = () => useAppStore((state) => state.serverStatus);
