/**
 * Completeness Score Component
 *
 * Displays resume completeness score with visual progress indicators
 * for each section, highlighting missing or incomplete content.
 */

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  LinearProgress,
  Chip,
  Grid,
  Paper,
  Divider,
  Tooltip,
  Alert,
  AlertTitle,
  CircularProgress,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';

/**
 * Resume section completeness data
 */
export interface SectionCompleteness {
  /** Section name/identifier */
  section: string;
  /** Display label for the section */
  label: string;
  /** Completeness percentage (0-100) */
  completeness: number;
  /** Whether the section is required */
  required: boolean;
  /** Whether the section exists in resume */
  exists: boolean;
  /** Missing fields or suggestions */
  missing_items?: string[];
  /** Icon name for the section */
  icon?: string;
}

/**
 * CompletenessScore Component Props
 */
export interface CompletenessScoreProps {
  /** Overall completeness percentage (0-100) */
  overallScore: number;
  /** Individual section completeness data */
  sections: SectionCompleteness[];
  /** Component title */
  title?: string;
  /** Component description */
  description?: string;
  /** Show detailed breakdown */
  showDetails?: boolean;
  /** Compact mode */
  compact?: boolean;
  /** Loading state */
  loading?: boolean;
  /** Error message */
  error?: string | null;
}

/**
 * Get completeness color based on percentage
 */
const getCompletenessColor = (percentage: number): 'success' | 'warning' | 'error' => {
  if (percentage >= 80) return 'success';
  if (percentage >= 50) return 'warning';
  return 'error';
};

/**
 * Get completeness level label
 */
const getCompletenessLabel = (percentage: number): string => {
  if (percentage >= 95) return 'Excellent';
  if (percentage >= 80) return 'Very Good';
  if (percentage >= 65) return 'Good';
  if (percentage >= 50) return 'Fair';
  if (percentage >= 30) return 'Needs Work';
  return 'Incomplete';
};

/**
 * Get section icon
 */
const getSectionIcon = (section: string, customIcon?: string): string => {
  if (customIcon) return customIcon;

  const iconMap: Record<string, string> = {
    personal_info: 'user',
    contact: 'mail',
    summary: 'file-text',
    work_experience: 'briefcase',
    education: 'book',
    skills: 'code',
    certifications: 'award',
    languages: 'globe',
    projects: 'folder',
    achievements: 'star',
    references: 'users',
  };

  return iconMap[section] || 'file';
};

/**
 * Section Completeness Row Component
 */
interface SectionRowProps {
  section: SectionCompleteness;
  compact: boolean;
}

const SectionRow: React.FC<SectionRowProps> = ({ section, compact }) => {
  const [expanded, setExpanded] = React.useState(false);
  const color = getCompletenessColor(section.completeness);
  const icon = getSectionIcon(section.section, section.icon);

  const hasMissingItems = section.missing_items && section.missing_items.length > 0;

  return (
    <Card variant="outlined" sx={{ mb: 1.5 }}>
      <CardContent sx={{ p: compact ? 1.5 : 2, '&:last-child': { pb: compact ? 1.5 : 2 } }}>
        <Grid container spacing={2} alignItems="center">
          {/* Icon and Title */}
          <Grid item xs={12} sm={4}>
            <Stack direction="row" alignItems="center" spacing={1}>
              <Box
                sx={{
                  p: 1,
                  borderRadius: 1,
                  bgcolor: section.exists ? `${color}.light` : 'grey.200',
                  color: section.exists ? `${color}.dark` : 'grey.600',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Icon name={icon} sx={{ fontSize: '1.25rem' }} />
              </Box>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="subtitle2" fontWeight={600} noWrap>
                  {section.label}
                </Typography>
                <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }}>
                  {section.required && (
                    <Chip
                      label="Required"
                      size="small"
                      color="primary"
                      variant="outlined"
                      sx={{ height: 18, fontSize: '0.65rem' }}
                    />
                  )}
                  {!section.exists && (
                    <Chip
                      label="Missing"
                      size="small"
                      color="error"
                      variant="filled"
                      sx={{ height: 18, fontSize: '0.65rem' }}
                    />
                  )}
                </Stack>
              </Box>
            </Stack>
          </Grid>

          {/* Progress Bar */}
          <Grid item xs={12} sm={6}>
            <Stack spacing={0.5}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="caption" color="text.secondary">
                  {section.exists ? 'Completeness' : 'Not Added'}
                </Typography>
                <Typography variant="body2" fontWeight={600} color={`${color}.main`}>
                  {section.completeness}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={section.completeness}
                color={color}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  bgcolor: 'grey.200',
                }}
              />
            </Stack>
          </Grid>

          {/* Action Button */}
          <Grid item xs={12} sm={2}>
            <Box sx={{ textAlign: 'right' }}>
              {hasMissingItems && (
                <Tooltip title={expanded ? 'Hide details' : 'Show missing items'} arrow>
                  <Chip
                    icon={<Icon name={expanded ? 'chevron-up' : 'chevron-down'} sx={{ fontSize: '0.875rem' }} />}
                    label={`${section.missing_items!.length} missing`}
                    size="small"
                    color="warning"
                    variant="outlined"
                    onClick={() => setExpanded(!expanded)}
                    sx={{ cursor: 'pointer', fontSize: '0.75rem' }}
                  />
                </Tooltip>
              )}
              {!hasMissingItems && section.completeness === 100 && (
                <Chip
                  icon={<Icon name="check-circle" sx={{ fontSize: '0.875rem' }} />}
                  label="Complete"
                  size="small"
                  color="success"
                  variant="outlined"
                  sx={{ fontSize: '0.75rem' }}
                />
              )}
            </Box>
          </Grid>
        </Grid>

        {/* Expanded Missing Items */}
        {expanded && hasMissingItems && (
          <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
              <Icon name="alert-circle" color="warning" sx={{ fontSize: '1rem' }} />
              <Typography variant="subtitle2" fontWeight={600}>
                Missing or Incomplete:
              </Typography>
            </Box>
            <Stack spacing={0.5}>
              {section.missing_items!.map((item, index) => (
                <Box
                  key={index}
                  sx={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 1,
                    pl: 1,
                  }}
                >
                  <Icon name="circle" sx={{ fontSize: '0.5rem', mt: 0.75, color: 'warning.main' }} />
                  <Typography variant="body2" color="text.secondary">
                    {item}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * CompletenessScore Component
 *
 * Visualizes resume completeness with:
 * - Overall completeness score with circular progress
 * - Individual section progress bars
 * - Color-coded indicators (green=complete, yellow=partial, red=missing)
 * - Expandable missing items for each section
 * - Required vs optional section indicators
 *
 * @example
 * ```tsx
 * const sections = [
 *   {
 *     section: 'personal_info',
 *     label: 'Personal Information',
 *     completeness: 100,
 *     required: true,
 *     exists: true,
 *   },
 *   {
 *     section: 'work_experience',
 *     label: 'Work Experience',
 *     completeness: 60,
 *     required: true,
 *     exists: true,
 *     missing_items: ['Add 2+ more years of experience', 'Include quantifiable achievements'],
 *   },
 * ];
 * <CompletenessScore
 *   overallScore={75}
 *   sections={sections}
 *   showDetails={true}
 * />
 * ```
 */
const CompletenessScore: React.FC<CompletenessScoreProps> = ({
  overallScore,
  sections,
  title = 'Resume Completeness',
  description = 'Track your resume progress and ensure all important sections are complete',
  showDetails = true,
  compact = false,
  loading = false,
  error = null,
}) => {
  const scoreColor = getCompletenessColor(overallScore);
  const scoreLabel = getCompletenessLabel(overallScore);

  /**
   * Calculate section statistics
   */
  const sectionStats = React.useMemo(() => {
    const total = sections.length;
    const complete = sections.filter((s) => s.completeness === 100).length;
    const partial = sections.filter((s) => s.completeness > 0 && s.completeness < 100).length;
    const missing = sections.filter((s) => !s.exists).length;
    const required = sections.filter((s) => s.required).length;
    const requiredComplete = sections.filter((s) => s.required && s.completeness === 100).length;

    return { total, complete, partial, missing, required, requiredComplete };
  }, [sections]);

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
              Analyzing resume completeness...
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
          <Alert severity="error">
            <AlertTitle>Error</AlertTitle>
            {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          <Icon name="clipboard-check" color="primary" />
          <Typography variant="h5" fontWeight={700}>
            {title}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      </Box>

      {/* Overall Score Card */}
      <Paper
        elevation={2}
        sx={{
          p: 3,
          bgcolor: 'background.default',
          border: '2px solid',
          borderColor: 'divider',
        }}
      >
        <Grid container spacing={3} alignItems="center">
          {/* Circular Progress */}
          <Grid item xs={12} sm={4}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
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
                  value={overallScore}
                  size={compact ? 100 : 120}
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
                    variant={compact ? 'h4' : 'h3'}
                    fontWeight={700}
                    color={`${scoreColor}.main`}
                  >
                    {overallScore}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Complete
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Grid>

          {/* Score Details */}
          <Grid item xs={12} sm={8}>
            <Stack spacing={2}>
              <Box>
                <Typography variant="h6" fontWeight={600} color={`${scoreColor}.main`} gutterBottom>
                  {scoreLabel}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {overallScore >= 80
                    ? 'Your resume is well-structured and comprehensive.'
                    : overallScore >= 50
                    ? 'Your resume is on the right track. Add more details to strengthen it.'
                    : 'Your resume needs more content. Focus on completing required sections.'}
                </Typography>
              </Box>

              {/* Stats */}
              <Grid container spacing={1}>
                <Grid item xs={6}>
                  <Paper variant="outlined" sx={{ p: 1, textAlign: 'center' }}>
                    <Typography variant="h6" fontWeight={700} color="success.main">
                      {sectionStats.complete}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Complete Sections
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper variant="outlined" sx={{ p: 1, textAlign: 'center' }}>
                    <Typography variant="h6" fontWeight={700} color="warning.main">
                      {sectionStats.partial}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Partial Sections
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper variant="outlined" sx={{ p: 1, textAlign: 'center' }}>
                    <Typography variant="h6" fontWeight={700} color="error.main">
                      {sectionStats.missing}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Missing Sections
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper variant="outlined" sx={{ p: 1, textAlign: 'center' }}>
                    <Typography variant="h6" fontWeight={700} color="primary.main">
                      {sectionStats.requiredComplete}/{sectionStats.required}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Required Done
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Stack>
          </Grid>
        </Grid>
      </Paper>

      {showDetails && (
        <>
          <Divider />

          {/* Required Sections Alert */}
          {sectionStats.requiredComplete < sectionStats.required && (
            <Alert severity="warning">
              <AlertTitle>Required Sections Incomplete</AlertTitle>
              You have {sectionStats.required - sectionStats.requiredComplete} required section
              {sectionStats.required - sectionStats.requiredComplete !== 1 ? 's' : ''} to complete.
              Focus on these first for a strong resume foundation.
            </Alert>
          )}

          {/* Section Breakdown */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <Icon name="list" color="primary" />
              <Typography variant="h6" fontWeight={600}>
                Section Breakdown
              </Typography>
              <Chip
                label={`${sections.length} sections`}
                size="small"
                color="primary"
                variant="outlined"
                sx={{ fontSize: '0.7rem' }}
              />
            </Box>

            <Stack spacing={0}>
              {sections.map((section, index) => (
                <SectionRow key={index} section={section} compact={compact} />
              ))}
            </Stack>
          </Box>

          {/* Tips */}
          {overallScore < 80 && (
            <Alert severity="info">
              <AlertTitle>Tips to Improve Completeness</AlertTitle>
              <Box component="ul" sx={{ m: 0, pl: 2 }}>
                {sectionStats.missing > 0 && (
                  <li>
                    <Typography variant="body2">
                      Add {sectionStats.missing} missing section{sectionStats.missing !== 1 ? 's' : ''} to your
                      resume
                    </Typography>
                  </li>
                )}
                {sectionStats.partial > 0 && (
                  <li>
                    <Typography variant="body2">
                      Complete {sectionStats.partial} partially filled section
                      {sectionStats.partial !== 1 ? 's' : ''}
                    </Typography>
                  </li>
                )}
                <li>
                  <Typography variant="body2">
                    Focus on required sections first, then enhance with optional sections
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Include specific details, metrics, and achievements in each section
                  </Typography>
                </li>
              </Box>
            </Alert>
          )}
        </>
      )}
    </Stack>
  );
};

export default CompletenessScore;
