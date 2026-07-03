"""
MetaPilot AI - Constants

Application constants and configuration values.
"""

// Application constants
export const APP_NAME = 'MetaPilot AI';
export const APP_VERSION = '1.0.0';
export const APP_DESCRIPTION = 'One Request. Multiple AI Systems. One Intelligent Result.';
export const APP_AUTHOR = 'Abdulraheem Nohari';

// API constants
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
export const API_TIMEOUT = 30000; // 30 seconds

// Local storage keys
export const STORAGE_KEYS = {
  TOKEN: 'metapilot_token',
  REFRESH_TOKEN: 'metapilot_refresh_token',
  USER: 'metapilot_user',
  THEME: 'metapilot_theme',
  SETTINGS: 'metapilot_settings',
  CHAT_HISTORY: 'metapilot_chat_history',
  LAST_CONVERSATION: 'metapilot_last_conversation',
};

// Theme constants
export const THEME = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system',
};

// Color constants
export const COLORS = {
  PRIMARY: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },
  SUCCESS: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },
  WARNING: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
  },
  ERROR: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
  },
  NEUTRAL: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#e5e5e5',
    300: '#d4d4d4',
    400: '#a3a3a3',
    500: '#737373',
    600: '#525252',
    700: '#404040',
    800: '#262626',
    900: '#171717',
  },
};

// Breakpoints for responsive design
export const BREAKPOINTS = {
  XS: 480,
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  XXL: 1536,
};

// Z-index values
export const Z_INDEX = {
  DROPDOWN: 100,
  STICKY: 200,
  DRAWER: 300,
  MODAL: 400,
  POPUP: 500,
  TOOLTIP: 600,
  TOAST: 700,
  LOADING: 800,
};

// Animation durations
export const DURATIONS = {
  FAST: 100,
  NORMAL: 200,
  SLOW: 300,
  SLOWER: 500,
};

// Spacing values
export const SPACING = {
  XXS: 2,
  XS: 4,
  SM: 8,
  MD: 12,
  LG: 16,
  XL: 20,
  XXL: 24,
  XXXL: 32,
};

// Border radius values
export const RADIUS = {
  SM: 4,
  MD: 6,
  LG: 8,
  XL: 12,
  FULL: 9999,
};

// Shadow values
export const SHADOWS = {
  SM: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  MD: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  LG: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  XL: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
};

// Typography
export const TYPOGRAPHY = {
  FONT_FAMILY: {
    SANS: 'Inter, system-ui, -apple-system, sans-serif',
    MONO: 'Fira Code, Monaco, Consolas, monospace',
  },
  FONT_SIZE: {
    XS: 12,
    SM: 14,
    MD: 16,
    LG: 18,
    XL: 20,
    XXL: 24,
    XXXL: 30,
  },
  FONT_WEIGHT: {
    LIGHT: 300,
    NORMAL: 400,
    MEDIUM: 500,
    SEMIBOLD: 600,
    BOLD: 700,
  },
  LINE_HEIGHT: {
    TIGHT: 1.25,
    NORMAL: 1.5,
    RELAXED: 1.75,
  },
};

// AI Provider constants
export const PROVIDERS = {
  OPENROUTER: {
    ID: 'openrouter',
    NAME: 'OpenRouter',
    BASE_URL: 'https://openrouter.ai/api/v1',
    TYPE: 'openai-compatible',
  },
  OPENAI: {
    ID: 'openai',
    NAME: 'OpenAI',
    BASE_URL: 'https://api.openai.com/v1',
    TYPE: 'openai',
  },
  ANTHROPIC: {
    ID: 'anthropic',
    NAME: 'Anthropic',
    BASE_URL: 'https://api.anthropic.com/v1',
    TYPE: 'anthropic',
  },
  MISTRAL: {
    ID: 'mistral',
    NAME: 'Mistral',
    BASE_URL: 'https://api.mistral.ai/v1',
    TYPE: 'openai-compatible',
  },
  GOOGLE: {
    ID: 'google',
    NAME: 'Google',
    BASE_URL: 'https://generativelanguage.googleapis.com/v1',
    TYPE: 'google',
  },
  PERPLEXITY: {
    ID: 'perplexity',
    NAME: 'Perplexity',
    BASE_URL: 'https://api.perplexity.ai/v1',
    TYPE: 'openai-compatible',
  },
  LOCAL: {
    ID: 'local',
    NAME: 'Local',
    BASE_URL: '',
    TYPE: 'local',
  },
};

// Model capabilities
export const MODEL_CAPABILITIES = {
  CHAT: 'chat',
  COMPLETION: 'completion',
  EMBEDDINGS: 'embeddings',
  IMAGE_GENERATION: 'image_generation',
  IMAGE_RECOGNITION: 'image_recognition',
  AUDIO_TRANSCRIPTION: 'audio_transcription',
  AUDIO_GENERATION: 'audio_generation',
  FUNCTION_CALLING: 'function_calling',
  VISION: 'vision',
};

// Task types
export const TASK_TYPES = {
  CHAT: 'chat',
  GENERATE: 'generate',
  ANALYZE: 'analyze',
  SUMMARIZE: 'summarize',
  TRANSLATE: 'translate',
  EXPLAIN: 'explain',
  COMPARE: 'compare',
  RESEARCH: 'research',
  CODE: 'code',
  DEBUG: 'debug',
  CUSTOM: 'custom',
};

// Message roles
export const MESSAGE_ROLES = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system',
  PROVIDER: 'provider',
};

// Storage limits
export const STORAGE_LIMITS = {
  MAX_CHAT_HISTORY: 100,
  MAX_CONVERSATIONS: 50,
  MAX_DOCUMENTS: 1000,
  MAX_DOCUMENT_SIZE: 10 * 1024 * 1024, // 10MB
  MAX_IMAGE_SIZE: 5 * 1024 * 1024, // 5MB
};

// Default AI settings
export const DEFAULT_AI_SETTINGS = {
  TEMPERATURE: 0.7,
  MAX_TOKENS: 2000,
  TOP_P: 1.0,
  FREQUENCY_PENALTY: 0.0,
  PRESENCE_PENALTY: 0.0,
  STOP_SEQUENCES: ['\n\n\n'],
};

// Notification types
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
};

// Export all constants
export {
  APP_NAME as default,
};
