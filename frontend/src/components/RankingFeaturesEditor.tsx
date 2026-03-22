import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Typography,
  Stack,
  Slider,
  Alert,
  Grid,
} from '@mui/material';

/**
 * Ranking feature weights interface
 */
export interface RankingFeatureWeights {
  skill_match_weight: number;
  experience_weight: number;
  education_weight: number;
  location_weight: number;
  keyword_weight: number;
  tfidf_weight: number;
  vector_weight: number;
  recency_weight: number;
  culture_fit_weight: number;
  salary_match_weight: number;
  availability_weight: number;
  certifications_weight: number;
  industry_experience_weight: number;
}

/**
 * Weight field configuration
 */
interface WeightFieldConfig {
  key: keyof RankingFeatureWeights;
  label: string;
  description: string;
  color: string;
}

/**
 * Configuration for all 13 weight fields
 */
const WEIGHT_FIELDS: WeightFieldConfig[] = [
  {
    key: 'skill_match_weight',
    label: 'Skill Matching',
    description: 'Match between required skills and candidate skills',
    color: 'primary.main',
  },
  {
    key: 'experience_weight',
    label: 'Experience',
    description: 'Years of experience and seniority level',
    color: 'secondary.main',
  },
  {
    key: 'education_weight',
    label: 'Education',
    description: 'Educational background and degrees',
    color: 'info.main',
  },
  {
    key: 'location_weight',
    label: 'Location',
    description: 'Geographic location and remote work compatibility',
    color: 'success.main',
  },
  {
    key: 'keyword_weight',
    label: 'Keyword Matching',
    description: 'Exact keyword and phrase matching',
    color: 'warning.main',
  },
  {
    key: 'tfidf_weight',
    label: 'TF-IDF Matching',
    description: 'Term frequency-inverse document frequency',
    color: 'error.main',
  },
  {
    key: 'vector_weight',
    label: 'Vector Similarity',
    description: 'Semantic vector embeddings similarity',
    color: 'primary.dark',
  },
  {
    key: 'recency_weight',
    label: 'Recency',
    description: 'Recent activity and profile updates',
    color: 'secondary.dark',
  },
  {
    key: 'culture_fit_weight',
    label: 'Culture Fit',
    description: 'Alignment with company culture and values',
    color: 'info.dark',
  },
  {
    key: 'salary_match_weight',
    label: 'Salary Expectations',
    description: 'Match between expected and offered salary',
    color: 'success.dark',
  },
  {
    key: 'availability_weight',
    label: 'Availability',
    description: 'Candidate availability and start date',
    color: 'warning.dark',
  },
  {
    key: 'certifications_weight',
    label: 'Certifications',
    description: 'Professional certifications and licenses',
    color: 'error.dark',
  },
  {
    key: 'industry_experience_weight',
    label: 'Industry Experience',
    description: 'Experience in relevant industries',
    color: 'text.secondary',
  },
];

/**
 * Default weights that sum to 1.0
 */
export const DEFAULT_RANKING_WEIGHTS: RankingFeatureWeights = {
  skill_match_weight: 0.25,
  experience_weight: 0.15,
  education_weight: 0.10,
  location_weight: 0.05,
  keyword_weight: 0.10,
  tfidf_weight: 0.10,
  vector_weight: 0.10,
  recency_weight: 0.05,
  culture_fit_weight: 0.05,
  salary_match_weight: 0.02,
  availability_weight: 0.01,
  certifications_weight: 0.01,
  industry_experience_weight: 0.01,
};

/**
 * RankingFeaturesEditor Component Props
 */
interface RankingFeaturesEditorProps {
  /** Current weight values */
  weights: RankingFeatureWeights;
  /** Callback when weights change */
  onChange: (weights: RankingFeatureWeights) => void;
  /** Whether the editor is disabled */
  disabled?: boolean;
  /** Show total validation alert */
  showValidation?: boolean;
}

/**
 * RankingFeaturesEditor Component
 *
 * Provides an interface for editing all 13 ranking feature weights with
 * automatic normalization to ensure weights sum to 100%.
 *
 * Features:
 * - 13 weight sliders with labels and descriptions
 * - Auto-normalization on every change
 * - Visual feedback showing current percentages
 * - Optional total validation display
 * - Organized in a 2-column grid for better UX
 *
 * @example
 * ```tsx
 * const [weights, setWeights] = useState(DEFAULT_RANKING_WEIGHTS);
 *
 * <RankingFeaturesEditor
 *   weights={weights}
 *   onChange={setWeights}
 *   showValidation={true}
 * />
 * ```
 */
const RankingFeaturesEditor: React.FC<RankingFeaturesEditorProps> = ({
  weights,
  onChange,
  disabled = false,
  showValidation = true,
}) => {
  const { t } = useTranslation();

  /**
   * Normalize weights to sum to 1.0
   */
  const normalizeWeights = (updatedWeights: RankingFeatureWeights): RankingFeatureWeights => {
    const total = Object.values(updatedWeights).reduce((sum, weight) => sum + weight, 0);

    if (total === 0) {
      return DEFAULT_RANKING_WEIGHTS;
    }

    const normalized: Partial<RankingFeatureWeights> = {};

    // Normalize each weight
    for (const key in updatedWeights) {
      const typedKey = key as keyof RankingFeatureWeights;
      normalized[typedKey] = Math.round((updatedWeights[typedKey] / total) * 100) / 100;
    }

    return normalized as RankingFeatureWeights;
  };

  /**
   * Handle slider change with auto-normalization
   */
  const handleSliderChange = (field: keyof RankingFeatureWeights, value: number) => {
    const newWeights = { ...weights, [field]: value };
    const normalized = normalizeWeights(newWeights);
    onChange(normalized);
  };

  /**
   * Calculate total percentage for validation
   */
  const totalPercentage = Math.round(
    Object.values(weights).reduce((sum, weight) => sum + weight, 0) * 100
  );

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Ranking Feature Weights (auto-normalized to 100%)
      </Typography>

      {/* Grid layout for better organization */}
      <Grid container spacing={3}>
        {WEIGHT_FIELDS.map((field, index) => (
          <Grid item xs={12} md={6} key={field.key}>
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  {field.label}
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  {Math.round(weights[field.key] * 100)}%
                </Typography>
              </Box>
              <Slider
                value={weights[field.key] * 100}
                onChange={(_, value) => handleSliderChange(field.key, (value as number) / 100)}
                disabled={disabled}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${Math.round(value)}%`}
                sx={{ color: field.color }}
              />
              <Typography variant="caption" color="text.secondary">
                {field.description}
              </Typography>
            </Box>
          </Grid>
        ))}
      </Grid>

      {/* Total Validation */}
      {showValidation && (
        <Alert
          severity={totalPercentage === 100 ? "success" : "info"}
          variant="outlined"
          sx={{ mt: 3 }}
        >
          <Typography variant="body2">
            <strong>Total: {totalPercentage}%</strong>
            {totalPercentage === 100 ? ' ✓' : ' (weights auto-normalized)'}
          </Typography>
          <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
            Skill Match ({Math.round(weights.skill_match_weight * 100)}%) +
            Experience ({Math.round(weights.experience_weight * 100)}%) +
            Education ({Math.round(weights.education_weight * 100)}%) +
            Location ({Math.round(weights.location_weight * 100)}%) +
            Keyword ({Math.round(weights.keyword_weight * 100)}%) +
            TF-IDF ({Math.round(weights.tfidf_weight * 100)}%) +
            Vector ({Math.round(weights.vector_weight * 100)}%) +
            Recency ({Math.round(weights.recency_weight * 100)}%) +
            Culture Fit ({Math.round(weights.culture_fit_weight * 100)}%) +
            Salary ({Math.round(weights.salary_match_weight * 100)}%) +
            Availability ({Math.round(weights.availability_weight * 100)}%) +
            Certifications ({Math.round(weights.certifications_weight * 100)}%) +
            Industry ({Math.round(weights.industry_experience_weight * 100)}%)
          </Typography>
        </Alert>
      )}
    </Box>
  );
};

export default RankingFeaturesEditor;
