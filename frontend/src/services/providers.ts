import { apiService } from './api';

interface AIProvider {
  id: string;
  name: string;
  type: string;
  isActive: boolean;
  models?: string[];
  baseUrl?: string;
}

interface AIRequest {
  prompt: string;
  model?: string;
  maxTokens?: number;
  temperature?: number;
  providerId: string;
}

interface AIResponse {
  id: string;
  content: string;
  model: string;
  provider: string;
  tokensUsed: number;
  finishReason: string;
  createdAt: string;
}

interface ProviderResponse {
  providers: AIProvider[];
  total: number;
}

export const providersService = {
  async getProviders(): Promise<AIProvider[]> {
    const response = await apiService.get<ProviderResponse>('/api/providers');
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to get providers');
    }
    
    return response.data?.providers || [];
  },
  
  async getProvider(id: string): Promise<AIProvider> {
    const response = await apiService.get<AIProvider>(`/api/providers/${id}`);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to get provider');
    }
    
    return response.data!;
  },
  
  async createProvider(provider: Omit<AIProvider, 'id'>): Promise<AIProvider> {
    const response = await apiService.post<AIProvider>('/api/providers', provider);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to create provider');
    }
    
    return response.data!;
  },
  
  async updateProvider(id: string, updates: Partial<AIProvider>): Promise<AIProvider> {
    const response = await apiService.put<AIProvider>(`/api/providers/${id}`, updates);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to update provider');
    }
    
    return response.data!;
  },
  
  async deleteProvider(id: string): Promise<void> {
    const response = await apiService.delete(`/api/providers/${id}`);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to delete provider');
    }
  },
  
  async testProvider(id: string): Promise<{ success: boolean; message: string }> {
    const response = await apiService.post<{ success: boolean; message: string }>(`/api/providers/${id}/test`);
    
    if (!response.success) {
      throw new Error(response.error || 'Test failed');
    }
    
    return response.data!;
  },
  
  async sendPrompt(request: AIRequest): Promise<AIResponse> {
    const response = await apiService.post<AIResponse>('/api/providers/prompt', request);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to send prompt');
    }
    
    return response.data!;
  },
  
  async getModels(providerId: string): Promise<string[]> {
    const response = await apiService.get<string[]>(`/api/providers/${providerId}/models`);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to get models');
    }
    
    return response.data || [];
  },
};