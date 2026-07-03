"""
MetaPilot AI - Chat Store

Chat interface and conversation state management.
"""

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'provider';
  content: string;
  timestamp: string;
  provider?: string;
  metadata?: Record<string, any>;
  isStreaming?: boolean;
  isError?: boolean;
}

interface Conversation {
  id: string;
  name: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, any>;
}

interface ChatState {
  // Current conversation
  currentConversationId: string | null;
  conversations: Conversation[];
  
  // Messages
  messages: Message[];
  
  // Chat state
  isSending: boolean;
  isStreaming: boolean;
  streamingMessageId: string | null;
  
  // Input
  inputText: string;
  isInputFocused: boolean;
  
  // Actions
  setCurrentConversationId: (id: string | null) => void;
  setConversations: (conversations: Conversation[]) => void;
  addConversation: (conversation: Conversation) => void;
  updateConversation: (id: string, updates: Partial<Conversation>) => void;
  deleteConversation: (id: string) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  deleteMessage: (id: string) => void;
  setIsSending: (isSending: boolean) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  setStreamingMessageId: (id: string | null) => void;
  setInputText: (text: string) => void;
  setIsInputFocused: (isFocused: boolean) => void;
  appendToMessage: (id: string, text: string) => void;
  clearMessages: () => void;
  clearInput: () => void;
  reset: () => void;
}

const initialState = {
  currentConversationId: null,
  conversations: [],
  messages: [],
  isSending: false,
  isStreaming: false,
  streamingMessageId: null,
  inputText: '',
  isInputFocused: false,
};

export const useChatStore = create<ChatState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,
        
        setCurrentConversationId: (id) => set({ currentConversationId: id }),
        
        setConversations: (conversations) => set({ conversations }),
        
        addConversation: (conversation) =>
          set((state) => ({
            conversations: [...state.conversations, conversation],
          })),
        
        updateConversation: (id, updates) =>
          set((state) => ({
            conversations: state.conversations.map((conv) =>
              conv.id === id ? { ...conv, ...updates } : conv
            ),
          })),
        
        deleteConversation: (id) =>
          set((state) => ({
            conversations: state.conversations.filter((conv) => conv.id !== id),
            currentConversationId: state.currentConversationId === id 
              ? null 
              : state.currentConversationId,
          })),
        
        setMessages: (messages) => set({ messages }),
        
        addMessage: (message) =>
          set((state) => ({
            messages: [...state.messages, message],
          })),
        
        updateMessage: (id, updates) =>
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === id ? { ...msg, ...updates } : msg
            ),
          })),
        
        deleteMessage: (id) =>
          set((state) => ({
            messages: state.messages.filter((msg) => msg.id !== id),
          })),
        
        setIsSending: (isSending) => set({ isSending }),
        setIsStreaming: (isStreaming) => set({ isStreaming }),
        setStreamingMessageId: (id) => set({ streamingMessageId: id }),
        
        setInputText: (text) => set({ inputText: text }),
        setIsInputFocused: (isFocused) => set({ isInputFocused: isFocused }),
        
        appendToMessage: (id, text) =>
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === id ? { ...msg, content: msg.content + text } : msg
            ),
          })),
        
        clearMessages: () => set({ messages: [] }),
        
        clearInput: () => set({ inputText: '' }),
        
        reset: () => set(initialState),
      }),
      {
        name: 'chat-store',
        partialize: (state) => ({
          currentConversationId: state.currentConversationId,
          conversations: state.conversations,
          messages: state.messages,
        }),
      }
    ),
    { name: 'ChatStore' }
  )
);

// Selector hooks
export const useCurrentConversationId = () => useChatStore((state) => state.currentConversationId);
export const useConversations = () => useChatStore((state) => state.conversations);
export const useMessages = () => useChatStore((state) => state.messages);
export const useIsSending = () => useChatStore((state) => state.isSending);
export const useIsStreaming = () => useChatStore((state) => state.isStreaming);
export const useStreamingMessageId = () => useChatStore((state) => state.streamingMessageId);
export const useInputText = () => useChatStore((state) => state.inputText);
export const useIsInputFocused = () => useChatStore((state) => state.isInputFocused);

// Helper hooks
export const useCurrentConversation = () => 
  useChatStore((state) => 
    state.conversations.find(c => c.id === state.currentConversationId) || null
  );

export const useMessageCount = () => useChatStore((state) => state.messages.length);
export const useHasMessages = () => useChatStore((state) => state.messages.length > 0);
