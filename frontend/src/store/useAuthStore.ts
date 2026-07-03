// Auth store for MetaPilot AI
// Zustand store for authentication state

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, AuthState, LoginCredentials, RegisterCredentials, AuthResponse } from '../types';
import authService from '../services/auth';

interface AuthActions {
  // Login
  login: (credentials: LoginCredentials) => Promise<void>;
  
  // Register
  register: (credentials: RegisterCredentials) => Promise<void>;
  
  // Logout
  logout: () => Promise<void>;
  
  // Check authentication
  checkAuth: () => Promise<void>;
  
  // Set user
  setUser: (user: User | null) => void;
  
  // Set token
  setToken: (token: string | null) => void;
  
  // Set loading state
  setLoading: (isLoading: boolean) => void;
  
  // Set error
  setError: (error: string | null) => void;
  
  // Clear error
  clearError: () => void;
  
  // Update profile
  updateProfile: (userData: Partial<User>) => Promise<void>;
  
  // Change password
  changePassword: (
    currentPassword: string,
    newPassword: string,
    confirmPassword: string
  ) => Promise<void>;
  
  // Forgot password
  forgotPassword: (email: string) => Promise<void>;
  
  // Reset password
  resetPassword: (
    token: string,
    password: string,
    confirmPassword: string
  ) => Promise<void>;
}

type AuthStore = AuthState & AuthActions;

// Initial state
const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

export const useAuth = create<AuthStore>()(
  persist(
    (set, get) => ({
      // State
      ...initialState,

      // Actions
      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });
        
        try {
          const response: AuthResponse = await authService.login(credentials);
          
          // Store auth data
          authService.storeAuthData(
            response.access_token,
            response.user,
            response.refresh_token
          );
          
          set({
            user: response.user,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 
            error.response?.data?.detail ||
            error.message ||
            'Login failed. Please check your credentials.';
          
          set({
            isLoading: false,
            error: errorMessage,
          });
          
          throw error;
        }
      },

      register: async (credentials: RegisterCredentials) => {
        set({ isLoading: true, error: null });
        
        try {
          const response: AuthResponse = await authService.register(credentials);
          
          // Store auth data
          authService.storeAuthData(
            response.access_token,
            response.user,
            response.refresh_token
          );
          
          set({
            user: response.user,
            token: response.access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 
            error.response?.data?.detail ||
            error.message ||
            'Registration failed. Please try again.';
          
          set({
            isLoading: false,
            error: errorMessage,
          });
          
          throw error;
        }
      },

      logout: async () => {
        try {
          await authService.logout();
        } catch (error) {
          // Ignore logout errors
          console.error('Logout error:', error);
        } finally {
          // Clear auth data
          authService.clearAuthData();
          
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      checkAuth: async () => {
        set({ isLoading: true });
        
        try {
          // Check if token exists
          const token = authService.getToken();
          const storedUser = authService.getStoredUser();
          
          if (!token || !storedUser) {
            set({
              user: null,
              token: null,
              isAuthenticated: false,
              isLoading: false,
            });
            return;
          }
          
          // Verify token by fetching current user
          const user: User = await authService.getCurrentUser();
          
          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          // Token is invalid, clear auth data
          authService.clearAuthData();
          
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },

      setUser: (user: User | null) => {
        set({ user });
      },

      setToken: (token: string | null) => {
        set({ token });
      },

      setLoading: (isLoading: boolean) => {
        set({ isLoading });
      },

      setError: (error: string | null) => {
        set({ error });
      },

      clearError: () => {
        set({ error: null });
      },

      updateProfile: async (userData: Partial<User>) => {
        set({ isLoading: true, error: null });
        
        try {
          const user: User = await authService.updateProfile(userData);
          
          // Update stored user
          const storedUser = authService.getStoredUser();
          if (storedUser) {
            authService.storeAuthData(
              authService.getToken() || '',
              { ...storedUser, ...user },
              authService.getStoredUser()?.api_keys?.join(',') || undefined
            );
          }
          
          set({
            user,
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 
            error.response?.data?.detail ||
            error.message ||
            'Failed to update profile.';
          
          set({
            isLoading: false,
            error: errorMessage,
          });
          
          throw error;
        }
      },

      changePassword: async (
        currentPassword: string,
        newPassword: string,
        confirmPassword: string
      ) => {
        set({ isLoading: true, error: null });
        
        try {
          await authService.changePassword(currentPassword, newPassword, confirmPassword);
          
          set({
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 
            error.response?.data?.detail ||
            error.message ||
            'Failed to change password.';
          
          set({
            isLoading: false,
            error: errorMessage,
          });
          
          throw error;
        }
      },

      forgotPassword: async (email: string) => {
        set({ isLoading: true, error: null });
        
        try {
          await authService.forgotPassword(email);
          
          set({
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 
            error.response?.data?.detail ||
            error.message ||
            'Failed to send password reset email.';
          
          set({
            isLoading: false,
            error: errorMessage,
          });
          
          throw error;
        }
      },

      resetPassword: async (
        token: string,
        password: string,
        confirmPassword: string
      ) => {
        set({ isLoading: true, error: null });
        
        try {
          await authService.resetPassword(token, password, confirmPassword);
          
          set({
            isLoading: false,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.error || 
            error.response?.data?.detail ||
            error.message ||
            'Failed to reset password.';
          
          set({
            isLoading: false,
            error: errorMessage,
          });
          
          throw error;
        }
      },
    }),
    {
      name: 'metapilot-auth-storage',
      partialize: (state) => ({
        // Only persist user data, not token (for security)
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export default useAuth;
