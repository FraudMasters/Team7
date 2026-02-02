import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Button,
  Stack,
  Paper,
  Chip,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Work as WorkIcon,
  Description as ResumeIcon,
  Search as SearchIcon,
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingIcon,
  ArrowForward as ArrowIcon,
  CheckCircle as CheckIcon,
  Business as BusinessIcon,
  School as SchoolIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import LoadingSpinner from '../components/LoadingSpinner';

interface Stats {
  totalResumes: number;
  totalVacancies: number;
  activeVacancies: number;
}

/**
 * Home Page - AgentHR Platform
 *
 * Modern landing page showcasing both job seeker and recruiter features.
 */
const HomePage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats>({ totalResumes: 0, totalVacancies: 0, activeVacancies: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [resumesRes, vacanciesRes] = await Promise.all([
          axios.get('/api/resumes/?limit=500'),
          axios.get('/api/vacancies/?limit=100'),
        ]);

        const vacancies = vacanciesRes.data;
        const activeVacancies = vacancies.filter((v: any) => v.status !== 'closed').length;

        setStats({
          totalResumes: resumesRes.data.total_count || resumesRes.data.length || 0,
          totalVacancies: vacancies.length,
          activeVacancies: activeVacancies,
        });
      } catch (e) {
        console.error('Error fetching stats:', e);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const jobSeekerActions = [
    {
      title: t('landing.actions.uploadResume.title'),
      description: t('landing.actions.uploadResume.description'),
      icon: <UploadIcon sx={{ fontSize: 32 }} />,
      color: '#1976d2',
      path: '/upload',
    },
    {
      title: t('landing.actions.findJobs.title'),
      description: t('landing.actions.findJobs.description'),
      icon: <WorkIcon sx={{ fontSize: 32 }} />,
      color: '#2e7d32',
      path: '/jobs',
    },
    {
      title: t('landing.actions.myApplications.title'),
      description: t('landing.actions.myApplications.description'),
      icon: <CheckIcon sx={{ fontSize: 32 }} />,
      color: '#ed6c02',
      path: '/jobs/applications',
    },
  ];

  const recruiterActions = [
    {
      title: t('landing.actions.resumeDatabase.title'),
      description: t('landing.actions.resumeDatabase.description', { count: stats.totalResumes }),
      icon: <ResumeIcon sx={{ fontSize: 32 }} />,
      color: '#9c27b0',
      path: '/recruiter/resumes',
    },
    {
      title: t('landing.actions.candidateSearch.title'),
      description: t('landing.actions.candidateSearch.description'),
      icon: <SearchIcon sx={{ fontSize: 32 }} />,
      color: '#ff5722',
      path: '/recruiter/search',
    },
    {
      title: t('landing.actions.manageVacancies.title'),
      description: t('landing.actions.manageVacancies.description', { count: stats.totalVacancies }),
      icon: <BusinessIcon sx={{ fontSize: 32 }} />,
      color: '#3f51b5',
      path: '/recruiter/vacancies',
    },
    {
      title: t('landing.actions.analytics.title'),
      description: t('landing.actions.analytics.description'),
      icon: <AnalyticsIcon sx={{ fontSize: 32 }} />,
      color: '#673ab7',
      path: '/recruiter/analytics',
    },
  ];

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
          color: 'white',
          py: { xs: 6, sm: 8, md: 10 },
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Background pattern */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            opacity: 0.1,
            backgroundImage: 'radial-gradient(circle at 20% 50%, white 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />

        <Container maxWidth="lg">
          <Box sx={{ position: 'relative', zIndex: 1 }}>
            <Typography
              variant="h2"
              component="h1"
              sx={{
                fontWeight: 700,
                mb: 2,
                fontSize: { xs: '2rem', md: '3rem' },
              }}
            >
              {t('landing.hero.title')}
            </Typography>
            <Typography
              variant="h5"
              sx={{
                mb: 4,
                opacity: 0.9,
                fontSize: { xs: '1.2rem', md: '1.5rem' },
              }}
            >
              {t('landing.hero.subtitle')}
            </Typography>

            {/* Quick Stats */}
            {loading ? (
              <Box sx={{ py: 4 }}>
                <LoadingSpinner size={40} />
              </Box>
            ) : (
              <Stack
                direction="row"
                spacing={{ xs: 2, sm: 3 }}
                sx={{ justifyContent: { xs: 'center', md: 'flex-start' }, mb: { xs: 3, md: 4 } }}
                flexWrap="wrap"
              >
                <Box sx={{ textAlign: 'center', minWidth: { xs: '80px', sm: '100px' } }}>
                  <Typography
                    variant="h3"
                    fontWeight={700}
                    sx={{ fontSize: { xs: '1.75rem', sm: '2.25rem', md: '3rem' } }}
                  >
                    {stats.totalResumes}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9, fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    {t('landing.stats.resumes')}
                  </Typography>
                </Box>
                <Box sx={{ textAlign: 'center', minWidth: { xs: '80px', sm: '100px' } }}>
                  <Typography
                    variant="h3"
                    fontWeight={700}
                    sx={{ fontSize: { xs: '1.75rem', sm: '2.25rem', md: '3rem' } }}
                  >
                    {stats.totalVacancies}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9, fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    {t('landing.stats.vacancies')}
                  </Typography>
                </Box>
                <Box sx={{ textAlign: 'center', minWidth: { xs: '80px', sm: '100px' } }}>
                  <Typography
                    variant="h3"
                    fontWeight={700}
                    sx={{ fontSize: { xs: '1.75rem', sm: '2.25rem', md: '3rem' } }}
                  >
                    {stats.activeVacancies}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9, fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    {t('landing.stats.active')}
                  </Typography>
                </Box>
              </Stack>
            )}

            {/* CTA Buttons */}
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              spacing={{ xs: 1.5, sm: 2 }}
              sx={{ justifyContent: { xs: 'center', md: 'flex-start' }, alignItems: { xs: 'stretch', sm: 'center' } }}
            >
              <Button
                variant="contained"
                size="large"
                startIcon={<UploadIcon />}
                onClick={() => navigate('/upload')}
                sx={{
                  bgcolor: 'white',
                  color: 'primary.main',
                  px: { xs: 2, sm: 3 },
                  py: { xs: 1, sm: 1.5 },
                  fontWeight: 600,
                  '&:hover': { bgcolor: 'grey.100' },
                }}
              >
                {t('landing.uploadResume')}
              </Button>
              <Button
                variant="outlined"
                size="large"
                startIcon={<WorkIcon />}
                onClick={() => navigate('/jobs')}
                sx={{
                  color: 'white',
                  borderColor: 'white',
                  px: { xs: 2, sm: 3 },
                  py: { xs: 1, sm: 1.5 },
                  fontWeight: 600,
                  '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' },
                }}
              >
                {t('landing.browseJobs')}
              </Button>
            </Stack>
          </Box>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ py: { xs: 4, sm: 5, md: 6 } }}>
        {/* For Job Seekers */}
        <Box sx={{ mb: { xs: 6, md: 8 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: { xs: 2, md: 3 } }}>
            <SchoolIcon sx={{ mr: 1, color: 'primary.main', fontSize: { xs: 24, md: 28 } }} />
            <Typography variant="h4" fontWeight={600} sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
              {t('landing.forJobSeekers')}
            </Typography>
          </Box>

          <Grid container spacing={3} columns={{ xs: 12, sm: 12, md: 12 }}>
            {jobSeekerActions.map((action) => (
              <Grid item xs={12} sm={6} md={4} key={action.path}>
                <Card
                  sx={{
                    height: '100%',
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    borderLeft: 4,
                    borderColor: action.color,
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    },
                  }}
                  onClick={() => navigate(action.path)}
                >
                  <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                    <Box sx={{ display: 'flex', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
                      <Box
                        sx={{
                          width: { xs: 40, sm: 48 },
                          height: { xs: 40, sm: 48 },
                          borderRadius: 2,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mr: { xs: 0, sm: 2 },
                          mb: { xs: 1, sm: 0 },
                          bgcolor: `${action.color}20`,
                          color: action.color,
                        }}
                      >
                        {action.icon}
                      </Box>
                      <Typography variant="h6" fontWeight={600} sx={{ textAlign: { xs: 'center', sm: 'left' }, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                        {action.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {action.description}
                    </Typography>
                    <Button
                      variant="text"
                      endIcon={<ArrowIcon />}
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(action.path);
                      }}
                      sx={{ color: action.color, fontWeight: 600 }}
                    >
                      {t('landing.getStarted')}
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>

        {/* For Recruiters */}
        <Box sx={{ mb: { xs: 6, md: 8 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: { xs: 2, md: 3 } }}>
            <BusinessIcon sx={{ mr: 1, color: 'success.main', fontSize: { xs: 24, md: 28 } }} />
            <Typography variant="h4" fontWeight={600} sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
              {t('landing.forRecruiters')}
            </Typography>
          </Box>

          <Grid container spacing={3} columns={{ xs: 12, sm: 12, md: 12 }}>
            {recruiterActions.map((action) => (
              <Grid item xs={12} sm={6} md={3} key={action.path}>
                <Card
                  sx={{
                    height: '100%',
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    borderLeft: 4,
                    borderColor: action.color,
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    },
                  }}
                  onClick={() => navigate(action.path)}
                >
                  <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                    <Box sx={{ display: 'flex', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
                      <Box
                        sx={{
                          width: { xs: 40, sm: 48 },
                          height: { xs: 40, sm: 48 },
                          borderRadius: 2,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mr: { xs: 0, sm: 2 },
                          mb: { xs: 1, sm: 0 },
                          bgcolor: `${action.color}20`,
                          color: action.color,
                        }}
                      >
                        {action.icon}
                      </Box>
                      <Typography variant="h6" fontWeight={600} sx={{ textAlign: { xs: 'center', sm: 'left' }, fontSize: { xs: '0.95rem', sm: '1rem' } }}>
                        {action.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {action.description}
                    </Typography>
                    <Button
                      variant="text"
                      endIcon={<ArrowIcon />}
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(action.path);
                      }}
                      sx={{ color: action.color, fontWeight: 600 }}
                    >
                      {t('landing.open')}
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>

        {/* How It Works */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: { xs: 3, md: 4 } }}>
            <TrendingIcon sx={{ mr: 1, color: 'info.main', fontSize: { xs: 24, md: 28 } }} />
            <Typography variant="h4" fontWeight={600} sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
              {t('landing.howItWorks')}
            </Typography>
          </Box>

          <Paper elevation={1} sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
            <Grid container spacing={{ xs: 3, sm: 4 }}>
              <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
                <Box
                  sx={{
                    width: { xs: 48, sm: 56 },
                    height: { xs: 48, sm: 56 },
                    borderRadius: '50%',
                    bgcolor: 'primary.main',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: { xs: 1.5, sm: 2 },
                    fontSize: { xs: '1.25rem', sm: '1.5rem' },
                    fontWeight: 700,
                  }}
                >
                  1
                </Box>
                <Typography variant="h6" fontWeight={600} gutterBottom sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
                  {t('landing.steps.step1.title')}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('landing.steps.step1.description')}
                </Typography>
              </Grid>

              <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
                <Box
                  sx={{
                    width: { xs: 48, sm: 56 },
                    height: { xs: 48, sm: 56 },
                    borderRadius: '50%',
                    bgcolor: 'info.main',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: { xs: 1.5, sm: 2 },
                    fontSize: { xs: '1.25rem', sm: '1.5rem' },
                    fontWeight: 700,
                  }}
                >
                  2
                </Box>
                <Typography variant="h6" fontWeight={600} gutterBottom sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
                  {t('landing.steps.step2.title')}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('landing.steps.step2.description')}
                </Typography>
              </Grid>

              <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
                <Box
                  sx={{
                    width: { xs: 48, sm: 56 },
                    height: { xs: 48, sm: 56 },
                    borderRadius: '50%',
                    bgcolor: 'success.main',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: { xs: 1.5, sm: 2 },
                    fontSize: { xs: '1.25rem', sm: '1.5rem' },
                    fontWeight: 700,
                  }}
                >
                  3
                </Box>
                <Typography variant="h6" fontWeight={600} gutterBottom sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
                  {t('landing.steps.step3.title')}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('landing.steps.step3.description')}
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </Box>
      </Container>
    </Box>
  );
};

export default HomePage;
