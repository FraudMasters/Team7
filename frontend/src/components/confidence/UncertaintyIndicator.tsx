import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Alert,
  Box,
  Chip,
  Tooltip,
  Typography,
  Stack,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

/**
 * Uncertainty level thresholds
 */
const UNCERTAINTY_THRESHOLDS = {
  CRITICAL: 30, // Very low confidence, critical uncertainty
  HIGH: 50, // Low confidence, high uncertainty
} as const;

/**
 * Confidence interval data
 */
export interface ConfidenceInterval {
  /** Lower bound of confidence interval (0-100) */
  lower: number;
  /** Upper bound of confidence interval (0-100) */
  upper: number;
  /** Confidence level (e.g., 95 for 95% confidence interval) */
  level?: number;
}

/**
 * UncertaintyIndicator Component Props
 */
export interface UncertaintyIndicatorProps {
  /** Confidence score (0-100) */
  confidence: number;
  /** Optional confidence interval bounds */
  confidenceInterval?: ConfidenceInterval;
  /** Display mode */
  mode?: 'alert' | 'chip' | 'inline';
  /** Optional candidate name for context */
  candidateName?: string;
  /** Whether to show detailed explanation */
  showDetails?: boolean;
  /** Optional custom message */
  customMessage?: string;
}

/**
 * Get uncertainty level based on confidence score
 */
const getUncertaintyLevel = (
  confidence: number
): 'none' | 'high' | 'critical' => {
  if (confidence >= UNCERTAINTY_THRESHOLDS.HIGH) return 'none';
  if (confidence >= UNCERTAINTY_THRESHOLDS.CRITICAL) return 'high';
  return 'critical';
};

/**
 * Get severity for uncertainty level
 */
const getUncertaintySeverity = (
  level: 'none' | 'high' | 'critical'
): 'warning' | 'error' => {
  return level === 'critical' ? 'error' : 'warning';
};

/**
 * Get icon for uncertainty level
 */
const getUncertaintyIcon = (level: 'none' | 'high' | 'critical') => {
  switch (level) {
    case 'critical':
      return <ErrorIcon />;
    case 'high':
      return <WarningIcon />;
    default:
      return <InfoIcon />;
  }
};

/**
 * UncertaintyIndicator Component
 *
 * Displays warning indicators for AI predictions with low confidence scores.
 * Highlights cases where the model is uncertain and manual review is recommended.
 *
 * Features:
 * - Warning badge for confidence < 50%
 * - Critical error badge for confidence < 30%
 * - Tooltip with detailed uncertainty explanation
 * - Optional confidence interval display
 * - Multiple display modes: alert, chip, or inline
 *
 * @example
 * ```tsx
 * // Alert mode for prominent warnings
 * <UncertaintyIndicator
 *   confidence={35}
 *   candidateName="John Doe"
 *   mode="alert"
 *   showDetails
 * />
 *
 * // Chip mode for compact display
 * <UncertaintyIndicator
 *   confidence={45}
 *   mode="chip"
 *   confidenceInterval={{ lower: 35, upper: 55, level: 95 }}
 * />
 *
 * // Inline mode for text integration
 * <UncertaintyIndicator
 *   confidence={25}
 *   mode="inline"
 * />
 * ```
 */
const UncertaintyIndicator: React.FC<UncertaintyIndicatorProps> = ({
  confidence,
  confidenceInterval,
  mode = 'alert',
  candidateName,
  showDetails = false,
  customMessage,
}) => {
  const { t } = useTranslation();

  const uncertaintyLevel = getUncertaintyLevel(confidence);

  // Don't render anything if confidence is adequate
  if (uncertaintyLevel === 'none') {
    return null;
  }

  const severity = getUncertaintySeverity(uncertaintyLevel);
  const icon = getUncertaintyIcon(uncertaintyLevel);

  /**
   * Get explanation text for uncertainty level
   */
  const getExplanation = () => {
    if (customMessage) return customMessage;

    const baseMessage =
      uncertaintyLevel === 'critical'
        ? t('uncertainty.explanation.critical', {
            defaultValue:
              'Very low confidence. The AI model has insufficient data or high uncertainty about this ranking. Strong manual review is required.',
          })
        : t('uncertainty.explanation.high', {
            defaultValue:
              'Low confidence. The AI model is uncertain about this ranking. Manual review is recommended to validate the decision.',
          });

    return baseMessage;
  };

  /**
   * Get short title for uncertainty warning
   */
  const getTitle = () => {
    if (candidateName) {
      return uncertaintyLevel === 'critical'
        ? t('uncertainty.title.criticalWithName', {
            defaultValue: 'Critical Uncertainty: {{name}}',
            name: candidateName,
          })
        : t('uncertainty.title.highWithName', {
            defaultValue: 'Low Confidence: {{name}}',
            name: candidateName,
          });
    }

    return uncertaintyLevel === 'critical'
      ? t('uncertainty.title.critical', {
          defaultValue: 'Critical Uncertainty Detected',
        })
      : t('uncertainty.title.high', {
          defaultValue: 'Low Confidence Warning',
        });
  };

  /**
   * Get tooltip content with detailed information
   */
  const getTooltipContent = () => {
    return (
      <Box>
        <Typography variant="body2" gutterBottom>
          {getExplanation()}
        </Typography>
        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
          {t('uncertainty.confidenceScore', {
            defaultValue: 'Confidence: {{score}}%',
            score: Math.round(confidence),
          })}
        </Typography>
        {confidenceInterval && (
          <Typography variant="caption" display="block">
            {t('uncertainty.confidenceInterval', {
              defaultValue:
                '{{level}}% CI: [{{lower}}%, {{upper}}%]',
              level: confidenceInterval.level || 95,
              lower: Math.round(confidenceInterval.lower),
              upper: Math.round(confidenceInterval.upper),
            })}
          </Typography>
        )}
      </Box>
    );
  };

  // Alert mode - Full alert box
  if (mode === 'alert') {
    return (
      <Alert
        severity={severity}
        icon={icon}
        sx={{
          '& .MuiAlert-message': {
            width: '100%',
          },
        }}
      >
        <Typography variant="subtitle2" fontWeight="medium" gutterBottom>
          {getTitle()}
        </Typography>
        {showDetails && (
          <Stack spacing={1} sx={{ mt: 1 }}>
            <Typography variant="body2">{getExplanation()}</Typography>
            <Box>
              <Typography variant="body2" color="text.secondary">
                {t('uncertainty.confidenceScore', {
                  defaultValue: 'Confidence: {{score}}%',
                  score: Math.round(confidence),
                })}
              </Typography>
              {confidenceInterval && (
                <Typography variant="body2" color="text.secondary">
                  {t('uncertainty.confidenceInterval', {
                    defaultValue:
                      '{{level}}% Confidence Interval: [{{lower}}%, {{upper}}%]',
                    level: confidenceInterval.level || 95,
                    lower: Math.round(confidenceInterval.lower),
                    upper: Math.round(confidenceInterval.upper),
                  })}
                </Typography>
              )}
            </Box>
          </Stack>
        )}
      </Alert>
    );
  }

  // Chip mode - Compact badge with tooltip
  if (mode === 'chip') {
    return (
      <Tooltip title={getTooltipContent()} arrow placement="top">
        <Chip
          icon={icon}
          label={t(`uncertainty.level.${uncertaintyLevel}`, {
            defaultValue:
              uncertaintyLevel === 'critical'
                ? 'Critical Uncertainty'
                : 'Low Confidence',
          })}
          color={severity}
          size="small"
          variant="outlined"
        />
      </Tooltip>
    );
  }

  // Inline mode - Minimal text with icon
  return (
    <Tooltip title={getTooltipContent()} arrow placement="top">
      <Box
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 0.5,
          color: severity === 'error' ? 'error.main' : 'warning.main',
          cursor: 'help',
        }}
      >
        {uncertaintyLevel === 'critical' ? (
          <ErrorIcon fontSize="small" />
        ) : (
          <WarningIcon fontSize="small" />
        )}
        <Typography variant="body2" color="inherit">
          {t(`uncertainty.inline.${uncertaintyLevel}`, {
            defaultValue:
              uncertaintyLevel === 'critical'
                ? 'Critical uncertainty'
                : 'Low confidence',
          })}
        </Typography>
      </Box>
    </Tooltip>
  );
};

export default UncertaintyIndicator;
