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
  Tooltip,
  Card,
  CardContent,
  Grid,
  Divider,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Cancel as CrossIcon,
  Refresh as RefreshIcon,
  Grid4x4 as MatrixIcon,
  EmojiEvents as TrophyIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material';

/**
 * Individual skill match interface
 */
interface SkillMatch {
  skill: string;
  matched: boolean;
  highlight: 'green' | 'red';
}

/**
 * Experience verification interface
 */
interface ExperienceVerification {
  skill: string;
  total_months: number;
  required_months: number;
  meets_requirement: boolean;
  projects: Array<{
    company: string;
    position: string;
    start_date: string;
    end_date: string | null;
    months: number;
  }>;
}

/**
 * Individual resume comparison result
 */
interface ResumeComparisonResult {
  resume_id: string;
  match_percentage: number;
  matched_skills: SkillMatch[];
  missing_skills: SkillMatch[];
  experience_verification?: ExperienceVerification[];
  overall_match: boolean;
}

/**
 * Comparison matrix data structure from backend
 */
interface ComparisonMatrixData {
  vacancy_id: string;
  comparisons: ResumeComparisonResult[];
  all_unique_skills: string[];
  processing_time?: number;
}

/**
 * ResumeComparisonMatrix Component Props
 */
interface ResumeComparisonMatrixProps {
  /** Array of resume IDs to compare */
  resumeIds: string[];
  /** Vacancy ID for the comparison */
  vacancyId: string;
  /** API endpoint URL for fetching comparison results */
  apiUrl?: string;
  /** Show additional details like experience verification */
  showDetails?: boolean;
  /** Enable ranking display */
  showRanking?: boolean;
}

/**
 * Get match percentage color and label
 */
const getMatchConfig = (percentage: number) => {
  if (percentage >= 70) {
    return {
      color: 'success' as const;
      label: 'Excellent',
      bgColor: 'success.main',
      textColor: 'success.contrastText',
      bgColorLight: 'success.50',
    };
  }
  if (percentage >= 40) {
    return {
      color: 'warning' as const,
      label: 'Moderate',
      bgColor: 'warning.main',
      textColor: 'warning.contrastText',
      bgColorLight: 'warning.50',
    };
  }
  return {
    color: 'error' as const,
    label: 'Poor',
    bgColor: 'error.main',
    textColor: 'error.contrastText',
    bgColorLight: 'error.50',
  };
};

/**
 * ResumeComparisonMatrix Component
 *
 * Displays a comprehensive skill matrix for comparing multiple resumes with:
 * - Interactive skill matrix with visual highlighting (green=has skill, red=missing)
 * - Rank ordering by match percentage
 * - Detailed match statistics
 * - Color-coded performance indicators
 * - Experience verification summaries
 *
 * @example
 * ```tsx
 * <ResumeComparisonMatrix
 *   resumeIds={['resume-1', 'resume-2', 'resume-3']}
 *   vacancyId="vacancy-123"
 *   showRanking={true}
 * />
 * ```
 */
const ResumeComparisonMatrix: React.FC<ResumeComparisonMatrixProps> = ({
  resumeIds,
  vacancyId,
  apiUrl = 'http://localhost:8000/api/comparisons',
  showDetails = true,
  showRanking = true,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ComparisonMatrixData | null>(null);

  /**
   * Fetch comparison data from backend
   */
  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/compare-multiple`, {
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

      const result: ComparisonMatrixData = await response.json();
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
    if (resumeIds && resumeIds.length >= 2 && resumeIds.length <= 5 && vacancyId) {
      fetchComparison();
    } else if (resumeIds.length < 2) {
      setError('At least 2 resumes are required for comparison');
      setLoading(false);
    } else if (resumeIds.length > 5) {
      setError('Maximum 5 resumes can be compared at once');
      setLoading(false);
    }
  }, [resumeIds, vacancyId]);

  /**
   * Check if a resume has a specific skill
   */
  const hasSkill = (comparison: ResumeComparisonResult, skill: string): boolean => {
    return comparison.matched_skills.some((s) => s.skill === skill);
  };

  /**
   * Get skill count statistics for a resume
   */
  const getSkillStats = (comparison: ResumeComparisonResult) => {
    return {
      matched: comparison.matched_skills.length,
      missing: comparison.missing_skills.length,
      total: comparison.matched_skills.length + comparison.missing_skills.length,
    };
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
          Building comparison matrix...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Analyzing {resumeIds.length} resumes against vacancy requirements
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
  if (!data || !data.comparisons || data.comparisons.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" fontWeight={600}>
          No Comparison Data
        </Typography>
        <Typography variant="body2">
          No comparison data found for the selected resumes and vacancy.
        </Typography>
      </Alert>
    );
  }

  // Sort comparisons by match percentage (descending)
  const sortedComparisons = [...data.comparisons].sort(
    (a, b) => b.match_percentage - a.match_percentage
  );

  return (
    <Stack spacing={3}>
      {/* Header Section with Title and Actions */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <MatrixIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Resume Comparison Matrix
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Vacancy: <strong>{vacancyId}</strong> • Comparing <strong>{resumeIds.length}</strong>{' '}
                resumes • <strong>{data.all_unique_skills.length}</strong> skills
              </Typography>
            </Box>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchComparison} size="small">
            Refresh
          </Button>
        </Box>

        {/* Ranking Overview */}
        {showRanking && (
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
            {sortedComparisons.map((comparison, index) => {
              const matchConfig = getMatchConfig(comparison.match_percentage);
              const stats = getSkillStats(comparison);
              return (
                <Tooltip
                  key={comparison.resume_id}
                  title={`${stats.matched}/${stats.total} skills matched`}
                  arrow
                >
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.5,
                      bgcolor: matchConfig.bgColorLight,
                      px: 2,
                      py: 1,
                      borderRadius: 2,
                      border: `1px solid ${matchConfig.bgColor}`,
                      cursor: 'pointer',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 3,
                      },
                    }}
                  >
                    <Typography
                      variant="h5"
                      fontWeight={700}
                      color={matchConfig.bgColor}
                      sx={{ minWidth: 32 }}
                    >
                      #{index + 1}
                    </Typography>
                    <Box>
                      <Typography variant="body2" fontWeight={600}>
                        {comparison.resume_id}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                          {stats.matched}/{stats.total} skills
                        </Typography>
                        <Chip
                          label={`${comparison.match_percentage.toFixed(0)}%`}
                          size="small"
                          color={matchConfig.color}
                          sx={{ height: 20, fontSize: '0.7rem', fontWeight: 700 }}
                        />
                      </Box>
                    </Box>
                  </Box>
                </Tooltip>
              );
            })}
          </Box>
        )}
      </Paper>

      {/* Performance Summary Cards */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <TrendingIcon sx={{ mr: 1, fontSize: 28, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Performance Summary
          </Typography>
        </Box>
        <Grid container spacing={2}>
          {sortedComparisons.map((comparison, index) => {
            const matchConfig = getMatchConfig(comparison.match_percentage);
            const stats = getSkillStats(comparison);
            const topPerformer = index === 0;
            return (
              <Grid item xs={12} sm={6} md={4} key={comparison.resume_id}>
                <Card
                  variant="outlined"
                  sx={{
                    borderColor: topPerformer ? 'primary.main' : matchConfig.bgColor,
                    bgcolor: matchConfig.bgColorLight,
                    position: 'relative',
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                    },
                  }}
                >
                  {topPerformer && (
                    <Tooltip title="Top Performer" arrow>
                      <TrophyIcon
                        sx={{
                          position: 'absolute',
                          top: 8,
                          right: 8,
                          fontSize: 24,
                          color: 'warning.main',
                        }}
                      />
                    </Tooltip>
                  )}
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Rank #{index + 1}
                        </Typography>
                        <Typography variant="h6" fontWeight={600} gutterBottom>
                          {comparison.resume_id}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                          <Chip
                            label={`${comparison.match_percentage.toFixed(0)}% Match`}
                            color={matchConfig.color}
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        </Box>
                      </Box>
                    </Box>
                    <Divider sx={{ my: 1.5 }} />
                    <Stack spacing={0.5}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Matched Skills:
                        </Typography>
                        <Typography variant="caption" fontWeight={600} color="success.main">
                          {stats.matched}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Missing Skills:
                        </Typography>
                        <Typography variant="caption" fontWeight={600} color="error.main">
                          {stats.missing}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Total Skills:
                        </Typography>
                        <Typography variant="caption" fontWeight={600}>
                          {stats.total}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      </Paper>

      {/* Skills Matrix Table */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <MatrixIcon sx={{ mr: 1, fontSize: 28, color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={600}>
            Skills Matrix
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Visual representation of which candidates possess the required skills for this vacancy
        </Typography>

        <TableContainer sx={{ maxHeight: 600, overflow: 'auto', border: '1px solid', borderColor: 'divider' }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                <TableCell
                  sx={{
                    fontWeight: 700,
                    bgcolor: 'primary.main',
                    color: 'primary.contrastText',
                    minWidth: 180,
                    position: 'sticky',
                    left: 0,
                    zIndex: 3,
                  }}
                >
                  Required Skill
                </TableCell>
                {sortedComparisons.map((comparison) => (
                  <TableCell
                    key={comparison.resume_id}
                    align="center"
                    sx={{
                      fontWeight: 700,
                      bgcolor: 'grey.100',
                      minWidth: 140,
                    }}
                  >
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                      <Typography variant="body2" fontWeight={600}>
                        {comparison.resume_id}
                      </Typography>
                      <Chip
                        label={`${comparison.match_percentage.toFixed(0)}%`}
                        size="small"
                        color={getMatchConfig(comparison.match_percentage).color}
                        sx={{ height: 22, fontSize: '0.7rem', fontWeight: 700 }}
                      />
                    </Box>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {data.all_unique_skills.map((skill, skillIndex) => (
                <TableRow
                  key={skill}
                  sx={{
                    '&:nth-of-type(odd)': { bgcolor: 'action.hover' },
                    '&:hover': { bgcolor: 'action.selected' },
                  }}
                >
                  <TableCell
                    sx={{
                      fontWeight: 600,
                      position: 'sticky',
                      left: 0,
                      bgcolor: skillIndex % 2 === 0 ? 'background.paper' : 'action.hover',
                      zIndex: 2,
                      borderRight: '2px solid',
                      borderRightColor: 'divider',
                    }}
                  >
                    {skill}
                  </TableCell>
                  {sortedComparisons.map((comparison) => {
                    const skillMatch = hasSkill(comparison, skill);
                    return (
                      <TableCell
                        key={`${comparison.resume_id}-${skill}`}
                        align="center"
                        sx={{
                          bgcolor: skillMatch ? 'success.50' : 'error.50',
                          transition: 'bgcolor 0.2s',
                        }}
                      >
                        {skillMatch ? (
                          <Tooltip title="Has this skill" arrow>
                            <CheckIcon
                              color="success"
                              sx={{
                                fontSize: 24,
                                transition: 'transform 0.2s',
                                '&:hover': {
                                  transform: 'scale(1.2)',
                                },
                              }}
                            />
                          </Tooltip>
                        ) : (
                          <Tooltip title="Missing this skill" arrow>
                            <CrossIcon
                              color="error"
                              sx={{
                                fontSize: 24,
                                transition: 'transform 0.2s',
                                '&:hover': {
                                  transform: 'scale(1.2)',
                                },
                              }}
                            />
                          </Tooltip>
                        )}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Legend */}
        <Box sx={{ display: 'flex', gap: 3, mt: 2, justifyContent: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CheckIcon color="success" sx={{ fontSize: 20 }} />
            <Typography variant="caption" color="text.secondary">
              Has Skill
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CrossIcon color="error" sx={{ fontSize: 20 }} />
            <Typography variant="caption" color="text.secondary">
              Missing Skill
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Detailed Experience Breakdown */}
      {showDetails &&
        sortedComparisons.some((c) => c.experience_verification && c.experience_verification.length > 0) && (
          <Paper elevation={1} sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Experience Verification Summary
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Verified work experience for required skills across all candidates
            </Typography>

            <Stack spacing={2}>
              {sortedComparisons.map((comparison) => {
                const matchConfig = getMatchConfig(comparison.match_percentage);
                const hasExperience =
                  comparison.experience_verification && comparison.experience_verification.length > 0;

                if (!hasExperience) return null;

                return (
                  <Box
                    key={comparison.resume_id}
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      border: `1px solid ${matchConfig.bgColor}`,
                      bgcolor: matchConfig.bgColorLight,
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {comparison.resume_id}
                      </Typography>
                      <Chip
                        label={`${comparison.match_percentage.toFixed(0)}% Match`}
                        color={matchConfig.color}
                        size="small"
                        sx={{ fontWeight: 600 }}
                      />
                    </Box>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {comparison.experience_verification!.map((exp, expIndex) => (
                        <Chip
                          key={expIndex}
                          label={`${exp.skill}: ${exp.total_months}mo`}
                          size="small"
                          color={exp.meets_requirement ? 'success' : 'warning'}
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Box>
                );
              })}
            </Stack>
          </Paper>
        )}

      {/* Processing Time */}
      {data.processing_time && (
        <Typography variant="caption" color="text.secondary" align="center" display="block">
          Matrix generated in {data.processing_time.toFixed(2)} seconds
        </Typography>
      )}
    </Stack>
  );
};

export default ResumeComparisonMatrix;
