import { Container, Box, Typography, Grid, Paper, Icon } from '@/components/ui';
import { BentoCard } from '../../components/dashboard/BentoCard';
import { useRecruiterAnalytics, useCandidates, useRecruiterVacancies } from '../../hooks/useRecruiterData';

export function DashboardPage() {
  const { data: analytics } = useRecruiterAnalytics();
  const { data: candidatesData } = useCandidates();
  const { data: vacanciesData } = useRecruiterVacancies();

  const candidateCount = candidatesData?.candidates?.length || 0;
  const vacancyCount = vacanciesData?.vacancies?.length || 0;

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>
          Recruiter Dashboard
        </Typography>
        <Typography variant="body1" color="secondary">
          Welcome back! Here's what's happening today.
        </Typography>
      </Box>

      {/* Bento Grid Metrics */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Active Jobs"
            value={vacancyCount}
            subtitle="Open positions"
            icon={<Icon name="briefcase" size={24} sx={{ color: '#fff' }} />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Total Candidates"
            value={candidateCount}
            subtitle="In pipeline"
            icon={<Icon name="users" size={24} sx={{ color: '#fff' }} />}
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Time to Hire"
            value={analytics?.time_to_hire ? `${analytics.time_to_hire}d` : '--'}
            subtitle="Average days"
            icon={<Icon name="zap" size={24} sx={{ color: '#fff' }} />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Applications/Job"
            value={analytics?.applications_per_job?.toFixed(1) || '--'}
            subtitle="This month"
            icon={<Icon name="trending-up" size={24} sx={{ color: '#fff' }} />}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* Pipeline Funnel */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Pipeline Funnel
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="secondary">
              Pipeline metrics will be displayed here...
            </Typography>
          </Box>
        </Paper>
      </Grid>
    </Container>
  );
}
