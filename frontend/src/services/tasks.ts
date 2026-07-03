// Tasks service for MetaPilot AI
// Handles task-related API calls

import { apiService } from './api';
import { Task, AIRequest, AIResponse, ApiResponse, PaginatedResponse } from '../types';

// Tasks API base path
const TASKS_BASE_URL = '/api/tasks';

// Tasks service
const tasksService = {
  // Get all tasks
  getAllTasks: async (
    page: number = 1,
    limit: number = 20,
    status?: Task['status'],
    task_type?: string,
    project_id?: string
  ): Promise<PaginatedResponse<Task>> => {
    const params: Record<string, any> = { page, limit };
    if (status) params.status = status;
    if (task_type) params.task_type = task_type;
    if (project_id) params.project_id = project_id;
    
    const response = await apiService.get<PaginatedResponse<Task>>(
      TASKS_BASE_URL,
      { params }
    );
    return response.data;
  },

  // Get task by ID
  getTaskById: async (taskId: string): Promise<Task> => {
    const response = await apiService.get<Task>(`${TASKS_BASE_URL}/${taskId}`);
    return response.data;
  },

  // Create new task
  createTask: async (taskData: Partial<Task> & AIRequest): Promise<Task> => {
    const response = await apiService.post<Task>(TASKS_BASE_URL, taskData);
    return response.data;
  },

  // Update task
  updateTask: async (taskId: string, data: Partial<Task>): Promise<Task> => {
    const response = await apiService.put<Task>(
      `${TASKS_BASE_URL}/${taskId}`,
      data
    );
    return response.data;
  },

  // Delete task
  deleteTask: async (taskId: string): Promise<void> => {
    await apiService.delete(`${TASKS_BASE_URL}/${taskId}`);
  },

  // Execute task (run immediately)
  executeTask: async (taskId: string): Promise<AIResponse> => {
    const response = await apiService.post<AIResponse>(
      `${TASKS_BASE_URL}/${taskId}/execute`
    );
    return response.data;
  },

  // Cancel task
  cancelTask: async (taskId: string): Promise<Task> => {
    const response = await apiService.patch<Task>(
      `${TASKS_BASE_URL}/${taskId}/cancel`
    );
    return response.data;
  },

  // Retry failed task
  retryTask: async (taskId: string): Promise<Task> => {
    const response = await apiService.post<Task>(
      `${TASKS_BASE_URL}/${taskId}/retry`
    );
    return response.data;
  },

  // Get task result
  getTaskResult: async (taskId: string): Promise<AIResponse> => {
    const response = await apiService.get<AIResponse>(
      `${TASKS_BASE_URL}/${taskId}/result`
    );
    return response.data;
  },

  // Get task logs
  getTaskLogs: async (taskId: string): Promise<ApiResponse<string[]>> => {
    const response = await apiService.get<ApiResponse<string[]>>(
      `${TASKS_BASE_URL}/${taskId}/logs`
    );
    return response.data;
  },

  // Get tasks by project
  getTasksByProject: async (
    projectId: string,
    page: number = 1,
    limit: number = 20
  ): Promise<PaginatedResponse<Task>> => {
    const response = await apiService.get<PaginatedResponse<Task>>(
      `${TASKS_BASE_URL}/project/${projectId}`,
      { params: { page, limit } }
    );
    return response.data;
  },

  // Get tasks by user
  getTasksByUser: async (
    userId: number,
    page: number = 1,
    limit: number = 20
  ): Promise<PaginatedResponse<Task>> => {
    const response = await apiService.get<PaginatedResponse<Task>>(
      `${TASKS_BASE_URL}/user/${userId}`,
      { params: { page, limit } }
    );
    return response.data;
  },

  // Get tasks stats
  getTasksStats: async (): Promise<ApiResponse<{
    total: number;
    completed: number;
    processing: number;
    pending: number;
    failed: number;
    cancelled: number;
    avg_latency: number;
    total_tokens: number;
  }>> => {
    const response = await apiService.get<ApiResponse<{
      total: number;
      completed: number;
      processing: number;
      pending: number;
      failed: number;
      cancelled: number;
      avg_latency: number;
      total_tokens: number;
    }>>(`${TASKS_BASE_URL}/stats`);
    return response.data;
  },

  // Clear completed tasks
  clearCompletedTasks: async (): Promise<ApiResponse<{ deleted_count: number }>> => {
    const response = await apiService.delete<ApiResponse<{ deleted_count: number }>>(
      `${TASKS_BASE_URL}/clear-completed`
    );
    return response.data;
  },

  // Clear all tasks
  clearAllTasks: async (): Promise<void> => {
    await apiService.delete(`${TASKS_BASE_URL}/clear-all`);
  },

  // Batch create tasks
  createTasksBatch: async (tasks: (Partial<Task> & AIRequest)[]): Promise<Task[]> => {
    const response = await apiService.post<Task[]>(
      `${TASKS_BASE_URL}/batch`,
      { tasks }
    );
    return response.data;
  },

  // Update task priority
  updateTaskPriority: async (
    taskId: string,
    priority: number
  ): Promise<Task> => {
    const response = await apiService.patch<Task>(
      `${TASKS_BASE_URL}/${taskId}/priority`,
      { priority }
    );
    return response.data;
  },

  // Get task dependencies
  getTaskDependencies: async (taskId: string): Promise<ApiResponse<Task[]>> => {
    const response = await apiService.get<ApiResponse<Task[]>>(
      `${TASKS_BASE_URL}/${taskId}/dependencies`
    );
    return response.data;
  },

  // Add task dependency
  addTaskDependency: async (
    taskId: string,
    dependsOnTaskId: string
  ): Promise<ApiResponse<Task>> => {
    const response = await apiService.post<ApiResponse<Task>>(
      `${TASKS_BASE_URL}/${taskId}/dependencies`,
      { depends_on: dependsOnTaskId }
    );
    return response.data;
  },

  // Remove task dependency
  removeTaskDependency: async (
    taskId: string,
    dependsOnTaskId: string
  ): Promise<void> => {
    await apiService.delete(
      `${TASKS_BASE_URL}/${taskId}/dependencies/${dependsOnTaskId}`
    );
  },

  // Schedule task
  scheduleTask: async (
    taskId: string,
    scheduledAt: string
  ): Promise<Task> => {
    const response = await apiService.patch<Task>(
      `${TASKS_BASE_URL}/${taskId}/schedule`,
      { scheduled_at: scheduledAt }
    );
    return response.data;
  },

  // Get scheduled tasks
  getScheduledTasks: async (): Promise<Task[]> => {
    const response = await apiService.get<Task[]>(`${TASKS_BASE_URL}/scheduled`);
    return response.data;
  },

  // Run scheduled tasks
  runScheduledTasks: async (): Promise<ApiResponse<{ started_count: number }>> => {
    const response = await apiService.post<ApiResponse<{ started_count: number }>>(
      `${TASKS_BASE_URL}/run-scheduled`
    );
    return response.data;
  },
};

export default tasksService;
