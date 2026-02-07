import { Container, Box, Typography, Grid, Paper } from '@mui/material';
import { AdminPanelSettings as AdminIcon, People as PeopleIcon, Business as BusinessIcon, Assessment as AnalyticsIcon } from '@mui/icons-material';
import { BentoCard } from '../../components/dashboard/BentoCard';

export function AdminDashboard() {
  // TODO: Create useAdminData hook when admin API endpoints are available
  // const { data: adminData } = useAdminData();

  // Placeholder metrics - will be replaced with real API data
  const organizationCount = 0;
  const userCount = 0;
  const systemHealth = 'Operational';
  const analyticsCount = 0;

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>
          Admin Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          System overview and administrative controls
        </Typography>
      </Box>

      {/* Bento Grid Metrics */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Organizations"
            value={organizationCount}
            subtitle="Registered organizations"
            icon={<BusinessIcon sx={{ color: 'white' }} />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Total Users"
            value={userCount}
            subtitle="Active accounts"
            icon={<PeopleIcon sx={{ color: 'white' }} />}
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="System Health"
            value={systemHealth}
            subtitle="All services operational"
            icon={<AdminIcon sx={{ color: 'white' }} />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <BentoCard
            title="Analytics Reports"
            value={analyticsCount}
            subtitle="Generated this month"
            icon={<AnalyticsIcon sx={{ color: 'white' }} />}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* System Overview */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            System Overview
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              System metrics and administrative actions will be displayed here...
            </Typography>
          </Box>
        </Paper>
      </Grid>
    </Container>
  );
}
