/**
 * Weight Slider Card Component
 *
 * A reusable card component for adjusting matching algorithm weights.
 * Displays a slider, percentage value, and description for each matching method.
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
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Info as InfoIcon,
  Tune as TuneIcon,
  Search as KeywordIcon,
  Analytics as TfidfIcon,
  Psychology as VectorIcon,
} from '@mui/icons-material';

export interface WeightSliderCardProps {
  /** Type of matching method */
  type: 'keyword' | 'tfidf' | 'vector';
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

const METHOD_CONFIG = {
  keyword: {
    icon: <KeywordIcon />,
    color: '#2196F3' as const, // Blue
    labelKey: 'matchingWeights.keyword.label',
    descriptionKey: 'matchingWeights.keyword.description',
    explanationKey: 'matchingWeights.keyword.explanation',
    examplesKey: 'matchingWeights.keyword.examples',
  },
  tfidf: {
    icon: <TfidfIcon />,
    color: '#FF9800' as const, // Orange
    labelKey: 'matchingWeights.tfidf.label',
    descriptionKey: 'matchingWeights.tfidf.description',
    explanationKey: 'matchingWeights.tfidf.explanation',
    examplesKey: 'matchingWeights.tfidf.examples',
  },
  vector: {
    icon: <VectorIcon />,
    color: '#9C27B0' as const, // Purple
    labelKey: 'matchingWeights.vector.label',
    descriptionKey: 'matchingWeights.vector.description',
    explanationKey: 'matchingWeights.vector.explanation',
    examplesKey: 'matchingWeights.vector.examples',
  },
};

/**
 * Weight Slider Card Component
 */
export default function WeightSliderCard({
  type,
  value,
  onChange,
  disabled = false,
  isPreset = false,
  presetName = '',
}: WeightSliderCardProps) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = React.useState(false);

  const config = METHOD_CONFIG[type];

  const handleSliderChange = (_: Event, newValue: number | number[]) => {
    onChange(typeof newValue === 'number' ? newValue : newValue[0]);
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
                defaultValue: type === 'keyword' ? 'Keyword Matching' :
                type === 'tfidf' ? 'TF-IDF Matching' : 'Vector Similarity',
              })}
            </Typography>
            {isPreset && (
              <Chip
                label={presetName || t('matchingWeights.preset', { defaultValue: 'Preset' })}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
          </Box>
        }
        subheader={t(config.descriptionKey, {
          defaultValue: 'Weighted importance in overall score',
        })}
        action={
          <Tooltip title={t('matchingWeights.showDetails', { defaultValue: 'Show Details' })}>
            <IconButton
              onClick={() => setExpanded(!expanded)}
              size="small"
            >
              {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
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
              label={t(`matchingWeights.level.${getColorClass()}`, {
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
                icon={<InfoIcon />}
                sx={{
                  backgroundColor: `${config.color}10`,
                  '& .MuiAlert-icon': {
                    color: config.color,
                  },
                }}
              >
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {t(config.explanationKey, {
                    defaultValue: 'Explanation of how this matching method works...',
                  })}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  <strong>{t('matchingWeights.examples', { defaultValue: 'Examples:' })}</strong>{' '}
                  {t(config.examplesKey, {
                    defaultValue: 'Use cases for this matching method...',
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
 * Props for the WeightSliderCardStack component
 */
export interface WeightSliderCardStackProps {
  /** Current weight values */
  weights: {
    keyword: number;
    tfidf: number;
    vector: number;
  };
  /** Callback when any weight changes */
  onWeightChange: (type: 'keyword' | 'tfidf' | 'vector', value: number) => void;
  /** Whether sliders are disabled */
  disabled?: boolean;
  /** Preset information */
  presetInfo?: {
    type?: 'keyword' | 'tfidf' | 'vector' | 'custom';
    name?: string;
  };
}

/**
 * Weight Slider Card Stack Component
 *
 * Renders all three weight slider cards in a responsive grid.
 */
export function WeightSliderCardStack({
  weights,
  onWeightChange,
  disabled = false,
  presetInfo,
}: WeightSliderCardStackProps) {
  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={4}>
        <WeightSliderCard
          type="keyword"
          value={weights.keyword}
          onChange={(v) => onWeightChange('keyword', v)}
          disabled={disabled}
          isPreset={presetInfo?.type === 'keyword'}
          presetName={presetInfo?.type === 'keyword' ? presetInfo.name : undefined}
        />
      </Grid>
      <Grid item xs={12} md={4}>
        <WeightSliderCard
          type="tfidf"
          value={weights.tfidf}
          onChange={(v) => onWeightChange('tfidf', v)}
          disabled={disabled}
          isPreset={presetInfo?.type === 'tfidf'}
          presetName={presetInfo?.type === 'tfidf' ? presetInfo.name : undefined}
        />
      </Grid>
      <Grid item xs={12} md={4}>
        <WeightSliderCard
          type="vector"
          value={weights.vector}
          onChange={(v) => onWeightChange('vector', v)}
          disabled={disabled}
          isPreset={presetInfo?.type === 'vector'}
          presetName={presetInfo?.type === 'vector' ? presetInfo.name : undefined}
        />
      </Grid>
    </Grid>
  );
}
