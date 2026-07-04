import { create } from 'zustand';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  id?: string;
  timestamp?: Date;
}

interface ChatState {
  messages: Message[];
  currentConversationId: string | null;
  isLoading: boolean;
  
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  clearMessages: () => void;
  setConversationId: (id: string | null) => void;
  setLoading: (isLoading: boolean) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  currentConversationId: null,
  isLoading: false,
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, { ...message, id: Date.now().toString(), timestamp: new Date() }]
  })),
  
  setMessages: (messages) => set({ messages }),
  
  clearMessages: () => set({ messages: [] }),
  
  setConversationId: (id) => set({ currentConversationId: id }),
  
  setLoading: (isLoading) => set({ isLoading }),
}));