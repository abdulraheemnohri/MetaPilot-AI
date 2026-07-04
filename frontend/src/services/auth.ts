import { apiService } from './api';

interface LoginCredentials {
  email: string;
  password: string;
}

interface RegisterCredentials extends LoginCredentials {
  username: string;
  fullName?: string;
}

interface AuthResponse {
  user: {
    id: string;
    email: string;
    username: string;
    fullName?: string;
  };
  accessToken: string;
  refreshToken?: string;
}

interface User {
  id: string;
  email: string;
  username: string;
  fullName?: string;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiService.post<AuthResponse>('/api/auth/token', {
      email: credentials.email,
      password: credentials.password,
    });
    
    if (!response.success) {
      throw new Error(response.error || 'Login failed');
    }
    
    return response.data!;
  },
  
  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    const response = await apiService.post<AuthResponse>('/api/auth/register', {
      email: credentials.email,
      username: credentials.username,
      password: credentials.password,
      full_name: credentials.fullName,
    });
    
    if (!response.success) {
      throw new Error(response.error || 'Registration failed');
    }
    
    return response.data!;
  },
  
  async logout(): Promise<void> {
    await apiService.post('/api/auth/logout');
  },
  
  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await apiService.post<AuthResponse>('/api/auth/refresh', {
      refresh_token: refreshToken,
    });
    
    if (!response.success) {
      throw new Error(response.error || 'Token refresh failed');
    }
    
    return response.data!;
  },
  
  async getCurrentUser(): Promise<User> {
    const response = await apiService.get<User>('/api/auth/me');
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to get current user');
    }
    
    return response.data!;
  },
  
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    const response = await apiService.post('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    
    if (!response.success) {
      throw new Error(response.error || 'Password change failed');
    }
  },
};