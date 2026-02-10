import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { savedJobsClient } from '../api/savedJobs';
import type {
  SaveJobRequest,
  SavedJobResponse,
  SavedJobsListResponse,
  CheckJobSavedResponse,
} from '@/types/api';

export function useSavedJobs(userId: string, params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ['saved-jobs', userId, params],
    queryFn: async () => {
      return await savedJobsClient.getSavedJobs(
        userId,
        params?.skip ?? 0,
        params?.limit ?? 100
      );
    },
    enabled: !!userId,
  });
}

export function useCheckJobSaved(vacancyId: string, userId: string) {
  return useQuery({
    queryKey: ['check-job-saved', vacancyId, userId],
    queryFn: async () => {
      return await savedJobsClient.checkJobSaved(vacancyId, userId);
    },
    enabled: !!vacancyId && !!userId,
  });
}

export function useSaveJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: SaveJobRequest) => {
      return await savedJobsClient.saveJob(request);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['saved-jobs', variables.user_id] });
      queryClient.invalidateQueries({ queryKey: ['check-job-saved', variables.vacancy_id, variables.user_id] });
    },
  });
}

export function useUnsaveJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ savedJobId, vacancyId, userId }: { savedJobId?: string; vacancyId?: string; userId: string }) => {
      if (savedJobId) {
        await savedJobsClient.unsaveJob(savedJobId);
      } else if (vacancyId && userId) {
        await savedJobsClient.unsaveJobByVacancy(vacancyId, userId);
      }
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['saved-jobs', variables.userId] });
      if (variables.vacancyId) {
        queryClient.invalidateQueries({ queryKey: ['check-job-saved', variables.vacancyId, variables.userId] });
      }
    },
  });
}
