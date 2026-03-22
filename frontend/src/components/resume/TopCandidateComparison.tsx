import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Stack,
  CircularProgress,
  Alert,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import { config } from '@/config';
import {
  TrendingUp as TrendingUpIcon,
  Person as PersonIcon,
  CheckCircle as CheckIcon,
  Cancel as CrossIcon,
  Star as StarIcon,
  Warning as WarningIcon,
  Lightbulb as LightbulbIcon,
  EmojiEvents as TrophyIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

/**
 * Individual candidate in comparison
 */
interface ComparisonCandidate {
  candidate_id: string;
  name: string;
  ranking_score: number;
  match_percentage: number;
  key_strengths: string[];
  skills: string[];
}

/**
 * Top candidate comparison data structure from backend
 */
interface TopCandidateComparisonData {
  vacancy_id: string;
  vacancy_title: string;
  current_resume_rank: number | null;
  current_resume_score: number | null;
  top_candidates: ComparisonCandidate[];
  total_candidates: number;
  skills_gap_vs_top: string[];
  competitive_insights: string | null;
}

/**
 * TopCandidateComparison Component Props
 */
interface TopCandidateComparisonProps {
  /** Resume ID to compare */
  resumeId: string;
  /** Vacancy ID for comparison context */
  vacancyId: string;
  /** API endpoint URL for fetching comparison data */
  apiUrl?: string;
  /** Number of top candidates to show */
  topN?: number;
}

/**
 * TopCandidateComparison Component
 *
 * Displays a comparison between the user's resume and top-performing candidates:
 * - Current ranking position and score
 * - Top performers leaderboard with key strengths
 * - Skills gap analysis showing missing skills
 * - Competitive insights and recommendations
 * - Visual indicators for performance positioning
 *
 * @example
 * ```tsx
 * <TopCandidateComparison
 *   resumeId="resume-123"
 *   vacancyId="vacancy-456"
 *   topN={5}
 * />
 * ```
 */
const TopCandidateComparison: React.FC<TopCandidateComparisonProps> = ({
  resumeId,
  vacancyId,
  apiUrl = `${config.api.url}/api/resumes/optimization`,
  topN = 5,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<TopCandidateComparisonData | null>(null);

  /**
   * Fetch top candidate comparison data from backend
   */
  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${apiUrl}/${resumeId}/top-candidate-comparison?vacancy_id=${vacancyId}&top_n=${topN}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch comparison: ${response.statusText}`);
      }

      const result: TopCandidateComparisonData = await response.json();
      setData(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load top candidate comparison data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (resumeId && vacancyId) {
      fetchComparison();
    }
  }, [resumeId, vacancyId, topN]);

  /**
   * Get rank display color and status
   */
  const getRankConfig = (rank: number | null, total: number) => {
    if (rank === null) {
      return {
        color: 'default' as const,
        label: 'Unranked',
        description: 'Not yet ranked for this vacancy',
      };
    }

    const percentile = ((total - rank) / total) * 100;

    if (percentile >= 90) {
      return {
        color: 'success' as const,
        label: 'Top 10%',
        description: 'Excellent positioning',
      };
    }
    if (percentile >= 75) {
      return {
        color: 'success' as const,
        label: 'Top 25%',
        description: 'Strong positioning',
      };
    }
    if (percentile >= 50) {
      return {
        color: 'warning' as const,
        label: 'Top 50%',
        description: 'Average positioning',
      };
    }
    return {
      color: 'error' as const,
      label: 'Below Average',
      description: 'Needs improvement',
    };
  };

  /**
   * Get score color based on value
   */
  const getScoreColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score >= 0.7) return 'success';
    if (score >= 0.4) return 'warning';
    return 'error';
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
          Analyzing your position vs top candidates...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Comparing against {topN} top performers for this role
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
          <button onClick={fetchComparison} style={{ cursor: 'pointer' }}>
            <RefreshIcon />
            <span style={{ marginLeft: 4 }}>Retry</span>
          </button>
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
  if (!data) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" fontWeight={600}>
          No Comparison Data
        </Typography>
        <Typography variant="body2">
          No top candidate comparison data available for this vacancy.
        </Typography>
      </Alert>
    );
  }

  const rankConfig = getRankConfig(data.current_resume_rank, data.total_candidates);
  const scoreColor = data.current_resume_score
    ? getScoreColor(data.current_resume_score)
    : 'default';

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <TrendingUpIcon sx={{ mr: 1, fontSize: 32, color: 'primary.main' }} />
          <Box sx={{ flex: 1 }}>
            <Typography variant="h5" fontWeight={600}>
              Competitive Analysis
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {data.vacancy_title}
            </Typography>
          </Box>
        </Box>

        {/* Current Position Summary */}
        <Box
          sx={{
            display: 'flex',
            gap: 2,
            flexWrap: 'wrap',
            p: 2,
            borderRadius: 2,
            bgcolor: `${rankConfig.color}.50`,
            border: `1px solid`,
            borderColor: `${rankConfig.color}.main`,
          }}
        >
          <Box sx={{ flex: 1, minWidth: 200 }}>
            <Typography variant="caption" color="text.secondary" display="block">
              Your Current Rank
            </Typography>
            <Typography variant="h4" fontWeight={700} color={`${rankConfig.color}.main`}>
              {data.current_resume_rank !== null
                ? `#${data.current_resume_rank}`
                : 'Unranked'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              out of {data.total_candidates} candidates
            </Typography>
          </Box>

          {data.current_resume_score !== null && (
            <Box sx={{ flex: 1, minWidth: 200 }}>
              <Typography variant="caption" color="text.secondary" display="block">
                Your Match Score
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
                <Typography variant="h4" fontWeight={700} color={`${scoreColor}.main`}>
                  {(data.current_resume_score * 100).toFixed(0)}
                </Typography>
                <Typography variant="h6" color="text.secondary">
                  / 100
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={data.current_resume_score * 100}
                color={scoreColor}
                sx={{ mt: 1, height: 8, borderRadius: 4 }}
              />
            </Box>
          )}

          <Box sx={{ flex: 1, minWidth: 200 }}>
            <Typography variant="caption" color="text.secondary" display="block">
              Competitive Position
            </Typography>
            <Chip
              label={rankConfig.label}
              color={rankConfig.color}
              size="medium"
              sx={{ mt: 1, fontWeight: 600 }}
            />
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
              {rankConfig.description}
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Top Performers Leaderboard */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <TrophyIcon sx={{ mr: 1, fontSize: 28, color: 'warning.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Top {topN} Performers
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Learn from the strengths of top-ranked candidates for this position
        </Typography>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 700 }}>Rank</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Candidate</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>
                  Match Score
                </TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Key Strengths</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>
                  Skills Count
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.top_candidates.map((candidate, index) => {
                const rank = index + 1;
                return (
                  <TableRow
                    key={candidate.candidate_id}
                    sx={{
                      '&:nth-of-type(odd)': { bgcolor: 'action.hover' },
                      bgcolor:
                        data.current_resume_rank === rank
                          ? 'primary.50'
                          : undefined,
                      borderLeft:
                        data.current_resume_rank === rank
                          ? '4px solid'
                          : undefined,
                      borderColor:
                        data.current_resume_rank === rank
                          ? 'primary.main'
                          : undefined,
                    }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {rank <= 3 && (
                          <StarIcon
                            sx={{
                              fontSize: 20,
                              color:
                                rank === 1
                                  ? 'warning.main'
                                  : rank === 2
                                    ? 'grey.400'
                                    : 'warning.light',
                            }}
                          />
                        )}
                        <Typography fontWeight={600}>#{rank}</Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <PersonIcon sx={{ fontSize: 20, color: 'text.secondary' }} />
                        <Typography variant="body2">
                          {data.current_resume_rank === rank ? 'You' : candidate.name}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={`${candidate.match_percentage}%`}
                        size="small"
                        color={
                          candidate.match_percentage >= 70
                            ? 'success'
                            : candidate.match_percentage >= 40
                              ? 'warning'
                              : 'error'
                        }
                        sx={{ fontWeight: 600, minWidth: 60 }}
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {candidate.key_strengths.slice(0, 3).map((strength, idx) => (
                          <Chip
                            key={idx}
                            label={strength}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem' }}
                          />
                        ))}
                        {candidate.key_strengths.length > 3 && (
                          <Chip
                            label={`+${candidate.key_strengths.length - 3}`}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem' }}
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Typography variant="body2" fontWeight={600}>
                        {candidate.skills.length}
                      </Typography>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Skills Gap Analysis */}
      {data.skills_gap_vs_top.length > 0 && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <WarningIcon sx={{ mr: 1, fontSize: 28, color: 'warning.main' }} />
            <Typography variant="h6" fontWeight={600}>
              Skills Gap vs Top Performers
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            These skills are common among top performers but missing from your resume
          </Typography>

          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {data.skills_gap_vs_top.map((skill, idx) => (
              <Tooltip
                key={idx}
                title="Add this skill to improve your ranking"
                arrow
              >
                <Chip
                  icon={<CrossIcon />}
                  label={skill}
                  color="warning"
                  variant="outlined"
                  sx={{
                    fontWeight: 500,
                    '&:hover': {
                      bgcolor: 'warning.50',
                      borderColor: 'warning.main',
                    },
                  }}
                />
              </Tooltip>
            ))}
          </Box>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              Consider highlighting or adding these {data.skills_gap_vs_top.length} skills to
              your resume to become more competitive with top performers.
            </Typography>
          </Alert>
        </Paper>
      )}

      {/* Competitive Insights */}
      {data.competitive_insights && (
        <Card elevation={1}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <LightbulbIcon sx={{ mr: 1, fontSize: 28, color: 'info.main' }} />
              <Typography variant="h6" fontWeight={600}>
                Competitive Insights
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>
              {data.competitive_insights}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Summary Stats */}
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        <Chip
          icon={<PersonIcon />}
          label={`${data.top_candidates.length} top candidates analyzed`}
          variant="outlined"
          size="small"
        />
        <Chip
          icon={<CheckIcon />}
          label={`${data.total_candidates} total candidates`}
          variant="outlined"
          size="small"
        />
        {data.skills_gap_vs_top.length > 0 && (
          <Chip
            icon={<WarningIcon />}
            label={`${data.skills_gap_vs_top.length} skills to improve`}
            variant="outlined"
            color="warning"
            size="small"
          />
        )}
      </Box>
    </Stack>
  );
};

export default TopCandidateComparison;
