import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Chip,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Work as WorkIcon,
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  Money as MoneyIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { WeightProfileSelector } from '../components';
import { apiClient } from '../api/client';

interface Vacancy {
  id: string;
  title: string;
  description: string;
  location: string;
  work_format: string;
  required_skills: string[];
  min_experience_months: number;
  salary_min?: number;
  salary_max?: number;
  created_at: string;
}

const VacancyDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [vacancy, setVacancy] = useState<Vacancy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Weight profile state
  const organizationId = 'org123'; // TODO: Get from auth context
  const [selectedProfileId, setSelectedProfileId] = useState<string | undefined>();
  const [rematching, setRematching] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  useEffect(() => {
    const fetchVacancy = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`/api/vacancies/${id}`);
        setVacancy(response.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load vacancy');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchVacancy();
    }
  }, [id]);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this vacancy?')) return;

    try {
      await axios.delete(`/api/vacancies/${id}`);
      navigate('/recruiter/vacancies');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete vacancy');
    }
  };

  const handleProfileSelect = async (profile: any) => {
    if (!id || !profile?.id) return;

    setRematching(true);
    setError(null);

    try {
      const result = await apiClient.rematchWithWeights(profile.id, {
        vacancy_id: id,
      });

      setSelectedProfileId(profile.id);
      setSnackbar({
        open: true,
        message: `Successfully re-matched ${result.candidates_matched} candidates with new weights`,
        severity: 'success',
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to re-match candidates';
      setError(errorMessage);
      setSnackbar({
        open: true,
        message: errorMessage,
        severity: 'error',
      });
    } finally {
      setRematching(false);
    }
  };

  const handleSnackbarClose = () => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !vacancy) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">{error || 'Vacancy not found'}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/recruiter/vacancies')}
          sx={{ mb: 2 }}
        >
          {t('common.back')}
        </Button>
      </Box>

      <Paper sx={{ p: 4 }}>
        {/* Title and Actions */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" fontWeight={600} gutterBottom>
              {vacancy.title}
            </Typography>
            <Stack direction="row" spacing={1} mt={1}>
              <Chip
                icon={<LocationIcon />}
                label={vacancy.location || 'Remote'}
                size="small"
                variant="outlined"
              />
              <Chip
                label={vacancy.work_format || 'Full-time'}
                size="small"
                color="primary"
                variant="outlined"
              />
            </Stack>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button
              startIcon={<EditIcon />}
              variant="outlined"
              onClick={() => navigate(`/recruiter/vacancies/${vacancy.id}/edit`)}
            >
              {t('common.edit')}
            </Button>
            <Button
              startIcon={<DeleteIcon />}
              variant="outlined"
              color="error"
              onClick={handleDelete}
            >
              {t('common.delete')}
            </Button>
          </Stack>
        </Box>

        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={3}>
          {/* Details */}
          <Grid item xs={12} md={8}>
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Description
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ whiteSpace: 'pre-wrap' }}>
                {vacancy.description || 'No description provided'}
              </Typography>
            </Box>
          </Grid>

          {/* Sidebar */}
          <Grid item xs={12} md={4}>
            <Stack spacing={2}>
              {/* Details Card */}
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    Details
                  </Typography>
                  <Stack spacing={2}>
                    {vacancy.min_experience_months && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Experience Required
                        </Typography>
                        <Typography variant="body1">
                          {Math.floor(vacancy.min_experience_months / 12)}+ years
                        </Typography>
                      </Box>
                    )}
                    {(vacancy.salary_min || vacancy.salary_max) && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Salary
                        </Typography>
                        <Typography variant="body1">
                          {vacancy.salary_min && vacancy.salary_max
                            ? `$${vacancy.salary_min} - $${vacancy.salary_max}`
                            : vacancy.salary_min
                              ? `$${vacancy.salary_min}+`
                              : `Up to $${vacancy.salary_max}`}
                        </Typography>
                      </Box>
                    )}
                  </Stack>
                </CardContent>
              </Card>

              {/* Weight Profile Selector */}
              <Card variant="outlined">
                <CardContent>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                        Matching Algorithm
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Select a weight profile to re-match candidates
                      </Typography>
                    </Box>
                    <Box sx={{ position: 'relative' }}>
                      {rematching && (
                        <Box
                          sx={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            backgroundColor: 'rgba(255, 255, 255, 0.7)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            zIndex: 1,
                            borderRadius: 1,
                          }}
                        >
                          <CircularProgress size={24} />
                        </Box>
                      )}
                      <WeightProfileSelector
                        organizationId={organizationId}
                        selectedProfileId={selectedProfileId}
                        onProfileSelect={handleProfileSelect}
                        compact={true}
                        disabled={rematching}
                      />
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Stack>
          </Grid>
        </Grid>

        {/* Required Skills */}
        {vacancy.required_skills && vacancy.required_skills.length > 0 && (
          <>
            <Divider sx={{ my: 3 }} />
            <Box>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Required Skills
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {vacancy.required_skills.map((skill) => (
                  <Chip key={skill} label={skill} size="small" />
                ))}
              </Box>
            </Box>
          </>
        )}
      </Paper>

      {/* Success/Error Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleSnackbarClose}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
          icon={snackbar.severity === 'success' ? <CheckCircleIcon /> : undefined}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default VacancyDetails;
