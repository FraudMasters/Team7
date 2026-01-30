import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Button,
  Alert,
  AlertTitle,
  Stack,
  Grid,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Business as BusinessIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';

/**
 * Taxonomy usage statistics interface from backend
 */
interface TaxonomyUsageStats {
  taxonomy_id: string;
  taxonomy_name: string;
  usage_count: number;
  avg_match_score: number;
  success_rate: number;
  total_candidates_matched: number;
  industry?: string;
}

/**
 * Taxonomy usage response from backend
 */
interface TaxonomyUsageResponse {
  most_used_taxonomies: TaxonomyUsageStats[];
  most_effective_taxonomies: TaxonomyUsageStats[];
  industry_filter?: string;
  total_taxonomies_analyzed: number;
}

/**
 * TaxonomyAnalytics Component Props
 */
interface TaxonomyAnalyticsProps {
  /** API endpoint URL for taxonomy analytics */
  apiUrl?: string;
  /** Optional industry filter */
  industry?: string;
  /** Maximum number of taxonomies to display */
  limit?: number;
}

/**
 * TaxonomyAnalytics Component
 *
 * Displays industry-specific taxonomy analytics including:
 * - Most used taxonomies with usage counts
 * - Most effective taxonomies with match scores
 * - Industry breakdown with filters
 * - Success rates and candidate matches
 * - Summary statistics
 *
 * @example
 * ```tsx
 * <TaxonomyAnalytics />
 * ```
 *
 * @example
 * ```tsx
 * <TaxonomyAnalytics industry="healthcare" limit={15} />
 * ```
 */
const TaxonomyAnalytics: React.FC<TaxonomyAnalyticsProps> = ({
  apiUrl = 'http://localhost:8000/api/analytics/taxonomy-usage',
  industry,
  limit = 10,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [taxonomyData, setTaxonomyData] = useState<TaxonomyUsageResponse | null>(null);

  /**
   * Fetch taxonomy analytics data from backend
   */
  const fetchTaxonomyAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      // Build URL with query parameters
      const url = new URL(apiUrl);
      if (industry) {
        url.searchParams.append('industry', industry);
      }
      if (limit) {
        url.searchParams.append('limit', limit.toString());
      }

      const response = await fetch(url.toString());

      if (!response.ok) {
        throw new Error(`Failed to fetch taxonomy analytics: ${response.statusText}`);
      }

      const result: TaxonomyUsageResponse = await response.json();
      setTaxonomyData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load taxonomy analytics data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTaxonomyAnalytics();
  }, [apiUrl, industry, limit]);

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          Loading taxonomy analytics...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          This may take a few moments
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" onClick={fetchTaxonomyAnalytics} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Taxonomy Analytics</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!taxonomyData || taxonomyData.most_used_taxonomies.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>No Taxonomy Analytics Data</AlertTitle>
        No taxonomy analytics data found. Start using industry-specific taxonomies in your job vacancies to populate this dashboard.
      </Alert>
    );
  }

  // Calculate summary statistics
  const totalUsage = taxonomyData.most_used_taxonomies.reduce((sum, t) => sum + t.usage_count, 0);
  const avgMatchScore =
    taxonomyData.most_effective_taxonomies.reduce((sum, t) => sum + t.avg_match_score, 0) /
    taxonomyData.most_effective_taxonomies.length;
  const avgSuccessRate =
    taxonomyData.most_effective_taxonomies.reduce((sum, t) => sum + t.success_rate, 0) /
    taxonomyData.most_effective_taxonomies.length;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BusinessIcon fontSize="large" color="primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Taxonomy Usage Analytics
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Industry-specific skill taxonomy performance metrics
                {taxonomyData.industry_filter && ` - Filtered by: ${taxonomyData.industry_filter}`}
              </Typography>
            </Box>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchTaxonomyAnalytics} size="small">
            Refresh
          </Button>
        </Box>

        {/* Summary Stats */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {taxonomyData.total_taxonomies_analyzed}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Total Taxonomies
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {totalUsage.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Total Usage
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" fontWeight={700}>
                  {avgMatchScore.toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Avg Match Score
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {(avgSuccessRate * 100).toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Avg Success Rate
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Most Used Taxonomies */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Most Used Taxonomies
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Taxonomies ranked by frequency of usage in job postings
        </Typography>

        <Stack spacing={2} sx={{ mt: 3 }}>
          {taxonomyData.most_used_taxonomies.map((taxonomy, index) => (
            <Card
              key={taxonomy.taxonomy_id}
              variant="outlined"
              sx={{
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateX(4px)',
                  boxShadow: 2,
                },
              }}
            >
              <CardContent sx={{ py: 2 }}>
                <Grid container spacing={2} alignItems="center">
                  {/* Rank and Taxonomy Name */}
                  <Grid item xs={12} sm={4}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={`#${index + 1}`}
                        size="small"
                        color={index < 3 ? 'primary' : 'default'}
                        sx={{
                          fontWeight: 700,
                          minWidth: 45,
                          bgcolor: index < 3 ? 'primary.main' : 'action.disabledBackground',
                        }}
                      />
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {taxonomy.taxonomy_name}
                        </Typography>
                        {taxonomy.industry && (
                          <Typography variant="caption" color="text.secondary">
                            {taxonomy.industry}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </Grid>

                  {/* Usage Bar Chart */}
                  <Grid item xs={12} sm={5}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ flexGrow: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                          <Typography variant="caption" color="text.secondary">
                            Usage
                          </Typography>
                          <Typography variant="body2" fontWeight={600}>
                            {taxonomy.usage_count.toLocaleString()} times
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={(taxonomy.usage_count / totalUsage) * 100}
                          sx={{
                            height: 8,
                            borderRadius: 1,
                            bgcolor: 'action.hover',
                            '& .MuiLinearProgress-bar': {
                              bgcolor: index < 3 ? 'success.main' : 'success.light',
                            },
                          }}
                        />
                      </Box>
                    </Box>
                  </Grid>

                  {/* Success Rate Indicator */}
                  <Grid item xs={12} sm={3}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        gap: 0.5,
                      }}
                    >
                      <CheckIcon
                        fontSize="small"
                        color={taxonomy.success_rate >= 0.8 ? 'success' : taxonomy.success_rate >= 0.6 ? 'warning' : 'error'}
                      />
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        color={
                          taxonomy.success_rate >= 0.8 ? 'success.main' : taxonomy.success_rate >= 0.6 ? 'warning.main' : 'error.main'
                        }
                      >
                        {(taxonomy.success_rate * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        success
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          ))}
        </Stack>
      </Paper>

      {/* Most Effective Taxonomies */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Most Effective Taxonomies
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Taxonomies ranked by average match score and success rate
        </Typography>

        <Stack spacing={2} sx={{ mt: 3 }}>
          {taxonomyData.most_effective_taxonomies.map((taxonomy, index) => (
            <Card
              key={taxonomy.taxonomy_id}
              variant="outlined"
              sx={{
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateX(4px)',
                  boxShadow: 2,
                },
              }}
            >
              <CardContent sx={{ py: 2 }}>
                <Grid container spacing={2} alignItems="center">
                  {/* Rank and Taxonomy Name */}
                  <Grid item xs={12} sm={4}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={`#${index + 1}`}
                        size="small"
                        color={index < 3 ? 'success' : 'default'}
                        sx={{
                          fontWeight: 700,
                          minWidth: 45,
                          bgcolor: index < 3 ? 'success.main' : 'action.disabledBackground',
                        }}
                      />
                      <Box>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {taxonomy.taxonomy_name}
                        </Typography>
                        {taxonomy.industry && (
                          <Typography variant="caption" color="text.secondary">
                            {taxonomy.industry}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </Grid>

                  {/* Match Score Bar Chart */}
                  <Grid item xs={12} sm={5}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ flexGrow: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                          <Typography variant="caption" color="text.secondary">
                            Match Score
                          </Typography>
                          <Typography variant="body2" fontWeight={600}>
                            {taxonomy.avg_match_score.toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={taxonomy.avg_match_score}
                          sx={{
                            height: 8,
                            borderRadius: 1,
                            bgcolor: 'action.hover',
                            '& .MuiLinearProgress-bar': {
                              bgcolor: index < 3 ? 'primary.main' : 'primary.light',
                            },
                          }}
                        />
                      </Box>
                    </Box>
                  </Grid>

                  {/* Candidates Matched */}
                  <Grid item xs={12} sm={3}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        gap: 0.5,
                      }}
                    >
                      <TrendingUpIcon fontSize="small" color="primary" />
                      <Typography variant="body2" fontWeight={600} color="primary.main">
                        {taxonomy.total_candidates_matched.toLocaleString()}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        candidates
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          ))}
        </Stack>
      </Paper>
    </Stack>
  );
};

export default TaxonomyAnalytics;
