import { useQuery } from '@tanstack/react-query';
import { jobSearchClient } from '../api/jobSearch';
import type { JobSearchRequest, JobSearchResponse } from '@/types/api';

export function useJobSearch(params: JobSearchRequest = {}) {
  return useQuery({
    queryKey: ['job-search', params],
    queryFn: async () => {
      return await jobSearchClient.searchJobs(params);
    },
  });
}

export function useJobSearchGet(params: JobSearchRequest = {}) {
  return useQuery({
    queryKey: ['job-search-get', params],
    queryFn: async () => {
      return await jobSearchClient.searchJobsGet(params);
    },
  });
}
