import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Stack,
  Button,
  Divider,
  Card,
  CardContent,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as TrendingFlatIcon,
  Compare as CompareIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';

/**
 * Weight profile interface
 */
interface WeightProfile {
  id: string;
  name: string;
  organization_id: string;
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  is_preset: boolean;
  preset_type?: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Candidate score difference interface
 */
interface CandidateScoreDifference {
  resume_id: string;
  profile_a_score: number;
  profile_b_score: number;
  score_difference: number;
  rank_change: number;
}

/**
 * Comparison response from backend
 */
interface WeightComparisonData {
  vacancy_id: string;
  profile_a: WeightProfile;
  profile_b: WeightProfile;
  differences: CandidateScoreDifference[];
  processing_time?: number;
}

/**
 * MatchingWeightsComparison Component Props
 */
interface MatchingWeightsComparisonProps {
  /** Profile A ID to compare */
  profileAId: string;
  /** Profile B ID to compare */
  profileBId: string;
  /** Vacancy ID for the comparison */
  vacancyId: string;
  /** API endpoint URL for fetching comparison results */
  apiUrl?: string;
}

/**
 * MatchingWeightsComparison Component
 *
 * Displays side-by-side comparison of two weight profiles (A/B testing) with:
 * - Weight distribution for each profile (Keyword, TF-IDF, Vector)
 * - Candidate score differences between profiles
 * - Rank change indicators (up/down/no change)
 * - Visual highlighting of score differences
 * - Statistical summary of comparison
 *
 * @example
 * ```tsx
 * <MatchingWeightsComparison
 *   profileAId="profile-1"
 *   profileBId="profile-2"
 *   vacancyId="vacancy-123"
 * />
 * ```
 */
const MatchingWeightsComparison: React.FC<MatchingWeightsComparisonProps> = ({
  profileAId,
  profileBId,
  vacancyId,
  apiUrl = 'http://localhost:8000/api/matching-weights',
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<WeightComparisonData | null>(null);

  /**
   * Fetch comparison data from backend
   */
  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/compare`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          profile_a_id: profileAId,
          profile_b_id: profileBId,
          vacancy_id: vacancyId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch comparison: ${response.statusText}`);
      }

      const result: WeightComparisonData = await response.json();
      setData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load comparison data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (profileAId && profileBId && vacancyId) {
      if (profileAId === profileBId) {
        setError('Profile A and Profile B must be different');
        setLoading(false);
      } else {
        fetchComparison();
      }
    } else {
      setError('Profile A, Profile B, and Vacancy ID are required');
      setLoading(false);
    }
  }, [profileAId, profileBId, vacancyId]);

  /**
   * Get rank change icon and color
   */
  const getRankChangeConfig = (rankChange: number) => {
    if (rankChange > 0) {
      return {
        icon: <TrendingUpIcon />,
        label: `+${rankChange}`,
        color: 'success' as const,
        bgColor: 'success.50',
        borderColor: 'success.main',
      };
    }
    if (rankChange < 0) {
      return {
        icon: <TrendingDownIcon />,
        label: `${rankChange}`,
        color: 'error' as const,
        bgColor: 'error.50',
        borderColor: 'error.main',
      };
    }
    return {
      icon: <TrendingFlatIcon />,
      label: '0',
      color: 'default' as const,
      bgColor: 'grey.50',
      borderColor: 'grey.300',
    };
  };

  /**
   * Get score difference color
   */
  const getScoreDifferenceColor = (difference: number) => {
    if (difference > 5) {
      return 'success.main';
    }
    if (difference < -5) {
      return 'error.main';
    }
    return 'text.primary';
  };

  /**
   * Render weight distribution chips
   */
  const renderWeightDistribution = (profile: WeightProfile) => {
    return (
      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
        <Chip
          label={`Keyword: ${(profile.keyword_weight * 100).toFixed(0)}%`}
          size="small"
          color="primary"
          variant="outlined"
        />
        <Chip
          label={`TF-IDF: ${(profile.tfidf_weight * 100).toFixed(0)}%`}
          size="small"
          color="secondary"
          variant="outlined"
        />
        <Chip
          label={`Vector: ${(profile.vector_weight * 100).toFixed(0)}%`}
          size="small"
          color="info"
          variant="outlined"
        />
      </Stack>
    );
  };

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
          Comparing weight profiles...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Analyzing candidate score differences between profiles
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
          <Button color="inherit" onClick={fetchComparison} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <Typography variant="subtitle1" fontWeight={600}>
          Comparison Failed
        </Typography>
        <Typography variant="body2">{error}</Typography>
      </Alert>
    );
  }

  /**
   * Render no data state
   */
  if (!data || !data.differences || data.differences.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" fontWeight={600}>
          No Comparison Data
        </Typography>
        <Typography variant="body2">
          No comparison data found for the selected profiles and vacancy.
        </Typography>
      </Alert>
    );
  }

  // Calculate statistics
  const avgScoreA =
    data.differences.reduce((sum, d) => sum + d.profile_a_score, 0) / data.differences.length;
  const avgScoreB =
    data.differences.reduce((sum, d) => sum + d.profile_b_score, 0) / data.differences.length;
  const avgDifference =
    data.differences.reduce((sum, d) => sum + d.score_difference, 0) / data.differences.length;
  const significantChanges = data.differences.filter((d) => Math.abs(d.rank_change) > 0).length;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CompareIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Weight Profile Comparison
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Vacancy: <strong>{vacancyId}</strong>
              </Typography>
            </Box>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchComparison} size="small">
            Refresh
          </Button>
        </Box>

        {/* Profile Cards Side by Side */}
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} md={6}>
            <Card
              variant="outlined"
              sx={{
                borderColor: 'primary.main',
                borderWidth: 2,
                bgcolor: 'primary.50',
              }}
            >
              <CardContent>
                <Typography variant="subtitle1" fontWeight={600} color="primary.main">
                  Profile A
                </Typography>
                <Typography variant="h6" gutterBottom>
                  {data.profile_a.name}
                </Typography>
                {renderWeightDistribution(data.profile_a)}
                {data.profile_a.is_preset && (
                  <Chip
                    label={`${data.profile_a.preset_type} preset`}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                )}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card
              variant="outlined"
              sx={{
                borderColor: 'secondary.main',
                borderWidth: 2,
                bgcolor: 'secondary.50',
              }}
            >
              <CardContent>
                <Typography variant="subtitle1" fontWeight={600} color="secondary.main">
                  Profile B
                </Typography>
                <Typography variant="h6" gutterBottom>
                  {data.profile_b.name}
                </Typography>
                {renderWeightDistribution(data.profile_b)}
                {data.profile_b.is_preset && (
                  <Chip
                    label={`${data.profile_b.preset_type} preset`}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Statistical Summary */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <SpeedIcon sx={{ mr: 1, fontSize: 24, color: 'info.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Statistical Summary
          </Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={6} md={3}>
            <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'primary.50', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Avg Score (A)
              </Typography>
              <Typography variant="h5" fontWeight={700} color="primary.main">
                {avgScoreA.toFixed(1)}%
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} md={3}>
            <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'secondary.50', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Avg Score (B)
              </Typography>
              <Typography variant="h5" fontWeight={700} color="secondary.main">
                {avgScoreB.toFixed(1)}%
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} md={3}>
            <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.100', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Avg Difference
              </Typography>
              <Typography variant="h5" fontWeight={700} color="text.primary">
                {avgDifference > 0 ? '+' : ''}
                {avgDifference.toFixed(1)}%
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} md={3}>
            <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'info.50', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Rank Changes
              </Typography>
              <Typography variant="h5" fontWeight={700} color="info.main">
                {significantChanges} / {data.differences.length}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Score Differences Table */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Candidate Score Differences
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Showing how candidate scores change between Profile A and Profile B
        </Typography>

        <TableContainer sx={{ maxHeight: 600, overflow: 'auto' }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell
                  sx={{
                    fontWeight: 700,
                    bgcolor: 'grey.100',
                    minWidth: 150,
                    position: 'sticky',
                    left: 0,
                    zIndex: 3,
                  }}
                >
                  Resume ID
                </TableCell>
                <TableCell
                  align="center"
                  sx={{
                    fontWeight: 700,
                    bgcolor: 'primary.50',
                    minWidth: 120,
                  }}
                >
                  Profile A Score
                </TableCell>
                <TableCell
                  align="center"
                  sx={{
                    fontWeight: 700,
                    bgcolor: 'secondary.50',
                    minWidth: 120,
                  }}
                >
                  Profile B Score
                </TableCell>
                <TableCell
                  align="center"
                  sx={{
                    fontWeight: 700,
                    bgcolor: 'grey.100',
                    minWidth: 120,
                  }}
                >
                  Difference
                </TableCell>
                <TableCell
                  align="center"
                  sx={{
                    fontWeight: 700,
                    bgcolor: 'grey.100',
                    minWidth: 120,
                  }}
                >
                  Rank Change
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.differences.map((difference) => {
                const rankConfig = getRankChangeConfig(difference.rank_change);
                return (
                  <TableRow
                    key={difference.resume_id}
                    sx={{ '&:nth-of-type(odd)': { bgcolor: 'action.hover' } }}
                  >
                    <TableCell
                      sx={{
                        fontWeight: 600,
                        position: 'sticky',
                        left: 0,
                        bgcolor: 'background.paper',
                        zIndex: 2,
                      }}
                    >
                      {difference.resume_id}
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={`${difference.profile_a_score.toFixed(1)}%`}
                        size="small"
                        color="primary"
                        variant="outlined"
                        sx={{ fontWeight: 600 }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={`${difference.profile_b_score.toFixed(1)}%`}
                        size="small"
                        color="secondary"
                        variant="outlined"
                        sx={{ fontWeight: 600 }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        color={getScoreDifferenceColor(difference.score_difference)}
                      >
                        {difference.score_difference > 0 ? '+' : ''}
                        {difference.score_difference.toFixed(1)}%
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 0.5,
                          bgcolor: rankConfig.bgColor,
                          px: 1,
                          py: 0.5,
                          borderRadius: 1,
                          border: `1px solid ${rankConfig.borderColor}`,
                        }}
                      >
                        <Box sx={{ color: `${rankConfig.color}.main` }}>
                          {rankConfig.icon}
                        </Box>
                        <Typography
                          variant="body2"
                          fontWeight={600}
                          color={`${rankConfig.color}.main`}
                        >
                          {rankConfig.label}
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Processing Time */}
      {data.processing_time && (
        <Typography variant="caption" color="text.secondary" align="center" display="block">
          Comparison completed in {data.processing_time.toFixed(2)} seconds
        </Typography>
      )}
    </Stack>
  );
};

export default MatchingWeightsComparison;
