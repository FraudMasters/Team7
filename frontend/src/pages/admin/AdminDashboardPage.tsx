import React from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Work as WorkIcon,
  Description as DescriptionIcon,
  TrendingUp as TrendingUpIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';

const AdminDashboardPage: React.FC = () => {
  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Admin Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          System overview and management controls
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* System Status Card */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    p: 1,
                    borderRadius: 2,
                    bgcolor: 'success.light',
                    color: 'success.contrastText',
                  }}
                >
                  <DashboardIcon />
                </Box>
                <Box sx={{ ml: 2 }}>
                  <Typography variant="h6" fontWeight={600}>
                    System Status
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label="Operational" color="success" size="small" />
                <Typography variant="body2" color="text.secondary">
                  All systems running
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Active Users Card */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    p: 1,
                    borderRadius: 2,
                    bgcolor: 'primary.light',
                    color: 'primary.contrastText',
                  }}
                >
                  <PeopleIcon />
                </Box>
                <Box sx={{ ml: 2 }}>
                  <Typography variant="h6" fontWeight={600}>
                    Active Users
                  </Typography>
                </Box>
              </Box>
              <Typography variant="h4" fontWeight={700}>
                0
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Currently online
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Vacancies Card */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    p: 1,
                    borderRadius: 2,
                    bgcolor: 'info.light',
                    color: 'info.contrastText',
                  }}
                >
                  <WorkIcon />
                </Box>
                <Box sx={{ ml: 2 }}>
                  <Typography variant="h6" fontWeight={600}>
                    Vacancies
                  </Typography>
                </Box>
              </Box>
              <Typography variant="h4" fontWeight={700}>
                0
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active job postings
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Resumes Card */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    p: 1,
                    borderRadius: 2,
                    bgcolor: 'warning.light',
                    color: 'warning.contrastText',
                  }}
                >
                  <DescriptionIcon />
                </Box>
                <Box sx={{ ml: 2 }}>
                  <Typography variant="h6" fontWeight={600}>
                    Resumes
                  </Typography>
                </Box>
              </Box>
              <Typography variant="h4" fontWeight={700}>
                0
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total resumes
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Quick Actions
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    cursor: 'pointer',
                    '&:hover': {
                      bgcolor: 'action.hover',
                    },
                  }}
                >
                  <PeopleIcon color="primary" sx={{ mb: 1 }} />
                  <Typography variant="subtitle2" fontWeight={600}>
                    Manage Users
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Add, edit, or remove users
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    cursor: 'pointer',
                    '&:hover': {
                      bgcolor: 'action.hover',
                    },
                  }}
                >
                  <SecurityIcon color="primary" sx={{ mb: 1 }} />
                  <Typography variant="subtitle2" fontWeight={600}>
                    Security Settings
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Configure access controls
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    cursor: 'pointer',
                    '&:hover': {
                      bgcolor: 'action.hover',
                    },
                  }}
                >
                  <TrendingUpIcon color="primary" sx={{ mb: 1 }} />
                  <Typography variant="subtitle2" fontWeight={600}>
                    View Analytics
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    System performance metrics
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    cursor: 'pointer',
                    '&:hover': {
                      bgcolor: 'action.hover',
                    },
                  }}
                >
                  <DashboardIcon color="primary" sx={{ mb: 1 }} />
                  <Typography variant="subtitle2" fontWeight={600}>
                    System Health
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Monitor system status
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default AdminDashboardPage;
