import { Plugin, PaginatedResponse } from "../types";

export const pluginsService = {
  async listPlugins(page = 1, size = 20): Promise<PaginatedResponse<Plugin>> {
    return { items: [], total: 0, page, size };
  },
  async getPlugin(_id: string): Promise<Plugin> {
    throw new Error('Not implemented');
  },
  async installPlugin(_id: string): Promise<Plugin> {
    throw new Error('Not implemented');
  },
  async uninstallPlugin(_id: string): Promise<void> {},
  async togglePlugin(_id: string, _enabled: boolean): Promise<Plugin> {
    throw new Error('Not implemented');
  }
};
