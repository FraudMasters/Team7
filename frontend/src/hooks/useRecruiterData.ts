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

/**
 * Recruiter feedback for a candidate in review queue
 */
export interface RecruiterFeedbackItem {
  recruiter_name: string;
  rating: number | null;
  recommendation: string | null;
  notes: string | null;
  created_at: string;
}

/**
 * Candidate in the recruiter review queue
 */
export interface ReviewQueueCandidateItem {
  id: string;
  filename: string;
  candidate_name: string | null;
  vacancy_id: string | null;
  vacancy_title: string | null;
  current_stage: string;
  stage_name: string;
  priority: string | null;
  days_in_stage: number;
  match_score: number | null;
  recruiter_feedback: RecruiterFeedbackItem[];
  team_consensus: string | null;
  tags: string[];
  assigned_recruiter_id: string | null;
  assigned_recruiter_name: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Review queue metrics
 */
export interface ReviewQueueMetrics {
  total_pending: number;
  urgent_count: number;
  avg_wait_days: number;
  reviewed_today: number;
  throughput_week: number;
}

/**
 * Review queue response
 */
export interface ReviewQueueResponse {
  total_candidates: number;
  candidates: ReviewQueueCandidateItem[];
  metrics: ReviewQueueMetrics;
  filters_applied: Record<string, unknown>;
  pagination: {
    skip: number;
    limit: number;
    total: number;
  };
}

/**
 * Review queue filters
 */
export interface ReviewQueueFilters {
  vacancy_id?: string;
  priority?: 'urgent' | 'high' | 'normal' | 'low';
  stage_id?: string;
  search?: string;
  min_match_score?: number;
  assigned_to_me?: boolean;
  skip?: number;
  limit?: number;
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

/**
 * Hook for fetching the recruiter review queue
 *
 * @param filters - Optional filters for the review queue
 * @returns Query result with review queue data including candidates and metrics
 */
export function useRecruiterReviewQueue(filters?: ReviewQueueFilters) {
  return useQuery({
    queryKey: ['recruiter-review-queue', filters],
    queryFn: async () => {
      const params: Record<string, string | number | boolean> = {};
      if (filters?.vacancy_id) params.vacancy_id = filters.vacancy_id;
      if (filters?.priority) params.priority = filters.priority;
      if (filters?.stage_id) params.stage_id = filters.stage_id;
      if (filters?.search) params.search = filters.search;
      if (filters?.min_match_score !== undefined) params.min_match_score = filters.min_match_score;
      if (filters?.assigned_to_me !== undefined) params.assigned_to_me = filters.assigned_to_me;
      if (filters?.skip !== undefined) params.skip = filters.skip;
      if (filters?.limit !== undefined) params.limit = filters.limit;

      const response = await apiClient.get<ReviewQueueResponse>('/recruiter/review-queue', { params });
      return response.data;
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}
