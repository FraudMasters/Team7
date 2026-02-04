import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Stack,
  LinearProgress,
  Chip,
  Grid,
  Card,
  CardContent,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';

interface MatchScoreBreakdownProps {
  keywordScore: number;
  tfidfScore: number;
  vectorScore: number;
  overallScore?: number;
}

interface ScoreBreakdown {
  title: string;
  score: number;
  weight: number;
  iconName: string;
  color: 'primary' | 'secondary' | 'info';
}

const MatchScoreBreakdown: React.FC<MatchScoreBreakdownProps> = ({
  keywordScore,
  tfidfScore,
  vectorScore,
  overallScore,
}) => {
  const getScoreValue = (score: number) => Math.round(score * 100);
  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'success';
    if (score >= 0.4) return 'warning';
    return 'error';
  };

  // Calculate weighted contribution
  const keywordWeight = 0.5;
  const tfidfWeight = 0.3;
  const vectorWeight = 0.2;

  const keywordContribution = keywordScore * keywordWeight;
  const tfidfContribution = tfidfScore * tfidfWeight;
  const vectorContribution = vectorScore * vectorWeight;

  const calculatedOverall = keywordContribution + tfidfContribution + vectorContribution;

  const scoreBreakdowns: ScoreBreakdown[] = [
    {
      title: 'Keyword Matching',
      score: keywordScore,
      weight: keywordWeight,
      iconName: 'key',
      color: 'primary',
    },
    {
      title: 'TF-IDF Weighting',
      score: tfidfScore,
      weight: tfidfWeight,
      iconName: 'tune',
      color: 'secondary',
    },
    {
      title: 'Vector Similarity',
      score: vectorScore,
      weight: vectorWeight,
      iconName: 'brain',
      color: 'info',
    },
  ];

  const ScoreBreakdownRow: React.FC<{
    breakdown: ScoreBreakdown;
    contribution: number;
  }> = ({ breakdown, contribution }) => (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent>
        <Grid container spacing={2} alignItems="center">
          {/* Icon and Title */}
          <Grid item xs={12} sm={3}>
            <Stack spacing={1} direction="row" alignItems="center">
              <Box
                sx={{
                  p: 1,
                  borderRadius: 1,
                  bgcolor: `${breakdown.color}.main`,
                  color: `${breakdown.color}.contrastText`,
                }}
              >
                <Icon name={breakdown.iconName} />
              </Box>
              <Box>
                <Typography variant="subtitle2" fontWeight={600}>
                  {breakdown.title}
                </Typography>
                <Chip
                  label={`${getScoreValue(breakdown.weight)}% weight`}
                  size="small"
                  color={breakdown.color}
                  variant="outlined"
                />
              </Box>
            </Stack>
          </Grid>

          {/* Score Bar */}
          <Grid item xs={12} sm={6}>
            <Stack spacing={1}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  Raw Score
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {getScoreValue(breakdown.score)}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={getScoreValue(breakdown.score)}
                color={getScoreColor(breakdown.score)}
                sx={{ height: 10, borderRadius: 5 }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" color="text.secondary">
                  Contribution to overall
                </Typography>
                <Typography variant="caption" fontWeight={600} color={breakdown.color}>
                  +{getScoreValue(contribution)}%
                </Typography>
              </Box>
            </Stack>
          </Grid>

          {/* Weight Visualization */}
          <Grid item xs={12} sm={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" fontWeight={700} color={breakdown.color}>
                {getScoreValue(breakdown.weight)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Algorithm Weight
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );

  return (
    <Stack spacing={3}>
      {/* Header */}
      <Box>
        <Typography variant="h5" fontWeight={700} gutterBottom>
          Score Breakdown
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Detailed view of how each algorithm contributes to the overall match score
        </Typography>
      </Box>

      {/* Overall Score Summary */}
      <Paper
        elevation={2}
        sx={{
          p: 3,
          bgcolor: 'background.default',
          border: '2px solid',
          borderColor: 'divider',
        }}
      >
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Overall Match Score
            </Typography>
            <Typography variant="h3" fontWeight={700}>
              {getScoreValue(overallScore !== undefined ? overallScore : calculatedOverall)}%
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Stack spacing={1}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="caption" color="text.secondary">
                  Weighted Formula
                </Typography>
              </Box>
              <Typography variant="body2" fontWeight={500}>
                {getScoreValue(keywordContribution)}% + {getScoreValue(tfidfContribution)}% +{' '}
                {getScoreValue(vectorContribution)}% ={' '}
                {getScoreValue(overallScore !== undefined ? overallScore : calculatedOverall)}%
              </Typography>
            </Stack>
          </Grid>
        </Grid>
      </Paper>

      {/* Individual Algorithm Breakdowns */}
      <Stack spacing={2}>
        <ScoreBreakdownRow
          breakdown={scoreBreakdowns[0]}
          contribution={keywordContribution}
        />
        <ScoreBreakdownRow
          breakdown={scoreBreakdowns[1]}
          contribution={tfidfContribution}
        />
        <ScoreBreakdownRow
          breakdown={scoreBreakdowns[2]}
          contribution={vectorContribution}
        />
      </Stack>

      {/* Formula Explanation */}
      <Paper elevation={1} sx={{ p: 2, bgcolor: 'action.hover' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>Formula:</strong> Overall = (Keyword × 0.5) + (TF-IDF × 0.3) + (Vector × 0.2)
          {' • '}
          <strong>Weights:</strong> Keyword 50%, TF-IDF 30%, Vector 20%
        </Typography>
      </Paper>
    </Stack>
  );
};

export default MatchScoreBreakdown;
