import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Paper,
  Card,
  CardContent,
  CircularProgress,
  Stack,
} from '@mui/material';
import {
  TrendingUp as TrendingIcon,
  Description as ResumeIcon,
  Work as WorkIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import RecruitingFunnel from '@components/RecruitingFunnel';
import ModelQualityMetrics from '@components/ModelQualityMetrics';

interface SummaryStats {
  totalResumes: number;
  totalVacancies: number;
  highMatchCount: number;
  mediumMatchCount: number;
}

/**
 * Analytics Dashboard Page (Recruiter Module)
 *
 * Shows hiring metrics and funnel visualization using real data from existing APIs.
 */
const AnalyticsDashboardPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<SummaryStats | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);

        // Fetch resumes and vacancies
        const [resumesResponse, vacanciesResponse] = await Promise.all([
          axios.get('/api/resumes/?limit=200'),
          axios.get('/api/vacancies/?limit=50'),
        ]);

        const resumes = resumesResponse.data;
        const vacancies = vacanciesResponse.data;

        // Calculate match statistics
        let highMatch = 0;
        let mediumMatch = 0;

        // Sample first 20 resumes for speed
        const sampleSize = Math.min(resumes.length, 20);

        for (let i = 0; i < sampleSize; i++) {
          const resume = resumes[i];
          for (const vacancy of vacancies) {
            try {
              const matchResponse = await axios.get(
                `/api/vacancies/match/${vacancy.id}?resume_id=${resume.id}`
              );
              const pct = matchResponse.data.match_percentage || 0;
              if (pct >= 70) highMatch++;
              if (pct >= 50) mediumMatch++;
            } catch (e) {
              // Skip errors
            }
          }
        }

        setStats({
          totalResumes: resumes.length,
          totalVacancies: vacancies.length,
          highMatchCount: highMatch,
          mediumMatchCount: mediumMatch,
        });
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight={700} gutterBottom>
          {t('analyticsDashboard.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('analyticsDashboard.subtitle')}
        </Typography>
      </Box>

      {/* Summary Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={6} md={3}>
          <Card
            sx={{
              borderTop: 4,
              borderColor: 'primary.main',
              boxShadow: 2,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ResumeIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="body2" color="text.secondary">
                  {t('analyticsDashboard.stats.totalResumes')}
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="primary.main">
                {stats?.totalResumes || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} md={3}>
          <Card
            sx={{
              borderTop: 4,
              borderColor: 'success.main',
              boxShadow: 2,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <WorkIcon sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="body2" color="text.secondary">
                  {t('analyticsDashboard.stats.activeVacancies')}
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="success.main">
                {stats?.totalVacancies || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} md={3}>
          <Card
            sx={{
              borderTop: 4,
              borderColor: 'warning.main',
              boxShadow: 2,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CheckIcon sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="body2" color="text.secondary">
                  {t('analyticsDashboard.stats.highMatches')}
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="warning.main">
                {stats?.highMatchCount || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6} md={3}>
          <Card
            sx={{
              borderTop: 4,
              borderColor: 'info.main',
              boxShadow: 2,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingIcon sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="body2" color="text.secondary">
                  {t('analyticsDashboard.stats.mediumMatches')}
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={700} color="info.main">
                {stats?.mediumMatchCount || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recruiting Funnel */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <RecruitingFunnel />
      </Paper>

      {/* ML/NLP Quality Metrics */}
      <Paper sx={{ p: 3 }}>
        <ModelQualityMetrics />
      </Paper>
    </Container>
  );
};

export default AnalyticsDashboardPage;
