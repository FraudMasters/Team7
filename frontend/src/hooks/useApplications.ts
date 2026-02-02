export interface JobApplication {
  id: string;
  vacancy_id: string;
  title: string;
  description?: string;
  location?: string;
  work_format?: 'remote' | 'office' | 'hybrid';
  min_experience_months?: number;
  required_skills: string[];
  status: string;
  stage_name?: string;
  applied_at: string;
  match_score?: number;
}

export interface ApplicationsResponse {
  applications: JobApplication[];
  total: number;
}

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export function useApplications(params?: { limit?: number; skip?: number }) {
  return useQuery({
    queryKey: ['applications', params],
    queryFn: async () => {
      const response = await apiClient.get<ApplicationsResponse>('/applications', { params });
      return response.data;
    },
  });
}

export function useApplication(id: string) {
  return useQuery({
    queryKey: ['application', id],
    queryFn: async () => {
      const response = await apiClient.get<JobApplication>(`/applications/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}
