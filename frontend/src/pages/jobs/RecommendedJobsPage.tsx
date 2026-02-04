import { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Paper,
  Chip,
  Button,
  CircularProgress,
  Icon,
} from '@/components/ui';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import { JobCard } from '../../components/jobs/JobCard';
import { PageTransition } from '../../components/ui/PageTransition';

interface Job {
  id: string;
  title: string;
  description: string;
  company: string;
  location: string;
  work_format: string;
  salary_min?: number;
  salary_max?: number;
  skills: string[];
  match_score?: number;
}

interface RecommendationsResponse {
  jobs: Job[];
  total: number;
  insights: {
    top_skills: string[];
    recommended_industries: string[];
  };
}

export function RecommendedJobsPage() {
  const [filter, setFilter] = useState<'all' | 'high-match'>('all');

  const { data, isLoading, error } = useQuery({
    queryKey: ['recommended-jobs', filter],
    queryFn: async () => {
      const response = await apiClient.getAxiosInstance().get<RecommendationsResponse>(
        `/api/v1/jobs/recommendations?min_match=${filter === 'high-match' ? 70 : 0}`
      );
      return response.data;
    },
  });

  const filteredJobs = data?.jobs.filter(job =>
    filter === 'all' || (job.match_score && job.match_score >= 70)
  ) ?? [];

  return (
    <PageTransition>
      <Container maxWidth="xl" sx={{ py: 2 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <RecommendIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" fontWeight={700}>
                Recommended Jobs
              </Typography>
              <Typography variant="body1" color="text.secondary">
                AI-powered recommendations based on your profile
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Insights Section */}
        {data?.insights && (
          <Paper sx={{ p: 3, mb: 4, bgcolor: 'primary.50', border: '1px solid', borderColor: 'primary.200' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <AIIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                AI Insights
              </Typography>
            </Box>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Your Top Skills
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {data.insights.top_skills.map((skill) => (
                    <Chip key={skill} label={skill} size="small" variant="outlined" />
                  ))}
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Recommended Industries
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {data.insights.recommended_industries.map((industry) => (
                    <Chip key={industry} label={industry} size="small" color="primary" variant="filled" />
                  ))}
                </Box>
              </Grid>
            </Grid>
          </Paper>
        )}

        {/* Filters */}
        <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
          <Button
            variant={filter === 'all' ? 'contained' : 'outlined'}
            onClick={() => setFilter('all')}
            startIcon={<RecommendIcon />}
          >
            All Recommendations
          </Button>
          <Button
            variant={filter === 'high-match' ? 'contained' : 'outlined'}
            onClick={() => setFilter('high-match')}
            startIcon={<TrendingUpIcon />}
          >
            High Match (70%+)
          </Button>
        </Box>

        {/* Loading State */}
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Typography color="error">Failed to load recommendations</Typography>
            <Button variant="outlined" sx={{ mt: 2 }} onClick={() => window.location.reload()}>
              Retry
            </Button>
          </Box>
        ) : filteredJobs.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <RecommendIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No recommendations yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Complete your profile and upload your resume to get personalized job recommendations
            </Typography>
            <Button variant="contained" component="a" href="/jobs/upload">
              Upload Resume
            </Button>
          </Box>
        ) : (
          <Grid container spacing={2}>
            {filteredJobs.map((job) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={job.id}>
                <Box sx={{ position: 'relative' }}>
                  {job.match_score && (
                    <Chip
                      label={`${job.match_score}% match`}
                      size="small"
                      color="primary"
                      sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        zIndex: 1,
                        fontWeight: 600,
                      }}
                    />
                  )}
                  <JobCard job={job} />
                </Box>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>
    </PageTransition>
  );
}
