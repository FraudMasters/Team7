import { Container, Box, Typography, Grid, Paper, Card, CardContent, Button, Icon } from '@/components/ui';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  RateReview as RateReviewIcon,
  Work as WorkIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { BentoCard } from '../../components/dashboard/BentoCard';
import { useHiringManagerDashboard, useHiringManagerReviewQueue } from '../../hooks/useHiringManagerData';

/**
 * Hiring Manager Dashboard Page
 *
 * Simplified dashboard for hiring managers showing candidates pending review,
 * quick actions for common tasks, and key metrics for decision making.
 * Mobile-optimized for tablet access between meetings.
 */
export function DashboardPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Fetch dashboard statistics
  const { data: dashboardStats, isLoading: statsLoading } = useHiringManagerDashboard();

  // Fetch review queue for quick preview
  const { data: reviewQueue } = useHiringManagerReviewQueue({ limit: 5 });

  // Extract stats with defaults
  const pendingReview = dashboardStats?.pending_review;
  const quickStats = dashboardStats?.quick_stats;
  const myVacancies = dashboardStats?.my_vacancies || [];
  const recentActivity = dashboardStats?.recent_activity || [];

  // Quick action modules
  const quickActions = [
    {
      title: t('hiringManagerDashboard.quickActions.reviewQueue.title', 'Review Queue'),
      description: t('hiringManagerDashboard.quickActions.reviewQueue.description', 'View candidates awaiting your decision'),
      iconName: 'rate-review',
      path: '/hiring-manager/review-queue',
      color: '#1976d2',
      badge: pendingReview?.total_pending,
    },
    {
      title: t('hiringManagerDashboard.quickActions.approvals.title', 'Approvals'),
      description: t('hiringManagerDashboard.quickActions.approvals.description', 'Manage approved candidates'),
      iconName: 'check-circle',
      path: '/hiring-manager/approvals',
      color: '#388e3c',
    },
    {
      title: t('hiringManagerDashboard.quickActions.interviews.title', 'Interviews'),
      description: t('hiringManagerDashboard.quickActions.interviews.description', 'Schedule and manage interviews'),
      iconName: 'schedule',
      path: '/hiring-manager/schedule',
      color: '#ff9800',
      badge: quickStats?.interviews_scheduled,
    },
    {
      title: t('hiringManagerDashboard.quickActions.profile.title', 'My Profile'),
      description: t('hiringManagerDashboard.quickActions.profile.description', 'Update your preferences'),
      iconName: 'person',
      path: '/hiring-manager/profile',
      color: '#9c27b0',
    },
  ];

  // Get icon component by name
  const getIconComponent = (iconName: string, color: string) => {
    const icons: Record<string, React.ReactNode> = {
      'rate-review': <RateReviewIcon sx={{ color }} />,
      'check-circle': <CheckCircleIcon sx={{ color }} />,
      schedule: <ScheduleIcon sx={{ color }} />,
      person: <PersonIcon sx={{ color }} />,
    };
    return icons[iconName] || <RateReviewIcon sx={{ color }} />;
  };

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Dashboard Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>
          {t('hiringManagerDashboard.title', 'Hiring Manager Dashboard')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('hiringManagerDashboard.welcome', 'Welcome back! Here are the candidates awaiting your review.')}
        </Typography>
      </Box>

      {/* Stats Grid in Bento Style */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {/* Pending Review Card */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title={t('hiringManagerDashboard.stats.pendingReview', 'Pending Review')}
            value={statsLoading ? '...' : (pendingReview?.total_pending ?? 0)}
            subtitle={t('hiringManagerDashboard.stats.awaitingDecision', 'Awaiting your decision')}
            icon={<RateReviewIcon sx={{ color: 'white' }} />}
            color="primary"
          />
        </Grid>

        {/* Urgent Candidates Card */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title={t('hiringManagerDashboard.stats.urgent', 'Urgent')}
            value={statsLoading ? '...' : (pendingReview?.urgent_count ?? 0)}
            subtitle={t('hiringManagerDashboard.stats.needsAttention', 'Needs immediate attention')}
            icon={<WarningIcon sx={{ color: 'white' }} />}
            color="warning"
          />
        </Grid>

        {/* Approved This Month */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title={t('hiringManagerDashboard.stats.approved', 'Approved')}
            value={statsLoading ? '...' : (quickStats?.approved_this_month ?? 0)}
            subtitle={t('hiringManagerDashboard.stats.thisMonth', 'This month')}
            icon={<CheckCircleIcon sx={{ color: 'white' }} />}
            color="success"
          />
        </Grid>

        {/* Average Decision Time */}
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title={t('hiringManagerDashboard.stats.avgTime', 'Avg. Decision Time')}
            value={
              statsLoading
                ? '...'
                : quickStats?.avg_time_to_decision_days
                  ? `${quickStats.avg_time_to_decision_days}d`
                  : '--'
            }
            subtitle={t('hiringManagerDashboard.stats.days', 'Days average')}
            icon={<TrendingUpIcon sx={{ color: 'white' }} />}
            color="secondary"
          />
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Typography variant="h6" gutterBottom sx={{ mt: 4, mb: 2 }}>
        {t('hiringManagerDashboard.quickActions.title', 'Quick Actions')}
      </Typography>
      <Grid container spacing={3}>
        {quickActions.map((action, index) => (
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
              onClick={() => navigate(action.path)}
            >
              <CardContent disableGutters sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        borderRadius: 2,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        mr: 2,
                        bgcolor: `${action.color}20`,
                      }}
                    >
                      {getIconComponent(action.iconName, action.color)}
                    </Box>
                    <Typography variant="h6" sx={{ color: action.color }}>
                      {action.title}
                    </Typography>
                  </Box>
                  {action.badge !== undefined && action.badge > 0 && (
                    <Box
                      sx={{
                        bgcolor: action.color,
                        color: 'white',
                        borderRadius: '50%',
                        width: 28,
                        height: 28,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.875rem',
                        fontWeight: 600,
                      }}
                    >
                      {action.badge}
                    </Box>
                  )}
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1 }}>
                  {action.description}
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  sx={{ mt: 2, alignSelf: 'flex-start', borderColor: action.color }}
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(action.path);
                  }}
                >
                  {t('common.open', 'Open')}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* My Vacancies Section */}
      {myVacancies.length > 0 && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            {t('hiringManagerDashboard.myVacancies.title', 'My Vacancies')}
          </Typography>
          <Grid container spacing={2}>
            {myVacancies.slice(0, 4).map((vacancy) => (
              <Grid item xs={12} sm={6} md={3} key={vacancy.vacancy_id}>
                <Paper sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <WorkIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography variant="subtitle2" noWrap sx={{ flexGrow: 1 }}>
                      {vacancy.vacancy_title}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {vacancy.pending_review} {t('hiringManagerDashboard.myVacancies.pending', 'pending')}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {vacancy.total_candidates} {t('hiringManagerDashboard.myVacancies.totalCandidates', 'total candidates')}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Recent Activity Preview */}
      {recentActivity.length > 0 && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            {t('hiringManagerDashboard.recentActivity.title', 'Recent Activity')}
          </Typography>
          <Paper sx={{ p: 2 }}>
            {recentActivity.slice(0, 5).map((activity, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  py: 1.5,
                  borderBottom: index < recentActivity.slice(0, 5).length - 1 ? 1 : 0,
                  borderColor: 'divider',
                }}
              >
                <Icon
                  name={
                    activity.activity_type === 'approved'
                      ? 'check-circle'
                      : activity.activity_type === 'rejected'
                        ? 'cancel'
                        : 'schedule'
                  }
                  size={20}
                  sx={{ mr: 2, color: activity.activity_type === 'approved' ? 'success.main' : activity.activity_type === 'rejected' ? 'error.main' : 'warning.main' }}
                />
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="body2">
                    {activity.candidate_name} - {activity.vacancy_title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(activity.timestamp).toLocaleDateString()}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Paper>
        </Box>
      )}

      {/* Mobile-optimized tip */}
      <Box sx={{ mt: 4, p: 2, bgcolor: 'info.lighter', borderRadius: 2 }}>
        <Typography variant="body2" color="text.secondary">
          <strong>
            {t('hiringManagerDashboard.tip.icon', '💡')} {t('hiringManagerDashboard.tip.title', 'Tip:')}
          </strong>{' '}
          {t(
            'hiringManagerDashboard.tip.content',
            'You can quickly approve or reject candidates directly from the review queue. Swipe on mobile or use the action buttons.'
          )}
        </Typography>
      </Box>
    </Container>
  );
}

export default DashboardPage;
