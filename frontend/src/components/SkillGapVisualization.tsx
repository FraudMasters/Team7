/**
 * Skill Gap Visualization Component
 *
 * Displays skill gap analysis results with visual indicators for
 * matched, missing, and partial skills.
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
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Cancel as MissingIcon,
  Warning as PartialIcon,
  TrendingUp as BridgeabilityIcon,
  AccessTime as TimeIcon,
} from '@mui/icons-material';
import type { SkillGapAnalysisResponse, MissingSkillDetail } from '@/types/api';

interface SkillGapVisualizationProps {
  analysis: SkillGapAnalysisResponse;
}

/**
 * Get severity color
 */
function getSeverityColor(severity: string): 'error' | 'warning' | 'info' | 'success' {
  switch (severity) {
    case 'critical':
      return 'error';
    case 'moderate':
      return 'warning';
    case 'minimal':
      return 'info';
    case 'none':
      return 'success';
    default:
      return 'info';
  }
}

/**
 * Get severity chip color
 */
function getSeverityChipColor(severity: string):
  | 'error'
  | 'warning'
  | 'default'
  | 'success'
  | 'primary' {
  switch (severity) {
    case 'critical':
      return 'error';
    case 'moderate':
      return 'warning';
    case 'minimal':
      return 'primary';
    case 'none':
      return 'success';
    default:
      return 'default';
  }
}

/**
 * Skill Chip Component
 */
interface SkillChipProps {
  skill: string;
  detail?: MissingSkillDetail;
  type: 'matched' | 'missing' | 'partial';
}

function SkillChip({ skill, detail, type }: SkillChipProps) {
  const { t } = useTranslation();

  if (type === 'matched') {
    return (
      <Chip
        icon={<CheckIcon />}
        label={skill}
        color="success"
        size="small"
        sx={{ m: 0.5 }}
      />
    );
  }

  if (type === 'partial') {
    return (
      <Chip
        icon={<PartialIcon />}
        label={skill}
        color="warning"
        size="small"
        sx={{ m: 0.5 }}
      />
    );
  }

  // Missing skill with detail
  const importance = detail?.importance || 'medium';
  const level = detail?.required_level || '';

  return (
    <Chip
      icon={<MissingIcon />}
      label={`${skill}${level ? ` (${level})` : ''}`}
      color={importance === 'high' ? 'error' : 'default'}
      size="small"
      sx={{ m: 0.5 }}
    />
  );
}

/**
 * Skill Gap Visualization Component
 */
export function SkillGapVisualization({ analysis }: SkillGapVisualizationProps) {
  const { t } = useTranslation();

  const {
    candidate_skills,
    matched_skills,
    missing_skills,
    partial_match_skills,
    missing_skill_details,
    gap_severity,
    gap_percentage,
    bridgeability_score,
    estimated_time_to_bridge,
    priority_ordering,
    processing_time_ms,
  } = analysis;

  const severityColor = getSeverityColor(gap_severity);
  const matchPercentage = 100 - gap_percentage;

  // Format estimated time to human-readable
  function formatTimeToBridge(hours: number): string {
    if (hours < 40) {
      return t('skillGap.daysCount', { count: Math.ceil(hours / 8), defaultValue: '{{count}} days' });
    }
    if (hours < 160) {
      return t('skillGap.weeksCount', { count: Math.ceil(hours / 40), defaultValue: '{{count}} weeks' });
    }
    return t('skillGap.monthsCount', { count: Math.ceil(hours / 160), defaultValue: '{{count}} months' });
  }

  return (
    <Stack spacing={3}>
      {/* Summary Alert */}
      <Alert severity={severityColor}>
        <AlertTitle>
          {t('skillGap.severityTitle', {
            defaultValue: 'Skill Gap: {{severity}}',
            severity: t(`skillGap.severity.${gap_severity}`, { defaultValue: gap_severity })
          })}
        </AlertTitle>
        <Typography variant="body2">
          {t('skillGap.summaryMessage', {
            defaultValue: '{{match}}% of required skills matched. {{missing}} skills missing.',
            match: matchPercentage.toFixed(0),
            missing: missing_skills.length,
          })}
        </Typography>
      </Alert>

      {/* Metrics Grid */}
      <Grid container spacing={2}>
        {/* Match Percentage */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color={matchPercentage >= 70 ? 'success.main' : matchPercentage >= 40 ? 'warning.main' : 'error.main'}>
              {matchPercentage.toFixed(0)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('skillGap.matchPercentage', { defaultValue: 'Skill Match' })}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={matchPercentage}
              color={matchPercentage >= 70 ? 'success' : matchPercentage >= 40 ? 'warning' : 'error'}
              sx={{ mt: 1 }}
            />
          </Paper>
        </Grid>

        {/* Bridgeability Score */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Box display="flex" alignItems="center" justifyContent="center" mb={1}>
              <BridgeabilityIcon color="action" fontSize="small" />
            </Box>
            <Typography variant="h4" color={bridgeability_score > 0.6 ? 'success.main' : bridgeability_score > 0.3 ? 'warning.main' : 'error.main'}>
              {(bridgeability_score * 100).toFixed(0)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('skillGap.bridgeability', { defaultValue: 'Bridgeability' })}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={bridgeability_score * 100}
              color={bridgeability_score > 0.6 ? 'success' : bridgeability_score > 0.3 ? 'warning' : 'error'}
              sx={{ mt: 1 }}
            />
          </Paper>
        </Grid>

        {/* Estimated Time to Bridge */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Box display="flex" alignItems="center" justifyContent="center" mb={1}>
              <TimeIcon color="action" fontSize="small" />
            </Box>
            <Typography variant="h4">
              {formatTimeToBridge(estimated_time_to_bridge)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('skillGap.timeToBridge', { defaultValue: 'Time to Bridge' })}
            </Typography>
          </Paper>
        </Grid>

        {/* Gap Severity */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Chip
              label={t(`skillGap.severity.${gap_severity}`, { defaultValue: gap_severity })}
              color={getSeverityChipColor(gap_severity)}
              sx={{ mb: 1 }}
            />
            <Typography variant="caption" color="text.secondary" display="block">
              {t('skillGap.gapSeverity', { defaultValue: 'Gap Severity' })}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Matched Skills */}
      {matched_skills.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            {t('skillGap.matchedSkills', { defaultValue: 'Matched Skills' })} ({matched_skills.length})
          </Typography>
          <Box flexWrap="wrap" display="flex">
            {matched_skills.map((skill) => (
              <SkillChip key={skill} skill={skill} type="matched" />
            ))}
          </Box>
        </Paper>
      )}

      {/* Partial Match Skills */}
      {partial_match_skills.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            {t('skillGap.partialSkills', { defaultValue: 'Partial Match Skills' })} ({partial_match_skills.length})
          </Typography>
          <Box flexWrap="wrap" display="flex">
            {partial_match_skills.map((skill) => (
              <SkillChip
                key={skill}
                skill={skill}
                detail={missing_skill_details[skill]}
                type="partial"
              />
            ))}
          </Box>
        </Paper>
      )}

      {/* Missing Skills */}
      {missing_skills.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom color="error.main">
            {t('skillGap.missingSkills', { defaultValue: 'Missing Skills' })} ({missing_skills.length})
          </Typography>
          <Box flexWrap="wrap" display="flex">
            {missing_skills.map((skill) => (
              <SkillChip
                key={skill}
                skill={skill}
                detail={missing_skill_details[skill]}
                type="missing"
              />
            ))}
          </Box>
        </Paper>
      )}

      {/* Priority Ordering */}
      {priority_ordering.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            {t('skillGap.recommendedOrder', { defaultValue: 'Recommended Learning Order' })}
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {priority_ordering.map((skill, index) => (
              <Chip
                key={skill}
                label={`${index + 1}. ${skill}`}
                variant="outlined"
                size="small"
                color="primary"
              />
            ))}
          </Stack>
        </Paper>
      )}

      {/* Processing Time */}
      <Typography variant="caption" color="text.secondary" align="center" display="block">
        {t('skillGap.processingTime', {
          defaultValue: 'Analysis completed in {{ms}}ms',
          ms: processing_time_ms.toFixed(0),
        })}
      </Typography>
    </Stack>
  );
}

export default SkillGapVisualization;
