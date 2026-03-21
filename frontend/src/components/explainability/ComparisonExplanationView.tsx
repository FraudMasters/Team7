import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  Stack,
  Button,
  Chip,
  LinearProgress,
  Avatar,
  Grid,
  Divider,
  Card,
  CardContent,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { explainability } from '@/api/explainability';
import type {
  DetailedCompareResponse,
  FactorComparison,
} from '@/api/explainability';

/**
 * ComparisonExplanationView Component Props
 */
interface ComparisonExplanationViewProps {
  /** First candidate resume ID */
  resumeAId: string;
  /** Second candidate resume ID */
  resumeBId: string;
  /** Vacancy ID for comparison context */
  vacancyId: string;
  /** Whether to show detailed factor breakdowns */
  showDetailedFactors?: boolean;
}

/**
 * Helper to get score color based on value
 */
const getScoreColor = (score: number): 'success' | 'warning' | 'error' => {
  const percentage = score * 100;
  if (percentage >= 70) return 'success';
  if (percentage >= 40) return 'warning';
  return 'error';
};

/**
 * Helper to get margin category color
 */
const getMarginColor = (
  category: 'significant' | 'moderate' | 'slight'
): 'success' | 'warning' | 'info' => {
  switch (category) {
    case 'significant':
      return 'success';
    case 'moderate':
      return 'warning';
    case 'slight':
      return 'info';
  }
};

/**
 * Helper to get winner icon
 */
const getWinnerIcon = (winner: 'A' | 'B' | 'tie') => {
  switch (winner) {
    case 'A':
    case 'B':
      return 'trophy';
    case 'tie':
      return 'minus';
  }
};

/**
 * ComparisonExplanationView Component
 *
 * Displays side-by-side comparison of two candidates with detailed explanations:
 * - Candidate profile cards with scores
 * - Score differential analysis
 * - Winner narrative (natural language explanation)
 * - Factor-by-factor breakdown table
 * - Strengths and weaknesses comparison
 * - Hiring recommendation
 *
 * @example
 * ```tsx
 * <ComparisonExplanationView
 *   resumeAId="resume-1"
 *   resumeBId="resume-2"
 *   vacancyId="vacancy-123"
 *   showDetailedFactors={true}
 * />
 * ```
 */
const ComparisonExplanationView: React.FC<ComparisonExplanationViewProps> = ({
  resumeAId,
  resumeBId,
  vacancyId,
  showDetailedFactors = true,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<DetailedCompareResponse | null>(null);

  /**
   * Fetch comparison data from backend
   */
  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await explainability.getDetailedComparison({
        resume_a_id: resumeAId,
        resume_b_id: resumeBId,
        vacancy_id: vacancyId,
        use_llm: true,
      });

      setData(response);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load comparison data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparison();
  }, [resumeAId, resumeBId, vacancyId]);

  /**
   * Render candidate info card
   */
  const renderCandidateCard = (
    candidate: DetailedCompareResponse['candidate_a_info'] | DetailedCompareResponse['candidate_b_info'],
    label: 'A' | 'B',
    isWinner: boolean
  ) => {
    const scoreColor = getScoreColor(candidate.rank_score);

    return (
      <Card
        sx={{
          height: '100%',
          border: isWinner ? 2 : 1,
          borderColor: isWinner ? 'success.main' : 'divider',
          position: 'relative',
        }}
      >
        {isWinner && (
          <Box
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
            }}
          >
            <Chip
              icon={<Icon name="trophy" size={16} />}
              label="Winner"
              color="success"
              size="small"
            />
          </Box>
        )}
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Avatar
              sx={{
                bgcolor: isWinner ? 'success.main' : 'grey.400',
                width: 48,
                height: 48,
                mr: 2,
              }}
            >
              {label}
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" fontWeight={600}>
                {candidate.candidate_name}
              </Typography>
              {candidate.rank_position && (
                <Typography variant="body2" color="text.secondary">
                  Rank #{candidate.rank_position}
                </Typography>
              )}
            </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Score */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="body2" color="text.secondary">
                Overall Score
              </Typography>
              <Chip
                label={`${(candidate.rank_score * 100).toFixed(1)}%`}
                size="small"
                color={scoreColor}
              />
            </Box>
            <LinearProgress
              variant="determinate"
              value={candidate.rank_score * 100}
              color={scoreColor}
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>

          {/* Confidence */}
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="body2" color="text.secondary">
                Confidence
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {(candidate.confidence * 100).toFixed(1)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={candidate.confidence * 100}
              sx={{ height: 6, borderRadius: 3 }}
            />
          </Box>
        </CardContent>
      </Card>
    );
  };

  /**
   * Render score differential section
   */
  const renderScoreDifferential = () => {
    if (!data) return null;

    const { score_differential } = data;
    const higherCandidate =
      score_differential.higher_candidate === 'A'
        ? data.candidate_a_info
        : data.candidate_b_info;

    return (
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Icon name="bar-chart" size={24} color="primary" />
          <Typography variant="h6" fontWeight={600} sx={{ ml: 1 }}>
            Score Differential
          </Typography>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Score Difference
              </Typography>
              <Typography variant="h4" fontWeight={700} color="primary.main">
                {(score_differential.score_difference * 100).toFixed(1)}%
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Margin Category
              </Typography>
              <Chip
                label={score_differential.margin_category.toUpperCase()}
                color={getMarginColor(score_differential.margin_category)}
                sx={{ fontWeight: 600 }}
              />
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Higher Candidate
              </Typography>
              <Typography variant="h5" fontWeight={700}>
                {higherCandidate.candidate_name}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    );
  };

  /**
   * Render winner narrative section
   */
  const renderWinnerNarrative = () => {
    if (!data) return null;

    return (
      <Paper
        sx={{
          p: 3,
          bgcolor: 'primary.main',
          color: 'primary.contrastText',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
          <Icon name="brain" size={28} />
          <Typography variant="h6" fontWeight={600} sx={{ ml: 1 }}>
            AI Explanation
          </Typography>
        </Box>
        <Typography variant="body1" sx={{ whiteSpace: 'pre-line', lineHeight: 1.7 }}>
          {data.winner_narrative}
        </Typography>

        {data.key_differences.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>
              Key Differences:
            </Typography>
            <Stack spacing={1}>
              {data.key_differences.map((diff, index) => (
                <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start' }}>
                  <Icon name="check-circle" size={16} sx={{ mr: 1, mt: 0.5 }} />
                  <Typography variant="body2">{diff}</Typography>
                </Box>
              ))}
            </Stack>
          </Box>
        )}
      </Paper>
    );
  };

  /**
   * Render factor-by-factor comparison table
   */
  const renderFactorComparison = () => {
    if (!data || !showDetailedFactors) return null;

    return (
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Icon name="list" size={24} color="primary" />
          <Typography variant="h6" fontWeight={600} sx={{ ml: 1 }}>
            Factor-by-Factor Breakdown
          </Typography>
        </Box>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>
                  <Typography variant="subtitle2" fontWeight={600}>
                    Factor
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="subtitle2" fontWeight={600}>
                    Candidate A
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="subtitle2" fontWeight={600}>
                    Candidate B
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="subtitle2" fontWeight={600}>
                    Winner
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="subtitle2" fontWeight={600}>
                    Explanation
                  </Typography>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.factor_by_factor_comparison.map((factor, index) => (
                <TableRow key={index} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={600}>
                      {factor.factor_name}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={`${(factor.candidate_a_score * 100).toFixed(0)}%`}
                      size="small"
                      color={factor.winner === 'A' ? 'success' : 'default'}
                      variant={factor.winner === 'A' ? 'filled' : 'outlined'}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={`${(factor.candidate_b_score * 100).toFixed(0)}%`}
                      size="small"
                      color={factor.winner === 'B' ? 'success' : 'default'}
                      variant={factor.winner === 'B' ? 'filled' : 'outlined'}
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title={factor.winner === 'tie' ? 'Tie' : `Candidate ${factor.winner}`}>
                      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                        <Icon
                          name={getWinnerIcon(factor.winner)}
                          size={20}
                          color={factor.winner === 'tie' ? 'inherit' : 'success'}
                        />
                      </Box>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {factor.explanation}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    );
  };

  /**
   * Render strengths and weaknesses comparison
   */
  const renderStrengthsWeaknesses = () => {
    if (!data) return null;

    const { strengths_weaknesses_table } = data;

    return (
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Icon name="target" size={24} color="primary" />
          <Typography variant="h6" fontWeight={600} sx={{ ml: 1 }}>
            Strengths & Weaknesses
          </Typography>
        </Box>

        <Grid container spacing={3}>
          {/* Candidate A */}
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              {data.candidate_a_info.candidate_name}
            </Typography>

            {/* Strengths */}
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Icon name="trending-up" size={16} color="success" />
                <Typography variant="subtitle2" fontWeight={600} sx={{ ml: 0.5 }}>
                  Strengths
                </Typography>
              </Box>
              <Stack spacing={0.5}>
                {strengths_weaknesses_table.candidate_a_strengths.map((strength, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start' }}>
                    <Icon name="check" size={14} color="success" sx={{ mr: 1, mt: 0.5 }} />
                    <Typography variant="body2">{strength}</Typography>
                  </Box>
                ))}
              </Stack>
            </Box>

            {/* Weaknesses */}
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Icon name="trending-down" size={16} color="error" />
                <Typography variant="subtitle2" fontWeight={600} sx={{ ml: 0.5 }}>
                  Areas for Improvement
                </Typography>
              </Box>
              <Stack spacing={0.5}>
                {strengths_weaknesses_table.candidate_a_weaknesses.map((weakness, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start' }}>
                    <Icon name="minus" size={14} color="error" sx={{ mr: 1, mt: 0.5 }} />
                    <Typography variant="body2">{weakness}</Typography>
                  </Box>
                ))}
              </Stack>
            </Box>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              {data.candidate_b_info.candidate_name}
            </Typography>

            {/* Strengths */}
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Icon name="trending-up" size={16} color="success" />
                <Typography variant="subtitle2" fontWeight={600} sx={{ ml: 0.5 }}>
                  Strengths
                </Typography>
              </Box>
              <Stack spacing={0.5}>
                {strengths_weaknesses_table.candidate_b_strengths.map((strength, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start' }}>
                    <Icon name="check" size={14} color="success" sx={{ mr: 1, mt: 0.5 }} />
                    <Typography variant="body2">{strength}</Typography>
                  </Box>
                ))}
              </Stack>
            </Box>

            {/* Weaknesses */}
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Icon name="trending-down" size={16} color="error" />
                <Typography variant="subtitle2" fontWeight={600} sx={{ ml: 0.5 }}>
                  Areas for Improvement
                </Typography>
              </Box>
              <Stack spacing={0.5}>
                {strengths_weaknesses_table.candidate_b_weaknesses.map((weakness, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start' }}>
                    <Icon name="minus" size={14} color="error" sx={{ mr: 1, mt: 0.5 }} />
                    <Typography variant="body2">{weakness}</Typography>
                  </Box>
                ))}
              </Stack>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    );
  };

  /**
   * Render recommendation section
   */
  const renderRecommendation = () => {
    if (!data) return null;

    return (
      <Paper
        sx={{
          p: 3,
          bgcolor: 'success.main',
          color: 'success.contrastText',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Icon name="thumbs-up" size={24} />
          <Typography variant="h6" fontWeight={600} sx={{ ml: 1 }}>
            Recommendation
          </Typography>
        </Box>
        <Typography variant="body1" sx={{ lineHeight: 1.7 }}>
          {data.recommendation}
        </Typography>
      </Paper>
    );
  };

  // Loading state
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 400,
          gap: 2,
        }}
      >
        <CircularProgress size={48} />
        <Typography variant="body1" color="text.secondary">
          Analyzing candidates...
        </Typography>
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={fetchComparison} startIcon={<Icon name="refresh-cw" />}>
          Retry
        </Button>
      </Box>
    );
  }

  // No data state
  if (!data) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">No comparison data available.</Alert>
      </Box>
    );
  }

  // Main render
  return (
    <Stack spacing={3} sx={{ p: 3 }}>
      {/* Header */}
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Candidate Comparison
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Side-by-side analysis with AI-powered explanations
        </Typography>
      </Box>

      {/* Candidate Cards */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          {renderCandidateCard(
            data.candidate_a_info,
            'A',
            data.score_differential.higher_candidate === 'A'
          )}
        </Grid>
        <Grid item xs={12} md={6}>
          {renderCandidateCard(
            data.candidate_b_info,
            'B',
            data.score_differential.higher_candidate === 'B'
          )}
        </Grid>
      </Grid>

      {/* Score Differential */}
      {renderScoreDifferential()}

      {/* Winner Narrative */}
      {renderWinnerNarrative()}

      {/* Factor-by-Factor Comparison */}
      {renderFactorComparison()}

      {/* Strengths & Weaknesses */}
      {renderStrengthsWeaknesses()}

      {/* Recommendation */}
      {renderRecommendation()}

      {/* Metadata */}
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, pt: 2 }}>
        <Chip
          icon={<Icon name="cpu" size={14} />}
          label={`${data.provider} - ${data.model}`}
          size="small"
          variant="outlined"
        />
        <Chip
          icon={<Icon name="clock" size={14} />}
          label={new Date(data.generated_at).toLocaleString()}
          size="small"
          variant="outlined"
        />
      </Box>
    </Stack>
  );
};

export default ComparisonExplanationView;
