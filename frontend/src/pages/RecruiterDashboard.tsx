import React from 'react';
import { Container, Typography, Box, Grid, Card, CardContent, Button, Paper } from '@mui/material';
import { Work as WorkIcon, Description as ResumeIcon, Analytics as AnalyticsIcon, Search as SearchIcon, ViewKanban as ViewKanbanIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import RecruitingFunnel from '@components/RecruitingFunnel';

/**
 * Recruiter Dashboard Page (Recruiter Module)
 *
 * Main dashboard for recruiters with quick access to all recruiter features.
 */
const RecruiterDashboardPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const modules = [
    {
      title: t('recruiterDashboard.modules.resumeDatabase.title'),
      description: t('recruiterDashboard.modules.resumeDatabase.description'),
      icon: <ResumeIcon />,
      path: '/recruiter/resumes',
      color: '#1976d2',
    },
    {
      title: t('recruiterDashboard.modules.manageVacancies.title'),
      description: t('recruiterDashboard.modules.manageVacancies.description'),
      icon: <WorkIcon />,
      path: '/recruiter/vacancies',
      color: '#388e3c',
    },
    {
      title: t('recruiterDashboard.modules.candidateSearch.title'),
      description: t('recruiterDashboard.modules.candidateSearch.description'),
      icon: <SearchIcon />,
      path: '/recruiter/search',
      color: '#ff9800',
    },
    {
      title: t('recruiterDashboard.modules.analytics.title'),
      description: t('recruiterDashboard.modules.analytics.description'),
      icon: <AnalyticsIcon />,
      path: '/recruiter/analytics',
      color: '#9c27b0',
    },
    {
      title: t('recruiterDashboard.modules.workflowBoard.title'),
      description: t('recruiterDashboard.modules.workflowBoard.description'),
      icon: <ViewKanbanIcon />,
      path: '/recruiter/workflow',
      color: '#00bcd4',
    },
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
          {t('recruiterDashboard.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('recruiterDashboard.welcome')}
        </Typography>
      </Box>

      {/* Stats Summary */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <WorkIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">{t('recruiterDashboard.stats.vacancies')}</Typography>
              </Box>
              <Typography variant="h4" color="primary">5</Typography>
              <Typography variant="caption" color="text.secondary">{t('recruiterDashboard.stats.activeJobPostings')}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ResumeIcon sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">{t('recruiterDashboard.stats.resumes')}</Typography>
              </Box>
              <Typography variant="h4" color="success.main">65</Typography>
              <Typography variant="caption" color="text.secondary">{t('recruiterDashboard.stats.inDatabase')}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
        {t('recruiterDashboard.quickActions')}
      </Typography>
      <Grid container spacing={3}>
        {modules.map((module, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card
              sx={{
                height: '100%',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
              onClick={() => navigate(module.path)}
            >
              <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mr: 2,
                      bgcolor: `${module.color}20`,
                    }}
                  >
                    {module.icon}
                  </Box>
                  <Typography variant="h6" sx={{ color: module.color }}>
                    {module.title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1 }}>
                  {module.description}
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  sx={{ mt: 2, alignSelf: 'flex-start', borderColor: module.color }}
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(module.path);
                  }}
                >
                  {t('landing.open')}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Recruiting Funnel */}
      <Box sx={{ mt: 4 }}>
        <Paper sx={{ p: 3 }}>
          <RecruitingFunnel />
        </Paper>
      </Box>

      {/* Info Box */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="body2" color="text.secondary">
          <strong>💡 {t('recruiterDashboard.tip')}</strong>
        </Typography>
      </Box>
    </Container>
  );
};

export default RecruiterDashboardPage;
