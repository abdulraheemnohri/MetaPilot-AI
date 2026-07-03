// Providers service for MetaPilot AI
// Handles AI provider-related API calls

import { apiService } from './api';
import { AIProvider, ModelInfo, AIRequest, AIResponse, ApiResponse } from '../types';

// Providers API base path
const PROVIDERS_BASE_URL = '/api/providers';

// Providers service
const providersService = {
  // Get all providers
  getAllProviders: async (): Promise<AIProvider[]> => {
    const response = await apiService.get<AIProvider[]>(PROVIDERS_BASE_URL);
    return response.data;
  },

  // Get provider by name
  getProviderByName: async (providerName: string): Promise<AIProvider> => {
    const response = await apiService.get<AIProvider>(
      `${PROVIDERS_BASE_URL}/${providerName}`
    );
    return response.data;
  },

  // Get enabled providers
  getEnabledProviders: async (): Promise<AIProvider[]> => {
    const response = await apiService.get<AIProvider[]>(
      `${PROVIDERS_BASE_URL}/enabled`
    );
    return response.data;
  },

  // Enable provider
  enableProvider: async (providerName: string): Promise<AIProvider> => {
    const response = await apiService.patch<AIProvider>(
      `${PROVIDERS_BASE_URL}/${providerName}/enable`
    );
    return response.data;
  },

  // Disable provider
  disableProvider: async (providerName: string): Promise<AIProvider> => {
    const response = await apiService.patch<AIProvider>(
      `${PROVIDERS_BASE_URL}/${providerName}/disable`
    );
    return response.data;
  },

  // Update provider config
  updateProviderConfig: async (
    providerName: string,
    config: Record<string, any>
  ): Promise<AIProvider> => {
    const response = await apiService.put<AIProvider>(
      `${PROVIDERS_BASE_URL}/${providerName}/config`,
      { config }
    );
    return response.data;
  },

  // Get all models
  getAllModels: async (): Promise<ModelInfo[]> => {
    const response = await apiService.get<ModelInfo[]>(`${PROVIDERS_BASE_URL}/models`);
    return response.data;
  },

  // Get models by provider
  getModelsByProvider: async (providerName: string): Promise<ModelInfo[]> => {
    const response = await apiService.get<ModelInfo[]>(
      `${PROVIDERS_BASE_URL}/${providerName}/models`
    );
    return response.data;
  },

  // Get default model for provider
  getDefaultModel: async (providerName: string): Promise<ModelInfo> => {
    const response = await apiService.get<ModelInfo>(
      `${PROVIDERS_BASE_URL}/${providerName}/default-model`
    );
    return response.data;
  },

  // Set default model for provider
  setDefaultModel: async (
    providerName: string,
    modelId: string
  ): Promise<AIProvider> => {
    const response = await apiService.patch<AIProvider>(
      `${PROVIDERS_BASE_URL}/${providerName}/default-model`,
      { model_id: modelId }
    );
    return response.data;
  },

  // Test provider connection
  testProvider: async (providerName: string): Promise<ApiResponse<{
    success: boolean;
    message?: string;
    error?: string;
  }>> => {
    const response = await apiService.post<ApiResponse<{
      success: boolean;
      message?: string;
      error?: string;
    }>>(`${PROVIDERS_BASE_URL}/${providerName}/test`);
    return response.data;
  },

  // Test model
  testModel: async (
    providerName: string,
    modelId: string,
    request?: AIRequest
  ): Promise<AIResponse> => {
    const response = await apiService.post<AIResponse>(
      `${PROVIDERS_BASE_URL}/${providerName}/models/${modelId}/test`,
      request || { prompt: 'Hello, how are you?' }
    );
    return response.data;
  },

  // Get provider stats
  getProviderStats: async (providerName: string): Promise<ApiResponse<{
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    total_tokens: number;
    avg_latency: number;
    models_available: number;
  }>> => {
    const response = await apiService.get<ApiResponse<{
      total_requests: number;
      successful_requests: number;
      failed_requests: number;
      total_tokens: number;
      avg_latency: number;
      models_available: number;
    }>>(`${PROVIDERS_BASE_URL}/${providerName}/stats`);
    return response.data;
  },

  // Get all providers stats
  getAllProvidersStats: async (): Promise<ApiResponse<Record<string, {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    total_tokens: number;
  }>>> => {
    const response = await apiService.get<ApiResponse<Record<string, {
      total_requests: number;
      successful_requests: number;
      failed_requests: number;
      total_tokens: number;
    }>>>(`${PROVIDERS_BASE_URL}/stats`);
    return response.data;
  },

  // Reset provider stats
  resetProviderStats: async (providerName: string): Promise<void> => {
    await apiService.delete(`${PROVIDERS_BASE_URL}/${providerName}/stats`);
  },

  // Get provider capabilities
  getProviderCapabilities: async (
    providerName: string
  ): Promise<ApiResponse<{
    supports_streaming: boolean;
    supports_images: boolean;
    supports_audio: boolean;
    supports_video: boolean;
    supports_functions: boolean;
    max_tokens: number;
    max_context_length: number;
    models: string[];
  }>> => {
    const response = await apiService.get<ApiResponse<{
      supports_streaming: boolean;
      supports_images: boolean;
      supports_audio: boolean;
      supports_video: boolean;
      supports_functions: boolean;
      max_tokens: number;
      max_context_length: number;
      models: string[];
    }>>(`${PROVIDERS_BASE_URL}/${providerName}/capabilities`);
    return response.data;
  },

  // Get provider pricing
  getProviderPricing: async (
    providerName: string
  ): Promise<ApiResponse<{
    currency: string;
    models: Record<string, {
      prompt_price: number;
      completion_price: number;
      image_price?: number;
      audio_price?: number;
    }>;
  }>> => {
    const response = await apiService.get<ApiResponse<{
      currency: string;
      models: Record<string, {
        prompt_price: number;
        completion_price: number;
        image_price?: number;
        audio_price?: number;
      }>;
    }>>(`${PROVIDERS_BASE_URL}/${providerName}/pricing`);
    return response.data;
  },

  // Estimate cost
  estimateCost: async (
    providerName: string,
    modelId: string,
    promptTokens: number,
    completionTokens: number
  ): Promise<ApiResponse<{
    prompt_cost: number;
    completion_cost: number;
    total_cost: number;
    currency: string;
  }>> => {
    const response = await apiService.post<ApiResponse<{
      prompt_cost: number;
      completion_cost: number;
      total_cost: number;
      currency: string;
    }>>(`${PROVIDERS_BASE_URL}/${providerName}/estimate`, {
      model_id: modelId,
      prompt_tokens: promptTokens,
      completion_tokens: completionTokens,
    });
    return response.data;
  },

  // Get API key status
  getApiKeyStatus: async (providerName: string): Promise<ApiResponse<{
    has_key: boolean;
    is_valid: boolean;
    error?: string;
  }>> => {
    const response = await apiService.get<ApiResponse<{
      has_key: boolean;
      is_valid: boolean;
      error?: string;
    }>>(`${PROVIDERS_BASE_URL}/${providerName}/api-key-status`);
    return response.data;
  },

  // Set API key
  setApiKey: async (
    providerName: string,
    apiKey: string
  ): Promise<ApiResponse<{ success: boolean }>> => {
    const response = await apiService.post<ApiResponse<{ success: boolean }>>(
      `${PROVIDERS_BASE_URL}/${providerName}/api-key`,
      { api_key: apiKey }
    );
    return response.data;
  },

  // Remove API key
  removeApiKey: async (providerName: string): Promise<void> => {
    await apiService.delete(`${PROVIDERS_BASE_URL}/${providerName}/api-key`);
  },

  // Get custom provider
  getCustomProvider: async (providerName: string): Promise<AIProvider> => {
    const response = await apiService.get<AIProvider>(
      `${PROVIDERS_BASE_URL}/custom/${providerName}`
    );
    return response.data;
  },

  // Create custom provider
  createCustomProvider: async (provider: AIProvider): Promise<AIProvider> => {
    const response = await apiService.post<AIProvider>(
      `${PROVIDERS_BASE_URL}/custom`,
      provider
    );
    return response.data;
  },

  // Update custom provider
  updateCustomProvider: async (
    providerName: string,
    provider: Partial<AIProvider>
  ): Promise<AIProvider> => {
    const response = await apiService.put<AIProvider>(
      `${PROVIDERS_BASE_URL}/custom/${providerName}`,
      provider
    );
    return response.data;
  },

  // Delete custom provider
  deleteCustomProvider: async (providerName: string): Promise<void> => {
    await apiService.delete(`${PROVIDERS_BASE_URL}/custom/${providerName}`);
  },

  // Get all custom providers
  getAllCustomProviders: async (): Promise<AIProvider[]> => {
    const response = await apiService.get<AIProvider[]>(
      `${PROVIDERS_BASE_URL}/custom`
    );
    return response.data;
  },

  // Reload providers
  reloadProviders: async (): Promise<ApiResponse<{ reloaded: number }>> => {
    const response = await apiService.post<ApiResponse<{ reloaded: number }>>(
      `${PROVIDERS_BASE_URL}/reload`
    );
    return response.data;
  },

  // Get provider health
  getProviderHealth: async (): Promise<ApiResponse<Record<string, {
    status: 'healthy' | 'unhealthy' | 'disabled';
    latency?: number;
    error?: string;
  }>>> => {
    const response = await apiService.get<ApiResponse<Record<string, {
      status: 'healthy' | 'unhealthy' | 'disabled';
      latency?: number;
      error?: string;
    }>>>(`${PROVIDERS_BASE_URL}/health`);
    return response.data;
  },
};

export default providersService;
