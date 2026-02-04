import { useState } from 'react';
import {
  Container,
  Typography,
  TextField,
  Grid,
  Paper,
  Box,
  Button,
} from '@/components/ui';
import { Icon } from '@/components/ui';
import { useSavedJobs, useRemoveSavedJob } from '../../hooks/useSavedJobs';
import { JobCard } from '../../components/jobs/JobCard';
import { useQueryClient } from '@tanstack/react-query';
import { PageTransition } from '../../components/ui/PageTransition';
import { LoadingState } from '../../components/ui/LoadingState';
import { ErrorState } from '../../components/ui/ErrorState';

export function SavedJobsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useSavedJobs();
  const removeSavedJob = useRemoveSavedJob();

  const filteredJobs = data?.saved_jobs.filter((job) => {
    return (
      searchTerm === '' ||
      job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.description.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }) ?? [];

  const handleRemoveSavedJob = (savedJobId: string) => {
    removeSavedJob.mutate(savedJobId, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['saved-jobs'] });
      },
    });
  };

  return (
    <PageTransition>
      <Container maxWidth="xl" sx={{ py: 2 }}>
        <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Saved Jobs
        </Typography>
        <Typography variant="body1" color="secondary">
          Your bookmarked job opportunities
        </Typography>
      </Box>

      {/* Search */}
      <Paper
        sx={{
          p: 2,
          mb: 4,
          display: 'flex',
          gap: 2,
          alignItems: 'center',
        }}
      >
        <TextField
          placeholder="Search saved jobs..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          inputProps={{
            startAdornment: <Icon name="search" size={20} color="secondary" sx={{ mr: 1 }} />,
          }}
          sx={{ flexGrow: 1, minWidth: 200 }}
        />
        <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
          <Icon name="bookmark" size={20} color="primary" filled />
          <Typography variant="body2" color="secondary">
            {data?.total || 0} saved
          </Typography>
        </Box>
      </Paper>

      {/* Loading State */}
      {isLoading ? (
        <LoadingState message="Loading saved jobs..." />
      ) : error ? (
        <ErrorState
          title="Error"
          message="Failed to load saved jobs. Please try again later."
          onRetry={() => queryClient.invalidateQueries({ queryKey: ['saved-jobs'] })}
        />
      ) : filteredJobs.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Icon name="bookmark" size={64} color="secondary" sx={{ mb: 2 }} filled />
          <Typography variant="h6" color="secondary" gutterBottom>
            {searchTerm ? 'No saved jobs match your search' : 'No saved jobs yet'}
          </Typography>
          <Typography variant="body2" color="secondary" sx={{ mb: 3 }}>
            {searchTerm
              ? 'Try adjusting your search terms'
              : 'Start bookmarking jobs to see them here'}
          </Typography>
          {!searchTerm && (
            <Button variant="contained" as="a" href="/jobs">
              Browse Jobs
            </Button>
          )}
        </Box>
      ) : (
        <Grid container spacing={2}>
          {filteredJobs.map((job) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={job.id}>
              <JobCard
                job={job}
                saved={true}
                onSave={() => handleRemoveSavedJob(job.id)}
              />
            </Grid>
          ))}
        </Grid>
      )}
      </Container>
    </PageTransition>
  );
}
