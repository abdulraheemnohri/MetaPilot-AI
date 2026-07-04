import { apiService } from './api';

interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadedAt: string;
}

interface KnowledgeResponse {
  documents: Document[];
  total: number;
}

export const knowledgeService = {
  async getDocuments(page: number = 1, limit: number = 20): Promise<KnowledgeResponse> {
    const response = await apiService.get<KnowledgeResponse>('/api/knowledge/documents', {
      page: page.toString(),
      limit: limit.toString(),
    });
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to get documents');
    }
    
    return response.data!;
  },
  
  async uploadDocument(file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/knowledge/upload`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    });
    
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error || 'Upload failed');
    }
    
    return result.data;
  },
  
  async deleteDocument(id: string): Promise<void> {
    const response = await apiService.delete(`/api/knowledge/documents/${id}`);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to delete document');
    }
  },
  
  async processDocument(id: string): Promise<Document> {
    const response = await apiService.post<Document>(`/api/knowledge/documents/${id}/process`);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to process document');
    }
    
    return response.data!;
  },
  
  async searchKnowledge(query: string, limit: number = 5): Promise<Document[]> {
    const response = await apiService.get<Document[]>('/api/knowledge/search', {
      q: query,
      limit: limit.toString(),
    });
    
    if (!response.success) {
      throw new Error(response.error || 'Search failed');
    }
    
    return response.data || [];
  },
};