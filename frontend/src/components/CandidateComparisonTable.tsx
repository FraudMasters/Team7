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
  LinearProgress,
  Avatar,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  EmojiEvents as TrophyIcon,
  Person as PersonIcon,
  Key as KeywordIcon,
  Tune as TfidfIcon,
  Psychology as VectorIcon,
} from '@mui/icons-material';

/**
 * Individual candidate score breakdown from backend
 */
interface CandidateScoreBreakdown {
  resume_id: string;
  filename: string;
  match_score: {
    overall_score: number;
    keyword_score: number;
    tfidf_score: number;
    vector_score: number;
  };
  passed: boolean;
  recommendation: string;
  matched_skills: string[];
  missing_skills: string[];
  rank: number;
}

/**
 * Candidate comparison data structure from backend
 */
interface CandidateComparisonData {
  vacancy_id: string;
  vacancy_title: string;
  candidates: CandidateScoreBreakdown[];
  summary: {
    total_candidates: number;
    best_score: number;
    average_score: number;
    worst_score: number;
    passed_count: number;
  };
  processing_time_ms: number;
}

/**
 * CandidateComparisonTable Component Props
 */
interface CandidateComparisonTableProps {
  /** Vacancy ID for the comparison */
  vacancyId: string;
  /** Array of resume IDs to compare (1-10 candidates) */
  resumeIds: string[];
  /** API endpoint URL for fetching comparison results */
  apiUrl?: string;
}

/**
 * Helper to get score color
 */
const getScoreColor = (score: number): 'success' | 'warning' | 'error' => {
  const percentage = score * 100;
  if (percentage >= 70) return 'success';
  if (percentage >= 40) return 'warning';
  return 'error';
};

/**
 * Helper to get score label
 */
const getScoreLabel = (score: number): string => {
  const percentage = score * 100;
  if (percentage >= 70) return 'Excellent';
  if (percentage >= 40) return 'Moderate';
  return 'Poor';
};

/**
 * CandidateComparisonTable Component
 *
 * Displays side-by-side comparison of top candidates with detailed score breakdowns:
 * - Overall match score comparison
 * - Component scores (Keyword, TF-IDF, Vector) with visual bars
 * - Highlighting of best scores in each category
 * - Skills matched vs missing
 * - Responsive table layout
 *
 * @example
 * ```tsx
 * <CandidateComparisonTable
 *   vacancyId="vacancy-123"
 *   resumeIds={['resume-1', 'resume-2', 'resume-3']}
 * />
 * ```
 */
const CandidateComparisonTable: React.FC<CandidateComparisonTableProps> = ({
  vacancyId,
  resumeIds,
  apiUrl = 'http://localhost:8000/api/matching',
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<CandidateComparisonData | null>(null);

  /**
   * Fetch candidate comparison data from backend
   */
  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/compare-candidates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          vacancy_id: vacancyId,
          resume_ids: resumeIds,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch comparison: ${response.statusText}`);
      }

      const result: CandidateComparisonData = await response.json();
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
    if (vacancyId && resumeIds && resumeIds.length > 0) {
      fetchComparison();
    } else if (!resumeIds || resumeIds.length === 0) {
      setError('At least one resume ID is required for comparison');
      setLoading(false);
    }
  }, [vacancyId, resumeIds]);

  /**
   * Find best score in a specific category
   */
  const getBestScore = (category: 'overall_score' | 'keyword_score' | 'tfidf_score' | 'vector_score'): number => {
    if (!data || !data.candidates || data.candidates.length === 0) return 0;
    return Math.max(...data.candidates.map((c) => c.match_score[category]));
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
          Comparing candidates...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Analyzing {resumeIds.length} candidate(s) for vacancy requirements
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
  if (!data || !data.candidates || data.candidates.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" fontWeight={600}>
          No Comparison Data
        </Typography>
        <Typography variant="body2">
          No candidates found for comparison. Check that the vacancy and resume IDs are valid.
        </Typography>
      </Alert>
    );
  }

  // Get best scores for highlighting
  const bestOverall = getBestScore('overall_score');
  const bestKeyword = getBestScore('keyword_score');
  const bestTfidf = getBestScore('tfidf_score');
  const bestVector = getBestScore('vector_score');

  /**
   * Render score bar with highlighting
   */
  const ScoreBar: React.FC<{
    value: number;
    isBest: boolean;
  }> = ({ value, isBest }) => {
    const percentage = Math.round(value * 100);
    const color = getScoreColor(value);

    return (
      <Stack spacing={0.5} sx={{ width: '100%' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" fontWeight={600} color={isBest ? `${color}.main` : 'text.primary'}>
            {percentage}%
            {isBest && <TrophyIcon sx={{ fontSize: 14, ml: 0.5, verticalAlign: 'middle' }} />}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={percentage}
          color={color}
          sx={{
            height: 8,
            borderRadius: 4,
            bgcolor: isBest ? `${color}.100` : 'grey.200',
            ...(isBest && {
              boxShadow: `0 0 0 2px ${color}.main`,
            }),
          }}
        />
      </Stack>
    );
  };

  /**
   * Render candidate card for mobile view
   */
  const CandidateCard: React.FC<{
    candidate: CandidateScoreBreakdown;
    rank: number;
  }> = ({ candidate, rank }) => {
    const isBestOverall = candidate.match_score.overall_score === bestOverall;

    return (
      <Paper
        variant="outlined"
        sx={{
          p: 2,
          border: isBestOverall ? 2 : 1,
          borderColor: isBestOverall ? `${getScoreColor(candidate.match_score.overall_score)}.main` : 'divider',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar
            sx={{
              mr: 2,
              bgcolor: rank === 1 ? 'warning.main' : 'primary.main',
              width: 48,
              height: 48,
            }}
          >
            {rank === 1 ? <TrophyIcon /> : <PersonIcon />}
          </Avatar>
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle1" fontWeight={700}>
              #{rank} {candidate.filename}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {getScoreLabel(candidate.match_score.overall_score)} Match
            </Typography>
          </Box>
          <Chip
            label={`${Math.round(candidate.match_score.overall_score * 100)}%`}
            color={getScoreColor(candidate.match_score.overall_score)}
            sx={{ fontWeight: 700 }}
          />
        </Box>

        <Stack spacing={1.5}>
          {/* Keyword Score */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
              <KeywordIcon sx={{ fontSize: 16, mr: 0.5, color: 'primary.main' }} />
              <Typography variant="caption" color="text.secondary">
                Keyword (50%)
              </Typography>
            </Box>
            <ScoreBar
              value={candidate.match_score.keyword_score}
              isBest={candidate.match_score.keyword_score === bestKeyword}
            />
          </Box>

          {/* TF-IDF Score */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
              <TfidfIcon sx={{ fontSize: 16, mr: 0.5, color: 'secondary.main' }} />
              <Typography variant="caption" color="text.secondary">
                TF-IDF (30%)
              </Typography>
            </Box>
            <ScoreBar
              value={candidate.match_score.tfidf_score}
              isBest={candidate.match_score.tfidf_score === bestTfidf}
            />
          </Box>

          {/* Vector Score */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
              <VectorIcon sx={{ fontSize: 16, mr: 0.5, color: 'info.main' }} />
              <Typography variant="caption" color="text.secondary">
                Vector (20%)
              </Typography>
            </Box>
            <ScoreBar
              value={candidate.match_score.vector_score}
              isBest={candidate.match_score.vector_score === bestVector}
            />
          </Box>

          {/* Skills Summary */}
          <Box
            sx={{
              pt: 1,
              borderTop: 1,
              borderColor: 'divider',
              display: 'flex',
              justifyContent: 'space-between',
            }}
          >
            <Typography variant="caption" color="success.main">
              ✓ {candidate.matched_skills.length} matched
            </Typography>
            <Typography variant="caption" color="error.main">
              ✗ {candidate.missing_skills.length} missing
            </Typography>
          </Box>
        </Stack>
      </Paper>
    );
  };

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h5" fontWeight={600}>
              Top {data.candidates.length} Candidates Comparison
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {data.vacancy_title} • Score breakdown by algorithm
            </Typography>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchComparison} size="small">
            Refresh
          </Button>
        </Box>

        {/* Legend */}
        <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <TrophyIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              Best score in category
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 16, height: 16, bgcolor: 'primary.main', borderRadius: 0.5 }} />
            <Typography variant="caption" color="text.secondary">
              Keyword (50%)
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 16, height: 16, bgcolor: 'secondary.main', borderRadius: 0.5 }} />
            <Typography variant="caption" color="text.secondary">
              TF-IDF (30%)
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 16, height: 16, bgcolor: 'info.main', borderRadius: 0.5 }} />
            <Typography variant="caption" color="text.secondary">
              Vector (20%)
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Desktop Table View */}
      <Box sx={{ display: { xs: 'none', md: 'block' } }}>
        <TableContainer component={Paper} elevation={1}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell
                  sx={{
                    fontWeight: 700,
                    bgcolor: 'grey.100',
                    minWidth: 180,
                    position: 'sticky',
                    left: 0,
                    zIndex: 3,
                  }}
                >
                  Candidate
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 150 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                    <Typography variant="body2" fontWeight={600}>
                      Overall
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 180 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                    <KeywordIcon sx={{ fontSize: 16 }} />
                    <Typography variant="body2" fontWeight={600}>
                      Keyword (50%)
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 180 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                    <TfidfIcon sx={{ fontSize: 16 }} />
                    <Typography variant="body2" fontWeight={600}>
                      TF-IDF (30%)
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 180 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                    <VectorIcon sx={{ fontSize: 16 }} />
                    <Typography variant="body2" fontWeight={600}>
                      Vector (20%)
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="center" sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 120 }}>
                  Skills
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.candidates.map((candidate, index) => {
                const isBestOverall = candidate.match_score.overall_score === bestOverall;
                const isBestKeyword = candidate.match_score.keyword_score === bestKeyword;
                const isBestTfidf = candidate.match_score.tfidf_score === bestTfidf;
                const isBestVector = candidate.match_score.vector_score === bestVector;

                return (
                  <TableRow
                    key={candidate.resume_id}
                    sx={{
                      '&:nth-of-type(odd)': { bgcolor: 'action.hover' },
                      ...(isBestOverall && {
                        bgcolor: `${getScoreColor(candidate.match_score.overall_score)}.50`,
                      }),
                    }}
                  >
                    {/* Candidate Name/ID */}
                    <TableCell
                      sx={{
                        fontWeight: 600,
                        position: 'sticky',
                        left: 0,
                        bgcolor: 'background.paper',
                        zIndex: 2,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Avatar
                          sx={{
                            width: 32,
                            height: 32,
                            bgcolor: index === 0 ? 'warning.main' : 'primary.main',
                          }}
                        >
                          {index === 0 ? <TrophyIcon sx={{ fontSize: 18 }} /> : index + 1}
                        </Avatar>
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {candidate.filename}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {getScoreLabel(candidate.match_score.overall_score)}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>

                    {/* Overall Score */}
                    <TableCell align="center">
                      <Chip
                        label={`${Math.round(candidate.match_score.overall_score * 100)}%`}
                        color={getScoreColor(candidate.match_score.overall_score)}
                        sx={{
                          fontWeight: 700,
                          ...(isBestOverall && {
                            boxShadow: `0 0 0 2px ${getScoreColor(candidate.match_score.overall_score)}.main`,
                          }),
                        }}
                      />
                    </TableCell>

                    {/* Keyword Score */}
                    <TableCell align="center">
                      <ScoreBar value={candidate.match_score.keyword_score} isBest={isBestKeyword} />
                    </TableCell>

                    {/* TF-IDF Score */}
                    <TableCell align="center">
                      <ScoreBar value={candidate.match_score.tfidf_score} isBest={isBestTfidf} />
                    </TableCell>

                    {/* Vector Score */}
                    <TableCell align="center">
                      <ScoreBar value={candidate.match_score.vector_score} isBest={isBestVector} />
                    </TableCell>

                    {/* Skills Summary */}
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                        <Typography variant="caption" color="success.main" fontWeight={600}>
                          ✓ {candidate.matched_skills.length}
                        </Typography>
                        <Typography variant="caption" color="error.main" fontWeight={600}>
                          ✗ {candidate.missing_skills.length}
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

      {/* Mobile Card View */}
      <Box sx={{ display: { xs: 'block', md: 'none' } }}>
        <Stack spacing={2}>
          {data.candidates.map((candidate, index) => (
            <CandidateCard key={candidate.resume_id} candidate={candidate} rank={index + 1} />
          ))}
        </Stack>
      </Box>

      {/* Processing Time */}
      {data.processing_time_ms && (
        <Typography variant="caption" color="text.secondary" align="center" display="block">
          Comparison completed in {(data.processing_time_ms / 1000).toFixed(2)} seconds
        </Typography>
      )}
    </Stack>
  );
};

export default CandidateComparisonTable;
