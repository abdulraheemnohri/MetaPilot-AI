import { apiService } from './api';

interface Task {
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

interface TaskResponse {
  tasks: Task[];
  total: number;
}

interface CreateTaskRequest {
  type: Task['type'];
  title: string;
  description?: string;
  data?: Record<string, unknown>;
}

export const tasksService = {
  async getTasks(status?: Task['status'], page: number = 1, limit: number = 20): Promise<TaskResponse> {
    const params: Record<string, string> = {
      page: page.toString(),
      limit: limit.toString(),
    };
    
    if (status) {
      params.status = status;
    }
    
    const response = await apiService.get<TaskResponse>('/api/tasks', params);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to get tasks');
    }
    
    return response.data!;
  },
  
  async getTask(id: string): Promise<Task> {
    const response = await apiService.get<Task>(`/api/tasks/${id}`);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to get task');
    }
    
    return response.data!;
  },
  
  async createTask(request: CreateTaskRequest): Promise<Task> {
    const response = await apiService.post<Task>('/api/tasks', request);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to create task');
    }
    
    return response.data!;
  },
  
  async cancelTask(id: string): Promise<Task> {
    const response = await apiService.post<Task>(`/api/tasks/${id}/cancel`);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to cancel task');
    }
    
    return response.data!;
  },
  
  async retryTask(id: string): Promise<Task> {
    const response = await apiService.post<Task>(`/api/tasks/${id}/retry`);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to retry task');
    }
    
    return response.data!;
  },
  
  async deleteTask(id: string): Promise<void> {
    const response = await apiService.delete(`/api/tasks/${id}`);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to delete task');
    }
  },
  
  async getTaskResult(id: string): Promise<unknown> {
    const response = await apiService.get<{ result: unknown }>(`/api/tasks/${id}/result`);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to get task result');
    }
    
    return response.data?.result;
  },
  
  async clearCompletedTasks(): Promise<{ cleared: number }> {
    const response = await apiService.delete<{ cleared: number }>('/api/tasks/completed');
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to clear tasks');
    }
    
    return response.data!;
  },
};