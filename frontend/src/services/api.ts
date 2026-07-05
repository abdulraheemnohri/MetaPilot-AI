import { ApiResponse } from "../types";
const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

export const apiService = {
  async get<T>(endpoint: string, params?: Record<string, string>): Promise<ApiResponse<T>> {
    const url = new URL(`${API_BASE}${endpoint}`);
    if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, v));
    const response = await fetch(url.toString(), { credentials: 'include' });
    return await response.json();
  },
  async post<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    const response = await fetch(`${API_BASE}${endpoint}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: data ? JSON.stringify(data) : undefined, credentials: 'include' });
    return await response.json();
  },
  async put<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    const response = await fetch(`${API_BASE}${endpoint}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: data ? JSON.stringify(data) : undefined, credentials: 'include' });
    return await response.json();
  },
  async patch<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    const response = await fetch(`${API_BASE}${endpoint}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: data ? JSON.stringify(data) : undefined, credentials: 'include' });
    return await response.json();
  },
  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    const response = await fetch(`${API_BASE}${endpoint}`, { method: 'DELETE', credentials: 'include' });
    return await response.json();
  },
  async upload<T>(endpoint: string, formData: FormData): Promise<ApiResponse<T>> {
    const response = await fetch(`${API_BASE}${endpoint}`, { method: 'POST', body: formData, credentials: 'include' });
    return await response.json();
  }
};
