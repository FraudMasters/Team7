import { useParams } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Stack,
  Chip,
  Button,
  Divider,
  CircularProgress,
} from '@/components/ui';
import { Icon } from '@/components/ui';
import { useJob } from '../../hooks/useJobs';

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: job, isLoading, error } = useJob(id || '');

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 12 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !job) {
    return (
      <Box sx={{ textAlign: 'center', py: 12 }}>
        <Typography variant="h6">Job not found</Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper
        sx={{
          p: { xs: 3, md: 5 },
          animation: 'fadeInUp 0.5s ease-out both',
          '@keyframes fadeInUp': {
            '0%': {
              opacity: 0,
              transform: 'translateY(20px)',
            },
            '100%': {
              opacity: 1,
              transform: 'translateY(0)',
            },
          },
        }}
      >
        <Stack spacing={4}>
          {/* Header */}
          <Box>
            <Typography variant="h3" fontWeight={700} gutterBottom>
              {job.title}
            </Typography>
            <Stack direction="row" spacing={2} flexWrap="wrap" color="secondary">
              {job.industry && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <Icon name="building" size={18} />
                  <Typography>{job.industry}</Typography>
                </Stack>
              )}
              {job.location && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <Icon name="map-pin" size={18} />
                  <Typography>{job.location}</Typography>
                </Stack>
              )}
              <Stack direction="row" spacing={1} alignItems="center">
                <Icon name="briefcase" size={18} />
                <Typography>
                  {job.work_format && `${job.work_format}`}
                  {job.min_experience_months > 0 && ` • ${Math.floor(job.min_experience_months / 12)}+ years`}
                </Typography>
              </Stack>
            </Stack>
          </Box>

          <Divider />

          {/* Salary */}
          {job.salary_min && (
            <Stack direction="row" spacing={1} alignItems="center" color="success">
              <Icon name="dollar-sign" size={20} />
              <Typography variant="h6" fontWeight={600} color="success">
                {job.salary_min.toLocaleString()}
                {job.salary_max && ` - ${job.salary_max.toLocaleString()}`}
              </Typography>
            </Stack>
          )}

          {/* Required Skills */}
          <Box>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Required Skills
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
              {job.required_skills.map((skill) => (
                <Chip
                  key={skill}
                  label={skill}
                  variant="outlined"
                  sx={{
                    borderRadius: 2,
                    px: 1,
                  }}
                />
              ))}
            </Stack>
          </Box>

          <Divider />

          {/* Description */}
          <Box>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Description
            </Typography>
            <Typography
              variant="body1"
              color="secondary"
              sx={{
                whiteSpace: 'pre-wrap',
                lineHeight: 1.8,
              }}
            >
              {job.description}
            </Typography>
          </Box>

          {/* Action Buttons */}
          <Stack direction="row" spacing={2} sx={{ pt: 2 }}>
            <Button
              variant="contained"
              size="large"
              href={`/jobs/${job.id}/apply`}
              sx={{ flexGrow: 1 }}
            >
              Apply Now
            </Button>
            <Button
              variant="outlined"
              size="large"
              sx={{ minWidth: 120 }}
            >
              Save
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Container>
  );
}
