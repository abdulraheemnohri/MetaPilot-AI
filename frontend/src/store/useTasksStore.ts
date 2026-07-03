"""
MetaPilot AI - Tasks Store

Task management and execution state.
"""

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface Task {
  id: string;
  name: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number; // 0-100
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  result?: any;
  error?: string;
  metadata?: Record<string, any>;
}

interface TaskLog {
  id: string;
  taskId: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  metadata?: Record<string, any>;
}

interface TasksState {
  // Tasks
  tasks: Task[];
  selectedTaskIds: string[];
  
  // Logs
  logs: TaskLog[];
  
  // Execution
  isExecuting: boolean;
  executingTaskId: string | null;
  
  // Queue
  queueSize: number;
  activeTasks: number;
  
  // State
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  deleteTask: (id: string) => void;
  setSelectedTaskIds: (ids: string[]) => void;
  
  setLogs: (logs: TaskLog[]) => void;
  addLog: (log: TaskLog) => void;
  clearLogs: (taskId?: string) => void;
  
  setIsExecuting: (isExecuting: boolean) => void;
  setExecutingTaskId: (id: string | null) => void;
  
  setQueueSize: (size: number) => void;
  setActiveTasks: (count: number) => void;
  
  setIsLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  
  cancelTask: (id: string) => void;
  retryTask: (id: string) => void;
  clearCompletedTasks: () => void;
  
  reset: () => void;
}

const initialState = {
  tasks: [],
  selectedTaskIds: [],
  logs: [],
  isExecuting: false,
  executingTaskId: null,
  queueSize: 0,
  activeTasks: 0,
  isLoading: false,
  error: null,
};

export const useTasksStore = create<TasksState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,
        
        setTasks: (tasks) => set({ tasks }),
        
        addTask: (task) =>
          set((state) => ({
            tasks: [...state.tasks, task],
          })),
        
        updateTask: (id, updates) =>
          set((state) => ({
            tasks: state.tasks.map((t) =>
              t.id === id ? { ...t, ...updates } : t
            ),
          })),
        
        deleteTask: (id) =>
          set((state) => ({
            tasks: state.tasks.filter((t) => t.id !== id),
            selectedTaskIds: state.selectedTaskIds.filter((tid) => tid !== id),
          })),
        
        setSelectedTaskIds: (ids) => set({ selectedTaskIds: ids }),
        
        setLogs: (logs) => set({ logs }),
        
        addLog: (log) =>
          set((state) => ({
            logs: [...state.logs, log],
          })),
        
        clearLogs: (taskId) =>
          set((state) => ({
            logs: taskId 
              ? state.logs.filter((l) => l.taskId !== taskId)
              : [],
          })),
        
        setIsExecuting: (isExecuting) => set({ isExecuting }),
        setExecutingTaskId: (id) => set({ executingTaskId: id }),
        
        setQueueSize: (size) => set({ queueSize: size }),
        setActiveTasks: (count) => set({ activeTasks: count }),
        
        setIsLoading: (isLoading) => set({ isLoading }),
        setError: (error) => set({ error }),
        
        cancelTask: (id) =>
          set((state) => ({
            tasks: state.tasks.map((t) =>
              t.id === id ? { ...t, status: 'cancelled' as const } : t
            ),
          })),
        
        retryTask: (id) =>
          set((state) => ({
            tasks: state.tasks.map((t) =>
              t.id === id 
                ? { 
                    ...t, 
                    status: 'pending' as const, 
                    progress: 0, 
                    startedAt: undefined, 
                    completedAt: undefined, 
                    error: undefined 
                  }
                : t
            ),
          })),
        
        clearCompletedTasks: () =>
          set((state) => ({
            tasks: state.tasks.filter((t) => 
              t.status === 'pending' || t.status === 'running'
            ),
          })),
        
        reset: () => set(initialState),
      }),
      {
        name: 'tasks-store',
        partialize: (state) => ({
          tasks: state.tasks,
          selectedTaskIds: state.selectedTaskIds,
        }),
      }
    ),
    { name: 'TasksStore' }
  )
);

// Selector hooks
export const useTasks = () => useTasksStore((state) => state.tasks);
export const useSelectedTaskIds = () => useTasksStore((state) => state.selectedTaskIds);
export const useLogs = () => useTasksStore((state) => state.logs);
export const useIsExecuting = () => useTasksStore((state) => state.isExecuting);
export const useExecutingTaskId = () => useTasksStore((state) => state.executingTaskId);
export const useQueueSize = () => useTasksStore((state) => state.queueSize);
export const useActiveTasks = () => useTasksStore((state) => state.activeTasks);
export const useIsLoading = () => useTasksStore((state) => state.isLoading);
export const useError = () => useTasksStore((state) => state.error);

// Helper hooks
export const useTaskCount = () => useTasksStore((state) => state.tasks.length);
export const useRunningTasks = () => 
  useTasksStore((state) => 
    state.tasks.filter(t => t.status === 'running')
  );

export const usePendingTasks = () => 
  useTasksStore((state) => 
    state.tasks.filter(t => t.status === 'pending')
  );

export const useCompletedTasks = () => 
  useTasksStore((state) => 
    state.tasks.filter(t => t.status === 'completed')
  );

export const useFailedTasks = () => 
  useTasksStore((state) => 
    state.tasks.filter(t => t.status === 'failed')
  );

export const useTaskById = (id: string) => 
  useTasksStore((state) => 
    state.tasks.find(t => t.id === id) || null
  );

export const useSelectedTasks = () => 
  useTasksStore((state) => 
    state.tasks.filter(t => state.selectedTaskIds.includes(t.id))
  );

export const useTaskLogs = (taskId: string) => 
  useTasksStore((state) => 
    state.logs.filter(l => l.taskId === taskId)
  );

export const useHasRunningTasks = () => 
  useTasksStore((state) => 
    state.tasks.some(t => t.status === 'running')
  );

export const useHasPendingTasks = () => 
  useTasksStore((state) => 
    state.tasks.some(t => t.status === 'pending')
  );
