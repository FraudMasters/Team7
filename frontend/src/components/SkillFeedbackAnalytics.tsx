import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { config } from '@/config';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Button,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  School as SkillIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';

/**
 * Skill feedback entry interface from backend
 */
interface SkillFeedbackEntry {
  id: string;
  resume_id: string;
  vacancy_id: string;
  skill: string;
  was_correct: boolean;
  confidence_score?: number;
  recruiter_correction?: string;
  actual_skill?: string;
  feedback_source: string;
  processed: boolean;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

/**
 * Skill feedback list response from backend
 */
interface SkillFeedbackListResponse {
  feedback: SkillFeedbackEntry[];
  total_count: number;
}

/**
 * Skill correction statistics
 */
interface SkillCorrectionStats {
  skill: string;
  total_corrections: number;
  correct_count: number;
  incorrect_count: number;
  accuracy: number;
}

/**
 * Accuracy data point for chart
 */
interface AccuracyDataPoint {
  date: string;
  accuracy: number;
  sample_size: number;
}

/**
 * SkillFeedbackAnalytics Component Props
 */
interface SkillFeedbackAnalyticsProps {
  /** API endpoint URL for skill feedback */
  feedbackApiUrl?: string;
}

/**
 * SkillFeedbackAnalytics Component
 *
 * Displays skill feedback analytics dashboard including:
 * - Total feedback count and accuracy metrics
 * - Accuracy improvement chart over time
 * - Most frequently corrected skills
 * - Skill extraction performance trends
 *
 * @example
 * ```tsx
 * <SkillFeedbackAnalytics />
 * ```
 */
const SkillFeedbackAnalytics: React.FC<SkillFeedbackAnalyticsProps> = ({
  feedbackApiUrl = `${config.api.url}/api/feedback`,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<SkillFeedbackEntry[]>([]);

  /**
   * Fetch skill feedback data from backend
   */
  const fetchFeedback = async () => {
    try {
      const response = await fetch(`${feedbackApiUrl}/?limit=1000`);

      if (!response.ok) {
        throw new Error(`Failed to fetch skill feedback: ${response.statusText}`);
      }

      const result: SkillFeedbackListResponse = await response.json();
      setFeedback(result.feedback || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load skill feedback data';
      setError(errorMessage);
    }
  };

  /**
   * Fetch all analytics data
   */
  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);

    await fetchFeedback();

    setLoading(false);
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  /**
   * Calculate feedback statistics
   */
  const feedbackStats = {
    total: feedback.length,
    correct: feedback.filter((f) => f.was_correct).length,
    incorrect: feedback.filter((f) => !f.was_correct).length,
    processed: feedback.filter((f) => f.processed).length,
    unprocessed: feedback.filter((f) => !f.processed).length,
    accuracy:
      feedback.length > 0
        ? (feedback.filter((f) => f.was_correct).length / feedback.length) * 100
        : 0,
  };

  /**
   * Calculate most corrected skills
   */
  const mostCorrectedSkills: SkillCorrectionStats[] = React.useMemo(() => {
    const skillMap = new Map<string, SkillCorrectionStats>();

    feedback.forEach((entry) => {
      const skillName = entry.skill;
      const existing = skillMap.get(skillName);

      if (existing) {
        existing.total_corrections += 1;
        if (entry.was_correct) {
          existing.correct_count += 1;
        } else {
          existing.incorrect_count += 1;
        }
      } else {
        skillMap.set(skillName, {
          skill: skillName,
          total_corrections: 1,
          correct_count: entry.was_correct ? 1 : 0,
          incorrect_count: entry.was_correct ? 0 : 1,
          accuracy: 0,
        });
      }
    });

    // Calculate accuracy for each skill
    skillMap.forEach((stats) => {
      stats.accuracy =
        stats.total_corrections > 0
          ? (stats.correct_count / stats.total_corrections) * 100
          : 0;
    });

    // Sort by total corrections descending
    return Array.from(skillMap.values())
      .sort((a, b) => b.total_corrections - a.total_corrections)
      .slice(0, 10);
  }, [feedback]);

  /**
   * Calculate accuracy improvement over time
   */
  const accuracyTrend: AccuracyDataPoint[] = React.useMemo(() => {
    if (feedback.length === 0) return [];

    // Group feedback by date
    const dateMap = new Map<string, { correct: number; total: number }>();

    feedback.forEach((entry) => {
      const date = new Date(entry.created_at).toISOString().split('T')[0];
      const existing = dateMap.get(date);

      if (existing) {
        existing.total += 1;
        if (entry.was_correct) existing.correct += 1;
      } else {
        dateMap.set(date, {
          correct: entry.was_correct ? 1 : 0,
          total: 1,
        });
      }
    });

    // Convert to array and calculate cumulative accuracy
    const sortedDates = Array.from(dateMap.keys()).sort();
    let cumulativeCorrect = 0;
    let cumulativeTotal = 0;

    return sortedDates.map((date) => {
      const dayData = dateMap.get(date)!;
      cumulativeCorrect += dayData.correct;
      cumulativeTotal += dayData.total;

      return {
        date,
        accuracy: (cumulativeCorrect / cumulativeTotal) * 100,
        sample_size: cumulativeTotal,
      };
    });
  }, [feedback]);

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
          Loading Skill Feedback Analytics
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Analyzing skill extraction performance...
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
          <Button color="inherit" onClick={fetchAnalytics} startIcon={<RefreshIcon />}>
            Try Again
          </Button>
        }
      >
        <AlertTitle>Error Loading Analytics</AlertTitle>
        {error}
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h5" fontWeight={600}>
              Skill Feedback Analytics
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Monitor skill extraction accuracy and recruiter corrections
            </Typography>
          </Box>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchAnalytics} size="small">
            Refresh
          </Button>
        </Box>

        {/* Summary Statistics */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {feedbackStats.total}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Total Feedback
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined" sx={{ borderColor: 'success.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {feedbackStats.correct}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Correct Detections
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card variant="outlined" sx={{ borderColor: 'error.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="error.main" fontWeight={700}>
                  {feedbackStats.incorrect}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Incorrect Detections
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Card
              variant="outlined"
              sx={{
                borderColor:
                  feedbackStats.accuracy >= 80
                    ? 'success.main'
                    : feedbackStats.accuracy >= 60
                      ? 'warning.main'
                      : 'error.main',
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                  <Typography variant="h4" color={feedbackStats.accuracy >= 80 ? 'success.main' : feedbackStats.accuracy >= 60 ? 'warning.main' : 'error.main'} fontWeight={700}>
                    {feedbackStats.accuracy.toFixed(1)}%
                  </Typography>
                  {feedbackStats.accuracy >= 70 ? (
                    <TrendingUpIcon fontSize="small" color="success" />
                  ) : (
                    <TrendingDownIcon fontSize="small" color="error" />
                  )}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Accuracy
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Accuracy Improvement Chart */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          <TimelineIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
          Accuracy Improvement Over Time
        </Typography>
        <Divider sx={{ mb: 3 }} />

        {accuracyTrend.length === 0 ? (
          <Alert severity="info">
            <AlertTitle>No Data Available</AlertTitle>
            No skill feedback data available yet. Accuracy trends will appear as recruiters provide
            feedback on skill extractions.
          </Alert>
        ) : (
          <Box>
            {/* Chart Visualization */}
            <Box sx={{ mb: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Box sx={{ height: 200, position: 'relative' }}>
                    <Stack spacing={1}>
                      {accuracyTrend.slice(-10).map((point, index) => {
                        const barWidth = (point.accuracy / 100) * 100;
                        const color =
                          point.accuracy >= 80
                            ? '#388e3c'
                            : point.accuracy >= 60
                              ? '#fbc02d'
                              : '#d32f2f';

                        return (
                          <Box key={point.date}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">
                                {new Date(point.date).toLocaleDateString()}
                              </Typography>
                              <Typography variant="caption" fontWeight={600}>
                                {point.accuracy.toFixed(1)}% (n={point.sample_size})
                              </Typography>
                            </Box>
                            <Box
                              sx={{
                                height: 12,
                                borderRadius: 1,
                                bgcolor: 'action.hover',
                                position: 'relative',
                                overflow: 'hidden',
                              }}
                            >
                              <Box
                                sx={{
                                  position: 'absolute',
                                  left: 0,
                                  top: 0,
                                  bottom: 0,
                                  width: `${barWidth}%`,
                                  bgcolor: color,
                                  transition: 'width 0.5s ease-in-out',
                                }}
                              />
                            </Box>
                          </Box>
                        );
                      })}
                    </Stack>
                  </Box>
                </Grid>
              </Grid>
            </Box>

            {/* Trend Summary */}
            <Alert
              severity={
                feedbackStats.accuracy >= 80
                  ? 'success'
                  : feedbackStats.accuracy >= 60
                    ? 'warning'
                    : 'info'
              }
            >
              <AlertTitle>Performance Trend</AlertTitle>
              {accuracyTrend.length > 1 ? (
                <>
                  {accuracyTrend[accuracyTrend.length - 1].accuracy >
                  accuracyTrend[0].accuracy ? (
                    <>
                      <TrendingUpIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                      Accuracy has improved by{' '}
                      {(
                        accuracyTrend[accuracyTrend.length - 1].accuracy - accuracyTrend[0].accuracy
                      ).toFixed(1)}
                      % since the first feedback entry.
                    </>
                  ) : (
                    <>
                      <TrendingDownIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                      Accuracy has decreased by{' '}
                      {(
                        accuracyTrend[0].accuracy - accuracyTrend[accuracyTrend.length - 1].accuracy
                      ).toFixed(1)}
                      % since the first feedback entry.
                    </>
                  )}
                </>
              ) : (
                'Not enough data to show trends. More feedback entries needed.'
              )}
            </Alert>
          </Box>
        )}
      </Paper>

      {/* Most Corrected Skills */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          <SkillIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
          Most Corrected Skills
        </Typography>
        <Divider sx={{ mb: 3 }} />

        {mostCorrectedSkills.length === 0 ? (
          <Alert severity="info">
            <AlertTitle>No Skill Data</AlertTitle>
            No skill correction data available yet. This section will show the skills that
            receive the most feedback from recruiters.
          </Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Skill</TableCell>
                  <TableCell align="right">Total Feedback</TableCell>
                  <TableCell align="right">Correct</TableCell>
                  <TableCell align="right">Incorrect</TableCell>
                  <TableCell align="right">Accuracy</TableCell>
                  <TableCell align="center">Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {mostCorrectedSkills.map((skill, index) => (
                  <TableRow key={`${skill.skill}-${index}`} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>
                        {skill.skill}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">{skill.total_corrections}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="success.main">
                        {skill.correct_count}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="error.main">
                        {skill.incorrect_count}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        color={
                          skill.accuracy >= 80
                            ? 'success.main'
                            : skill.accuracy >= 60
                              ? 'warning.main'
                              : 'error.main'
                        }
                      >
                        {skill.accuracy.toFixed(1)}%
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      {skill.accuracy >= 80 ? (
                        <Chip label="Excellent" size="small" color="success" icon={<CheckIcon />} />
                      ) : skill.accuracy >= 60 ? (
                        <Chip label="Good" size="small" color="warning" />
                      ) : (
                        <Chip label="Needs Improvement" size="small" color="error" icon={<ErrorIcon />} />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {mostCorrectedSkills.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Showing top {mostCorrectedSkills.length} skills by feedback volume. Skills with low accuracy
              may need additional training data or model improvements.
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Learning Status */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom fontWeight={600}>
          Learning Status
        </Typography>
        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Processed Feedback
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {feedbackStats.processed} / {feedbackStats.total}
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={feedbackStats.total > 0 ? (feedbackStats.processed / feedbackStats.total) * 100 : 0}
                sx={{ height: 10, borderRadius: 1 }}
                color="success"
              />
            </Box>

            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Pending Processing
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {feedbackStats.unprocessed} / {feedbackStats.total}
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={feedbackStats.total > 0 ? (feedbackStats.unprocessed / feedbackStats.total) * 100 : 0}
                sx={{ height: 10, borderRadius: 1 }}
                color="warning"
              />
            </Box>

            <Alert
              severity={
                feedbackStats.accuracy >= 80
                  ? 'success'
                  : feedbackStats.accuracy >= 60
                    ? 'warning'
                    : 'info'
              }
            >
              <AlertTitle>Current Status</AlertTitle>
              {feedbackStats.total === 0
                ? 'No feedback data available yet. Skill extraction accuracy will improve as recruiters provide feedback.'
                : feedbackStats.unprocessed > 0
                  ? `${feedbackStats.unprocessed} feedback entries are pending processing. The model will be retrained once these are processed.`
                  : 'All feedback has been processed. The model is learning from recruiter corrections.'}
            </Alert>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              Performance Metrics
            </Typography>
            <List>
              <ListItem>
                <ListItemText
                  primary="Current Accuracy"
                  secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                      <Typography variant="h4" fontWeight={700} color={feedbackStats.accuracy >= 80 ? 'success.main' : feedbackStats.accuracy >= 60 ? 'warning.main' : 'error.main'}>
                        {feedbackStats.accuracy.toFixed(1)}%
                      </Typography>
                      {feedbackStats.accuracy >= 80 ? (
                        <Chip label="Excellent" size="small" color="success" />
                      ) : feedbackStats.accuracy >= 60 ? (
                        <Chip label="Good" size="small" color="warning" />
                      ) : (
                        <Chip label="Needs Improvement" size="small" color="error" />
                      )}
                    </Box>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Target Accuracy"
                  secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                      <Typography variant="h5" fontWeight={600}>
                        90.0%
                      </Typography>
                      <Chip label="Goal" size="small" color="info" variant="outlined" />
                    </Box>
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Gap to Target"
                  secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                      <Typography variant="h5" fontWeight={600} color={Math.max(0, 90 - feedbackStats.accuracy) <= 10 ? 'success.main' : 'warning.main'}>
                        {Math.max(0, 90 - feedbackStats.accuracy).toFixed(1)}%
                      </Typography>
                      {Math.max(0, 90 - feedbackStats.accuracy) <= 10 ? (
                        <TrendingUpIcon fontSize="small" color="success" />
                      ) : (
                        <TrendingDownIcon fontSize="small" color="warning" />
                      )}
                    </Box>
                  }
                />
              </ListItem>
            </List>
          </Grid>
        </Grid>
      </Paper>
    </Stack>
  );
};

export default SkillFeedbackAnalytics;
