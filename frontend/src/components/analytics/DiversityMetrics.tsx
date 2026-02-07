import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Button,
  Alert,
  AlertTitle,
  Stack,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Diversity3 as DiversityIcon,
  People as PeopleIcon,
  School as SchoolIcon,
  Public as PublicIcon,
  Translate as LanguageIcon,
  CheckCircle as CheckIcon,
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
 * Language demographics metrics from backend
 */
interface LanguageDemographics {
  language: string;
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
  languages: LanguageDemographics[];
  total_analyzed: number;
}

/**
 * DiversityMetrics Component Props
 */
interface DiversityMetricsProps {
  /** API endpoint URL for diversity metrics */
  apiUrl?: string;
  /** Optional date range filter */
  startDate?: string;
  /** Optional date range filter */
  endDate?: string;
}

/**
 * Get color for gender display
 */
function getGenderColor(gender: string): string {
  switch (gender.toLowerCase()) {
    case 'male':
      return 'primary.main';
    case 'female':
      return 'secondary.main';
    case 'non_binary':
      return 'success.main';
    default:
      return 'info.main';
  }
}

/**
 * Get icon for education level
 */
function getEducationIcon(level: string) {
  if (level.includes('PhD') || level.includes('Doctorate')) {
    return <SchoolIcon sx={{ color: 'warning.main' }} />;
  }
  if (level.includes('Master')) {
    return <SchoolIcon sx={{ color: 'primary.main' }} />;
  }
  if (level.includes('Bachelor')) {
    return <SchoolIcon sx={{ color: 'info.main' }} />;
  }
  return <SchoolIcon sx={{ color: 'text.secondary' }} />;
}

/**
 * DiversityMetrics Component
 *
 * Displays diversity and inclusion metrics including:
 * - Gender distribution with percentages
 * - Age group demographics
 * - Education level breakdown
 * - Geographic distribution
 * - Language diversity
 * - Overall diversity summary
 *
 * @example
 * ```tsx
 * <DiversityMetrics />
 * ```
 *
 * @example
 * ```tsx
 * <DiversityMetrics startDate="2024-01-01" endDate="2024-12-31" />
 * ```
 */
const DiversityMetrics: React.FC<DiversityMetricsProps> = ({
  apiUrl = '/api/analytics/diversity-metrics',
  startDate,
  endDate,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [diversityData, setDiversityData] = useState<DiversityMetricsResponse | null>(null);

  /**
   * Fetch diversity metrics from backend
   */
  const fetchDiversityData = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: Record<string, string> = {};
      if (startDate) {
        params.start_date = startDate;
      }
      if (endDate) {
        params.end_date = endDate;
      }

      const response = await axios.get<DiversityMetricsResponse>(apiUrl, { params });
      setDiversityData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load diversity metrics';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiversityData();
  }, [startDate, endDate]);

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
          <Button color="inherit" onClick={fetchDiversityData} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Diversity Data</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!diversityData) {
    return null;
  }

  const { gender, age_groups, education_levels, geographic_distribution, languages, total_analyzed } =
    diversityData;

  // Gender distribution data
  const genderDistribution = [
    { label: 'Male', count: gender.male_count, percentage: gender.male_percentage, color: 'primary.main' },
    { label: 'Female', count: gender.female_count, percentage: gender.female_percentage, color: 'secondary.main' },
    { label: 'Non-Binary', count: gender.non_binary_count, percentage: gender.non_binary_percentage, color: 'success.main' },
    { label: 'Other/Unspecified', count: gender.other_count, percentage: gender.other_percentage, color: 'info.main' },
  ];

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Diversity & Inclusion Metrics
          </Typography>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchDiversityData} size="small">
            Refresh
          </Button>
        </Box>

        {/* Summary Cards */}
        <Grid container spacing={2}>
          {/* Total Analyzed Card */}
          <Grid item xs={12} sm={6} md={3}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: 'primary.main',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <PeopleIcon fontSize="large" sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6" fontWeight={600}>
                    Total Analyzed
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight={700} color="primary.main">
                  {total_analyzed}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Candidates with demographic data
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Gender Diversity Card */}
          <Grid item xs={12} sm={6} md={3}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: 'secondary.main',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <DiversityIcon fontSize="large" sx={{ mr: 1, color: 'secondary.main' }} />
                  <Typography variant="h6" fontWeight={600}>
                    Gender Diversity
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight={700} color="secondary.main">
                  {gender.total_candidates}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  With gender information
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Education Levels Card */}
          <Grid item xs={12} sm={6} md={3}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: 'info.main',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <SchoolIcon fontSize="large" sx={{ mr: 1, color: 'info.main' }} />
                  <Typography variant="h6" fontWeight={600}>
                    Education Levels
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight={700} color="info.main">
                  {education_levels.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Different levels represented
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Geographic Diversity Card */}
          <Grid item xs={12} sm={6} md={3}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                borderColor: 'success.main',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <PublicIcon fontSize="large" sx={{ mr: 1, color: 'success.main' }} />
                  <Typography variant="h6" fontWeight={600}>
                    Geographic Reach
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight={700} color="success.main">
                  {geographic_distribution.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Locations represented
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Gender Distribution Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Gender Distribution
        </Typography>
        <Grid container spacing={2}>
          {genderDistribution.map((item) => (
            <Grid item xs={12} sm={6} md={3} key={item.label}>
              <Card
                variant="outlined"
                sx={{
                  borderColor: item.color,
                  height: '100%',
                }}
              >
                <CardContent>
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      {item.label}
                    </Typography>
                    <Typography variant="h5" fontWeight={600} color={item.color}>
                      {item.percentage.toFixed(1)}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={item.percentage}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: 'action.hover',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: item.color,
                      },
                    }}
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    {item.count} candidates
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Age Groups Section */}
      {age_groups.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Age Group Distribution
          </Typography>
          <Stack spacing={2}>
            {age_groups.map((ageGroup) => (
              <Card
                key={ageGroup.age_group}
                variant="outlined"
                sx={{
                  borderLeft: 4,
                  borderLeftColor: 'primary.main',
                }}
              >
                <CardContent sx={{ py: 1.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle2" fontWeight={600}>
                      {ageGroup.age_group}
                    </Typography>
                    <Chip
                      label={`${ageGroup.percentage.toFixed(1)}%`}
                      size="small"
                      color="primary"
                    />
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={ageGroup.percentage}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: 'action.hover',
                    }}
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    {ageGroup.count} candidates
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Paper>
      )}

      {/* Education Levels Section */}
      {education_levels.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Education Level Distribution
          </Typography>
          <Grid container spacing={2}>
            {education_levels.map((education) => (
              <Grid item xs={12} sm={6} md={3} key={education.education_level}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Box sx={{ mr: 1 }}>
                        {getEducationIcon(education.education_level)}
                      </Box>
                      <Typography variant="subtitle2" fontWeight={600} sx={{ flex: 1 }}>
                        {education.education_level}
                      </Typography>
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="h5" fontWeight={600} color="primary.main">
                        {education.percentage.toFixed(1)}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={education.percentage}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'action.hover',
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

      {/* Geographic Distribution Section */}
      {geographic_distribution.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Geographic Distribution
          </Typography>
          <Grid container spacing={2}>
            {geographic_distribution.slice(0, 8).map((location) => (
              <Grid item xs={12} sm={6} md={4} key={location.location}>
                <Card
                  variant="outlined"
                  sx={{
                    borderLeft: 4,
                    borderLeftColor: 'success.main',
                    height: '100%',
                  }}
                >
                  <CardContent sx={{ py: 1.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <PublicIcon sx={{ mr: 1, fontSize: 'small', color: 'success.main' }} />
                        <Typography variant="subtitle2" fontWeight={600}>
                          {location.location}
                        </Typography>
                      </Box>
                      <Chip
                        label={`${location.percentage.toFixed(1)}%`}
                        size="small"
                        color="success"
                      />
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={location.percentage}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'action.hover',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: 'success.main',
                        },
                      }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                      {location.count} candidates
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Language Distribution Section */}
      {languages.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Language Diversity
          </Typography>
          <Grid container spacing={2}>
            {languages.map((lang) => (
              <Grid item xs={12} sm={6} md={4} key={lang.language}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                  }}
                >
                  <CardContent sx={{ py: 1.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <LanguageIcon sx={{ mr: 1, fontSize: 'small', color: 'info.main' }} />
                        <Typography variant="subtitle2" fontWeight={600}>
                          {lang.language}
                        </Typography>
                      </Box>
                      <Chip
                        label={`${lang.percentage.toFixed(1)}%`}
                        size="small"
                        color="info"
                      />
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={lang.percentage}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'action.hover',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: 'info.main',
                        },
                      }}
                    />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                      {lang.count} resumes
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* No Data Message */}
      {total_analyzed === 0 && (
        <Paper elevation={2} sx={{ p: 4, textAlign: 'center' }}>
          <CheckIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Diversity Data Available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No demographic information has been collected yet. As candidates are processed,
            diversity metrics will be displayed here.
          </Typography>
        </Paper>
      )}
    </Stack>
  );
};

export default DiversityMetrics;
