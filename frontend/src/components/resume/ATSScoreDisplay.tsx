/**
 * ATS Score Display Component
 *
 * Displays comprehensive ATS optimization score for resume builder,
 * showing compatibility analysis results, keywords, and issues.
 */

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Stack,
  CircularProgress,
  Alert,
  Divider,
  Tooltip,
  Collapse,
  IconButton,
  Button,
  LinearProgress,
  Paper,
  Grid,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import type { ATSScoreResponse, ATSIssue, ATSIssueSeverity } from '@/types/resumeBuilder';

/**
 * Get score color based on value
 */
const getScoreColor = (score: number): 'success' | 'warning' | 'error' => {
  if (score >= 70) return 'success';
  if (score >= 50) return 'warning';
  return 'error';
};

/**
 * Get score chip color
 */
const getScoreChipColor = (score: number): 'success' | 'warning' | 'error' | 'default' => {
  if (score >= 70) return 'success';
  if (score >= 50) return 'warning';
  if (score > 0) return 'error';
  return 'default';
};

/**
 * Get severity configuration
 */
const getSeverityConfig = (severity: ATSIssueSeverity) => {
  switch (severity) {
    case 'high':
      return {
        label: 'High',
        iconName: 'alert-circle',
        color: 'error' as const,
        description: 'Critical issue - should be fixed',
      };
    case 'medium':
      return {
        label: 'Medium',
        iconName: 'alert-triangle',
        color: 'warning' as const,
        description: 'Important issue - recommended fix',
      };
    case 'low':
      return {
        label: 'Low',
        iconName: 'info',
        color: 'info' as const,
        description: 'Minor issue - optional fix',
      };
    default:
      return {
        label: 'Unknown',
        iconName: 'help-circle',
        color: 'default' as const,
        description: 'Issue of unknown severity',
      };
  }
};

/**
 * Get issue type label
 */
const getIssueTypeLabel = (issueType: string): string => {
  const labels: Record<string, string> = {
    missing_keyword: 'Missing Keyword',
    format: 'Format Issue',
    length: 'Length Issue',
    structure: 'Structure Issue',
    readability: 'Readability Issue',
    contact: 'Contact Info',
    grammar: 'Grammar Issue',
    duplicate: 'Duplicate Content',
    vague: 'Vague Description',
  };
  return labels[issueType] || issueType.replace(/_/g, ' ');
};

/**
 * Get section label
 */
const getSectionLabel = (section: string): string => {
  const labels: Record<string, string> = {
    personal_info: 'Personal Information',
    summary: 'Professional Summary',
    work_experience: 'Work Experience',
    education: 'Education',
    skills: 'Skills',
    certifications: 'Certifications',
    languages: 'Languages',
    projects: 'Projects',
    header: 'Header',
    contact: 'Contact Information',
  };
  return labels[section] || section.replace(/_/g, ' ');
};

/**
 * Get score level label
 */
const getScoreLevelLabel = (score: number): string => {
  if (score >= 90) return 'Excellent';
  if (score >= 80) return 'Very Good';
  if (score >= 70) return 'Good';
  if (score >= 60) return 'Fair';
  if (score >= 50) return 'Needs Improvement';
  return 'Poor';
};

/**
 * ATSScoreDisplay Component Props
 */
interface ATSScoreDisplayProps {
  /** ATS score data */
  scoreData: ATSScoreResponse | null;
  /** Loading state */
  loading?: boolean;
  /** Error message */
  error?: string | null;
  /** Component title */
  title?: string;
  /** Show recalculate button */
  showRecalculate?: boolean;
  /** Callback to recalculate score */
  onRecalculate?: () => void;
  /** Disabled state */
  disabled?: boolean;
  /** Compact mode */
  compact?: boolean;
  /** Show detailed breakdown */
  showDetails?: boolean;
  /** Maximum issues to display */
  maxIssues?: number;
}

/**
 * Score Card Component
 */
interface ScoreCardProps {
  label: string;
  value: number | string;
  icon: string;
  color: 'success' | 'warning' | 'error' | 'primary' | 'default';
  suffix?: string;
}

const ScoreCard: React.FC<ScoreCardProps> = ({ label, value, icon, color, suffix }) => (
  <Paper
    sx={{
      p: 2,
      textAlign: 'center',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
    }}
  >
    <Box display="flex" alignItems="center" justifyContent="center" mb={1}>
      <Icon name={icon} color={color} />
    </Box>
    <Typography variant="h4" color={`${color}.main`}>
      {value}{suffix}
    </Typography>
    <Typography variant="caption" color="secondary">
      {label}
    </Typography>
  </Paper>
);

/**
 * Issue Item Component
 */
interface IssueItemProps {
  issue: ATSIssue;
  expanded: boolean;
  onToggle: () => void;
  compact: boolean;
}

const IssueItem: React.FC<IssueItemProps> = ({ issue, expanded, onToggle, compact }) => {
  const severityConfig = getSeverityConfig(issue.severity);

  return (
    <Box
      sx={{
        p: compact ? 1 : 1.5,
        borderRadius: 1,
        backgroundColor: 'background.default',
        border: '1px solid',
        borderColor: 'divider',
        transition: 'all 0.2s',
        '&:hover': {
          borderColor: `${severityConfig.color}.light`,
        },
      }}
    >
      {/* Issue Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
            <Icon name={severityConfig.iconName} color={severityConfig.color} sx={{ fontSize: '1rem' }} />
            <Typography sx={{ fontWeight: 600, fontSize: '0.95rem' }} color="text.primary">
              {getIssueTypeLabel(issue.issue_type)}
            </Typography>
          </Box>

          <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', mt: 0.5 }}>
            <Tooltip title={severityConfig.description} arrow>
              <Chip
                label={severityConfig.label}
                size="small"
                color={severityConfig.color}
                variant="outlined"
                sx={{ fontSize: '0.65rem', height: 20 }}
              />
            </Tooltip>
            <Chip
              label={getSectionLabel(issue.section)}
              size="small"
              color="default"
              variant="outlined"
              sx={{ fontSize: '0.65rem', height: 20 }}
            />
          </Stack>
        </Box>

        <IconButton size="small" onClick={onToggle}>
          <Icon name={expanded ? 'chevron-up' : 'chevron-down'} />
        </IconButton>
      </Box>

      {/* Expanded Content */}
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <Box sx={{ mt: 1.5 }}>
          <Typography color="text.secondary" sx={{ mb: 1, fontSize: '0.875rem' }}>
            {issue.description}
          </Typography>

          {issue.suggestion && (
            <Box
              sx={{
                p: 1,
                borderRadius: 0.75,
                backgroundColor: 'success.light',
                border: '1px solid',
                borderColor: 'success.main',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                <Icon name="lightbulb" sx={{ fontSize: '0.875rem', color: 'success.main' }} />
                <Typography fontWeight={600} sx={{ fontSize: '0.8rem' }} color="success.dark">
                  Suggestion:
                </Typography>
              </Box>
              <Typography color="text.secondary" sx={{ fontSize: '0.85rem', pl: 2 }}>
                {issue.suggestion}
              </Typography>
            </Box>
          )}
        </Box>
      </Collapse>
    </Box>
  );
};

/**
 * ATSScoreDisplay Component
 *
 * Displays comprehensive ATS optimization score with:
 * - Overall score visualization with progress bar
 * - Keywords found and missing analysis
 * - Issues list with severity and suggestions
 * - Sections analyzed breakdown
 * - Recalculate functionality
 *
 * @example
 * ```tsx
 * <ATSScoreDisplay
 *   scoreData={atsScore}
 *   loading={isCalculating}
 *   onRecalculate={() => calculateATSScore()}
 *   showDetails={true}
 * />
 * ```
 */
const ATSScoreDisplay: React.FC<ATSScoreDisplayProps> = ({
  scoreData,
  loading = false,
  error = null,
  title = 'ATS Optimization Score',
  showRecalculate = true,
  onRecalculate,
  disabled = false,
  compact = false,
  showDetails = true,
  maxIssues = 10,
}) => {
  const [expandedIssues, setExpandedIssues] = React.useState<Set<number>>(new Set());
  const [showAllIssues, setShowAllIssues] = React.useState(false);

  /**
   * Toggle issue expansion
   */
  const toggleIssueExpanded = (index: number) => {
    setExpandedIssues((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
            <CircularProgress size={48} />
            <Typography sx={{ mt: 2 }} color="text.secondary">
              Analyzing ATS compatibility...
            </Typography>
            <Typography color="text.secondary" sx={{ fontSize: '0.875rem', mt: 1 }}>
              This may take a few seconds
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert
            severity="error"
            action={
              showRecalculate && onRecalculate && (
                <Button color="inherit" size="small" onClick={onRecalculate} disabled={disabled}>
                  Retry
                </Button>
              )
            }
          >
            {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  /**
   * Render empty state
   */
  if (!scoreData) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Icon name="file-search" sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography color="text.primary" fontWeight={600}>
              No ATS Score Available
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              Add content to your resume to calculate the ATS score.
            </Typography>
            {showRecalculate && onRecalculate && (
              <Button
                variant="outlined"
                startIcon={<Icon name="refresh-cw" />}
                onClick={onRecalculate}
                disabled={disabled}
                sx={{ mt: 2 }}
              >
                Calculate Score
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>
    );
  }

  const scoreColor = getScoreColor(scoreData.score);
  const scoreLevel = getScoreLevelLabel(scoreData.score);
  const passed = scoreData.score >= 60;

  // Group issues by severity
  const issuesBySeverity = React.useMemo(() => {
    const high = scoreData.issues.filter((i) => i.severity === 'high');
    const medium = scoreData.issues.filter((i) => i.severity === 'medium');
    const low = scoreData.issues.filter((i) => i.severity === 'low');
    return { high, medium, low };
  }, [scoreData.issues]);

  const displayIssues = showAllIssues
    ? scoreData.issues
    : scoreData.issues.slice(0, maxIssues);
  const hasMoreIssues = scoreData.issues.length > maxIssues;

  return (
    <Card>
      <CardContent>
        {/* Header Section */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            mb: 2,
            flexWrap: 'wrap',
            gap: 1,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Icon name="file-check" sx={{ color: 'primary.main' }} />
            <Typography fontWeight={600}>{title}</Typography>
            <Chip
              label={passed ? 'Passed' : 'Failed'}
              size="small"
              color={passed ? 'success' : 'error'}
              variant="outlined"
            />
          </Box>

          {showRecalculate && onRecalculate && (
            <Button
              size="small"
              variant="outlined"
              startIcon={<Icon name="refresh-cw" />}
              onClick={onRecalculate}
              disabled={disabled || loading}
            >
              Recalculate
            </Button>
          )}
        </Box>

        {/* Main Score Section */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Box
              sx={{
                position: 'relative',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <CircularProgress
                variant="determinate"
                value={scoreData.score}
                size={100}
                thickness={6}
                color={scoreColor}
              />
              <Box
                sx={{
                  top: 0,
                  left: 0,
                  bottom: 0,
                  right: 0,
                  position: 'absolute',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Typography
                  variant="h4"
                  fontWeight={700}
                  color={`${scoreColor}.main`}
                >
                  {scoreData.score}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  / 100
                </Typography>
              </Box>
            </Box>

            <Box sx={{ flex: 1 }}>
              <Typography
                variant="h6"
                fontWeight={600}
                color={`${scoreColor}.main`}
              >
                {scoreLevel}
              </Typography>
              <Typography color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                {passed
                  ? 'Your resume is likely to pass ATS screening.'
                  : 'Your resume needs improvement to pass ATS screening.'}
              </Typography>
              <Typography color="text.secondary" sx={{ fontSize: '0.75rem', mt: 0.5 }}>
                Threshold: 60% to pass
              </Typography>
            </Box>
          </Box>

          <LinearProgress
            variant="determinate"
            value={scoreData.score}
            color={scoreColor}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {/* Quick Stats Grid */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={6} sm={3}>
            <ScoreCard
              label="Issues"
              value={scoreData.issues.length}
              icon="alert-triangle"
              color={scoreData.issues.length === 0 ? 'success' : scoreData.issues.length <= 3 ? 'warning' : 'error'}
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <ScoreCard
              label="Keywords Found"
              value={scoreData.keywords_found.length}
              icon="tag"
              color="primary"
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <ScoreCard
              label="Keywords Missing"
              value={scoreData.keywords_missing.length}
              icon="x-circle"
              color={scoreData.keywords_missing.length === 0 ? 'success' : 'error'}
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <ScoreCard
              label="Sections Analyzed"
              value={scoreData.sections_analyzed.length}
              icon="layout"
              color="primary"
            />
          </Grid>
        </Grid>

        {showDetails && (
          <>
            <Divider sx={{ my: 2 }} />

            {/* Keywords Found */}
            {scoreData.keywords_found.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Icon name="check-circle" color="success" sx={{ fontSize: '1rem' }} />
                  <Typography variant="subtitle2">Keywords Found</Typography>
                  <Chip
                    label={scoreData.keywords_found.length}
                    size="small"
                    color="success"
                    variant="outlined"
                    sx={{ height: 20, fontSize: '0.65rem' }}
                  />
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {scoreData.keywords_found.map((keyword, index) => (
                    <Chip
                      key={index}
                      label={keyword}
                      size="small"
                      color="success"
                      variant="outlined"
                      sx={{ fontSize: '0.75rem' }}
                    />
                  ))}
                </Box>
              </Box>
            )}

            {/* Keywords Missing */}
            {scoreData.keywords_missing.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Icon name="x-circle" color="error" sx={{ fontSize: '1rem' }} />
                  <Typography variant="subtitle2">Keywords Missing</Typography>
                  <Chip
                    label={scoreData.keywords_missing.length}
                    size="small"
                    color="error"
                    variant="outlined"
                    sx={{ height: 20, fontSize: '0.65rem' }}
                  />
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {scoreData.keywords_missing.map((keyword, index) => (
                    <Tooltip key={index} title="Consider adding this keyword to your resume" arrow>
                      <Chip
                        label={keyword}
                        size="small"
                        color="error"
                        variant="outlined"
                        sx={{ fontSize: '0.75rem' }}
                      />
                    </Tooltip>
                  ))}
                </Box>
              </Box>
            )}

            {/* Issues Summary */}
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Icon name="alert-triangle" color="warning" sx={{ fontSize: '1rem' }} />
                <Typography variant="subtitle2">Issues by Severity</Typography>
              </Box>
              <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
                {issuesBySeverity.high.length > 0 && (
                  <Chip
                    icon={<Icon name="alert-circle" sx={{ fontSize: '0.875rem' }} />}
                    label={`${issuesBySeverity.high.length} High`}
                    size="small"
                    color="error"
                    variant="outlined"
                  />
                )}
                {issuesBySeverity.medium.length > 0 && (
                  <Chip
                    icon={<Icon name="alert-triangle" sx={{ fontSize: '0.875rem' }} />}
                    label={`${issuesBySeverity.medium.length} Medium`}
                    size="small"
                    color="warning"
                    variant="outlined"
                  />
                )}
                {issuesBySeverity.low.length > 0 && (
                  <Chip
                    icon={<Icon name="info" sx={{ fontSize: '0.875rem' }} />}
                    label={`${issuesBySeverity.low.length} Low`}
                    size="small"
                    color="info"
                    variant="outlined"
                  />
                )}
                {scoreData.issues.length === 0 && (
                  <Chip
                    icon={<Icon name="check-circle" sx={{ fontSize: '0.875rem' }} />}
                    label="No issues found"
                    size="small"
                    color="success"
                    variant="outlined"
                  />
                )}
              </Stack>
            </Box>

            {/* Issues List */}
            {scoreData.issues.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Detailed Issues
                </Typography>
                <Stack spacing={1}>
                  {displayIssues.map((issue, index) => (
                    <IssueItem
                      key={index}
                      issue={issue}
                      expanded={expandedIssues.has(index)}
                      onToggle={() => toggleIssueExpanded(index)}
                      compact={compact}
                    />
                  ))}
                </Stack>

                {hasMoreIssues && !showAllIssues && (
                  <Box sx={{ mt: 2, textAlign: 'center' }}>
                    <Button
                      variant="text"
                      size="small"
                      onClick={() => setShowAllIssues(true)}
                    >
                      Show all {scoreData.issues.length} issues
                    </Button>
                  </Box>
                )}
              </Box>
            )}

            {/* Sections Analyzed */}
            {scoreData.sections_analyzed.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Icon name="layout" color="primary" sx={{ fontSize: '1rem' }} />
                  <Typography variant="subtitle2">Sections Analyzed</Typography>
                </Box>
                <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap' }}>
                  {scoreData.sections_analyzed.map((section, index) => (
                    <Chip
                      key={index}
                      label={getSectionLabel(section)}
                      size="small"
                      color="primary"
                      variant="outlined"
                      sx={{ fontSize: '0.75rem' }}
                    />
                  ))}
                </Stack>
              </Box>
            )}

            {/* Analysis Timestamp */}
            {scoreData.analyzed_at && (
              <Box sx={{ textAlign: 'right', mt: 2 }}>
                <Typography color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                  Analyzed: {new Date(scoreData.analyzed_at).toLocaleString()}
                </Typography>
              </Box>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * Compact ATS Score Badge Component
 */
interface ATSScoreBadgeProps {
  score: number;
  showLabel?: boolean;
}

export const ATSScoreBadge: React.FC<ATSScoreBadgeProps> = ({ score, showLabel = false }) => {
  const color = getScoreChipColor(score);
  const passed = score >= 60;

  return (
    <Tooltip
      title={
        showLabel
          ? `ATS Score: ${score}%. ${passed ? 'Passed' : 'Failed'} threshold (60%)`
          : `ATS Score: ${score}%`
      }
      arrow
    >
      <Chip
        icon={passed ? <Icon name="check-circle" /> : <Icon name="x-circle" />}
        label={`${score}%`}
        color={color}
        size="small"
        variant={passed ? 'filled' : 'outlined'}
      />
    </Tooltip>
  );
};

export default ATSScoreDisplay;
