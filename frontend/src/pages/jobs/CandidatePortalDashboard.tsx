import { useMemo } from 'react';
// MUI компоненты для UI
import {
  Container,
  Typography,
  Grid,
  Paper,
  Box,
  Stack,
  Card,
  CardContent,
  Chip,
  Divider,
  Button,
} from '@mui/material';
// Иконки MUI
import {
  WorkOutline as WorkIcon,
  EventAvailable as InterviewIcon,
  Description as DocumentIcon,
  TrendingUp as TrendingIcon,
  AccessTime as TimeIcon,
  LocationOn as LocationIcon,
  ArrowForward as ArrowIcon,
} from '@mui/icons-material';
// Хуки для получения данных
import { useApplications } from '../../hooks/useApplications';
// Компоненты
import { ApplicationCard } from '../../components/jobs/ApplicationCard';
import { PageTransition } from '@components/mui/PageTransition';
import { LoadingState } from '@components/mui/LoadingState';
import { ErrorState } from '@components/mui/ErrorState';
import { useNavigate } from 'react-router-dom';

/**
 * Candidate Portal Dashboard - Unified view for candidates
 *
 * Shows:
 * - Application statistics summary
 * - Recent applications
 * - Upcoming interviews
 * - Quick actions
 */
export function CandidatePortalDashboard() {
  const navigate = useNavigate();

  // Получаем данные о заявках
  const { data, isLoading, error } = useApplications({ limit: 5 });

  // Вычисляем статистику по статусам заявок
  const statistics = useMemo(() => {
    if (!data?.applications) {
      return {
        total: 0,
        pending: 0,
        under_review: 0,
        interview: 0,
        offered: 0,
        rejected: 0,
      };
    }

    return {
      total: data.total || data.applications.length,
      pending: data.applications.filter((app) => app.status === 'pending').length,
      under_review: data.applications.filter((app) => app.status === 'under_review').length,
      interview: data.applications.filter((app) => app.status === 'interview').length,
      offered: data.applications.filter((app) => app.status === 'offered').length,
      rejected: data.applications.filter((app) => app.status === 'rejected').length,
    };
  }, [data]);

  // Mock data for upcoming interviews
  // В будущем это будет загружаться из API /api/candidate-portal/dashboard
  const upcomingInterviews = useMemo(() => {
    if (!data?.applications) return [];

    // Фильтруем заявки со статусом interview
    return data.applications
      .filter((app) => app.status === 'interview')
      .slice(0, 3)
      .map((app) => ({
        id: app.id,
        title: app.title,
        location: app.location || 'Remote',
        // Mock date - в будущем будет приходить из API
        scheduled_at: new Date(Date.now() + Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
        type: 'Technical Interview',
      }));
  }, [data]);

  /**
   * Форматирует дату в читаемый формат
   */
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Tomorrow';
    if (diffDays < 7) return `In ${diffDays} days`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  /**
   * Форматирует время
   */
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <PageTransition>
      <Container maxWidth="xl" sx={{ py: 2 }}>
        {/* Заголовок страницы */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            My Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Track your applications, interviews, and career progress
          </Typography>
        </Box>

        {/* Состояния загрузки и ошибки */}
        {isLoading ? (
          <LoadingState message="Loading dashboard..." />
        ) : error ? (
          <ErrorState
            title="Error"
            message="Failed to load dashboard. Please try again later."
            onRetry={() => window.location.reload()}
          />
        ) : (
          <>
            {/* Статистика */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
              {/* Общее количество заявок */}
              <Grid item xs={12} sm={6} md={3}>
                <Card
                  sx={{
                    height: '100%',
                    background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
                    color: 'white',
                  }}
                >
                  <CardContent>
                    <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
                      <WorkIcon sx={{ fontSize: 28 }} />
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        Total Applications
                      </Typography>
                    </Stack>
                    <Typography variant="h3" fontWeight={700}>
                      {statistics.total}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Под рассмотрением */}
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
                      <TrendingIcon color="info" sx={{ fontSize: 28 }} />
                      <Typography variant="body2" color="text.secondary">
                        Under Review
                      </Typography>
                    </Stack>
                    <Typography variant="h3" fontWeight={700} color="info.main">
                      {statistics.under_review}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Интервью */}
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
                      <InterviewIcon color="warning" sx={{ fontSize: 28 }} />
                      <Typography variant="body2" color="text.secondary">
                        Interviews
                      </Typography>
                    </Stack>
                    <Typography variant="h3" fontWeight={700} color="warning.main">
                      {statistics.interview}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Офферы */}
              <Grid item xs={12} sm={6} md={3}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
                      <DocumentIcon color="success" sx={{ fontSize: 28 }} />
                      <Typography variant="body2" color="text.secondary">
                        Offers
                      </Typography>
                    </Stack>
                    <Typography variant="h3" fontWeight={700} color="success.main">
                      {statistics.offered}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Основной контент */}
            <Grid container spacing={3}>
              {/* Последние заявки */}
              <Grid item xs={12} lg={8}>
                <Paper sx={{ p: 3, height: '100%' }}>
                  <Stack
                    direction="row"
                    justifyContent="space-between"
                    alignItems="center"
                    sx={{ mb: 3 }}
                  >
                    <Typography variant="h6" fontWeight={600}>
                      Recent Applications
                    </Typography>
                    <Button
                      size="small"
                      endIcon={<ArrowIcon />}
                      onClick={() => navigate('/jobs/applications')}
                    >
                      View All
                    </Button>
                  </Stack>

                  {data?.applications && data.applications.length > 0 ? (
                    <Grid container spacing={2}>
                      {data.applications.slice(0, 4).map((application) => (
                        <Grid item xs={12} sm={6} key={application.id}>
                          <ApplicationCard application={application} />
                        </Grid>
                      ))}
                    </Grid>
                  ) : (
                    <Box
                      sx={{
                        textAlign: 'center',
                        py: 6,
                        px: 3,
                      }}
                    >
                      <WorkIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                      <Typography variant="h6" gutterBottom>
                        No applications yet
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Start applying to jobs to track them here
                      </Typography>
                      <Button
                        variant="contained"
                        startIcon={<WorkIcon />}
                        onClick={() => navigate('/jobs')}
                      >
                        Browse Jobs
                      </Button>
                    </Box>
                  )}
                </Paper>
              </Grid>

              {/* Предстоящие интервью */}
              <Grid item xs={12} lg={4}>
                <Paper sx={{ p: 3, height: '100%' }}>
                  <Typography variant="h6" fontWeight={600} sx={{ mb: 3 }}>
                    Upcoming Interviews
                  </Typography>

                  {upcomingInterviews.length > 0 ? (
                    <Stack spacing={2}>
                      {upcomingInterviews.map((interview) => (
                        <Card
                          key={interview.id}
                          variant="outlined"
                          sx={{
                            transition: 'all 0.2s',
                            '&:hover': {
                              boxShadow: 2,
                              borderColor: 'primary.main',
                            },
                          }}
                        >
                          <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                            <Typography
                              variant="subtitle2"
                              fontWeight={600}
                              gutterBottom
                              sx={{
                                display: '-webkit-box',
                                WebkitLineClamp: 1,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden',
                              }}
                            >
                              {interview.title}
                            </Typography>
                            <Chip
                              label={interview.type}
                              size="small"
                              color="warning"
                              sx={{
                                mb: 1.5,
                                height: 20,
                                fontSize: '0.7rem',
                              }}
                            />
                            <Stack spacing={0.5}>
                              <Stack direction="row" spacing={0.5} alignItems="center">
                                <TimeIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                                <Typography variant="caption" color="text.secondary">
                                  {formatDate(interview.scheduled_at)} at{' '}
                                  {formatTime(interview.scheduled_at)}
                                </Typography>
                              </Stack>
                              <Stack direction="row" spacing={0.5} alignItems="center">
                                <LocationIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                                <Typography variant="caption" color="text.secondary">
                                  {interview.location}
                                </Typography>
                              </Stack>
                            </Stack>
                          </CardContent>
                        </Card>
                      ))}
                      <Divider />
                      <Button
                        size="small"
                        endIcon={<ArrowIcon />}
                        onClick={() => navigate('/candidate/interviews')}
                        fullWidth
                      >
                        View All Interviews
                      </Button>
                    </Stack>
                  ) : (
                    <Box
                      sx={{
                        textAlign: 'center',
                        py: 4,
                      }}
                    >
                      <InterviewIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        No upcoming interviews
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Your scheduled interviews will appear here
                      </Typography>
                    </Box>
                  )}
                </Paper>
              </Grid>
            </Grid>

            {/* Quick Actions - внизу */}
            <Paper sx={{ mt: 3, p: 3 }}>
              <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
                Quick Actions
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<WorkIcon />}
                    onClick={() => navigate('/jobs')}
                    sx={{ py: 1.5 }}
                  >
                    Browse Jobs
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<DocumentIcon />}
                    onClick={() => navigate('/candidate/documents')}
                    sx={{ py: 1.5 }}
                  >
                    My Documents
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<InterviewIcon />}
                    onClick={() => navigate('/candidate/interviews')}
                    sx={{ py: 1.5 }}
                  >
                    My Interviews
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<WorkIcon />}
                    onClick={() => navigate('/jobs/applications')}
                    sx={{ py: 1.5 }}
                  >
                    All Applications
                  </Button>
                </Grid>
              </Grid>
            </Paper>
          </>
        )}
      </Container>
    </PageTransition>
  );
}
