// Core types for MetaPilot AI application

// User and Authentication types
export interface User {
  id: string;
  email: string;
  username: string;
  fullName?: string;
  isActive: boolean;
  isVerified: boolean;
  createdAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials extends LoginCredentials {
  username: string;
  fullName?: string;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken?: string;
}

// AI Provider types
export interface AIProvider {
  id: string;
  name: string;
  type: string;
  apiKey?: string;
  isActive: boolean;
  baseUrl?: string;
  models?: string[];
}

export interface AIRequest {
  prompt: string;
  model?: string;
  maxTokens?: number;
  temperature?: number;
  providerId: string;
}

export interface AIResponse {
  id: string;
  content: string;
  model: string;
  provider: string;
  tokensUsed: number;
  finishReason: string;
  createdAt: string;
}

// Chat types
export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  id?: string;
  timestamp?: Date;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
  providerIds?: string[];
}

// Document and Knowledge types
export interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadedAt: string;
  processedAt?: string;
  status: 'uploaded' | 'processing' | 'processed' | 'failed';
}

// Task types
export interface Task {
  id: string;
  type: 'ai_inference' | 'document_processing' | 'export' | 'knowledge_update';
  title: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  createdAt: string;
  updatedAt: string;
  result?: unknown;
  error?: string;
}

// Plugin types
export interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  enabled: boolean;
  config?: Record<string, unknown>;
}

// Settings types
export interface Settings {
  maxTokens: number;
  temperature: number;
  theme: 'light' | 'dark' | 'system';
  language: string;
  autoSave: boolean;
}

// API Response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
  success: boolean;
}

// UI State types
export interface UiState {
  isSidebarCollapsed: boolean;
  isMobileMenuOpen: boolean;
  activeTab: string;
}

// Store types
export interface StoreState {
  isLoading: boolean;
  error: string | null;
}

// Utility types
export type ClassValue = string | number | boolean | undefined | null | ClassValue[];

// Event types
export interface WebSocketMessage {
  type: string;
  data: unknown;
  timestamp: string;
}

// Form types
export interface FormError {
  field: string;
  message: string;
}

export interface FormState<T> {
  data: T;
  errors: FormError[];
  isSubmitting: boolean;
  isValid: boolean;
}