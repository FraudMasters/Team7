import { useState } from 'react';
import {
  Container,
  Typography,
  TextField,
  Stack,
  Grid,
  Paper,
  Chip,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  CircularProgress,
  Box,
} from '@/components/ui';
import { Icon } from '@/components/ui';
import { useJobs } from '../../hooks/useJobs';
import { JobCard } from '../../components/jobs/JobCard';

export function JobsBrowsePage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<{
    workFormat?: string;
  }>({});

  const { data, isLoading, error } = useJobs();

  const filteredJobs = data?.vacancies.filter((job) => {
    const matchesSearch =
      searchTerm === '' ||
      job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.description.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFormat = !filters.workFormat || job.work_format === filters.workFormat;

    return matchesSearch && matchesFormat;
  }) ?? [];

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Find Your Next Job
        </Typography>
        <Typography variant="body1" color="secondary">
          Discover opportunities matched to your skills
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
          placeholder="Search jobs..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          inputProps={{
            startAdornment: <Icon name="search" size={20} color="secondary" sx={{ mr: 1 }} />,
          }}
          sx={{ flexGrow: 1, minWidth: 200 }}
        />
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Work Format</InputLabel>
          <Select
            value={filters.workFormat || ''}
            label="Work Format"
            onChange={(e) => setFilters({ ...filters, workFormat: e.target.value || undefined })}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="remote">Remote</MenuItem>
            <MenuItem value="office">Office</MenuItem>
            <MenuItem value="hybrid">Hybrid</MenuItem>
          </Select>
        </FormControl>
      </Paper>

      {/* Loading State */}
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography color="error">Failed to load jobs</Typography>
        </Box>
      ) : filteredJobs.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography color="secondary">No jobs found</Typography>
        </Box>
      ) : (
        <Grid container spacing={2}>
          {filteredJobs.map((job) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={job.id}>
              <JobCard job={job} />
            </Grid>
          ))}
        </Grid>
      )}
    </Container>
  );
}
