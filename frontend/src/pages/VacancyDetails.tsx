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
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Work as WorkIcon,
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  Money as MoneyIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

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
    </Container>
  );
};

export default VacancyDetails;
