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
  Compare as CompareIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import CandidateSelector from '../components/CandidateSelector';

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

interface Candidate {
  resume_id: string;
  name?: string;
  match_percentage?: number;
  matched_skills_count?: number;
  total_skills_count?: number;
  overall_match?: boolean;
}

const VacancyDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [vacancy, setVacancy] = useState<Vacancy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [candidatesLoading, setCandidatesLoading] = useState(true);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);

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

  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        setCandidatesLoading(true);
        const response = await axios.get('/api/candidates', {
          params: { vacancy_id: id, limit: 50 },
        });

        // Transform API response to match Candidate interface
        const transformedCandidates: Candidate[] = response.data.candidates.map((c: any) => ({
          resume_id: c.resume_id,
          name: c.name || `Candidate ${c.resume_id.slice(0, 8)}`,
          match_percentage: c.rank_score ? Math.round(c.rank_score * 100) : undefined,
          matched_skills_count: c.ranking_factors?.skills_match?.matched_skills_count,
          total_skills_count: c.ranking_factors?.skills_match?.total_skills_count,
          overall_match: c.recommendation === 'excellent' || c.recommendation === 'good',
        }));

        setCandidates(transformedCandidates);
      } catch (err) {
        // Don't set error state - candidates section is optional
      } finally {
        setCandidatesLoading(false);
      }
    };

    if (id) {
      fetchCandidates();
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

  const handleSelectionChange = (selectedIds: string[]) => {
    setSelectedCandidateIds(selectedIds);
  };

  const handleCompareCandidates = () => {
    if (selectedCandidateIds.length >= 2 && selectedCandidateIds.length <= 5) {
      const candidatesParam = selectedCandidateIds.join(',');
      navigate(`/recruiter/vacancies/${id}/compare?candidates=${candidatesParam}`);
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

      {/* Candidates Section */}
      <Paper sx={{ p: 4, mt: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" fontWeight={600}>
            Candidates for this Position
          </Typography>
          {selectedCandidateIds.length >= 2 && selectedCandidateIds.length <= 5 && (
            <Button
              variant="contained"
              startIcon={<CompareIcon />}
              onClick={handleCompareCandidates}
              size="large"
            >
              Compare Selected ({selectedCandidateIds.length})
            </Button>
          )}
        </Box>

        {candidatesLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <CandidateSelector
            candidates={candidates}
            onSelectionChange={handleSelectionChange}
            maxCandidates={5}
            minCandidates={2}
          />
        )}
      </Paper>
    </Container>
  );
};

export default VacancyDetails;
