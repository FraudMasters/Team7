/**
 * Ranking Weight Slider Card Component
 *
 * A reusable card component for adjusting ranking feature weights.
 * Displays a slider, percentage value, and description for each ranking feature.
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Slider,
  Chip,
  Tooltip,
  IconButton,
  Collapse,
  Alert,
  Grid,
  Stack,
  Button,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';

export type RankingFeatureType =
  | 'overall_match_score'
  | 'keyword_score'
  | 'tfidf_score'
  | 'vector_score'
  | 'skills_match_ratio'
  | 'experience_months'
  | 'experience_relevance'
  | 'education_level'
  | 'recent_experience'
  | 'skill_rarity'
  | 'title_similarity'
  | 'freshness_score'
  | 'completeness_score';

export interface RankingWeightSliderCardProps {
  /** Type of ranking feature */
  type: RankingFeatureType;
  /** Current weight value (0-100) */
  value: number;
  /** Callback when value changes */
  onChange: (value: number) => void;
  /** Whether the slider is disabled */
  disabled?: boolean;
  /** Show preset indicator */
  isPreset?: boolean;
  /** Preset name if applicable */
  presetName?: string;
}

const FEATURE_CONFIG: Record<
  RankingFeatureType,
  {
    icon: React.ReactNode;
    color: string;
    labelKey: string;
    descriptionKey: string;
    explanationKey: string;
    examplesKey: string;
  }
> = {
  overall_match_score: {
    icon: <Icon name="target" size={20} />,
    color: '#4CAF50',
    labelKey: 'rankingWeights.overall_match_score.label',
    descriptionKey: 'rankingWeights.overall_match_score.description',
    explanationKey: 'rankingWeights.overall_match_score.explanation',
    examplesKey: 'rankingWeights.overall_match_score.examples',
  },
  keyword_score: {
    icon: <Icon name="search" size={20} />,
    color: '#2196F3',
    labelKey: 'rankingWeights.keyword_score.label',
    descriptionKey: 'rankingWeights.keyword_score.description',
    explanationKey: 'rankingWeights.keyword_score.explanation',
    examplesKey: 'rankingWeights.keyword_score.examples',
  },
  tfidf_score: {
    icon: <Icon name="bar-chart-2" size={20} />,
    color: '#FF9800',
    labelKey: 'rankingWeights.tfidf_score.label',
    descriptionKey: 'rankingWeights.tfidf_score.description',
    explanationKey: 'rankingWeights.tfidf_score.explanation',
    examplesKey: 'rankingWeights.tfidf_score.examples',
  },
  vector_score: {
    icon: <Icon name="brain" size={20} />,
    color: '#9C27B0',
    labelKey: 'rankingWeights.vector_score.label',
    descriptionKey: 'rankingWeights.vector_score.description',
    explanationKey: 'rankingWeights.vector_score.explanation',
    examplesKey: 'rankingWeights.vector_score.examples',
  },
  skills_match_ratio: {
    icon: <Icon name="check-circle" size={20} />,
    color: '#00BCD4',
    labelKey: 'rankingWeights.skills_match_ratio.label',
    descriptionKey: 'rankingWeights.skills_match_ratio.description',
    explanationKey: 'rankingWeights.skills_match_ratio.explanation',
    examplesKey: 'rankingWeights.skills_match_ratio.examples',
  },
  experience_months: {
    icon: <Icon name="calendar" size={20} />,
    color: '#3F51B5',
    labelKey: 'rankingWeights.experience_months.label',
    descriptionKey: 'rankingWeights.experience_months.description',
    explanationKey: 'rankingWeights.experience_months.explanation',
    examplesKey: 'rankingWeights.experience_months.examples',
  },
  experience_relevance: {
    icon: <Icon name="trending-up" size={20} />,
    color: '#673AB7',
    labelKey: 'rankingWeights.experience_relevance.label',
    descriptionKey: 'rankingWeights.experience_relevance.description',
    explanationKey: 'rankingWeights.experience_relevance.explanation',
    examplesKey: 'rankingWeights.experience_relevance.examples',
  },
  education_level: {
    icon: <Icon name="book" size={20} />,
    color: '#009688',
    labelKey: 'rankingWeights.education_level.label',
    descriptionKey: 'rankingWeights.education_level.description',
    explanationKey: 'rankingWeights.education_level.explanation',
    examplesKey: 'rankingWeights.education_level.examples',
  },
  recent_experience: {
    icon: <Icon name="clock" size={20} />,
    color: '#795548',
    labelKey: 'rankingWeights.recent_experience.label',
    descriptionKey: 'rankingWeights.recent_experience.description',
    explanationKey: 'rankingWeights.recent_experience.explanation',
    examplesKey: 'rankingWeights.recent_experience.examples',
  },
  skill_rarity: {
    icon: <Icon name="star" size={20} />,
    color: '#FFC107',
    labelKey: 'rankingWeights.skill_rarity.label',
    descriptionKey: 'rankingWeights.skill_rarity.description',
    explanationKey: 'rankingWeights.skill_rarity.explanation',
    examplesKey: 'rankingWeights.skill_rarity.examples',
  },
  title_similarity: {
    icon: <Icon name="briefcase" size={20} />,
    color: '#607D8B',
    labelKey: 'rankingWeights.title_similarity.label',
    descriptionKey: 'rankingWeights.title_similarity.description',
    explanationKey: 'rankingWeights.title_similarity.explanation',
    examplesKey: 'rankingWeights.title_similarity.examples',
  },
  freshness_score: {
    icon: <Icon name="zap" size={20} />,
    color: '#E91E63',
    labelKey: 'rankingWeights.freshness_score.label',
    descriptionKey: 'rankingWeights.freshness_score.description',
    explanationKey: 'rankingWeights.freshness_score.explanation',
    examplesKey: 'rankingWeights.freshness_score.examples',
  },
  completeness_score: {
    icon: <Icon name="file-text" size={20} />,
    color: '#8BC34A',
    labelKey: 'rankingWeights.completeness_score.label',
    descriptionKey: 'rankingWeights.completeness_score.description',
    explanationKey: 'rankingWeights.completeness_score.explanation',
    examplesKey: 'rankingWeights.completeness_score.examples',
  },
};

// Default labels for each feature (fallback if translation missing)
const DEFAULT_LABELS: Record<RankingFeatureType, string> = {
  overall_match_score: 'Overall Match Score',
  keyword_score: 'Keyword Matching',
  tfidf_score: 'TF-IDF Relevance',
  vector_score: 'Semantic Similarity',
  skills_match_ratio: 'Skills Match Ratio',
  experience_months: 'Total Experience',
  experience_relevance: 'Relevant Experience',
  education_level: 'Education Level',
  recent_experience: 'Recent Activity',
  skill_rarity: 'Skill Rarity',
  title_similarity: 'Title Similarity',
  freshness_score: 'Profile Freshness',
  completeness_score: 'Profile Completeness',
};

/**
 * Ranking Weight Slider Card Component
 */
export default function RankingWeightSliderCard({
  type,
  value,
  onChange,
  disabled = false,
  isPreset = false,
  presetName = '',
}: RankingWeightSliderCardProps) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = React.useState(false);

  const config = FEATURE_CONFIG[type];

  const handleSliderChange = (_: Event, newValue: number | number[]) => {
    onChange(typeof newValue === 'number' ? newValue : (newValue[0] ?? 0));
  };

  const handleIncrement = () => {
    if (value < 100) {
      onChange(value + 5);
    }
  };

  const handleDecrement = () => {
    if (value > 0) {
      onChange(value - 5);
    }
  };

  const getColorClass = () => {
    if (value >= 60) return 'success';
    if (value >= 30) return 'warning';
    return 'error';
  };

  return (
    <Card
      sx={{
        height: '100%',
        transition: 'all 0.3s ease',
        border: `2px solid ${config.color}20`,
        '&:hover': {
          boxShadow: `0 4px 20px ${config.color}30`,
          transform: 'translateY(-2px)',
        },
      }}
    >
      <CardHeader
        avatar={
          <Box
            sx={{
              backgroundColor: `${config.color}20`,
              color: config.color,
              width: 48,
              height: 48,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 2,
            }}
          >
            {config.icon}
          </Box>
        }
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6">
              {t(config.labelKey, {
                defaultValue: DEFAULT_LABELS[type],
              })}
            </Typography>
            {isPreset && (
              <Chip
                label={presetName || t('rankingWeights.preset', { defaultValue: 'Preset' })}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
          </Box>
        }
        subheader={t(config.descriptionKey, {
          defaultValue: 'Weighted importance in ranking score',
        })}
        action={
          <Tooltip title={t('rankingWeights.showDetails', { defaultValue: 'Show Details' })}>
            <IconButton
              onClick={() => setExpanded(!expanded)}
              size="small"
            >
              {expanded ? <Icon name="chevron-up" size={20} /> : <Icon name="chevron-down" size={20} />}
            </IconButton>
          </Tooltip>
        }
      />

      <CardContent>
        <Stack direction="column" spacing={3}>
          {/* Current Value Display */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h3" sx={{ color: config.color, fontWeight: 'bold' }}>
              {value}%
            </Typography>
            <Chip
              label={t(`rankingWeights.level.${getColorClass()}`, {
                defaultValue: getColorClass() === 'success' ? 'High' :
                getColorClass() === 'warning' ? 'Medium' : 'Low',
              })}
              color={getColorClass() as 'success' | 'warning' | 'error'}
              size="small"
            />
          </Box>

          {/* Slider */}
          <Box sx={{ px: 1 }}>
            <Slider
              value={value}
              onChange={handleSliderChange}
              disabled={disabled}
              sx={{
                color: config.color,
                height: 8,
                '& .MuiSlider-thumb': {
                  width: 24,
                  height: 24,
                },
                '& .MuiSlider-rail': {
                  backgroundColor: `${config.color}30`,
                },
              }}
              valueLabelDisplay="auto"
              valueLabelFormat={(v) => `${v}%`}
            />
          </Box>

          {/* Quick Adjust Buttons */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
            <Button
              size="small"
              variant="outlined"
              onClick={handleDecrement}
              disabled={disabled || value === 0}
              sx={{ minWidth: 40 }}
            >
              -
            </Button>
            <Button
              size="small"
              variant="outlined"
              onClick={handleIncrement}
              disabled={disabled || value === 100}
              sx={{ minWidth: 40 }}
            >
              +
            </Button>
          </Box>

          {/* Explanation (Collapsible) */}
          <Collapse in={expanded}>
            <Box sx={{ mt: 2 }}>
              <Alert
                severity="info"
                icon={<Icon name="info" size="small" />}
                sx={{
                  backgroundColor: `${config.color}10`,
                  '& .MuiAlert-icon': {
                    color: config.color,
                  },
                }}
              >
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {t(config.explanationKey, {
                    defaultValue: 'Explanation of how this ranking feature works...',
                  })}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  <strong>{t('rankingWeights.examples', { defaultValue: 'Examples:' })}</strong>{' '}
                  {t(config.examplesKey, {
                    defaultValue: 'Use cases for this ranking feature...',
                  })}
                </Typography>
              </Alert>
            </Box>
          </Collapse>
        </Stack>
      </CardContent>
    </Card>
  );
}

/**
 * Props for the RankingWeightSliderCardStack component
 */
export interface RankingWeightSliderCardStackProps {
  /** Current weight values for all 13 ranking features */
  weights: {
    overall_match_score: number;
    keyword_score: number;
    tfidf_score: number;
    vector_score: number;
    skills_match_ratio: number;
    experience_months: number;
    experience_relevance: number;
    education_level: number;
    recent_experience: number;
    skill_rarity: number;
    title_similarity: number;
    freshness_score: number;
    completeness_score: number;
  };
  /** Callback when any weight changes */
  onWeightChange: (type: RankingFeatureType, value: number) => void;
  /** Whether sliders are disabled */
  disabled?: boolean;
  /** Preset information */
  presetInfo?: {
    type?: string;
    name?: string;
  };
}

/**
 * Ranking Weight Slider Card Stack Component
 *
 * Renders all thirteen ranking weight slider cards in a responsive grid.
 */
export function RankingWeightSliderCardStack({
  weights,
  onWeightChange,
  disabled = false,
  presetInfo,
}: RankingWeightSliderCardStackProps) {
  const features: RankingFeatureType[] = [
    'overall_match_score',
    'keyword_score',
    'tfidf_score',
    'vector_score',
    'skills_match_ratio',
    'experience_months',
    'experience_relevance',
    'education_level',
    'recent_experience',
    'skill_rarity',
    'title_similarity',
    'freshness_score',
    'completeness_score',
  ];

  return (
    <Grid container spacing={3}>
      {features.map((feature) => (
        <Grid item xs={12} sm={6} md={4} lg={3} key={feature}>
          <RankingWeightSliderCard
            type={feature}
            value={weights[feature]}
            onChange={(v) => onWeightChange(feature, v)}
            disabled={disabled}
            isPreset={presetInfo?.type === feature}
            presetName={presetInfo?.type === feature ? presetInfo.name : undefined}
          />
        </Grid>
      ))}
    </Grid>
  );
}
