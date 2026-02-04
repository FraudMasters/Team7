import { Box, Container, Typography, Paper, Stack, Grid, Card, CardContent } from '@mui/material';
import {
  CompareArrows as CompareIcon,
  Balance as EquityIcon,
  Assessment as AnalysisIcon,
} from '@mui/icons-material';
import OfferComparisonTool from '../../components/salary/OfferComparisonTool';
import EquityAnalysisDashboard from '../../components/salary/EquityAnalysisDashboard';

/**
 * CompensationAnalysisPage Component
 *
 * Main page for compensation analysis tools.
 * Displays offer comparison tools and internal equity analysis dashboards.
 *
 * Features:
 * - Offer comparison with cost-of-living adjustments
 * - Internal equity analysis and disparity detection
 * - Pay equity alerts and recommendations
 * - Multi-offer total compensation comparison
 *
 * @example
 * ```tsx
 * <CompensationAnalysisPage />
 * ```
 */
export function CompensationAnalysisPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Page Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Compensation Analysis
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Offer comparison and equity analysis tools
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
                  <CompareIcon fontSize="large" />
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    Offer Comparison
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Compare multiple offers
                  </Typography>
                </Box>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Compare job offers side-by-side with cost-of-living adjustments to make informed
                compensation decisions.
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
                  <EquityIcon fontSize="large" />
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    Equity Analysis
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Internal pay equity
                  </Typography>
                </Box>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Analyze internal pay equity across candidates and positions to ensure fair compensation
                practices.
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
                  <AnalysisIcon fontSize="large" />
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    Insights
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Data-driven decisions
                  </Typography>
                </Box>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Get actionable insights and recommendations for competitive and equitable compensation
                packages.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Offer Comparison Tool */}
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" fontWeight={600} gutterBottom>
            Offer Comparison Tool
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Compare multiple job offers with cost-of-living adjustments to determine the best
            compensation package
          </Typography>
        </Box>

        <OfferComparisonTool />
      </Paper>

      {/* Equity Analysis Dashboard */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" fontWeight={600} gutterBottom>
            Internal Equity Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Analyze pay equity across candidates for a specific vacancy to ensure fair compensation
            practices
          </Typography>
        </Box>

        <EquityAnalysisDashboard vacancyId="00000000-0000-0000-0000-000000000000" />
      </Paper>
    </Container>
  );
}
