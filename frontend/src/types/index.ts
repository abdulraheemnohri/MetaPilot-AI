export interface User { id: string; name: string; email: string; }
export interface AppStats { totalChats: number; totalDocuments: number; activeProviders: number; pendingTasks: number; }
export interface ApiResponse<T> { success: boolean; data?: T; error?: string; message?: string; }
export interface PaginatedResponse<T> { items: T[]; total: number; page: number; size: number; }
export interface Plugin { id: string; name: string; description: string; version: string; author: string; isEnabled: boolean; isInstalled: boolean; config: Record<string, any>; plugin_type?: string; }
export interface Document { id: string; name: string; type: string; size: number; status?: 'uploaded' | 'processing' | 'processed' | 'failed'; uploadedAt: string; }
export interface Task { id: string; name: string; type: string; status?: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'; progress: number; title?: string; description?: string; }
