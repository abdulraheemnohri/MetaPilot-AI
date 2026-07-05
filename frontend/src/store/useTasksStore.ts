import { create } from 'zustand';
import { Task } from '../types';

export interface TasksState {
  tasks: Task[];
  getTasksByStatus?: (status: string) => Task[];
}

export const useTasksStore = create<TasksState>(() => ({
  tasks: [],
}));
