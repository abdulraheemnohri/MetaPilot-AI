"""
MetaPilot AI - Authentication Store

User authentication and session state management.
"""

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface User {
  userId: string;
  username: string;
  email?: string;
  displayName?: string;
  isActive: boolean;
  isSuperuser: boolean;
  createdAt?: string;
  lastLogin?: string;
}

interface Session {
  sessionId: string;
  userId: string;
  createdAt: string;
  expiresAt: string;
  ipAddress?: string;
  userAgent?: string;
}

interface AuthState {
  // User state
  user: User | null;
  session: Session | null;
  isAuthenticated: boolean;
  
  // Authentication state
  isAuthenticating: boolean;
  authError: string | null;
  
  // Token state
  accessToken: string | null;
  refreshToken: string | null;
  
  // Actions
  setUser: (user: User | null) => void;
  setSession: (session: Session | null) => void;
  setAuthenticated: (isAuthenticated: boolean) => void;
  setAuthenticating: (isAuthenticating: boolean) => void;
  setAuthError: (error: string | null) => void;
  setAccessToken: (token: string | null) => void;
  setRefreshToken: (token: string | null) => void;
  login: (user: User, session: Session, accessToken: string, refreshToken?: string) => void;
  logout: () => void;
  setAuthState: (user: User | null, session: Session | null, isAuthenticated: boolean) => void;
  reset: () => void;
}

const initialState = {
  user: null,
  session: null,
  isAuthenticated: false,
  isAuthenticating: false,
  authError: null,
  accessToken: null,
  refreshToken: null,
};

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        ...initialState,
        
        setUser: (user) => set({ user }),
        setSession: (session) => set({ session }),
        setAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
        setAuthenticating: (isAuthenticating) => set({ isAuthenticating }),
        setAuthError: (authError) => set({ authError }),
        setAccessToken: (accessToken) => set({ accessToken }),
        setRefreshToken: (refreshToken) => set({ refreshToken }),
        
        login: (user, session, accessToken, refreshToken) =>
          set({
            user,
            session,
            isAuthenticated: true,
            isAuthenticating: false,
            authError: null,
            accessToken,
            refreshToken,
          }),
        
        logout: () =>
          set({
            user: null,
            session: null,
            isAuthenticated: false,
            accessToken: null,
            refreshToken: null,
          }),
        
        setAuthState: (user, session, isAuthenticated) =>
          set({ user, session, isAuthenticated }),
        
        reset: () => set(initialState),
      }),
      {
        name: 'auth-store',
        partialize: (state) => ({
          // Only persist these fields (not sensitive tokens in production!)
          user: state.user,
          isAuthenticated: state.isAuthenticated,
          // Note: In production, you might not want to persist tokens
          // accessToken: state.accessToken,
          // refreshToken: state.refreshToken,
        }),
      }
    ),
    { name: 'AuthStore' }
  )
);

// Selector hooks
export const useUser = () => useAuthStore((state) => state.user);
export const useSession = () => useAuthStore((state) => state.session);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useIsAuthenticating = () => useAuthStore((state) => state.isAuthenticating);
export const useAuthError = () => useAuthStore((state) => state.authError);
export const useAccessToken = () => useAuthStore((state) => state.accessToken);
export const useRefreshToken = () => useAuthStore((state) => state.refreshToken);

// Helper hooks
export const useUserId = () => useAuthStore((state) => state.user?.userId || null);
export const useUsername = () => useAuthStore((state) => state.user?.username || null);
export const useIsSuperuser = () => useAuthStore((state) => state.user?.isSuperuser || false);
