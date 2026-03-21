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
import { config } from '@/config';
import {
  Refresh as RefreshIcon,
  Diversity3 as DiversityIcon,
  People as PeopleIcon,
  School as SchoolIcon,
  Public as PublicIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';

/**
 * Gender demographics metrics from backend
 */
interface GenderDemographics {
  male_count: number;
  male_percentage: number;
  female_count: number;
  female_percentage: number;
  non_binary_count: number;
  non_binary_percentage: number;
  other_count: number;
  other_percentage: number;
  total_candidates: number;
}

/**
 * Age group demographics metrics from backend
 */
interface AgeGroupDemographics {
  age_group: string;
  count: number;
  percentage: number;
}

/**
 * Education level demographics metrics from backend
 */
interface EducationDemographics {
  education_level: string;
  count: number;
  percentage: number;
}

/**
 * Location demographics metrics from backend
 */
interface LocationDemographics {
  location: string;
  count: number;
  percentage: number;
}

/**
 * Diversity metrics response from backend
 */
interface DiversityMetricsResponse {
  gender: GenderDemographics;
  age_groups: AgeGroupDemographics[];
  education_levels: EducationDemographics[];
  geographic_distribution: LocationDemographics[];
  total_analyzed: number;
  diversity_score?: number;
}

/**
 * DiversityMetricsPanel Component Props
 */
interface DiversityMetricsPanelProps {
  /** API endpoint URL for diversity metrics */
  apiUrl?: string;
  /** Optional date range filter */
  startDate?: string;
  /** Optional date range filter */
  endDate?: string;
  /** Optional department filter */
  department?: string;
}

/**
 * DiversityMetricsPanel Component
 *
 * Displays diversity and inclusion metrics in a compact panel format including:
 * - Gender distribution overview
 * - Geographic diversity metrics
 * - Education level breakdown
 * - Age group distribution
 * - Overall diversity score
 *
 * @example
 * ```tsx
 * <DiversityMetricsPanel />
 * ```
 *
 * @example
 * ```tsx
 * <DiversityMetricsPanel
 *   startDate="2024-01-01"
 *   endDate="2024-12-31"
 *   department="Engineering"
 * />
 * ```
 */
const DiversityMetricsPanel: React.FC<DiversityMetricsPanelProps> = ({
  apiUrl = `${config.api.url}/api/analytics/diversity-metrics`,
  startDate,
  endDate,
  department,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [diversityData, setDiversityData] = useState<DiversityMetricsResponse | null>(null);

  /**
   * Fetch diversity metrics data from backend
   */
  const fetchDiversityMetrics = async () => {
    try {
      setLoading(true);
      setError(null);

      // Build URL with query parameters
      const url = new URL(apiUrl);
      if (startDate) {
        url.searchParams.append('start_date', startDate);
      }
      if (endDate) {
        url.searchParams.append('end_date', endDate);
      }
      if (department) {
        url.searchParams.append('department', department);
      }

      const response = await fetch(url.toString());

      if (!response.ok) {
        throw new Error(`Failed to fetch diversity metrics: ${response.statusText}`);
      }

      const result: DiversityMetricsResponse = await response.json();
      setDiversityData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load diversity metrics data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiversityMetrics();
  }, [apiUrl, startDate, endDate, department]);

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
          Loading diversity metrics...
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
          <Button color="inherit" onClick={fetchDiversityMetrics} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Diversity Metrics</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!diversityData || diversityData.total_analyzed === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>No Diversity Data Available</AlertTitle>
        No diversity metrics data found. Start processing candidates to populate this dashboard.
      </Alert>
    );
  }

  // Calculate summary statistics
  const genderDiversityIndex =
    (diversityData.gender.female_percentage + diversityData.gender.non_binary_percentage) / 100;
  const geographicDiversity = diversityData.geographic_distribution.length;
  const educationDiversity = diversityData.education_levels.length;

  // Gender distribution data
  const genderDistribution = [
    {
      label: 'Male',
      count: diversityData.gender.male_count,
      percentage: diversityData.gender.male_percentage,
      color: 'primary.main',
    },
    {
      label: 'Female',
      count: diversityData.gender.female_count,
      percentage: diversityData.gender.female_percentage,
      color: 'secondary.main',
    },
    {
      label: 'Non-Binary',
      count: diversityData.gender.non_binary_count,
      percentage: diversityData.gender.non_binary_percentage,
      color: 'success.main',
    },
    {
      label: 'Other',
      count: diversityData.gender.other_count,
      percentage: diversityData.gender.other_percentage,
      color: 'info.main',
    },
  ].filter((item) => item.count > 0);

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DiversityIcon fontSize="large" color="primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Diversity & Inclusion Metrics
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Workforce diversity analytics and demographic insights
                {department && ` - ${department}`}
              </Typography>
            </Box>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchDiversityMetrics} size="small">
            Refresh
          </Button>
        </Box>

        {/* Summary Stats */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {diversityData.total_analyzed}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Total Analyzed
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {(genderDiversityIndex * 100).toFixed(0)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Gender Diversity
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" fontWeight={700}>
                  {geographicDiversity}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Locations
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {educationDiversity}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Education Levels
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Gender Distribution */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Gender Distribution
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Gender representation across candidate pipeline
        </Typography>

        <Stack spacing={2} sx={{ mt: 3 }}>
          {genderDistribution.map((item, index) => (
            <Card
              key={item.label}
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
                  {/* Label */}
                  <Grid item xs={12} sm={3}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={item.label}
                        size="small"
                        sx={{
                          fontWeight: 600,
                          bgcolor: item.color,
                          color: 'white',
                        }}
                      />
                    </Box>
                  </Grid>

                  {/* Progress Bar */}
                  <Grid item xs={12} sm={6}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ flexGrow: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                          <Typography variant="caption" color="text.secondary">
                            Representation
                          </Typography>
                          <Typography variant="body2" fontWeight={600}>
                            {item.percentage.toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={item.percentage}
                          sx={{
                            height: 8,
                            borderRadius: 1,
                            bgcolor: 'action.hover',
                            '& .MuiLinearProgress-bar': {
                              bgcolor: item.color,
                            },
                          }}
                        />
                      </Box>
                    </Box>
                  </Grid>

                  {/* Count */}
                  <Grid item xs={12} sm={3}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        gap: 0.5,
                      }}
                    >
                      <PeopleIcon fontSize="small" color="action" />
                      <Typography variant="body2" fontWeight={600}>
                        {item.count.toLocaleString()}
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

      {/* Geographic Distribution */}
      {diversityData.geographic_distribution.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight={600}>
            Top Geographic Locations
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Geographic diversity across candidate pool
          </Typography>

          <Stack spacing={2} sx={{ mt: 3 }}>
            {diversityData.geographic_distribution.slice(0, 5).map((location, index) => (
              <Card
                key={location.location}
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
                    {/* Rank and Location */}
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
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <PublicIcon fontSize="small" color="action" />
                          <Typography variant="subtitle1" fontWeight={600}>
                            {location.location}
                          </Typography>
                        </Box>
                      </Box>
                    </Grid>

                    {/* Progress Bar */}
                    <Grid item xs={12} sm={5}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ flexGrow: 1 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              Distribution
                            </Typography>
                            <Typography variant="body2" fontWeight={600}>
                              {location.percentage.toFixed(1)}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={location.percentage}
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

                    {/* Count */}
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
                          {location.count.toLocaleString()}
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
      )}

      {/* Education Levels */}
      {diversityData.education_levels.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight={600}>
            Education Level Distribution
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Educational background diversity metrics
          </Typography>

          <Grid container spacing={2} sx={{ mt: 2 }}>
            {diversityData.education_levels.slice(0, 6).map((education, index) => (
              <Grid item xs={12} sm={6} md={4} key={education.education_level}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 2,
                    },
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <SchoolIcon fontSize="small" sx={{ mr: 1, color: 'info.main' }} />
                      <Typography variant="subtitle2" fontWeight={600}>
                        {education.education_level}
                      </Typography>
                    </Box>
                    <Typography variant="h5" fontWeight={600} color="primary.main" sx={{ mb: 1 }}>
                      {education.percentage.toFixed(1)}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={education.percentage}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        bgcolor: 'action.hover',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: 'info.main',
                        },
                      }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      {education.count} candidates
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Age Groups */}
      {diversityData.age_groups.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight={600}>
            Age Group Distribution
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Age diversity across candidate pipeline
          </Typography>

          <Grid container spacing={2} sx={{ mt: 2 }}>
            {diversityData.age_groups.map((ageGroup) => (
              <Grid item xs={12} sm={6} md={3} key={ageGroup.age_group}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    borderLeft: 4,
                    borderLeftColor: 'primary.main',
                  }}
                >
                  <CardContent>
                    <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                      {ageGroup.age_group}
                    </Typography>
                    <Typography variant="h5" fontWeight={600} color="primary.main" sx={{ mb: 1 }}>
                      {ageGroup.percentage.toFixed(1)}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={ageGroup.percentage}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        bgcolor: 'action.hover',
                      }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      {ageGroup.count} candidates
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}
    </Stack>
  );
};

export default DiversityMetricsPanel;
