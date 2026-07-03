// Auth service for MetaPilot AI
// Handles authentication-related API calls

import { apiService } from './api';
import { LoginCredentials, RegisterCredentials, AuthResponse, User } from '../types';

// Auth API base path
const AUTH_BASE_URL = '/api/auth';

// Auth service
const authService = {
  // Login user
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await apiService.post<AuthResponse>(
      `${AUTH_BASE_URL}/login`,
      credentials
    );
    return response.data;
  },

  // Register new user
  register: async (credentials: RegisterCredentials): Promise<AuthResponse> => {
    const response = await apiService.post<AuthResponse>(
      `${AUTH_BASE_URL}/register`,
      credentials
    );
    return response.data;
  },

  // Logout user
  logout: async (): Promise<void> => {
    await apiService.post(`${AUTH_BASE_URL}/logout`);
    // Clear local storage
    localStorage.removeItem('metapilot-token');
    localStorage.removeItem('metapilot-user');
    localStorage.removeItem('metapilot-refresh-token');
  },

  // Get current user
  getCurrentUser: async (): Promise<User> => {
    const response = await apiService.get<User>(`${AUTH_BASE_URL}/me`);
    return response.data;
  },

  // Refresh token
  refreshToken: async (refreshToken: string): Promise<AuthResponse> => {
    const response = await apiService.post<AuthResponse>(
      `${AUTH_BASE_URL}/refresh`,
      { refresh_token: refreshToken }
    );
    return response.data;
  },

  // Forgot password
  forgotPassword: async (email: string): Promise<void> => {
    await apiService.post(`${AUTH_BASE_URL}/forgot-password`, { email });
  },

  // Reset password
  resetPassword: async (
    token: string,
    password: string,
    confirmPassword: string
  ): Promise<void> => {
    await apiService.post(`${AUTH_BASE_URL}/reset-password`, {
      token,
      password,
      confirm_password: confirmPassword,
    });
  },

  // Change password
  changePassword: async (
    currentPassword: string,
    newPassword: string,
    confirmPassword: string
  ): Promise<void> => {
    await apiService.post(`${AUTH_BASE_URL}/change-password`, {
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    });
  },

  // Update profile
  updateProfile: async (userData: Partial<User>): Promise<User> => {
    const response = await apiService.put<User>(
      `${AUTH_BASE_URL}/me`,
      userData
    );
    return response.data;
  },

  // Verify email
  verifyEmail: async (token: string): Promise<void> => {
    await apiService.post(`${AUTH_BASE_URL}/verify-email`, { token });
  },

  // Resend verification email
  resendVerificationEmail: async (email: string): Promise<void> => {
    await apiService.post(`${AUTH_BASE_URL}/resend-verification`, { email });
  },

  // Get all users (admin only)
  getAllUsers: async (): Promise<User[]> => {
    const response = await apiService.get<User[]>(`${AUTH_BASE_URL}/users`);
    return response.data;
  },

  // Get user by ID (admin only)
  getUserById: async (userId: number): Promise<User> => {
    const response = await apiService.get<User>(`${AUTH_BASE_URL}/users/${userId}`);
    return response.data;
  },

  // Update user (admin only)
  updateUser: async (userId: number, userData: Partial<User>): Promise<User> => {
    const response = await apiService.put<User>(
      `${AUTH_BASE_URL}/users/${userId}`,
      userData
    );
    return response.data;
  },

  // Delete user (admin only)
  deleteUser: async (userId: number): Promise<void> => {
    await apiService.delete(`${AUTH_BASE_URL}/users/${userId}`);
  },

  // Check if user is authenticated
  isAuthenticated: (): boolean => {
    const token = localStorage.getItem('metapilot-token');
    return !!token;
  },

  // Get stored token
  getToken: (): string | null => {
    return localStorage.getItem('metapilot-token');
  },

  // Get stored user
  getStoredUser: (): User | null => {
    const user = localStorage.getItem('metapilot-user');
    return user ? JSON.parse(user) : null;
  },

  // Store token and user
  storeAuthData: (token: string, user: User, refreshToken?: string): void => {
    localStorage.setItem('metapilot-token', token);
    localStorage.setItem('metapilot-user', JSON.stringify(user));
    if (refreshToken) {
      localStorage.setItem('metapilot-refresh-token', refreshToken);
    }
  },

  // Clear auth data
  clearAuthData: (): void => {
    localStorage.removeItem('metapilot-token');
    localStorage.removeItem('metapilot-user');
    localStorage.removeItem('metapilot-refresh-token');
  },
};

export default authService;
