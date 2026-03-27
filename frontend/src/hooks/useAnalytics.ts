/**
 * Analytics Data Fetching Hook
 *
 * This module provides React hooks for fetching analytics data from the backend.
 * Supports key metrics, quality metrics, funnel analysis, source tracking, and more.
 *
 * @example
 * ```tsx
 * import { useKeyMetrics, useFunnelMetrics } from '@/hooks/useAnalytics';
 *
 * function AnalyticsDashboard() {
 *   const { data: keyMetrics, isLoading } = useKeyMetrics({
 *     start_date: '2026-01-01',
 *     end_date: '2026-03-21',
 *   });
 *
 *   if (isLoading) return <CircularProgress />;
 *
 *   return (
 *     <div>
 *       <h2>Time to Hire: {keyMetrics?.time_to_hire.average_days} days</h2>
 *     </div>
 *   );
 * }
 * ```
 */

import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import type {
  KeyMetricsResponse,
  FunnelMetricsResponse,
  StageDurationResponse,
  RankingMetricsResponse,
} from '@/types/api';

/**
 * Common analytics query parameters
 */
export interface AnalyticsDateParams {
  /** Start date filter (ISO 8601 format) */
  start_date?: string;
  /** End date filter (ISO 8601 format) */
  end_date?: string;
}

/**
 * Source tracking query parameters
 */
export interface SourceTrackingParams extends AnalyticsDateParams {
  /** Filter by specific source */
  source?: string;
  /** Minimum number of applications to include source */
  min_applications?: number;
}

/**
 * Recruiter performance query parameters
 */
export interface RecruiterPerformanceParams extends AnalyticsDateParams {
  /** Filter by specific recruiter ID */
  recruiter_id?: string;
  /** Minimum number of candidates to include recruiter */
  min_candidates?: number;
}

/**
 * Stage duration query parameters
 */
export interface StageDurationParams extends AnalyticsDateParams {
  /** Filter by specific stage name */
  stage_name?: string;
}

/**
 * Ranking accuracy query parameters
 */
export interface RankingAccuracyParams extends AnalyticsDateParams {
  /** Filter by specific vacancy ID */
  vacancy_id?: string;
  /** Include trend data */
  include_trends?: boolean;
}

/**
 * useKeyMetrics Hook
 *
 * Fetches key recruitment analytics metrics including time-to-hire,
 * resume processing stats, and match rate metrics.
 *
 * @param params - Optional date range filters
 * @param options - React Query options
 * @returns Query result with key metrics data
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useKeyMetrics({
 *   start_date: '2026-01-01',
 *   end_date: '2026-03-21',
 * });
 * ```
 */
export function useKeyMetrics(
  params?: AnalyticsDateParams,
  options?: Omit<UseQueryOptions<KeyMetricsResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery<KeyMetricsResponse>({
    queryKey: ['analytics', 'key-metrics', params],
    queryFn: async () => {
      const response = await apiClient.get<KeyMetricsResponse>('/analytics/key-metrics', {
        params,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * useQualityMetrics Hook
 *
 * Fetches ML/NLP model quality metrics including text extraction,
 * NER accuracy, matching performance, and error rates.
 *
 * @param params - Optional date range filters
 * @param options - React Query options
 * @returns Query result with quality metrics data
 *
 * @example
 * ```tsx
 * const { data: qualityMetrics } = useQualityMetrics({
 *   start_date: '2026-03-01',
 * });
 * ```
 */
export function useQualityMetrics(
  params?: AnalyticsDateParams,
  options?: Omit<UseQueryOptions<Record<string, unknown>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Record<string, unknown>>({
    queryKey: ['analytics', 'quality-metrics', params],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>('/analytics/quality-metrics', {
        params,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * useFunnelMetrics Hook
 *
 * Fetches funnel conversion metrics showing candidate progression
 * through recruitment stages.
 *
 * @param params - Optional date range filters
 * @param options - React Query options
 * @returns Query result with funnel metrics data
 *
 * @example
 * ```tsx
 * const { data: funnelData } = useFunnelMetrics();
 *
 * funnelData?.stages.forEach(stage => {
 *   console.log(`${stage.stage_name}: ${stage.count} (${stage.conversion_rate}%)`);
 * });
 * ```
 */
export function useFunnelMetrics(
  params?: AnalyticsDateParams,
  options?: Omit<UseQueryOptions<FunnelMetricsResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery<FunnelMetricsResponse>({
    queryKey: ['analytics', 'funnel', params],
    queryFn: async () => {
      const response = await apiClient.get<FunnelMetricsResponse>('/analytics/funnel', {
        params,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * useStageDuration Hook
 *
 * Fetches time spent in each recruitment stage with
 * average, median, and percentile breakdowns.
 *
 * @param params - Optional filters including date range and stage name
 * @param options - React Query options
 * @returns Query result with stage duration data
 *
 * @example
 * ```tsx
 * const { data: stageDurations } = useStageDuration({
 *   start_date: '2026-01-01',
 * });
 * ```
 */
export function useStageDuration(
  params?: StageDurationParams,
  options?: Omit<UseQueryOptions<StageDurationResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery<StageDurationResponse>({
    queryKey: ['analytics', 'stage-duration', params],
    queryFn: async () => {
      const response = await apiClient.get<StageDurationResponse>('/analytics/stage-duration', {
        params,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * useSourceTracking Hook
 *
 * Fetches source effectiveness metrics showing which job boards
 * and recruitment sources produce the best candidates.
 *
 * @param params - Optional filters including date range and source
 * @param options - React Query options
 * @returns Query result with source tracking data
 *
 * @example
 * ```tsx
 * const { data: sources } = useSourceTracking({
 *   min_applications: 5,
 * });
 * ```
 */
export function useSourceTracking(
  params?: SourceTrackingParams,
  options?: Omit<UseQueryOptions<Record<string, unknown>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Record<string, unknown>>({
    queryKey: ['analytics', 'source-tracking', params],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>('/analytics/source-tracking', {
        params,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * useRecruiterPerformance Hook
 *
 * Fetches recruiter performance metrics including candidates reviewed,
 * time-to-hire, and hire rates per recruiter.
 *
 * @param params - Optional filters including date range and recruiter ID
 * @param options - React Query options
 * @returns Query result with recruiter performance data
 *
 * @example
 * ```tsx
 * const { data: performance } = useRecruiterPerformance({
 *   recruiter_id: 'rec-123',
 * });
 * ```
 */
export function useRecruiterPerformance(
  params?: RecruiterPerformanceParams,
  options?: Omit<UseQueryOptions<Record<string, unknown>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Record<string, unknown>>({
    queryKey: ['analytics', 'recruiter-performance', params],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>(
        '/analytics/recruiter-performance',
        { params }
      );
      return response.data;
    },
    ...options,
  });
}

/**
 * useSkillDemand Hook
 *
 * Fetches skill demand analytics showing which skills are most
 * requested in job postings and trending over time.
 *
 * @param params - Optional date range filters
 * @param options - React Query options
 * @returns Query result with skill demand data
 *
 * @example
 * ```tsx
 * const { data: skillDemand } = useSkillDemand();
 * ```
 */
export function useSkillDemand(
  params?: AnalyticsDateParams,
  options?: Omit<UseQueryOptions<Record<string, unknown>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Record<string, unknown>>({
    queryKey: ['analytics', 'skill-demand', params],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>('/analytics/skill-demand', {
        params,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * useRankingAccuracy Hook
 *
 * Fetches ranking algorithm accuracy metrics including precision,
 * recall, and performance trends over time.
 *
 * @param params - Optional filters including date range and vacancy ID
 * @param options - React Query options
 * @returns Query result with ranking accuracy data
 *
 * @example
 * ```tsx
 * const { data: accuracy } = useRankingAccuracy({
 *   include_trends: true,
 * });
 * ```
 */
export function useRankingAccuracy(
  params?: RankingAccuracyParams,
  options?: Omit<UseQueryOptions<RankingMetricsResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery<RankingMetricsResponse>({
    queryKey: ['analytics', 'ranking-accuracy', params],
    queryFn: async () => {
      const response = await apiClient.get<RankingMetricsResponse>('/analytics/ranking-accuracy', {
        params,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * useTaxonomyUsage Hook
 *
 * Fetches taxonomy usage statistics showing which skill taxonomies
 * are most used and most effective.
 *
 * @param params - Optional date range filters
 * @param options - React Query options
 * @returns Query result with taxonomy usage data
 *
 * @example
 * ```tsx
 * const { data: taxonomyStats } = useTaxonomyUsage();
 * ```
 */
export function useTaxonomyUsage(
  params?: AnalyticsDateParams,
  options?: Omit<UseQueryOptions<Record<string, unknown>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Record<string, unknown>>({
    queryKey: ['analytics', 'taxonomy-usage', params],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>('/analytics/taxonomy-usage', {
        params,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * useAIConfidence Hook
 *
 * Fetches AI model confidence distribution metrics for explainability.
 *
 * @param params - Optional date range filters
 * @param options - React Query options
 * @returns Query result with AI confidence data
 *
 * @example
 * ```tsx
 * const { data: confidence } = useAIConfidence();
 * ```
 */
export function useAIConfidence(
  params?: AnalyticsDateParams,
  options?: Omit<UseQueryOptions<Record<string, unknown>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Record<string, unknown>>({
    queryKey: ['analytics', 'ai-confidence', params],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>(
        '/analytics/ai-explainability/confidence',
        { params }
      );
      return response.data;
    },
    ...options,
  });
}

/**
 * useFeatureImportance Hook
 *
 * Fetches feature importance metrics showing which factors
 * contribute most to candidate ranking decisions.
 *
 * @param params - Optional date range filters
 * @param options - React Query options
 * @returns Query result with feature importance data
 *
 * @example
 * ```tsx
 * const { data: features } = useFeatureImportance();
 * ```
 */
export function useFeatureImportance(
  params?: AnalyticsDateParams,
  options?: Omit<UseQueryOptions<Record<string, unknown>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Record<string, unknown>>({
    queryKey: ['analytics', 'feature-importance', params],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>(
        '/analytics/ai-explainability/feature-importance',
        { params }
      );
      return response.data;
    },
    ...options,
  });
}

/**
 * useRankingRationale Hook
 *
 * Fetches detailed ranking rationale for a specific candidate,
 * explaining why they were ranked at a particular position.
 *
 * @param candidateId - The candidate ID to get ranking rationale for
 * @param options - React Query options
 * @returns Query result with ranking rationale data
 *
 * @example
 * ```tsx
 * const { data: rationale } = useRankingRationale('candidate-123');
 * ```
 */
export function useRankingRationale(
  candidateId: string,
  options?: Omit<UseQueryOptions<Record<string, unknown>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Record<string, unknown>>({
    queryKey: ['analytics', 'ranking-rationale', candidateId],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>(
        `/analytics/ai-explainability/ranking-rationale/${candidateId}`
      );
      return response.data;
    },
    enabled: !!candidateId,
    ...options,
  });
}

/**
 * usePerformanceTrends Hook
 *
 * Fetches AI model performance trends over time for monitoring
 * model drift and improvements.
 *
 * @param params - Optional date range filters
 * @param options - React Query options
 * @returns Query result with performance trends data
 *
 * @example
 * ```tsx
 * const { data: trends } = usePerformanceTrends({
 *   start_date: '2026-01-01',
 *   end_date: '2026-03-21',
 * });
 * ```
 */
export function usePerformanceTrends(
  params?: AnalyticsDateParams,
  options?: Omit<UseQueryOptions<Record<string, unknown>>, 'queryKey' | 'queryFn'>
) {
  return useQuery<Record<string, unknown>>({
    queryKey: ['analytics', 'performance-trends', params],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>(
        '/analytics/ai-explainability/performance-trends',
        { params }
      );
      return response.data;
    },
    ...options,
  });
}

export default {
  useKeyMetrics,
  useQualityMetrics,
  useFunnelMetrics,
  useStageDuration,
  useSourceTracking,
  useRecruiterPerformance,
  useSkillDemand,
  useRankingAccuracy,
  useTaxonomyUsage,
  useAIConfidence,
  useFeatureImportance,
  useRankingRationale,
  usePerformanceTrends,
};
