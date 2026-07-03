// Knowledge service for MetaPilot AI
// Handles knowledge base-related API calls

import { apiService } from './api';
import {
  KnowledgeDocument,
  KnowledgeChunk,
  Embedding,
  SearchResult,
  ApiResponse,
  PaginatedResponse,
} from '../types';

// Knowledge API base path
const KNOWLEDGE_BASE_URL = '/api/knowledge';

// Knowledge service
const knowledgeService = {
  // Documents
  
  // Get all documents
  getAllDocuments: async (
    page: number = 1,
    limit: number = 20,
    search?: string
  ): Promise<PaginatedResponse<KnowledgeDocument>> => {
    const params: Record<string, any> = { page, limit };
    if (search) params.search = search;
    
    const response = await apiService.get<PaginatedResponse<KnowledgeDocument>>(
      `${KNOWLEDGE_BASE_URL}/documents`,
      { params }
    );
    return response.data;
  },

  // Get document by ID
  getDocumentById: async (documentId: string): Promise<KnowledgeDocument> => {
    const response = await apiService.get<KnowledgeDocument>(
      `${KNOWLEDGE_BASE_URL}/documents/${documentId}`
    );
    return response.data;
  },

  // Upload document
  uploadDocument: async (
    file: File,
    metadata?: Record<string, any>
  ): Promise<KnowledgeDocument> => {
    const formData = new FormData();
    formData.append('file', file);
    
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    const response = await apiService.upload<KnowledgeDocument>(
      `${KNOWLEDGE_BASE_URL}/documents/upload`,
      file,
      { metadata }
    );
    return response.data;
  },

  // Update document
  updateDocument: async (
    documentId: string,
    data: Partial<KnowledgeDocument>
  ): Promise<KnowledgeDocument> => {
    const response = await apiService.put<KnowledgeDocument>(
      `${KNOWLEDGE_BASE_URL}/documents/${documentId}`,
      data
    );
    return response.data;
  },

  // Delete document
  deleteDocument: async (documentId: string): Promise<void> => {
    await apiService.delete(`${KNOWLEDGE_BASE_URL}/documents/${documentId}`);
  },

  // Process document (extract text and create chunks)
  processDocument: async (documentId: string): Promise<ApiResponse<{
    document: KnowledgeDocument;
    chunks: KnowledgeChunk[];
  }>> => {
    const response = await apiService.post<ApiResponse<{
      document: KnowledgeDocument;
      chunks: KnowledgeChunk[];
    }>>(`${KNOWLEDGE_BASE_URL}/documents/${documentId}/process`);
    return response.data;
  },

  // Chunks
  
  // Get all chunks for a document
  getDocumentChunks: async (
    documentId: string,
    page: number = 1,
    limit: number = 50
  ): Promise<PaginatedResponse<KnowledgeChunk>> => {
    const response = await apiService.get<PaginatedResponse<KnowledgeChunk>>(
      `${KNOWLEDGE_BASE_URL}/documents/${documentId}/chunks`,
      { params: { page, limit } }
    );
    return response.data;
  },

  // Get chunk by ID
  getChunkById: async (chunkId: string): Promise<KnowledgeChunk> => {
    const response = await apiService.get<KnowledgeChunk>(
      `${KNOWLEDGE_BASE_URL}/chunks/${chunkId}`
    );
    return response.data;
  },

  // Update chunk
  updateChunk: async (
    chunkId: string,
    data: Partial<KnowledgeChunk>
  ): Promise<KnowledgeChunk> => {
    const response = await apiService.put<KnowledgeChunk>(
      `${KNOWLEDGE_BASE_URL}/chunks/${chunkId}`,
      data
    );
    return response.data;
  },

  // Delete chunk
  deleteChunk: async (chunkId: string): Promise<void> => {
    await apiService.delete(`${KNOWLEDGE_BASE_URL}/chunks/${chunkId}`);
  },

  // Embeddings
  
  // Get all embeddings
  getAllEmbeddings: async (
    page: number = 1,
    limit: number = 50
  ): Promise<PaginatedResponse<Embedding>> => {
    const response = await apiService.get<PaginatedResponse<Embedding>>(
      `${KNOWLEDGE_BASE_URL}/embeddings`,
      { params: { page, limit } }
    );
    return response.data;
  },

  // Get embeddings for a document
  getDocumentEmbeddings: async (
    documentId: string
  ): Promise<Embedding[]> => {
    const response = await apiService.get<Embedding[]>(
      `${KNOWLEDGE_BASE_URL}/documents/${documentId}/embeddings`
    );
    return response.data;
  },

  // Generate embeddings for text
  generateEmbeddings: async (
    text: string,
    model?: string
  ): Promise<ApiResponse<{ embedding: number[]; dimension: number }>> => {
    const response = await apiService.post<ApiResponse<{
      embedding: number[];
      dimension: number;
    }>>(`${KNOWLEDGE_BASE_URL}/embeddings/generate`, { text, model });
    return response.data;
  },

  // Delete embedding
  deleteEmbedding: async (embeddingId: string): Promise<void> => {
    await apiService.delete(`${KNOWLEDGE_BASE_URL}/embeddings/${embeddingId}`);
  },

  // Search
  
  // Search knowledge base
  searchKnowledge: async (
    query: string,
    options?: {
      limit?: number;
      model?: string;
      include_metadata?: boolean;
    }
  ): Promise<ApiResponse<{ results: SearchResult[] }>> => {
    const response = await apiService.post<ApiResponse<{ results: SearchResult[] }>>(
      `${KNOWLEDGE_BASE_URL}/search`,
      { query, ...options }
    );
    return response.data;
  },

  // Semantic search
  semanticSearch: async (
    query: string,
    options?: {
      limit?: number;
      model?: string;
      threshold?: number;
    }
  ): Promise<ApiResponse<{ results: SearchResult[] }>> => {
    const response = await apiService.post<ApiResponse<{ results: SearchResult[] }>>(
      `${KNOWLEDGE_BASE_URL}/search/semantic`,
      { query, ...options }
    );
    return response.data;
  },

  // Hybrid search (keyword + semantic)
  hybridSearch: async (
    query: string,
    options?: {
      limit?: number;
      model?: string;
      alpha?: number; // Weight for semantic vs keyword (0-1)
    }
  ): Promise<ApiResponse<{ results: SearchResult[] }>> => {
    const response = await apiService.post<ApiResponse<{ results: SearchResult[] }>>(
      `${KNOWLEDGE_BASE_URL}/search/hybrid`,
      { query, ...options }
    );
    return response.data;
  },

  // Knowledge base stats
  getStats: async (): Promise<ApiResponse<{
    total_documents: number;
    total_chunks: number;
    total_embeddings: number;
    storage_size: number;
    avg_chunk_size: number;
  }>> => {
    const response = await apiService.get<ApiResponse<{
      total_documents: number;
      total_chunks: number;
      total_embeddings: number;
      storage_size: number;
      avg_chunk_size: number;
    }>>(`${KNOWLEDGE_BASE_URL}/stats`);
    return response.data;
  },

  // Rebuild knowledge base index
  rebuildIndex: async (): Promise<ApiResponse<{ success: boolean }>> => {
    const response = await apiService.post<ApiResponse<{ success: boolean }>>(
      `${KNOWLEDGE_BASE_URL}/rebuild`
    );
    return response.data;
  },

  // Clear knowledge base
  clearKnowledgeBase: async (): Promise<void> => {
    await apiService.delete(`${KNOWLEDGE_BASE_URL}/clear`);
  },

  // Import knowledge base
  importKnowledgeBase: async (file: File): Promise<ApiResponse<{
    documents_imported: number;
    chunks_created: number;
    embeddings_generated: number;
  }>> => {
    const response = await apiService.upload<ApiResponse<{
      documents_imported: number;
      chunks_created: number;
      embeddings_generated: number;
    }>>(`${KNOWLEDGE_BASE_URL}/import`, file);
    return response.data;
  },

  // Export knowledge base
  exportKnowledgeBase: async (
    format: 'json' | 'csv' = 'json'
  ): Promise<void> => {
    await apiService.download(`${KNOWLEDGE_BASE_URL}/export?format=${format}`, 
      `knowledge-base-${format}-${new Date().toISOString().split('T')[0]}.${format}`
    );
  },
};

export default knowledgeService;
