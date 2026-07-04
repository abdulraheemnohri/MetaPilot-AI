// Application constants and configuration values

// API Configuration
export const API_ENDPOINTS = {
  HEALTH: '/api/health',
  AUTH: {
    LOGIN: '/api/auth/token',
    REGISTER: '/api/auth/register',
    LOGOUT: '/api/auth/logout',
    REFRESH: '/api/auth/refresh',
    ME: '/api/auth/me',
    CHANGE_PASSWORD: '/api/auth/change-password',
  },
  CHAT: {
    MESSAGES: '/api/chat/messages',
    CONVERSATIONS: '/api/chat/conversations',
  },
  KNOWLEDGE: {
    DOCUMENTS: '/api/knowledge/documents',
    UPLOAD: '/api/knowledge/upload',
    SEARCH: '/api/knowledge/search',
  },
  PROVIDERS: {
    LIST: '/api/providers',
    TEST: '/api/providers/test',
    PROMPT: '/api/providers/prompt',
  },
  TASKS: {
    LIST: '/api/tasks',
    CANCEL: '/api/tasks/cancel',
    RETRY: '/api/tasks/retry',
  },
  PLUGINS: {
    LIST: '/api/plugins',
    INSTALL: '/api/plugins/install',
    UNINSTALL: '/api/plugins/uninstall',
  },
  MERGE: {
    FUSE: '/api/merge/fuse',
    SIMILARITY: '/api/merge/similarity',
    DUPLICATES: '/api/merge/duplicates/remove',
    CONFLICTS: '/api/merge/conflicts/resolve',
  },
};

// AI Provider Types
export const AI_PROVIDER_TYPES = [
  'openai',
  'anthropic',
  'mistral',
  'google',
  'perplexity',
  'local',
] as const;

export type AIProviderType = typeof AI_PROVIDER_TYPES[number];

// Task Types
export const TASK_TYPES = [
  'ai_inference',
  'document_processing',
  'export',
  'knowledge_update',
] as const;

export type TaskType = typeof TASK_TYPES[number];

// Task Statuses
export const TASK_STATUSES = [
  'pending',
  'running',
  'completed',
  'failed',
  'cancelled',
] as const;

export type TaskStatus = typeof TASK_STATUSES[number];

// Message Roles
export const MESSAGE_ROLES = ['user', 'assistant', 'system'] as const;
export type MessageRole = typeof MESSAGE_ROLES[number];

// Default Settings
export const DEFAULT_SETTINGS = {
  MAX_TOKENS: 4096,
  TEMPERATURE: 0.7,
  TOP_P: 1.0,
  FREQUENCY_PENALTY: 0.0,
  PRESENCE_PENALTY: 0.0,
};

// Storage Keys
export const STORAGE_KEYS = {
  AUTH: 'meta-pilot-auth',
  SETTINGS: 'meta-pilot-settings',
  PROVIDERS: 'meta-pilot-providers',
  CHAT_HISTORY: 'meta-pilot-chat-history',
};

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  AUTH_ERROR: 'Authentication failed. Please login again.',
  VALIDATION_ERROR: 'Validation error. Please check your input.',
  NOT_FOUND: 'Resource not found.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  RATE_LIMIT: 'Rate limit exceeded. Please try again later.',
  SERVER_ERROR: 'Server error. Please try again later.',
};

// Success Messages
export const SUCCESS_MESSAGES = {
  LOGIN: 'Logged in successfully!',
  LOGOUT: 'Logged out successfully!',
  REGISTER: 'Account created successfully!',
  SAVE: 'Settings saved successfully!',
  DELETE: 'Deleted successfully!',
  UPDATE: 'Updated successfully!',
};