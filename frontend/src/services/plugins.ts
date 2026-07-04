/*

import { apiService } from './api';
import { Plugin, ApiResponse, PaginatedResponse } from '../types';
*/

const PLUGINS_BASE_URL = '/api/plugins';

const pluginsService = {
  // Get all plugins
  getAllPlugins: async (
    page: number = 1,
    limit: number = 20,
    category?: string,
    is_enabled?: boolean,
    is_installed?: boolean
  ): Promise<PaginatedResponse<Plugin>> => {
    const params: Record<string, any> = { page, limit };
    if (category) params.category = category;
    if (is_enabled !== undefined) params.is_enabled = is_enabled;
    if (is_installed !== undefined) params.is_installed = is_installed;
    
    const response = await apiService.get<PaginatedResponse<Plugin>>(
      PLUGINS_BASE_URL,
      { params }
    );
    return response.data;
  },

  // Get plugin by ID
  getPluginById: async (pluginId: string): Promise<Plugin> => {
    const response = await apiService.get<Plugin>(
      `${PLUGINS_BASE_URL}/${pluginId}`
    );
    return response.data;
  },

  // Upload plugin
  uploadPlugin: async (
    file: File,
    metadata?: Record<string, any>
  ): Promise<Plugin> => {
    const response = await apiService.upload<Plugin>(
      `${PLUGINS_BASE_URL}/upload`,
      file,
      { metadata }
    );
    return response.data;
  },

  // Install plugin
  installPlugin: async (pluginId: string): Promise<Plugin> => {
    const response = await apiService.post<Plugin>(
      `${PLUGINS_BASE_URL}/${pluginId}/install`
    );
    return response.data;
  },

  // Uninstall plugin
  uninstallPlugin: async (pluginId: string): Promise<Plugin> => {
    const response = await apiService.post<Plugin>(
      `${PLUGINS_BASE_URL}/${pluginId}/uninstall`
    );
    return response.data;
  },

  // Enable plugin
  enablePlugin: async (pluginId: string): Promise<Plugin> => {
    const response = await apiService.patch<Plugin>(
      `${PLUGINS_BASE_URL}/${pluginId}/enable`
    );
    return response.data;
  },

  // Disable plugin
  disablePlugin: async (pluginId: string): Promise<Plugin> => {
    const response = await apiService.patch<Plugin>(
      `${PLUGINS_BASE_URL}/${pluginId}/disable`
    );
    return response.data;
  },

  // Update plugin
  updatePlugin: async (
    pluginId: string,
    data: Partial<Plugin>
  ): Promise<Plugin> => {
    const response = await apiService.put<Plugin>(
      `${PLUGINS_BASE_URL}/${pluginId}`,
      data
    );
    return response.data;
  },

  // Delete plugin
  deletePlugin: async (pluginId: string): Promise<void> => {
    await apiService.delete(`${PLUGINS_BASE_URL}/${pluginId}`);
  },

  // Update plugin config
  updatePluginConfig: async (
    pluginId: string,
    config: Record<string, any>
  ): Promise<Plugin> => {
    const response = await apiService.patch<Plugin>(
      `${PLUGINS_BASE_URL}/${pluginId}/config`,
      { config }
    );
    return response.data;
  },

  // Get plugin categories
  getCategories: async (): Promise<ApiResponse<string[]>> => {
    const response = await apiService.get<ApiResponse<string[]>>(
      `${PLUGINS_BASE_URL}/categories`
    );
    return response.data;
  },

  // Get installed plugins
  getInstalledPlugins: async (): Promise<Plugin[]> => {
    const response = await apiService.get<Plugin[]>(
      `${PLUGINS_BASE_URL}/installed`
    );
    return response.data;
  },

  // Get enabled plugins
  getEnabledPlugins: async (): Promise<Plugin[]> => {
    const response = await apiService.get<Plugin[]>(
      `${PLUGINS_BASE_URL}/enabled`
    );
    return response.data;
  },

  // Get plugin stats
  getPluginStats: async (): Promise<ApiResponse<{
    total: number;
    installed: number;
    enabled: number;
    categories: Record<string, number>;
  }>> => {
    const response = await apiService.get<ApiResponse<{
      total: number;
      installed: number;
      enabled: number;
      categories: Record<string, number>;
    }>>(`${PLUGINS_BASE_URL}/stats`);
    return response.data;
  },

  // Check for plugin updates
  checkForUpdates: async (): Promise<ApiResponse<Plugin[]>> => {
    const response = await apiService.get<ApiResponse<Plugin[]>>(
      `${PLUGINS_BASE_URL}/updates`
    );
    return response.data;
  },

  // Update plugin
  updatePluginVersion: async (pluginId: string): Promise<Plugin> => {
    const response = await apiService.patch<Plugin>(
      `${PLUGINS_BASE_URL}/${pluginId}/update`
    );
    return response.data;
  },

  // Get plugin documentation
  getPluginDocumentation: async (pluginId: string): Promise<ApiResponse<{
    documentation: string;
    usage: string;
    examples: string[];
  }>> => {
    const response = await apiService.get<ApiResponse<{
      documentation: string;
      usage: string;
      examples: string[];
    }>>(`${PLUGINS_BASE_URL}/${pluginId}/docs`);
    return response.data;
  },

  // Test plugin
  testPlugin: async (
    pluginId: string,
    input: Record<string, any>
  ): Promise<ApiResponse<Record<string, any>>> => {
    const response = await apiService.post<ApiResponse<Record<string, any>>>(
      `${PLUGINS_BASE_URL}/${pluginId}/test`,
      { input }
    );
    return response.data;
  },

  // Reload plugins
  reloadPlugins: async (): Promise<ApiResponse<{ reloaded: number }>> => {
    const response = await apiService.post<ApiResponse<{ reloaded: number }>>(
      `${PLUGINS_BASE_URL}/reload`
    );
    return response.data;
  },

  // Clear plugins cache
  clearCache: async (): Promise<void> => {
    await apiService.delete(`${PLUGINS_BASE_URL}/cache`);
  },

  // Get plugin dependencies
  getPluginDependencies: async (pluginId: string): Promise<ApiResponse<Plugin[]>> => {
    const response = await apiService.get<ApiResponse<Plugin[]>>(
      `${PLUGINS_BASE_URL}/${pluginId}/dependencies`
    );
    return response.data;
  },

  // Search plugins
  searchPlugins: async (
    query: string,
    limit: number = 10
  ): Promise<Plugin[]> => {
    const response = await apiService.get<Plugin[]>(
      `${PLUGINS_BASE_URL}/search`,
      { params: { q: query, limit } }
    );
    return response.data;
  },
};

export default pluginsService;
