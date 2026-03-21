import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
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
  Chip,
  Avatar,
  Tooltip,
} from '@mui/material';
import { config } from '@/config';
import {
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as NoChangeIcon,
  EmojiEvents as TrophyIcon,
} from '@mui/icons-material';

/**
 * Individual candidate ranking
 */
interface CandidateRanking {
  resume_id: string;
  filename: string;
  overall_score: number;
  rank: number;
}

/**
 * Ranking comparison data from backend
 */
interface RankingComparisonData {
  vacancy_id: string;
  before: CandidateRanking[];
  after: CandidateRanking[];
}

/**
 * RankingWeightImpactPreview Component Props
 */
interface RankingWeightImpactPreviewProps {
  /** Vacancy ID for the preview */
  vacancyId: string;
  /** Current/before weights (0-1 scale) */
  beforeWeights: Record<string, number>;
  /** New/after weights (0-1 scale) */
  afterWeights: Record<string, number>;
  /** API endpoint URL for fetching ranking data */
  apiUrl?: string;
}

/**
 * Candidate with rank change information
 */
interface CandidateWithChange extends CandidateRanking {
  rankChange: number; // positive = moved up, negative = moved down
  previousRank: number;
  scoreChange: number;
}

/**
 * Helper to get rank change color
 */
const getRankChangeColor = (change: number): 'success' | 'error' | 'default' => {
  if (change > 0) return 'success'; // Moved up
  if (change < 0) return 'error'; // Moved down
  return 'default'; // No change
};

/**
 * Helper to get rank change icon
 */
const getRankChangeIcon = (change: number) => {
  if (change > 0) return <TrendingUpIcon fontSize="small" />;
  if (change < 0) return <TrendingDownIcon fontSize="small" />;
  return <NoChangeIcon fontSize="small" />;
};

/**
 * RankingWeightImpactPreview Component
 *
 * Displays before/after candidate rankings when weights change:
 * - Shows current and new rankings side-by-side
 * - Highlights candidates that moved up/down
 * - Displays rank change arrows and magnitude
 * - Visual indicators for significant changes
 *
 * @example
 * ```tsx
 * <RankingWeightImpactPreview
 *   vacancyId="vacancy-123"
 *   beforeWeights={currentWeights}
 *   afterWeights={newWeights}
 * />
 * ```
 */
const RankingWeightImpactPreview: React.FC<RankingWeightImpactPreviewProps> = ({
  vacancyId,
  beforeWeights,
  afterWeights,
  apiUrl = `${config.api.url}/api/ranking-weights`,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RankingComparisonData | null>(null);
  const [candidatesWithChanges, setCandidatesWithChanges] = useState<CandidateWithChange[]>([]);

  /**
   * Fetch ranking comparison data from backend
   */
  const fetchRankingPreview = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/preview-impact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          vacancy_id: vacancyId,
          before_weights: beforeWeights,
          after_weights: afterWeights,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch ranking preview: ${response.statusText}`);
      }

      const result: RankingComparisonData = await response.json();
      setData(result);

      // Calculate rank changes
      const changes = calculateRankChanges(result.before, result.after);
      setCandidatesWithChanges(changes);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load ranking preview data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Calculate rank changes for each candidate
   */
  const calculateRankChanges = (
    before: CandidateRanking[],
    after: CandidateRanking[]
  ): CandidateWithChange[] => {
    const afterMap = new Map(after.map((c) => [c.resume_id, c]));
    const beforeMap = new Map(before.map((c) => [c.resume_id, c]));

    const changes: CandidateWithChange[] = [];

    after.forEach((afterCandidate) => {
      const beforeCandidate = beforeMap.get(afterCandidate.resume_id);
      if (beforeCandidate) {
        changes.push({
          ...afterCandidate,
          previousRank: beforeCandidate.rank,
          rankChange: beforeCandidate.rank - afterCandidate.rank, // Higher rank = moved up
          scoreChange: afterCandidate.overall_score - beforeCandidate.overall_score,
        });
      }
    });

    // Sort by new rank
    return changes.sort((a, b) => a.rank - b.rank);
  };

  useEffect(() => {
    if (vacancyId && beforeWeights && afterWeights) {
      fetchRankingPreview();
    } else {
      setError('Vacancy ID and weights are required');
      setLoading(false);
    }
  }, [vacancyId, beforeWeights, afterWeights]);

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
          Calculating ranking impact...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Comparing before and after rankings
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
        sx={{ my: 3 }}
        action={
          <Button color="inherit" size="small" onClick={fetchRankingPreview}>
            Retry
          </Button>
        }
      >
        <Typography variant="body2" fontWeight="medium">
          {error}
        </Typography>
      </Alert>
    );
  }

  /**
   * Render empty state
   */
  if (!data || candidatesWithChanges.length === 0) {
    return (
      <Alert severity="info" sx={{ my: 3 }}>
        <Typography variant="body2">
          No ranking data available. Please select a vacancy with candidates.
        </Typography>
      </Alert>
    );
  }

  /**
   * Calculate summary statistics
   */
  const movedUp = candidatesWithChanges.filter((c) => c.rankChange > 0).length;
  const movedDown = candidatesWithChanges.filter((c) => c.rankChange < 0).length;
  const noChange = candidatesWithChanges.filter((c) => c.rankChange === 0).length;
  const biggestGainer = candidatesWithChanges.reduce(
    (max, c) => (c.rankChange > max.rankChange ? c : max),
    candidatesWithChanges[0]
  );
  const biggestLoser = candidatesWithChanges.reduce(
    (min, c) => (c.rankChange < min.rankChange ? c : min),
    candidatesWithChanges[0]
  );

  return (
    <Paper sx={{ p: 3 }}>
      <Stack spacing={3}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" component="h2">
            Ranking Impact Preview
          </Typography>
          <Button
            size="small"
            startIcon={<RefreshIcon />}
            onClick={fetchRankingPreview}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>

        {/* Summary Cards */}
        <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap' }}>
          <Chip
            icon={<TrendingUpIcon />}
            label={`${movedUp} moved up`}
            color="success"
            variant="outlined"
          />
          <Chip
            icon={<TrendingDownIcon />}
            label={`${movedDown} moved down`}
            color="error"
            variant="outlined"
          />
          <Chip
            icon={<NoChangeIcon />}
            label={`${noChange} unchanged`}
            color="default"
            variant="outlined"
          />
        </Stack>

        {/* Notable Changes */}
        {(biggestGainer.rankChange > 0 || biggestLoser.rankChange < 0) && (
          <Box sx={{ bgcolor: 'background.default', p: 2, borderRadius: 1 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Notable Changes
            </Typography>
            <Stack spacing={1}>
              {biggestGainer.rankChange > 0 && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TrendingUpIcon fontSize="small" color="success" />
                  <Typography variant="body2">
                    <strong>{biggestGainer.filename}</strong> moved up {biggestGainer.rankChange}{' '}
                    position(s) (#{biggestGainer.previousRank} → #{biggestGainer.rank})
                  </Typography>
                </Box>
              )}
              {biggestLoser.rankChange < 0 && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TrendingDownIcon fontSize="small" color="error" />
                  <Typography variant="body2">
                    <strong>{biggestLoser.filename}</strong> moved down{' '}
                    {Math.abs(biggestLoser.rankChange)} position(s) (#{biggestLoser.previousRank}{' '}
                    → #{biggestLoser.rank})
                  </Typography>
                </Box>
              )}
            </Stack>
          </Box>
        )}

        {/* Comparison Table */}
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell width="60">New Rank</TableCell>
                <TableCell>Candidate</TableCell>
                <TableCell align="center" width="100">
                  Change
                </TableCell>
                <TableCell align="center" width="100">
                  Previous Rank
                </TableCell>
                <TableCell align="right" width="120">
                  New Score
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {candidatesWithChanges.map((candidate) => (
                <TableRow
                  key={candidate.resume_id}
                  sx={{
                    backgroundColor:
                      candidate.rankChange > 0
                        ? 'success.lighter'
                        : candidate.rankChange < 0
                          ? 'error.lighter'
                          : 'transparent',
                    '&:hover': {
                      backgroundColor:
                        candidate.rankChange > 0
                          ? 'success.light'
                          : candidate.rankChange < 0
                            ? 'error.light'
                            : 'action.hover',
                    },
                  }}
                >
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {candidate.rank === 1 && (
                        <TrophyIcon fontSize="small" sx={{ color: 'warning.main' }} />
                      )}
                      <Typography
                        variant="body2"
                        fontWeight={candidate.rank <= 3 ? 'bold' : 'normal'}
                      >
                        #{candidate.rank}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Avatar
                        sx={{
                          width: 32,
                          height: 32,
                          bgcolor: 'primary.main',
                          fontSize: '0.875rem',
                        }}
                      >
                        {candidate.filename.charAt(0).toUpperCase()}
                      </Avatar>
                      <Typography variant="body2" noWrap>
                        {candidate.filename}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    {candidate.rankChange !== 0 ? (
                      <Tooltip
                        title={`${candidate.rankChange > 0 ? 'Moved up' : 'Moved down'} ${Math.abs(
                          candidate.rankChange
                        )} position(s)`}
                      >
                        <Chip
                          icon={getRankChangeIcon(candidate.rankChange)}
                          label={
                            candidate.rankChange > 0
                              ? `+${candidate.rankChange}`
                              : candidate.rankChange
                          }
                          size="small"
                          color={getRankChangeColor(candidate.rankChange)}
                          sx={{ minWidth: 70 }}
                        />
                      </Tooltip>
                    ) : (
                      <Chip icon={<NoChangeIcon />} label="—" size="small" variant="outlined" />
                    )}
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" color="text.secondary">
                      #{candidate.previousRank}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {(candidate.overall_score * 100).toFixed(1)}%
                      </Typography>
                      {candidate.scoreChange !== 0 && (
                        <Typography
                          variant="caption"
                          color={candidate.scoreChange > 0 ? 'success.main' : 'error.main'}
                        >
                          {candidate.scoreChange > 0 ? '+' : ''}
                          {(candidate.scoreChange * 100).toFixed(1)}%
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Stack>
    </Paper>
  );
};

export default RankingWeightImpactPreview;
