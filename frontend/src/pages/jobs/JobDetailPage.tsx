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
  Grid,
} from '@mui/material';
import {
  LocationOn,
  WorkOutline,
  AttachMoney,
  Business,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useJob } from '../../hooks/useJobs';

const MotionPaper = motion(Paper);

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
      <MotionPaper
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        sx={{ p: { xs: 3, md: 5 } }}
      >
        <Stack spacing={4}>
          {/* Header */}
          <Box>
            <Typography variant="h3" fontWeight={700} gutterBottom>
              {job.title}
            </Typography>
            <Stack direction="row" spacing={2} flexWrap="wrap" color="text.secondary">
              {job.industry && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <Business sx={{ fontSize: 18 }} />
                  <Typography>{job.industry}</Typography>
                </Stack>
              )}
              {job.location && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <LocationOn sx={{ fontSize: 18 }} />
                  <Typography>{job.location}</Typography>
                </Stack>
              )}
              <Stack direction="row" spacing={1} alignItems="center">
                <WorkOutline sx={{ fontSize: 18 }} />
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
            <Stack direction="row" spacing={1} alignItems="center" color="success.main">
              <AttachMoney sx={{ fontSize: 20 }} />
              <Typography variant="h6" fontWeight={600} color="success.main">
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
              color="text.secondary"
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
      </MotionPaper>
    </Container>
  );
}
