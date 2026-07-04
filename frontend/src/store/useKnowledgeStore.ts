import { create } from 'zustand';

interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadedAt: string;
  processedAt?: string;
  status: 'uploaded' | 'processing' | 'processed' | 'failed';
}

interface KnowledgeState {
  documents: Document[];
  isLoading: boolean;
  isUploading: boolean;
  
  addDocument: (document: Document) => void;
  removeDocument: (id: string) => void;
  updateDocument: (id: string, updates: Partial<Document>) => void;
  setDocuments: (documents: Document[]) => void;
  setLoading: (isLoading: boolean) => void;
  setUploading: (isUploading: boolean) => void;
  deleteDocument: (id: string) => void;
}

export const useKnowledgeStore = create<KnowledgeState>((set) => ({
  documents: [],
  isLoading: false,
  isUploading: false,
  
  addDocument: (document) => set((state) => ({
    documents: [...state.documents, document]
  })),
  
  removeDocument: (id) => set((state) => ({
    documents: state.documents.filter(doc => doc.id !== id)
  })),
  
  updateDocument: (id, updates) => set((state) => ({
    documents: state.documents.map(doc =>
      doc.id === id ? { ...doc, ...updates } : doc
    )
  })),
  
  setDocuments: (documents) => set({ documents }),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  setUploading: (isUploading) => set({ isUploading }),
  
  deleteDocument: (id) => set((state) => ({
    documents: state.documents.filter(doc => doc.id !== id)
  })),
}));