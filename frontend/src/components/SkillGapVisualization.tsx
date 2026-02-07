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
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
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
        iconName="check-circle"
        label={skill}
        color="success"
        size="small"
        css={{ m: 0.5 }}
      />
    );
  }

  if (type === 'partial') {
    return (
      <Chip
        iconName="alert-triangle"
        label={skill}
        color="warning"
        size="small"
        css={{ m: 0.5 }}
      />
    );
  }

  // Missing skill with detail
  const importance = detail?.importance || 'medium';
  const level = detail?.required_level || '';

  return (
    <Chip
      iconName="x-circle"
      label={`${skill}${level ? ` (${level})` : ''}`}
      color={importance === 'high' ? 'error' : 'default'}
      size="small"
      css={{ m: 0.5 }}
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
        <Typography>
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
          <Paper css={{ p: 2, textAlign: 'center' }}>
            <Typography color={matchPercentage >= 70 ? 'success.main' : matchPercentage >= 40 ? 'warning.main' : 'error.main'}>
              {matchPercentage.toFixed(0)}%
            </Typography>
            <Typography color="text.secondary">
              {t('skillGap.matchPercentage', { defaultValue: 'Skill Match' })}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={matchPercentage}
              color={matchPercentage >= 70 ? 'success' : matchPercentage >= 40 ? 'warning' : 'error'}
              css={{ mt: 1 }}
            />
          </Paper>
        </Grid>

        {/* Bridgeability Score */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper css={{ p: 2, textAlign: 'center' }}>
            <Box css={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
              <Icon name="trending-up" />
            </Box>
            <Typography color={bridgeability_score > 0.6 ? 'success.main' : bridgeability_score > 0.3 ? 'warning.main' : 'error.main'}>
              {(bridgeability_score * 100).toFixed(0)}%
            </Typography>
            <Typography color="text.secondary">
              {t('skillGap.bridgeability', { defaultValue: 'Bridgeability' })}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={bridgeability_score * 100}
              color={bridgeability_score > 0.6 ? 'success' : bridgeability_score > 0.3 ? 'warning' : 'error'}
              css={{ mt: 1 }}
            />
          </Paper>
        </Grid>

        {/* Estimated Time to Bridge */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper css={{ p: 2, textAlign: 'center' }}>
            <Box css={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
              <Icon name="clock" />
            </Box>
            <Typography>
              {formatTimeToBridge(estimated_time_to_bridge)}
            </Typography>
            <Typography color="text.secondary">
              {t('skillGap.timeToBridge', { defaultValue: 'Time to Bridge' })}
            </Typography>
          </Paper>
        </Grid>

        {/* Gap Severity */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper css={{ p: 2, textAlign: 'center' }}>
            <Chip
              label={t(`skillGap.severity.${gap_severity}`, { defaultValue: gap_severity })}
              color={getSeverityChipColor(gap_severity)}
              css={{ mb: 1 }}
            />
            <Typography color="text.secondary">
              {t('skillGap.gapSeverity', { defaultValue: 'Gap Severity' })}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Matched Skills */}
      {matched_skills.length > 0 && (
        <Paper css={{ p: 2 }}>
          <Typography>
            {t('skillGap.matchedSkills', { defaultValue: 'Matched Skills' })} ({matched_skills.length})
          </Typography>
          <Box css={{ flexWrap: 'wrap', display: 'flex' }}>
            {matched_skills.map((skill) => (
              <SkillChip key={skill} skill={skill} type="matched" />
            ))}
          </Box>
        </Paper>
      )}

      {/* Partial Match Skills */}
      {partial_match_skills.length > 0 && (
        <Paper css={{ p: 2 }}>
          <Typography>
            {t('skillGap.partialSkills', { defaultValue: 'Partial Match Skills' })} ({partial_match_skills.length})
          </Typography>
          <Box css={{ flexWrap: 'wrap', display: 'flex' }}>
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
        <Paper css={{ p: 2 }}>
          <Typography color="error.main">
            {t('skillGap.missingSkills', { defaultValue: 'Missing Skills' })} ({missing_skills.length})
          </Typography>
          <Box css={{ flexWrap: 'wrap', display: 'flex' }}>
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
        <Paper css={{ p: 2 }}>
          <Typography>
            {t('skillGap.recommendedOrder', { defaultValue: 'Recommended Learning Order' })}
          </Typography>
          <Stack css={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
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
      <Typography color="text.secondary" align="center">
        {t('skillGap.processingTime', {
          defaultValue: 'Analysis completed in {{ms}}ms',
          ms: processing_time_ms.toFixed(0),
        })}
      </Typography>
    </Stack>
  );
}

export default SkillGapVisualization;
