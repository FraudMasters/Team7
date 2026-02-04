import { Box, Container, Typography, Paper, Stack, Grid, Card, CardContent } from '@mui/material';
import {
  AttachMoney as SalaryIcon,
  TrendingUp as TrendingUpIcon,
  BarChart as AnalyticsIcon,
} from '@mui/icons-material';
import SalaryBenchmarkChart from '../../components/salary/SalaryBenchmarkChart';

/**
 * SalaryBenchmarkingPage Component
 *
 * Main page for salary benchmarking and compensation analysis.
 * Displays market salary data, analytics, and benchmarking tools.
 *
 * Features:
 * - Salary benchmark charts by role and location
 * - Market salary data visualization
 * - Export functionality for compensation data
 * - Real-time data refresh
 *
 * @example
 * ```tsx
 * <SalaryBenchmarkingPage />
 * ```
 */
export function SalaryBenchmarkingPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Page Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Salary Benchmarking
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Market compensation data and analytics
          </Typography>
        </Box>
      </Stack>

      {/* Feature Overview Cards */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card
            sx={{
              height: '100%',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 4,
              },
            }}
          >
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: 'primary.light',
                    color: 'primary.contrastText',
                  }}
                >
                  <SalaryIcon fontSize="large" />
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    Market Data
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Real-time salary benchmarks
                  </Typography>
                </Box>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Access comprehensive salary data from multiple sources, updated regularly to reflect
                current market conditions.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            sx={{
              height: '100%',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 4,
              },
            }}
          >
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: 'success.light',
                    color: 'success.contrastText',
                  }}
                >
                  <TrendingUpIcon fontSize="large" />
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    Cost of Living
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Geographic adjustments
                  </Typography>
                </Box>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Compare salaries across different locations with cost-of-living adjustments for
                accurate compensation analysis.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            sx={{
              height: '100%',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 4,
              },
            }}
          >
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: 'info.light',
                    color: 'info.contrastText',
                  }}
                >
                  <AnalyticsIcon fontSize="large" />
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    Analytics
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Data-driven insights
                  </Typography>
                </Box>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Export salary data for budgeting, planning, and compensation analysis with detailed
                breakdowns by role and location.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Salary Benchmark Chart */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" fontWeight={600} gutterBottom>
            Salary Benchmarks by Role and Location
          </Typography>
          <Typography variant="body2" color="text.secondary">
            View current market salary data for various roles and geographic locations
          </Typography>
        </Box>

        <SalaryBenchmarkChart />
      </Paper>
    </Container>
  );
}
