import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Chip,
  Stack,
  Grid,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Work as WorkIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

interface Vacancy {
  id: string;
  title: string;
  description: string;
  required_skills: string[];
  min_experience_months: number;
  additional_requirements: string[];
  industry?: string;
  work_format?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  english_level?: string;
  employment_type?: string;
  created_at: string;
  updated_at: string;
}

const VacancyList: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  // Determine if we're in job seeker or recruiter context
  const isJobsContext = location.pathname.startsWith('/jobs');
  const basePath = isJobsContext ? '/jobs' : '/recruiter/vacancies';

  const [vacancies, setVacancies] = useState<Vacancy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [vacancyToDelete, setVacancyToDelete] = useState<string | null>(null);

  useEffect(() => {
    fetchVacancies();
  }, []);

  const fetchVacancies = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/vacancies/');

      if (!response.ok) {
        throw new Error('Failed to fetch vacancies');
      }

      const data: Vacancy[] = await response.json();
      setVacancies(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch vacancies');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (id: string) => {
    setVacancyToDelete(id);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!vacancyToDelete) return;

    try {
      const response = await fetch(`/api/vacancies/${vacancyToDelete}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete vacancy');
      }

      // Remove from list
      setVacancies(vacancies.filter((v) => v.id !== vacancyToDelete));
      setDeleteDialogOpen(false);
      setVacancyToDelete(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete vacancy');
    }
  };

  const formatSalary = (min?: number, max?: number) => {
    if (min && max) {
      return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    }
    if (min) {
      return t('vacancyList.salary.from', { amount: min.toLocaleString() });
    }
    if (max) {
      return t('vacancyList.salary.to', { amount: max.toLocaleString() });
    }
    return t('vacancyList.salary.notSpecified');
  };

  const formatExperience = (months: number) => {
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;

    if (years === 0) {
      return `${remainingMonths} мес.`;
    }
    if (remainingMonths === 0) {
      return `${years} ${getYearWord(years)}`;
    }
    return `${years} ${getYearWord(years)} ${remainingMonths} мес.`;
  };

  const getYearWord = (years: number) => {
    const lastTwo = years % 100;
    const lastOne = years % 10;

    if (lastTwo >= 11 && lastTwo <= 19) {
      return 'лет';
    }
    if (lastOne === 1) {
      return 'год';
    }
    if (lastOne >= 2 && lastOne <= 4) {
      return 'года';
    }
    return 'лет';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" component="h1" fontWeight={600} gutterBottom>
            {t('vacancyList.title')}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('vacancyList.subtitle')}
          </Typography>
        </Box>
        <Button
          variant="contained"
          size="large"
          startIcon={<AddIcon />}
          onClick={() => navigate(`${basePath}/create`)}
        >
          {t('vacancyList.createRequest')}
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Vacancies List */}
      {vacancies.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <WorkIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {t('vacancyList.noActiveRequests')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {t('vacancyList.createFirstRequest')}
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate(`${basePath}/create`)}
          >
            {t('vacancyList.createRequest')}
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {vacancies.map((vacancy) => (
            <Grid item xs={12} md={6} lg={4} key={vacancy.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  {/* Title */}
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    {vacancy.title}
                  </Typography>

                  {/* Salary */}
                  <Typography variant="body2" color="primary" fontWeight={500} sx={{ mb: 1 }}>
                    {formatSalary(vacancy.salary_min, vacancy.salary_max)}
                  </Typography>

                  {/* Experience */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      {t('vacancyList.experience')}:
                    </Typography>
                    <Typography variant="body2" fontWeight={500}>
                      {formatExperience(vacancy.min_experience_months)}
                    </Typography>
                  </Box>

                  {/* Skills */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                      {t('vacancyList.requiredSkills', { count: vacancy.required_skills.length })}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {vacancy.required_skills.slice(0, 4).map((skill) => (
                        <Chip key={skill} label={skill} size="small" variant="outlined" />
                      ))}
                      {vacancy.required_skills.length > 4 && (
                        <Chip
                          label={t('vacancyList.more', { count: vacancy.required_skills.length - 4 })}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </Box>

                  {/* Meta info */}
                  <Stack direction="row" spacing={1} flexWrap="wrap">
                    {vacancy.employment_type && (
                      <Chip label={vacancy.employment_type} size="small" color="info" variant="outlined" />
                    )}
                    {vacancy.work_format && (
                      <Chip label={vacancy.work_format} size="small" color="success" variant="outlined" />
                    )}
                    {vacancy.english_level && (
                      <Chip label={`English: ${vacancy.english_level}`} size="small" />
                    )}
                  </Stack>
                </CardContent>

                <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                  <Button
                    size="small"
                    onClick={() => navigate(`${basePath}/${vacancy.id}`)}
                  >
                    {t('vacancyList.moreDetails')}
                  </Button>
                  <Box>
                    <IconButton
                      size="small"
                      onClick={() => navigate(`${basePath}/${vacancy.id}/edit`)}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteClick(vacancy.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>{t('vacancyList.deleteDialog.title')}</DialogTitle>
        <DialogContent>
          <Typography>
            {t('vacancyList.deleteDialog.message')}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            {t('common.delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default VacancyList;
