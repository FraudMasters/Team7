import { useState, useEffect, useCallback } from 'react';
import { config } from '@/config';

/**
 * Feedback entry interface from backend
 */
export interface FeedbackEntry {
  id: string;
  resume_id: string;
  vacancy_id: string;
  match_result_id?: string;
  skill: string;
  was_correct: boolean;
  confidence_score?: number;
  recruiter_correction?: string;
  actual_skill?: string;
  feedback_source: string;
  processed: boolean;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

/**
 * Feedback list response from backend
 */
export interface FeedbackListResponse {
  feedback: FeedbackEntry[];
  total_count: number;
}

/**
 * Feedback entry creation request
 */
export interface FeedbackEntryCreate {
  resume_id: string;
  vacancy_id: string;
  match_result_id?: string;
  skill: string;
  was_correct: boolean;
  confidence_score?: number;
  recruiter_correction?: string;
  actual_skill?: string;
  feedback_source?: string;
  extra_metadata?: Record<string, unknown>;
}

/**
 * Feedback creation request
 */
export interface FeedbackCreateRequest {
  feedback: FeedbackEntryCreate[];
}

/**
 * Feedback filter parameters
 */
export interface FeedbackFilters {
  resume_id?: string;
  vacancy_id?: string;
  skill?: string;
  was_correct?: boolean;
  processed?: boolean;
  feedback_source?: string;
  limit?: number;
  skip?: number;
}

/**
 * useSkillFeedback hook return type
 */
export interface UseSkillFeedbackResult {
  feedback: FeedbackEntry[];
  totalCount: number;
  loading: boolean;
  error: string | null;
  fetchFeedback: (filters?: FeedbackFilters) => Promise<void>;
  submitFeedback: (request: FeedbackCreateRequest) => Promise<void>;
  refetch: () => Promise<void>;
}

/**
 * Custom hook for managing skill feedback data
 *
 * Provides functionality to fetch and submit skill feedback entries.
 * Manages loading states, error handling, and data fetching from the feedback API.
 *
 * @param initialFilters - Optional initial filter parameters
 * @param apiUrl - Optional API endpoint URL override
 * @param autoFetch - Whether to automatically fetch data on mount (default: true)
 *
 * @example
 * ```tsx
 * const { feedback, loading, error, submitFeedback, refetch } = useSkillFeedback({
 *   resume_id: 'resume-123',
 *   limit: 50
 * });
 *
 * // Submit new feedback
 * await submitFeedback({
 *   feedback: [{
 *     resume_id: 'resume-123',
 *     vacancy_id: 'vacancy-456',
 *     skill: 'Python',
 *     was_correct: true,
 *     confidence_score: 0.95
 *   }]
 * });
 *
 * // Refresh data
 * await refetch();
 * ```
 */
export function useSkillFeedback(
  initialFilters?: FeedbackFilters,
  apiUrl: string = `${config.api.url}/api/feedback`,
  autoFetch: boolean = true
): UseSkillFeedbackResult {
  const [feedback, setFeedback] = useState<FeedbackEntry[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentFilters, setCurrentFilters] = useState<FeedbackFilters | undefined>(initialFilters);

  /**
   * Fetch feedback data from backend
   */
  const fetchFeedback = useCallback(async (filters?: FeedbackFilters) => {
    try {
      setLoading(true);
      setError(null);

      const filterParams = filters || currentFilters;
      setCurrentFilters(filterParams);

      const queryParams = new URLSearchParams();
      if (filterParams) {
        if (filterParams.resume_id) queryParams.append('resume_id', filterParams.resume_id);
        if (filterParams.vacancy_id) queryParams.append('vacancy_id', filterParams.vacancy_id);
        if (filterParams.skill) queryParams.append('skill', filterParams.skill);
        if (filterParams.was_correct !== undefined) queryParams.append('was_correct', String(filterParams.was_correct));
        if (filterParams.processed !== undefined) queryParams.append('processed', String(filterParams.processed));
        if (filterParams.feedback_source) queryParams.append('feedback_source', filterParams.feedback_source);
        if (filterParams.limit !== undefined) queryParams.append('limit', String(filterParams.limit));
        if (filterParams.skip !== undefined) queryParams.append('skip', String(filterParams.skip));
      }

      const url = queryParams.toString() ? `${apiUrl}/?${queryParams.toString()}` : `${apiUrl}/`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch feedback: ${response.statusText}`);
      }

      const result: FeedbackListResponse = await response.json();
      setFeedback(result.feedback || []);
      setTotalCount(result.total_count || 0);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load feedback data';
      setError(errorMessage);
      setFeedback([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, currentFilters]);

  /**
   * Submit new feedback entries to backend
   */
  const submitFeedback = useCallback(async (request: FeedbackCreateRequest) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${apiUrl}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to submit feedback: ${response.statusText}`);
      }

      await fetchFeedback(currentFilters);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to submit feedback';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiUrl, currentFilters, fetchFeedback]);

  /**
   * Refetch feedback data with current filters
   */
  const refetch = useCallback(async () => {
    await fetchFeedback(currentFilters);
  }, [currentFilters, fetchFeedback]);

  /**
   * Initial data fetch on mount
   */
  useEffect(() => {
    if (autoFetch) {
      fetchFeedback(initialFilters);
    }
  }, []);

  return {
    feedback,
    totalCount,
    loading,
    error,
    fetchFeedback,
    submitFeedback,
    refetch,
  };
}
