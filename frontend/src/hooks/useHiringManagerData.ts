/**
 * Hiring Manager Data Hooks
 *
 * React Query hooks for fetching hiring manager data including
 * dashboard statistics, review queue, and evaluation summaries.
 *
 * @example
 * ```tsx
 * import { useHiringManagerDashboard, useHiringManagerReviewQueue } from '@/hooks/useHiringManagerData';
 *
 * function DashboardPage() {
 *   const { data: dashboardStats, isLoading } = useHiringManagerDashboard();
 *   const { data: reviewQueue } = useHiringManagerReviewQueue({ priority: 'urgent' });
 *
 *   if (isLoading) return <Loading />;
 *   return <div>{dashboardStats.pending_review.total_pending} pending</div>;
 * }
 * ```
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  hiringManagerClient,
  DashboardStatsResponse,
  ReviewQueueResponse,
  EvaluationSummaryResponse,
  CandidateDecisionResponse,
  ReviewQueueFilters,
  DashboardStatsFilters,
  CandidateApprovalRequest,
  CandidateRejectionRequest,
} from '../api/hiringManager';

/**
 * Hook for fetching hiring manager dashboard statistics
 *
 * @param filters - Optional date filters for statistics
 * @returns Query result with dashboard statistics
 */
export function useHiringManagerDashboard(filters?: DashboardStatsFilters) {
  return useQuery({
    queryKey: ['hiring-manager-dashboard', filters],
    queryFn: () => hiringManagerClient.getDashboardStats(filters),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook for fetching the hiring manager review queue
 *
 * @param filters - Optional filters for the review queue
 * @returns Query result with review queue data
 */
export function useHiringManagerReviewQueue(filters?: ReviewQueueFilters) {
  return useQuery({
    queryKey: ['hiring-manager-review-queue', filters],
    queryFn: () => hiringManagerClient.getReviewQueue(filters),
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

/**
 * Hook for fetching evaluation summary for a specific candidate
 *
 * @param candidateId - UUID of the candidate
 * @returns Query result with evaluation summary
 */
export function useHiringManagerEvaluation(candidateId: string) {
  return useQuery({
    queryKey: ['hiring-manager-evaluation', candidateId],
    queryFn: () => hiringManagerClient.getEvaluationSummary(candidateId),
    enabled: !!candidateId,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook for approving a candidate
 *
 * Invalidates review queue and dashboard queries on success.
 *
 * @returns Mutation for approving candidates
 */
export function useApproveCandidate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      candidateId,
      request,
    }: {
      candidateId: string;
      request?: CandidateApprovalRequest;
    }) => hiringManagerClient.approveCandidate(candidateId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hiring-manager-review-queue'] });
      queryClient.invalidateQueries({ queryKey: ['hiring-manager-dashboard'] });
    },
  });
}

/**
 * Hook for rejecting a candidate
 *
 * Invalidates review queue and dashboard queries on success.
 *
 * @returns Mutation for rejecting candidates
 */
export function useRejectCandidate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      candidateId,
      request,
    }: {
      candidateId: string;
      request?: CandidateRejectionRequest;
    }) => hiringManagerClient.rejectCandidate(candidateId, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hiring-manager-review-queue'] });
      queryClient.invalidateQueries({ queryKey: ['hiring-manager-dashboard'] });
    },
  });
}

// Re-export types for convenience
export type {
  DashboardStatsResponse,
  ReviewQueueResponse,
  ReviewQueueCandidate,
  EvaluationSummaryResponse,
  CandidateDecisionResponse,
  ReviewQueueFilters,
  DashboardStatsFilters,
};
