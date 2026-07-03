"""
MetaPilot AI - Knowledge Store

Knowledge base and document management state.
"""

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface Document {
  id: string;
  name: string;
  path: string;
  type: string;
  size: number;
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, any>;
  isProcessed: boolean;
  isIndexed: boolean;
  chunks?: number;
  embeddingsGenerated?: boolean;
}

interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  documentCount: number;
  createdAt: string;
  updatedAt: string;
  isEnabled: boolean;
  metadata?: Record<string, any>;
}

interface SearchResult {
  id: string;
  documentId: string;
  content: string;
  score: number;
  metadata?: Record<string, any>;
}

interface KnowledgeState {
  // Knowledge bases
  knowledgeBases: KnowledgeBase[];
  currentKnowledgeBaseId: string | null;
  
  // Documents
  documents: Document[];
  selectedDocumentIds: string[];
  
  // Search
  searchQuery: string;
  searchResults: SearchResult[];
  isSearching: boolean;
  
  // Upload
  isUploading: boolean;
  uploadProgress: Record<string, number>;
  
  // Processing
  isProcessing: boolean;
  processingDocumentIds: string[];
  
  // State
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setKnowledgeBases: (knowledgeBases: KnowledgeBase[]) => void;
  addKnowledgeBase: (knowledgeBase: KnowledgeBase) => void;
  updateKnowledgeBase: (id: string, updates: Partial<KnowledgeBase>) => void;
  deleteKnowledgeBase: (id: string) => void;
  setCurrentKnowledgeBaseId: (id: string | null) => void;
  
  setDocuments: (documents: Document[]) => void;
  addDocument: (document: Document) => void;
  updateDocument: (id: string, updates: Partial<Document>) => void;
  deleteDocument: (id: string) => void;
  setSelectedDocumentIds: (ids: string[]) => void;
  
  setSearchQuery: (query: string) => void;
  setSearchResults: (results: SearchResult[]) => void;
  setIsSearching: (isSearching: boolean) => void;
  
  setIsUploading: (isUploading: boolean) => void;
  setUploadProgress: (id: string, progress: number) => void;
  
  setIsProcessing: (isProcessing: boolean) => void;
  addProcessingDocumentId: (id: string) => void;
  removeProcessingDocumentId: (id: string) => void;
  
  setIsLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  
  reset: () => void;
}

const initialState = {
  knowledgeBases: [],
  currentKnowledgeBaseId: null,
  documents: [],
  selectedDocumentIds: [],
  searchQuery: '',
  searchResults: [],
  isSearching: false,
  isUploading: false,
  uploadProgress: {},
  isProcessing: false,
  processingDocumentIds: [],
  isLoading: false,
  error: null,
};

export const useKnowledgeStore = create<KnowledgeState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,
        
        setKnowledgeBases: (knowledgeBases) => set({ knowledgeBases }),
        
        addKnowledgeBase: (knowledgeBase) =>
          set((state) => ({
            knowledgeBases: [...state.knowledgeBases, knowledgeBase],
          })),
        
        updateKnowledgeBase: (id, updates) =>
          set((state) => ({
            knowledgeBases: state.knowledgeBases.map((kb) =>
              kb.id === id ? { ...kb, ...updates } : kb
            ),
          })),
        
        deleteKnowledgeBase: (id) =>
          set((state) => ({
            knowledgeBases: state.knowledgeBases.filter((kb) => kb.id !== id),
            currentKnowledgeBaseId: state.currentKnowledgeBaseId === id 
              ? null 
              : state.currentKnowledgeBaseId,
          })),
        
        setCurrentKnowledgeBaseId: (id) => set({ currentKnowledgeBaseId: id }),
        
        setDocuments: (documents) => set({ documents }),
        
        addDocument: (document) =>
          set((state) => ({
            documents: [...state.documents, document],
          })),
        
        updateDocument: (id, updates) =>
          set((state) => ({
            documents: state.documents.map((doc) =>
              doc.id === id ? { ...doc, ...updates } : doc
            ),
          })),
        
        deleteDocument: (id) =>
          set((state) => ({
            documents: state.documents.filter((doc) => doc.id !== id),
            selectedDocumentIds: state.selectedDocumentIds.filter((id) => id !== id),
          })),
        
        setSelectedDocumentIds: (ids) => set({ selectedDocumentIds: ids }),
        
        setSearchQuery: (query) => set({ searchQuery: query }),
        setSearchResults: (results) => set({ searchResults: results }),
        setIsSearching: (isSearching) => set({ isSearching }),
        
        setIsUploading: (isUploading) => set({ isUploading }),
        setUploadProgress: (id, progress) =>
          set((state) => ({
            uploadProgress: {
              ...state.uploadProgress,
              [id]: progress,
            },
          })),
        
        setIsProcessing: (isProcessing) => set({ isProcessing }),
        
        addProcessingDocumentId: (id) =>
          set((state) => ({
            processingDocumentIds: [...state.processingDocumentIds, id],
          })),
        
        removeProcessingDocumentId: (id) =>
          set((state) => ({
            processingDocumentIds: state.processingDocumentIds.filter((docId) => docId !== id),
          })),
        
        setIsLoading: (isLoading) => set({ isLoading }),
        setError: (error) => set({ error }),
        
        reset: () => set(initialState),
      }),
      {
        name: 'knowledge-store',
        partialize: (state) => ({
          knowledgeBases: state.knowledgeBases,
          currentKnowledgeBaseId: state.currentKnowledgeBaseId,
          documents: state.documents,
        }),
      }
    ),
    { name: 'KnowledgeStore' }
  )
);

// Selector hooks
export const useKnowledgeBases = () => useKnowledgeStore((state) => state.knowledgeBases);
export const useCurrentKnowledgeBaseId = () => useKnowledgeStore((state) => state.currentKnowledgeBaseId);
export const useDocuments = () => useKnowledgeStore((state) => state.documents);
export const useSelectedDocumentIds = () => useKnowledgeStore((state) => state.selectedDocumentIds);
export const useSearchQuery = () => useKnowledgeStore((state) => state.searchQuery);
export const useSearchResults = () => useKnowledgeStore((state) => state.searchResults);
export const useIsSearching = () => useKnowledgeStore((state) => state.isSearching);
export const useIsUploading = () => useKnowledgeStore((state) => state.isUploading);
export const useUploadProgress = () => useKnowledgeStore((state) => state.uploadProgress);
export const useIsProcessing = () => useKnowledgeStore((state) => state.isProcessing);
export const useProcessingDocumentIds = () => useKnowledgeStore((state) => state.processingDocumentIds);
export const useIsLoading = () => useKnowledgeStore((state) => state.isLoading);
export const useError = () => useKnowledgeStore((state) => state.error);

// Helper hooks
export const useCurrentKnowledgeBase = () => 
  useKnowledgeStore((state) => 
    state.knowledgeBases.find(kb => kb.id === state.currentKnowledgeBaseId) || null
  );

export const useDocumentCount = () => useKnowledgeStore((state) => state.documents.length);
export const useSelectedDocuments = () => 
  useKnowledgeStore((state) => 
    state.documents.filter(doc => state.selectedDocumentIds.includes(doc.id))
  );

export const useKnowledgeBaseById = (id: string) => 
  useKnowledgeStore((state) => 
    state.knowledgeBases.find(kb => kb.id === id) || null
  );

export const useDocumentById = (id: string) => 
  useKnowledgeStore((state) => 
    state.documents.find(doc => doc.id === id) || null
  );

export const useUploadProgressById = (id: string) => 
  useKnowledgeStore((state) => 
    state.uploadProgress[id] || 0
  );

export const useIsDocumentProcessing = (id: string) => 
  useKnowledgeStore((state) => 
    state.processingDocumentIds.includes(id)
  );
