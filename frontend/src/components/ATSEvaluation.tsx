/**
 * ATS (Applicant Tracking System) Evaluation Component
 *
 * Displays comprehensive ATS simulation results showing how a resume
 * would be evaluated by commercial ATS systems.
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Stack,
  Divider,
  Grid,
  LinearProgress,
  Alert,
  AlertTitle,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Collapse,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as PassedIcon,
  Cancel as FailedIcon,
  Warning as WarningIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Visibility as VisualIcon,
  VisibilityOff as VisualOffIcon,
  Psychology as LLMIcon,
  Rule as RuleIcon,
} from '@mui/icons-material';
import type { ATSEvaluationResponse } from '@/types/api';

interface ATSEvaluationProps {
  result: ATSEvaluationResponse;
}

/**
 * Get score color based on value
 */
function getScoreColor(score: number): 'success' | 'warning' | 'error' {
  if (score >= 0.7) return 'success';
  if (score >= 0.5) return 'warning';
  return 'error';
}

/**
 * Get score chip color
 */
function getScoreChipColor(score: number):
  | 'success'
  | 'warning'
  | 'error'
  | 'default' {
  if (score >= 0.7) return 'success';
  if (score >= 0.5) return 'warning';
  if (score > 0) return 'error';
  return 'default';
}

/**
 * Score Card Component
 */
interface ScoreCardProps {
  title: string;
  score: number;
  icon: React.ReactNode;
  description?: string;
}

function ScoreCard({ title, score, icon, description }: ScoreCardProps) {
  const { t } = useTranslation();
  const percentage = Math.round(score * 100);
  const color = getScoreColor(score);

  return (
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
        {icon}
      </Box>
      <Typography variant="h4" color={`${color}.main`}>
        {percentage}%
      </Typography>
      <Typography variant="caption" color="text.secondary" gutterBottom>
        {title}
      </Typography>
      {description && (
        <Typography variant="caption" color="text.secondary">
          {description}
        </Typography>
      )}
      <LinearProgress
        variant="determinate"
        value={percentage}
        color={color}
        sx={{ mt: 'auto', pt: 1 }}
      />
    </Paper>
  );
}

/**
 * Expandable Section Component
 */
interface ExpandableSectionProps {
  title: string;
  icon: React.ReactNode;
  itemCount: number;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  color?: 'success' | 'warning' | 'error' | 'info' | 'default';
}

function ExpandableSection({
  title,
  icon,
  itemCount,
  children,
  defaultExpanded = false,
  color = 'default',
}: ExpandableSectionProps) {
  const [expanded, setExpanded] = React.useState(defaultExpanded);

  return (
    <Paper sx={{ p: 2 }}>
      <Box
        display="flex"
        alignItems="center"
        justifyContent="space-between"
        onClick={() => setExpanded(!expanded)}
        sx={{ cursor: 'pointer' }}
      >
        <Box display="flex" alignItems="center" gap={1}>
          {icon}
          <Typography variant="subtitle2">
            {title} {itemCount > 0 && `(${itemCount})`}
          </Typography>
        </Box>
        <IconButton size="small">
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        <Box sx={{ mt: 2 }}>
          {children}
        </Box>
      </Collapse>
    </Paper>
  );
}

/**
 * ATS Evaluation Component
 */
export function ATSEvaluation({ result }: ATSEvaluationProps) {
  const { t } = useTranslation();

  const {
    passed,
    overall_score,
    keyword_score,
    experience_score,
    education_score,
    fit_score,
    looks_professional,
    disqualified,
    visual_issues,
    ats_issues,
    missing_keywords,
    suggestions,
    feedback,
    provider,
    model,
    processing_time_ms,
  } = result;

  const isLLM = provider !== 'rule_based';
  const overallColor = getScoreColor(overall_score);

  return (
    <Stack spacing={3}>
      {/* Main Status Alert */}
      <Alert
        severity={disqualified ? 'error' : passed ? 'success' : 'warning'}
        icon={disqualified ? <FailedIcon /> : passed ? <PassedIcon /> : <WarningIcon />}
      >
        <AlertTitle>
          {disqualified
            ? t('ats.disqualified', { defaultValue: 'Resume Disqualified' })
            : passed
              ? t('ats.passed', { defaultValue: 'Resume Passed ATS Check' })
              : t('ats.failed', { defaultValue: 'Resume Did Not Pass ATS Check' })}
        </AlertTitle>
        <Typography variant="body2">
          {feedback}
        </Typography>
      </Alert>

      {/* Score Metrics Grid */}
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <ScoreCard
            title={t('ats.overallScore', { defaultValue: 'Overall Score' })}
            score={overall_score}
            icon={disqualified ? <FailedIcon color="error" /> : passed ? <PassedIcon color="success" /> : <WarningIcon color="warning" />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <ScoreCard
            title={t('ats.keywordScore', { defaultValue: 'Keyword Match' })}
            score={keyword_score}
            icon={<Typography variant="h6" color="action">#</Typography>}
            description={t('ats.keywordScoreDesc', { defaultValue: 'Required skills found' })}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <ScoreCard
            title={t('ats.experienceScore', { defaultValue: 'Experience' })}
            score={experience_score}
            icon={<Typography variant="h6" color="action">📅</Typography>}
            description={t('ats.experienceScoreDesc', { defaultValue: 'Relevant experience' })}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <ScoreCard
            title={t('ats.fitScore', { defaultValue: 'Overall Fit' })}
            score={fit_score}
            icon={<Typography variant="h6" color="action">🎯</Typography>}
            description={t('ats.fitScoreDesc', { defaultValue: 'Job fit assessment' })}
          />
        </Grid>
      </Grid>

      {/* Education Score (if applicable) */}
      {education_score > 0 && (
        <Paper sx={{ p: 2 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Typography variant="subtitle2">
              {t('ats.educationScore', { defaultValue: 'Education Match' })}
            </Typography>
            <Box display="flex" alignItems="center" gap={1} minWidth={150}>
              <LinearProgress
                variant="determinate"
                value={education_score * 100}
                color={getScoreColor(education_score)}
                sx={{ flexGrow: 1 }}
              />
              <Typography variant="body2" color="text.secondary" minWidth={40} textAlign="right">
                {Math.round(education_score * 100)}%
              </Typography>
            </Box>
          </Box>
        </Paper>
      )}

      {/* Visual/Professional Check */}
      <Paper sx={{ p: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6}>
            <Box display="flex" alignItems="center" gap={1}>
              {looks_professional ? (
                <VisualIcon color="success" />
              ) : (
                <VisualOffIcon color="error" />
              )}
              <Typography variant="subtitle2">
                {t('ats.professionalAppearance', { defaultValue: 'Professional Appearance' })}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Chip
              label={looks_professional
                ? t('ats.passed', { defaultValue: 'Passed' })
                : t('ats.failed', { defaultValue: 'Failed' })
              }
              color={looks_professional ? 'success' : 'error'}
              size="small"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Missing Keywords */}
      {missing_keywords.length > 0 && (
        <ExpandableSection
          title={t('ats.missingKeywords', { defaultValue: 'Missing Keywords' })}
          icon={<WarningIcon color="error" />}
          itemCount={missing_keywords.length}
          defaultExpanded
          color="error"
        >
          <Box flexWrap="wrap" display="flex">
            {missing_keywords.map((keyword) => (
              <Chip
                key={keyword}
                label={keyword}
                color="error"
                size="small"
                sx={{ m: 0.5 }}
              />
            ))}
          </Box>
        </ExpandableSection>
      )}

      {/* Visual/Format Issues */}
      {visual_issues.length > 0 && (
        <ExpandableSection
          title={t('ats.visualIssues', { defaultValue: 'Visual/Format Issues' })}
          icon={<WarningIcon color="warning" />}
          itemCount={visual_issues.length}
          color="warning"
        >
          <List dense>
            {visual_issues.map((issue, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <WarningIcon color="warning" fontSize="small" />
                </ListItemIcon>
                <ListItemText primary={issue} />
              </ListItem>
            ))}
          </List>
        </ExpandableSection>
      )}

      {/* ATS-Specific Issues */}
      {ats_issues.length > 0 && (
        <ExpandableSection
          title={t('ats.atsIssues', { defaultValue: 'ATS-Specific Issues' })}
          icon={<WarningIcon color="error" />}
          itemCount={ats_issues.length}
          color="error"
        >
          <List dense>
            {ats_issues.map((issue, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <FailedIcon color="error" fontSize="small" />
                </ListItemIcon>
                <ListItemText primary={issue} />
              </ListItem>
            ))}
          </List>
        </ExpandableSection>
      )}

      {/* Suggestions for Improvement */}
      {suggestions.length > 0 && (
        <ExpandableSection
          title={t('ats.suggestions', { defaultValue: 'Suggestions for Improvement' })}
          icon={<Typography variant="h6">💡</Typography>}
          itemCount={suggestions.length}
          defaultExpanded
          color="info"
        >
          <List dense>
            {suggestions.map((suggestion, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <Typography sx={{ color: 'info.main', fontWeight: 'bold' }}>
                    {index + 1}
                  </Typography>
                </ListItemIcon>
                <ListItemText primary={suggestion} />
              </ListItem>
            ))}
          </List>
        </ExpandableSection>
      )}

      {/* Evaluation Info Card */}
      <Card variant="outlined">
        <CardContent sx={{ py: 1 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm>
              <Box display="flex" alignItems="center" gap={1}>
                {isLLM ? (
                  <Tooltip title={t('ats.llmTooltip', { defaultValue: 'Evaluated using LLM-based analysis' })}>
                    <LLMIcon fontSize="small" color="action" />
                  </Tooltip>
                ) : (
                  <Tooltip title={t('ats.ruleTooltip', { defaultValue: 'Evaluated using rule-based analysis' })}>
                    <RuleIcon fontSize="small" color="action" />
                  </Tooltip>
                )}
                <Typography variant="caption" color="text.secondary">
                  {isLLM
                    ? `${provider} / ${model}`
                    : t('ats.ruleBased', { defaultValue: 'Rule-based evaluation' })
                  }
                </Typography>
              </Box>
            </Grid>
            <Grid item>
              <Typography variant="caption" color="text.secondary">
                {t('ats.processingTime', {
                  defaultValue: '{{ms}}ms',
                  ms: Math.round(processing_time_ms),
                })}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Threshold Info */}
      <Alert severity="info" variant="outlined">
        <AlertTitle>{t('ats.thresholdInfo', { defaultValue: 'About ATS Scoring' })}</AlertTitle>
        <Typography variant="body2">
          {t('ats.thresholdDesc', {
            defaultValue: 'Resumes scoring {{threshold}}% or higher pass the ATS check. Scores are based on keyword matching, experience relevance, education requirements, and overall fit assessment.',
            threshold: 60,
          })}
        </Typography>
      </Alert>
    </Stack>
  );
}

/**
 * Compact ATS Score Badge Component
 */
interface ATSScoreBadgeProps {
  result: ATSEvaluationResponse;
  showDetails?: boolean;
}

export function ATSScoreBadge({ result, showDetails = false }: ATSScoreBadgeProps) {
  const { t } = useTranslation();
  const percentage = Math.round(result.overall_score * 100);
  const color = getScoreChipColor(result.overall_score);

  return (
    <Tooltip
      title={
        showDetails
          ? `${t('ats.keywordScore', { defaultValue: 'Keywords' })}: ${Math.round(result.keyword_score * 100)}%, ` +
            `${t('ats.experienceScore', { defaultValue: 'Experience' })}: ${Math.round(result.experience_score * 100)}%, ` +
            `${t('ats.fitScore', { defaultValue: 'Fit' })}: ${Math.round(result.fit_score * 100)}%`
          : t('ats.atsScore', { defaultValue: 'ATS Score' })
      }
    >
      <Chip
        icon={result.passed ? <PassedIcon /> : <FailedIcon />}
        label={`${percentage}%`}
        color={color}
        size={showDetails ? 'medium' : 'small'}
        variant={result.passed ? 'filled' : 'outlined'}
      />
    </Tooltip>
  );
}

export default ATSEvaluation;
