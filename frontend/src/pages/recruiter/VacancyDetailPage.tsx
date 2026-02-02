import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Stack,
  Chip,
  Button,
  Divider,
} from '@mui/material';
import {
  LocationOn,
  WorkOutline,
  AttachMoney,
  Business,
  Edit,
  People,
} from '@mui/icons-material';
import { useJob } from '../../hooks/useJobs';
import { PageTransition } from '../../components/ui/PageTransition';
import { LoadingState } from '../../components/ui/LoadingState';
import { ErrorState } from '../../components/ui/ErrorState';

export function VacancyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: vacancy, isLoading, error } = useJob(id || '');

  if (isLoading) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <LoadingState message="Loading vacancy details..." />
        </Container>
      </PageTransition>
    );
  }

  if (error || !vacancy) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <ErrorState
            title="Vacancy Not Found"
            message="The vacancy you're looking for doesn't exist or you don't have permission to view it."
            onRetry={() => navigate('/recruiter/vacancies')}
          />
        </Container>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Paper sx={{ p: { xs: 3, md: 5 } }}>
          <Stack spacing={4}>
          {/* Header */}
          <Box>
            <Typography variant="h3" fontWeight={700} gutterBottom>
              {vacancy.title}
            </Typography>
            <Stack direction="row" spacing={2} flexWrap="wrap" color="text.secondary">
              {vacancy.industry && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <Business sx={{ fontSize: 18 }} />
                  <Typography>{vacancy.industry}</Typography>
                </Stack>
              )}
              {vacancy.location && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <LocationOn sx={{ fontSize: 18 }} />
                  <Typography>{vacancy.location}</Typography>
                </Stack>
              )}
              <Stack direction="row" spacing={1} alignItems="center">
                <WorkOutline sx={{ fontSize: 18 }} />
                <Typography>
                  {vacancy.work_format && `${vacancy.work_format}`}
                  {vacancy.min_experience_months > 0 && ` • ${Math.floor(vacancy.min_experience_months / 12)}+ years`}
                </Typography>
              </Stack>
            </Stack>
          </Box>

          <Divider />

          {/* Salary */}
          {vacancy.salary_min && (
            <Stack direction="row" spacing={1} alignItems="center" color="success.main">
              <AttachMoney sx={{ fontSize: 20 }} />
              <Typography variant="h6" fontWeight={600} color="success.main">
                {vacancy.salary_min.toLocaleString()}
                {vacancy.salary_max && ` - ${vacancy.salary_max.toLocaleString()}`}
              </Typography>
            </Stack>
          )}

          {/* Required Skills */}
          <Box>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Required Skills
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
              {vacancy.required_skills.map((skill) => (
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
              {vacancy.description}
            </Typography>
          </Box>

          {/* Action Buttons */}
          <Stack direction="row" spacing={2} sx={{ pt: 2 }}>
            <Button
              variant="contained"
              size="large"
              startIcon={<People />}
              onClick={() => navigate('/recruiter/candidates')}
              sx={{ flexGrow: 1 }}
            >
              View Candidates
            </Button>
            <Button
              variant="outlined"
              size="large"
              startIcon={<Edit />}
              onClick={() => navigate(`/recruiter/vacancies/${vacancy.id}/edit`)}
            >
              Edit Vacancy
            </Button>
          </Stack>
        </Stack>
      </Paper>
      </Container>
    </PageTransition>
  );
}
