import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
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
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';

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
  apiUrl = '/api/analytics/skill-demand',
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

      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (limit) params.limit = limit.toString();

      const response = await axios.get<SkillDemandResponse>(apiUrl, { params });
      setSkillData(response.data);
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
   * Export skill demand data as CSV
   */
  const exportAsCSV = useCallback(() => {
    if (!skillData || !skillData.skills || skillData.skills.length === 0) {
      return;
    }

    const headers = [
      'Rank',
      'Skill Name',
      'Demand Count',
      'Demand Percentage (%)',
      'Trend Percentage (%)',
    ];

    const rows = skillData.skills.map((skill, index) => [
      index + 1,
      `"${skill.skill_name}"`,
      skill.demand_count,
      (skill.demand_percentage * 100).toFixed(1),
      `${skill.trend_percentage > 0 ? '+' : ''}${(skill.trend_percentage * 100).toFixed(1)}`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `skill-demand-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [skillData]);

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        css={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '64px 0',
        }}
      >
        <CircularProgress size={60} css={{ marginBottom: '24px' }} />
        <Typography variant="h6" color="secondary">
          Loading skill demand analytics...
        </Typography>
        <Typography variant="body2" color="secondary" css={{ marginTop: '8px' }}>
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
          <Button color="inherit" onClick={fetchSkillDemand} startIcon={<Icon name="refresh" />}>
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
      <Paper elevation={2} css={{ padding: '24px' }}>
        <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <Box css={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Icon name="work" size={32} color="$primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Skill Demand Analytics
              </Typography>
              <Typography variant="body2" color="secondary">
                Most requested skills from job postings
              </Typography>
            </Box>
          </Box>
          <Box css={{ display: 'flex', gap: '8px' }}>
            <Button
              variant="outlined"
              startIcon={<Icon name="download" />}
              onClick={exportAsCSV}
              size="small"
              disabled={!skillData || skillData.skills.length === 0}
            >
              Export CSV
            </Button>
            <Button variant="outlined" startIcon={<Icon name="refresh" />} onClick={fetchSkillDemand} size="small">
              Refresh
            </Button>
          </Box>
        </Box>

        {/* Summary Stats */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent css={{ textAlign: 'center', padding: '8px' }}>
                <Typography variant="h4" color="$primary" fontWeight={700}>
                  {skillData.skills.length}
                </Typography>
                <Typography variant="caption" color="secondary">
                  Trending Skills
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent css={{ textAlign: 'center', padding: '8px' }}>
                <Typography variant="h4" color="$success" fontWeight={700}>
                  {skillData.skills[0]?.demand_count || 0}
                </Typography>
                <Typography variant="caption" color="secondary">
                  Top Skill Count
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent css={{ textAlign: 'center', padding: '8px' }}>
                <Typography variant="h4" fontWeight={700}>
                  {((skillData.skills[0]?.demand_percentage || 0) * 100).toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="secondary">
                  Highest Demand
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent css={{ textAlign: 'center', padding: '8px' }}>
                <Typography variant="h4" color="$info" fontWeight={700}>
                  {skillData.total_postings_analyzed.toLocaleString()}
                </Typography>
                <Typography variant="caption" color="secondary">
                  Postings Analyzed
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Skills Chart */}
      <Paper elevation={1} css={{ padding: '24px' }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Trending Skills by Demand
        </Typography>

        <Stack spacing={2} css={{ marginTop: '24px' }}>
          {skillData.skills.map((skill, index) => (
            <Card
              key={skill.skill_name}
              variant="outlined"
              css={{
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateX(4px)',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                },
              }}
            >
              <CardContent css={{ padding: '16px' }}>
                <Grid container spacing={2} alignItems="center">
                  {/* Rank and Skill Name */}
                  <Grid item xs={12} sm={4}>
                    <Box css={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Chip
                        label={`#${index + 1}`}
                        size="small"
                        color={index < 3 ? 'primary' : 'default'}
                        css={{
                          fontWeight: 700,
                          minWidth: '45px',
                          backgroundColor: index < 3 ? '$primary' : '$disabledBackground',
                        }}
                      />
                      <Typography variant="subtitle1" fontWeight={600}>
                        {skill.skill_name}
                      </Typography>
                    </Box>
                  </Grid>

                  {/* Demand Bar Chart */}
                  <Grid item xs={12} sm={5}>
                    <Box css={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Box css={{ flexGrow: 1 }}>
                        <Box css={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <Typography variant="caption" color="secondary">
                            Demand
                          </Typography>
                          <Typography variant="body2" fontWeight={600}>
                            {skill.demand_count.toLocaleString()} ({(skill.demand_percentage * 100).toFixed(1)}%)
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={skill.demand_percentage * 100}
                          css={{
                            height: '8px',
                            borderRadius: '4px',
                            backgroundColor: '$hover',
                            '& .MuiLinearProgress-bar': {
                              backgroundColor: index < 3 ? '$primary' : '$primaryLight',
                            },
                          }}
                        />
                      </Box>
                    </Box>
                  </Grid>

                  {/* Trend Indicator */}
                  <Grid item xs={12} sm={3}>
                    <Box
                      css={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        gap: '4px',
                      }}
                    >
                      {skill.trend_percentage > 0 ? (
                        <Icon name="trending-up" size={16} color="$success" />
                      ) : skill.trend_percentage < 0 ? (
                        <Icon name="trending-down" size={16} color="$error" />
                      ) : null}
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        color={
                          skill.trend_percentage > 0 ? '$success' : skill.trend_percentage < 0 ? '$error' : '$secondary'
                        }
                      >
                        {skill.trend_percentage > 0 ? '+' : ''}{(skill.trend_percentage * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="caption" color="secondary">
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
          <Box css={{ marginTop: '16px', textAlign: 'center' }}>
            <Typography variant="caption" color="secondary">
              Showing top {skillData.skills.length} skills of {skillData.total_postings_analyzed.toLocaleString()} job postings analyzed
            </Typography>
          </Box>
        )}
      </Paper>
    </Stack>
  );
};

export default SkillDemandChart;
