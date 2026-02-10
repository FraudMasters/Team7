import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobApplicationsClient } from '../api/jobApplications';
import type {
  JobApplicationSubmitRequest,
  JobApplicationResponse,
  JobApplicationsListResponse,
} from '@/types/api';

export function useJobApplications(params?: { skip?: number; limit?: number; status_filter?: string }) {
  return useQuery({
    queryKey: ['job-applications', params],
    queryFn: async () => {
      return await jobApplicationsClient.getMyApplications(
        params?.skip ?? 0,
        params?.limit ?? 10,
        params?.status_filter
      );
    },
  });
}

export function useJobApplication(id: string) {
  return useQuery({
    queryKey: ['job-application', id],
    queryFn: async () => {
      return await jobApplicationsClient.getApplication(id);
    },
    enabled: !!id,
  });
}

export function useSubmitJobApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: JobApplicationSubmitRequest) => {
      return await jobApplicationsClient.submitApplication(request);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-applications'] });
    },
  });
}
