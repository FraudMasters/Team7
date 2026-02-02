import { useState } from 'react';
import {
  Container,
  Typography,
  TextField,
  Grid,
  Paper,
  Box,
  Stack,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
} from '@mui/material';
import { Search as SearchIcon, WorkOutline as WorkIcon } from '@mui/icons-material';
import { useApplications } from '../../hooks/useApplications';
import { ApplicationCard } from '../../components/jobs/ApplicationCard';
import { PageTransition } from '../../components/ui/PageTransition';
import { LoadingState } from '../../components/ui/LoadingState';
import { ErrorState } from '../../components/ui/ErrorState';

export function MyApplicationsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<{
    status?: string;
  }>({});

  const { data, isLoading, error } = useApplications();

  const filteredApplications = data?.applications.filter((application) => {
    const matchesSearch =
      searchTerm === '' ||
      application.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      application.description?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = !filters.status || application.status === filters.status;

    return matchesSearch && matchesStatus;
  }) ?? [];

  const getStatusCount = (status: string) => {
    return data?.applications.filter((app) => app.status === status).length ?? 0;
  };

  return (
    <PageTransition>
      <Container maxWidth="xl" sx={{ py: 2 }}>
        <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          My Applications
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Track your job application progress
        </Typography>
      </Box>

      {/* Search and Filters */}
      <Paper
        sx={{
          p: 2,
          mb: 4,
          display: 'flex',
          gap: 2,
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <TextField
          placeholder="Search applications..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
          sx={{ flexGrow: 1, minWidth: 200 }}
        />
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={filters.status || ''}
            label="Status"
            onChange={(e) => setFilters({ ...filters, status: e.target.value || undefined })}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="under_review">Under Review</MenuItem>
            <MenuItem value="interview">Interview</MenuItem>
            <MenuItem value="offered">Offered</MenuItem>
            <MenuItem value="rejected">Rejected</MenuItem>
          </Select>
        </FormControl>
        <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
          <WorkIcon color="primary" />
          <Typography variant="body2" color="text.secondary">
            {data?.total || 0} total
          </Typography>
        </Box>
      </Paper>

      {/* Status Summary */}
      {data && data.applications.length > 0 && (
        <Paper sx={{ p: 2, mb: 4 }}>
          <Stack direction="row" spacing={2} flexWrap="wrap">
            <Typography variant="body2" color="text.secondary">
              Summary:
            </Typography>
            <Typography variant="body2" sx={{ minWidth: 80 }}>
              Pending: {getStatusCount('pending')}
            </Typography>
            <Typography variant="body2" sx={{ minWidth: 100 }}>
              Under Review: {getStatusCount('under_review')}
            </Typography>
            <Typography variant="body2" sx={{ minWidth: 70 }}>
              Interview: {getStatusCount('interview')}
            </Typography>
            <Typography variant="body2" sx={{ minWidth: 60 }}>
              Offered: {getStatusCount('offered')}
            </Typography>
            <Typography variant="body2" sx={{ minWidth: 70 }}>
              Rejected: {getStatusCount('rejected')}
            </Typography>
          </Stack>
        </Paper>
      )}

      {/* Loading State */}
      {isLoading ? (
        <LoadingState message="Loading applications..." />
      ) : error ? (
        <ErrorState
          title="Error"
          message="Failed to load applications. Please try again later."
          onRetry={() => window.location.reload()}
        />
      ) : filteredApplications.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <WorkIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {searchTerm || filters.status ? 'No applications match your search' : 'No applications yet'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {searchTerm || filters.status
              ? 'Try adjusting your search terms'
              : 'Start applying to jobs to track them here'}
          </Typography>
          {!searchTerm && !filters.status && (
            <Typography
              variant="body2"
              color="primary"
              sx={{ cursor: 'pointer', textDecoration: 'underline' }}
              component="a"
              href="/jobs"
            >
              Browse Jobs
            </Typography>
          )}
        </Box>
      ) : (
        <Grid container spacing={2}>
          {filteredApplications.map((application) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={application.id}>
              <ApplicationCard application={application} />
            </Grid>
          ))}
        </Grid>
      )}
      </Container>
    </PageTransition>
  );
}
