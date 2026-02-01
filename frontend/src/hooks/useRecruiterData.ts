import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export interface Candidate {
  id: string;
  name: string;
  email: string;
  resume_id: string;
  stage: string;
  tags: string[];
  notes_count: number;
  match_score?: number;
  vacancy_id?: string;
}

export interface AnalyticsMetrics {
  time_to_hire: number;
  applications_per_job: number;
  source_performance?: Record<string, number>;
  funnel_metrics?: {
    views: number;
    applications: number;
    interviews: number;
    offers: number;
  };
}

export function useCandidates(params?: { stage?: string; vacancy_id?: string }) {
  return useQuery({
    queryKey: ['candidates', params],
    queryFn: async () => {
      const response = await apiClient.get<{ candidates: Candidate[] }>('/candidates', { params });
      return response.data;
    },
  });
}

export function useCandidateStages() {
  return useQuery({
    queryKey: ['candidate-stages'],
    queryFn: async () => {
      const response = await apiClient.get('/candidates/stages');
      return response.data;
    },
  });
}

export function useUpdateCandidateStage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ candidateId, stage }: { candidateId: string; stage: string }) => {
      const response = await apiClient.put(`/candidates/${candidateId}/stage`, { stage });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
    },
  });
}

export function useRecruiterVacancies() {
  return useQuery({
    queryKey: ['recruiter-vacancies'],
    queryFn: async () => {
      const response = await apiClient.get('/vacancies');
      return response.data;
    },
  });
}

export function useRecruiterAnalytics() {
  return useQuery({
    queryKey: ['recruiter-analytics'],
    queryFn: async () => {
      const response = await apiClient.get<AnalyticsMetrics>('/analytics/key-metrics');
      return response.data;
    },
  });
}
