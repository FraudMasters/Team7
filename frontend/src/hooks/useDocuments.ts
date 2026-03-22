export interface CandidateDocument {
  id: string;
  filename: string;
  document_type: string;
  description?: string | null;
  application_id?: string | null;
  content_type: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentsResponse {
  documents: CandidateDocument[];
  total: number;
}

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export function useDocuments(params?: {
  document_type?: string;
  application_id?: string;
  limit?: number;
  skip?: number;
}) {
  return useQuery({
    queryKey: ['documents', params],
    queryFn: async () => {
      const response = await apiClient.get<DocumentsResponse>('/api/candidate-documents/list', { params });
      return response.data;
    },
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: ['document', id],
    queryFn: async () => {
      const response = await apiClient.get<CandidateDocument>(`/candidate-documents/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}
