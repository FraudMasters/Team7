export interface SavedJob {
  id: string;
  vacancy_id: string;
  title: string;
  description: string;
  required_skills: string[];
  min_experience_months: number;
  industry?: string;
  work_format?: 'remote' | 'office' | 'hybrid';
  location?: string;
  salary_min?: number;
  salary_max?: number;
  employment_type?: string;
  saved_at: string;
}

export interface SavedJobsResponse {
  saved_jobs: SavedJob[];
  total: number;
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export function useSavedJobs(params?: { limit?: number; skip?: number }) {
  return useQuery({
    queryKey: ['saved-jobs', params],
    queryFn: async () => {
      const response = await apiClient.get<SavedJobsResponse>('/saved-jobs', { params });
      return response.data;
    },
  });
}

export function useSavedJob(id: string) {
  return useQuery({
    queryKey: ['saved-job', id],
    queryFn: async () => {
      const response = await apiClient.get<SavedJob>(`/saved-jobs/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useSaveJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (vacancyId: string) => {
      const response = await apiClient.post<SavedJob>('/saved-jobs', { vacancy_id: vacancyId });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-jobs'] });
    },
  });
}

export function useRemoveSavedJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (savedJobId: string) => {
      await apiClient.delete(`/saved-jobs/${savedJobId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-jobs'] });
    },
  });
}
