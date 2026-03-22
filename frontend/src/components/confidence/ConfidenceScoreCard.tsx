import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Chip,
  Stack,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as HighConfidenceIcon,
  Warning as MediumConfidenceIcon,
  Error as LowConfidenceIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

/**
 * Confidence level thresholds
 */
const CONFIDENCE_THRESHOLDS = {
  HIGH: 80,
  MEDIUM: 50,
} as const;

/**
 * Confidence score data
 */
export interface ConfidenceScore {
  /** Candidate ID */
  candidateId: string;
  /** Candidate name */
  candidateName: string;
  /** Confidence score (0-100) */
  confidence: number;
  /** Optional rank score (0-1) */
  rankScore?: number;
  /** Optional rank position */
  rankPosition?: number;
  /** Optional model name */
  model?: string;
}

/**
 * ConfidenceScoreCard Component Props
 */
export interface ConfidenceScoreCardProps {
  /** Confidence score data */
  confidence: ConfidenceScore;
  /** Whether the card is in a loading state */
  loading?: boolean;
  /** Optional click handler */
  onClick?: () => void;
  /** Optional size variant */
  size?: 'small' | 'medium' | 'large';
}

/**
 * Get confidence level category based on score
 */
const getConfidenceLevel = (
  confidence: number
): 'high' | 'medium' | 'low' => {
  if (confidence >= CONFIDENCE_THRESHOLDS.HIGH) return 'high';
  if (confidence >= CONFIDENCE_THRESHOLDS.MEDIUM) return 'medium';
  return 'low';
};

/**
 * Get color for confidence level
 */
const getConfidenceColor = (
  level: 'high' | 'medium' | 'low'
): 'success' | 'warning' | 'error' => {
  switch (level) {
    case 'high':
      return 'success';
    case 'medium':
      return 'warning';
    case 'low':
      return 'error';
  }
};

/**
 * Get icon for confidence level
 */
const getConfidenceIcon = (level: 'high' | 'medium' | 'low') => {
  switch (level) {
    case 'high':
      return <HighConfidenceIcon />;
    case 'medium':
      return <MediumConfidenceIcon />;
    case 'low':
      return <LowConfidenceIcon />;
  }
};

/**
 * Get size values for circular progress
 */
const getSizeValues = (size: 'small' | 'medium' | 'large') => {
  switch (size) {
    case 'small':
      return { circularSize: 80, thickness: 4, fontSize: '1rem' };
    case 'medium':
      return { circularSize: 120, thickness: 5, fontSize: '1.5rem' };
    case 'large':
      return { circularSize: 160, thickness: 6, fontSize: '2rem' };
  }
};

/**
 * ConfidenceScoreCard Component
 *
 * Displays AI confidence score for a candidate ranking with visual indicators:
 * - Circular progress gauge showing confidence percentage (0-100%)
 * - Color-coded display: green (high ≥80%), yellow (medium 50-79%), red (low <50%)
 * - Confidence level chip with icon
 * - Candidate name and optional rank information
 * - Tooltip with interpretation guidance
 *
 * @example
 * ```tsx
 * <ConfidenceScoreCard
 *   confidence={{
 *     candidateId: 'abc-123',
 *     candidateName: 'John Doe',
 *     confidence: 85,
 *     rankScore: 0.92,
 *     rankPosition: 2,
 *   }}
 *   size="medium"
 * />
 * ```
 */
const ConfidenceScoreCard: React.FC<ConfidenceScoreCardProps> = ({
  confidence,
  loading = false,
  onClick,
  size = 'medium',
}) => {
  const { t } = useTranslation();

  const confidenceLevel = getConfidenceLevel(confidence.confidence);
  const confidenceColor = getConfidenceColor(confidenceLevel);
  const confidenceIcon = getConfidenceIcon(confidenceLevel);
  const { circularSize, thickness, fontSize } = getSizeValues(size);

  /**
   * Get interpretation text for confidence level
   */
  const getInterpretation = () => {
    switch (confidenceLevel) {
      case 'high':
        return t('confidence.interpretation.high', {
          defaultValue:
            'High confidence - AI ranking is reliable and well-supported by data.',
        });
      case 'medium':
        return t('confidence.interpretation.medium', {
          defaultValue:
            'Medium confidence - AI ranking is reasonable but may benefit from manual review.',
        });
      case 'low':
        return t('confidence.interpretation.low', {
          defaultValue:
            'Low confidence - Manual review recommended. Limited data or high uncertainty.',
        });
    }
  };

  return (
    <Card
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s',
        '&:hover': onClick
          ? {
              boxShadow: 4,
              transform: 'translateY(-2px)',
            }
          : {},
      }}
      onClick={onClick}
    >
      <CardContent>
        <Stack spacing={2}>
          {/* Header: Candidate name */}
          <Box>
            <Typography variant="h6" gutterBottom>
              {confidence.candidateName}
            </Typography>
            {confidence.rankPosition !== undefined && (
              <Typography variant="body2" color="text.secondary">
                {t('confidence.rankPosition', {
                  defaultValue: 'Rank #{{position}}',
                  position: confidence.rankPosition,
                })}
              </Typography>
            )}
          </Box>

          {/* Circular progress gauge */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              position: 'relative',
              my: 2,
            }}
          >
            {loading ? (
              <CircularProgress size={circularSize} />
            ) : (
              <>
                <CircularProgress
                  variant="determinate"
                  value={confidence.confidence}
                  size={circularSize}
                  thickness={thickness}
                  color={confidenceColor}
                  sx={{
                    circle: {
                      strokeLinecap: 'round',
                    },
                  }}
                />
                <Box
                  sx={{
                    position: 'absolute',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Typography
                    variant="h4"
                    component="div"
                    color={`${confidenceColor}.main`}
                    sx={{ fontSize }}
                  >
                    {Math.round(confidence.confidence)}%
                  </Typography>
                </Box>
              </>
            )}
          </Box>

          {/* Confidence level indicator */}
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Tooltip title={getInterpretation()} arrow>
              <Chip
                icon={confidenceIcon}
                label={t(`confidence.level.${confidenceLevel}`, {
                  defaultValue:
                    confidenceLevel.charAt(0).toUpperCase() +
                    confidenceLevel.slice(1),
                })}
                color={confidenceColor}
                size={size === 'small' ? 'small' : 'medium'}
              />
            </Tooltip>
          </Box>

          {/* Additional info */}
          {confidence.rankScore !== undefined && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {t('confidence.rankScore', { defaultValue: 'Rank Score:' })}
              </Typography>
              <Typography variant="body2" fontWeight="medium">
                {(confidence.rankScore * 100).toFixed(1)}%
              </Typography>
            </Box>
          )}

          {confidence.model && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
                justifyContent: 'center',
              }}
            >
              <InfoIcon fontSize="small" color="action" />
              <Typography variant="caption" color="text.secondary">
                {t('confidence.model', {
                  defaultValue: 'Model: {{model}}',
                  model: confidence.model,
                })}
              </Typography>
            </Box>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};

export default ConfidenceScoreCard;
