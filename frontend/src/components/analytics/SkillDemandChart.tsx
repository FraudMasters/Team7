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
  TrendingDown as TrendingDownIcon,
  Work as SkillIcon,
} from '@mui/icons-material';

/**
 * Skill demand item interface from backend
 */
interface SkillDemandItem {
  skill_name: string;
  demand_count: number;
  demand_percentage: number;
  trend_percentage: number;
}

/**
 * Skill demand response from backend
 */
interface SkillDemandResponse {
  skills: SkillDemandItem[];
  total_postings_analyzed: number;
}

/**
 * SkillDemandChart Component Props
 */
interface SkillDemandChartProps {
  /** API endpoint URL for skill demand analytics */
  apiUrl?: string;
  /** Optional date range filter */
  startDate?: string;
  /** Optional date range filter */
  endDate?: string;
  /** Maximum number of skills to display */
  limit?: number;
}

/**
 * SkillDemandChart Component
 *
 * Displays trending skills with demand metrics including:
 * - Skill name with demand count
 * - Demand percentage as a horizontal bar chart
 * - Trend percentage with up/down indicators
 * - Total job postings analyzed
 *
 * @example
 * ```tsx
 * <SkillDemandChart />
 * ```
 *
 * @example
 * ```tsx
 * <SkillDemandChart startDate="2024-01-01" endDate="2024-12-31" limit={15} />
 * ```
 */
const SkillDemandChart: React.FC<SkillDemandChartProps> = ({
  apiUrl = 'http://localhost:8000/api/analytics/skill-demand',
  startDate,
  endDate,
  limit = 20,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [skillData, setSkillData] = useState<SkillDemandResponse | null>(null);

  /**
   * Fetch skill demand data from backend
   */
  const fetchSkillDemand = async () => {
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
      if (limit) {
        url.searchParams.append('limit', limit.toString());
      }

      const response = await fetch(url.toString());

      if (!response.ok) {
        throw new Error(`Failed to fetch skill demand: ${response.statusText}`);
      }

      const result: SkillDemandResponse = await response.json();
      setSkillData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load skill demand data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSkillDemand();
  }, [apiUrl, startDate, endDate, limit]);

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
          Loading skill demand analytics...
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
          <Button color="inherit" onClick={fetchSkillDemand} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Skill Demand</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (!skillData || skillData.skills.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>No Skill Demand Data</AlertTitle>
        No skill demand data found. Start creating job vacancies with required skills to populate this chart.
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SkillIcon fontSize="large" color="primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Skill Demand Analytics
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Most requested skills from job postings
              </Typography>
            </Box>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchSkillDemand} size="small">
            Refresh
          </Button>
        </Box>

        {/* Summary Stats */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {skillData.skills.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Trending Skills
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {skillData.skills[0]?.demand_count || 0}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Top Skill Count
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" fontWeight={700}>
                  {(skillData.skills[0]?.demand_percentage * 100).toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Highest Demand
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {skillData.total_postings_analyzed.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Postings Analyzed
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Skills Chart */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Trending Skills by Demand
        </Typography>

        <Stack spacing={2} sx={{ mt: 3 }}>
          {skillData.skills.map((skill, index) => (
            <Card
              key={skill.skill_name}
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
                  {/* Rank and Skill Name */}
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
                  <Typography variant="subtitle1" fontWeight={600}>
                    {skill.skill_name}
                  </Typography>
                </Box>
              </Grid>

              {/* Demand Bar Chart */}
              <Grid item xs={12} sm={5}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Demand
                      </Typography>
                      <Typography variant="body2" fontWeight={600}>
                        {skill.demand_count.toLocaleString()} ({(skill.demand_percentage * 100).toFixed(1)}%)
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={skill.demand_percentage * 100}
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

              {/* Trend Indicator */}
              <Grid item xs={12} sm={3}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-end',
                    gap: 0.5,
                  }}
                >
                  {skill.trend_percentage > 0 ? (
                    <TrendingUpIcon fontSize="small" color="success" />
                  ) : skill.trend_percentage < 0 ? (
                    <TrendingDownIcon fontSize="small" color="error" />
                  ) : null}
                  <Typography
                    variant="body2"
                    fontWeight={600}
                    color={
                      skill.trend_percentage > 0 ? 'success.main' : skill.trend_percentage < 0 ? 'error.main' : 'text.secondary'
                    }
                  >
                    {skill.trend_percentage > 0 ? '+' : ''}{(skill.trend_percentage * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    trend
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      ))}
        </Stack>

        {skillData.skills.length >= limit && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Showing top {skillData.skills.length} skills of {skillData.total_postings_analyzed.toLocaleString()} job postings analyzed
            </Typography>
          </Box>
        )}
      </Paper>
    </Stack>
  );
};

export default SkillDemandChart;
