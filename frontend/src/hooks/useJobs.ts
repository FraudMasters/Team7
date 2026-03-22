export interface JobVacancy {
  id: string;
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
}

export interface JobsResponse {
  vacancies: JobVacancy[];
  total: number;
}

import { useQuery } from '@tanstack/react-query';
import { vacanciesClient } from '../api';

export function useJobs(params?: { limit?: number; skip?: number }) {
  return useQuery({
    queryKey: ['jobs', params],
    queryFn: async () => {
      const response = await vacanciesClient.get<JobsResponse>('/vacancies', { params });
      return response.data;
    },
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ['job', id],
    queryFn: async () => {
      const response = await vacanciesClient.get<JobVacancy>(`/vacancies/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}
