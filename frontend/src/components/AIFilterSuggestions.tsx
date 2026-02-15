import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Button,
  TextField,
  CircularProgress,
  Collapse,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import {
  filterSuggestionsClient,
  type FilterSuggestionResponse,
  type SuggestedFilterItem,
} from '@/api/filterSuggestions';

/**
 * AI Filter Suggestions component props
 */
interface AIFilterSuggestionsProps {
  /** Callback when filters are applied */
  onApplyFilters?: (filters: Record<string, unknown>) => void;
  /** Optional vacancy ID to pre-fill */
  vacancyId?: string;
  /** Optional initial job description text */
  initialJobDescription?: string;
  /** Whether the component is disabled */
  disabled?: boolean;
}

/**
 * Confidence level for display purposes
 */
type ConfidenceLevel = 'high' | 'medium' | 'low';

/**
 * Get confidence level from confidence score
 */
const getConfidenceLevel = (confidence: number): ConfidenceLevel => {
  if (confidence >= 0.8) return 'high';
  if (confidence >= 0.5) return 'medium';
  return 'low';
};

/**
 * Get color for confidence chip
 */
const getConfidenceColor = (level: ConfidenceLevel): 'success' | 'warning' | 'error' => {
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
 * Get source label for display
 */
const getSourceLabel = (source: SuggestedFilterItem['source']): string => {
  switch (source) {
    case 'extracted':
      return 'Extracted';
    case 'inferred':
      return 'Inferred';
    case 'synonym':
      return 'Synonym';
    case 'provided':
      return 'Provided';
    default:
      return source;
  }
};

/**
 * AIFilterSuggestions Component
 *
 * Provides AI-powered job description analysis for filter suggestions.
 * Users can paste a job description and get suggested search filters
 * including skills, experience, location, education, and languages.
 *
 * Features:
 * - Job description text input
 * - AI-powered filter suggestion analysis
 * - Preview of suggested filters with confidence scores
 * - One-click apply to search filters
 * - Toggle to expand/collapse suggestions
 *
 * @example
 * ```tsx
 * <AIFilterSuggestions
 *   onApplyFilters={(filters) => {
 *     console.log('Applying filters:', filters);
 *     // Apply to search...
 *   }}
 *   initialJobDescription="Senior Python Developer..."
 * />
 * ```
 */
const AIFilterSuggestions: React.FC<AIFilterSuggestionsProps> = ({
  onApplyFilters,
  initialJobDescription = '',
  disabled = false,
}) => {
  const { t } = useTranslation();

  // Input state
  const [jobDescription, setJobDescription] = useState(initialJobDescription);

  // Analysis state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<FilterSuggestionResponse | null>(null);

  // UI state
  const [expanded, setExpanded] = useState(true);
  const [selectedFilters, setSelectedFilters] = useState<Set<string>>(new Set());

  /**
   * Analyze job description and get filter suggestions
   */
  const handleAnalyze = useCallback(async () => {
    if (!jobDescription.trim()) {
      setError('Please enter a job description to analyze.');
      return;
    }

    setLoading(true);
    setError(null);
    setSuggestions(null);
    setSelectedFilters(new Set());

    try {
      const result = await filterSuggestionsClient.suggestFilters({
        job_description: jobDescription.trim(),
        max_skills: 10,
        min_confidence: 0.3,
      });

      setSuggestions(result);

      // Auto-select all high confidence filters
      const highConfidenceFilters = new Set<string>();
      result.skills.forEach((skill, idx) => {
        if (skill.confidence >= 0.7) {
          highConfidenceFilters.add(`skill-${idx}`);
        }
      });
      if (result.location && result.location.confidence >= 0.7) {
        highConfidenceFilters.add('location');
      }
      if (result.education_level && result.education_level.confidence >= 0.7) {
        highConfidenceFilters.add('education');
      }
      result.languages.forEach((_, idx) => {
        highConfidenceFilters.add(`language-${idx}`);
      });
      setSelectedFilters(highConfidenceFilters);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to analyze job description';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [jobDescription]);

  /**
   * Toggle filter selection
   */
  const toggleFilter = (filterId: string) => {
    const newSelected = new Set(selectedFilters);
    if (newSelected.has(filterId)) {
      newSelected.delete(filterId);
    } else {
      newSelected.add(filterId);
    }
    setSelectedFilters(newSelected);
  };

  /**
   * Apply selected filters to search
   */
  const handleApplyFilters = () => {
    if (!suggestions || !onApplyFilters) return;

    const filters: Record<string, unknown> = {};

    // Add selected skills
    const selectedSkills = suggestions.skills
      .filter((_, idx) => selectedFilters.has(`skill-${idx}`))
      .map((s) => s.value as string);

    if (selectedSkills.length > 0) {
      filters.skills = selectedSkills;
    }

    // Add experience range if selected
    if (suggestions.min_experience_years !== null) {
      filters.minExperienceYears = suggestions.min_experience_years;
    }
    if (suggestions.max_experience_years !== null) {
      filters.maxExperienceYears = suggestions.max_experience_years;
    }

    // Add location if selected
    if (selectedFilters.has('location') && suggestions.location) {
      filters.location = suggestions.location.value;
    }

    // Add education if selected
    if (selectedFilters.has('education') && suggestions.education_level) {
      filters.educationLevel = suggestions.education_level.value;
    }

    // Add selected languages
    const selectedLanguages = suggestions.languages
      .filter((_, idx) => selectedFilters.has(`language-${idx}`))
      .map((l) => l.value as string);

    if (selectedLanguages.length > 0) {
      filters.languages = selectedLanguages;
    }

    // Also use the pre-built search_filters as base and override with selections
    const finalFilters = {
      ...suggestions.search_filters,
      ...filters,
    };

    onApplyFilters(finalFilters);
  };

  /**
   * Clear suggestions and reset
   */
  const handleClear = () => {
    setJobDescription('');
    setSuggestions(null);
    setError(null);
    setSelectedFilters(new Set());
  };

  /**
   * Render a single filter item as a selectable chip
   */
  const renderFilterChip = (
    item: SuggestedFilterItem,
    id: string,
    label?: string
  ) => {
    const isSelected = selectedFilters.has(id);
    const confidenceLevel = getConfidenceLevel(item.confidence);

    return (
      <Chip
        key={id}
        label={label || String(item.value)}
        onClick={() => toggleFilter(id)}
        variant={isSelected ? 'filled' : 'outlined'}
        color={isSelected ? 'primary' : 'default'}
        icon={
          <Icon
            name={isSelected ? 'check' : 'plus'}
            size={16}
          />
        }
        sx={{
          cursor: 'pointer',
          '&:hover': {
            opacity: 0.9,
          },
        }}
        onDelete={undefined}
        deleteIcon={
          <Typography
            variant="caption"
            sx={{
              fontSize: '0.65rem',
              ml: 0.5,
              color: isSelected ? 'inherit' : 'text.secondary',
            }}
          >
            {Math.round(item.confidence * 100)}%
          </Typography>
        }
      />
    );
  };

  /**
   * Render skills section
   */
  const renderSkillsSection = () => {
    if (!suggestions || suggestions.skills.length === 0) return null;

    return (
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" color="secondary" gutterBottom>
          <Icon name="code" size={16} sx={{ mr: 0.5, verticalAlign: 'middle' }} />
          Skills ({suggestions.skills.length} suggested)
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {suggestions.skills.map((skill, idx) =>
            renderFilterChip(skill, `skill-${idx}`, String(skill.value))
          )}
        </Box>
      </Box>
    );
  };

  /**
   * Render experience section
   */
  const renderExperienceSection = () => {
    if (!suggestions) return null;
    if (
      suggestions.min_experience_years === null &&
      suggestions.max_experience_years === null &&
      !suggestions.seniority_level
    ) {
      return null;
    }

    const experienceText = [
      suggestions.min_experience_years !== null && `${suggestions.min_experience_years}+ years`,
      suggestions.seniority_level && suggestions.seniority_level,
    ]
      .filter(Boolean)
      .join(' • ');

    if (!experienceText) return null;

    return (
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" color="secondary" gutterBottom>
          <Icon name="briefcase" size={16} sx={{ mr: 0.5, verticalAlign: 'middle' }} />
          Experience
        </Typography>
        <Chip
          label={experienceText}
          variant="outlined"
          color="info"
          icon={<Icon name="clock" size={16} />}
        />
      </Box>
    );
  };

  /**
   * Render location section
   */
  const renderLocationSection = () => {
    if (!suggestions || !suggestions.location) return null;

    return (
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" color="secondary" gutterBottom>
          <Icon name="map-pin" size={16} sx={{ mr: 0.5, verticalAlign: 'middle' }} />
          Location
        </Typography>
        {renderFilterChip(suggestions.location, 'location')}
      </Box>
    );
  };

  /**
   * Render education section
   */
  const renderEducationSection = () => {
    if (!suggestions || !suggestions.education_level) return null;

    return (
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" color="secondary" gutterBottom>
          <Icon name="graduation-cap" size={16} sx={{ mr: 0.5, verticalAlign: 'middle' }} />
          Education
        </Typography>
        {renderFilterChip(suggestions.education_level, 'education')}
      </Box>
    );
  };

  /**
   * Render languages section
   */
  const renderLanguagesSection = () => {
    if (!suggestions || suggestions.languages.length === 0) return null;

    return (
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" color="secondary" gutterBottom>
          <Icon name="globe" size={16} sx={{ mr: 0.5, verticalAlign: 'middle' }} />
          Languages
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {suggestions.languages.map((lang, idx) =>
            renderFilterChip(lang, `language-${idx}`)
          )}
        </Box>
      </Box>
    );
  };

  /**
   * Render analysis summary
   */
  const renderAnalysisSummary = () => {
    if (!suggestions) return null;

    return (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          mb: 2,
          p: 1.5,
          bgcolor: 'action.hover',
          borderRadius: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Icon name="zap" size={20} color="success" />
          <Typography variant="body2" fontWeight={500}>
            Analysis Complete
          </Typography>
        </Box>
        <Divider orientation="vertical" flexItem />
        <Typography variant="caption" color="secondary">
          {suggestions.skills.length} skills
        </Typography>
        <Typography variant="caption" color="secondary">
          {suggestions.analysis_time_seconds.toFixed(2)}s
        </Typography>
        <Chip
          label={`${Math.round(suggestions.confidence * 100)}% overall confidence`}
          size="small"
          color={getConfidenceColor(getConfidenceLevel(suggestions.confidence))}
          variant="outlined"
        />
      </Box>
    );
  };

  return (
    <Paper elevation={2}>
      {/* Header */}
      <Box
        sx={{
          px: 3,
          py: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Stack direction="row" spacing={2} alignItems="center">
          <Icon name="sparkles" size={24} color="primary" />
          <Box>
            <Typography variant="h6" fontWeight={600}>
              AI Filter Suggestions
            </Typography>
            <Typography variant="caption" color="secondary">
              Paste a job description to get intelligent filter suggestions
            </Typography>
          </Box>
        </Stack>
        <Button
          size="small"
          variant="text"
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
          startIcon={<Icon name={expanded ? 'chevron-up' : 'chevron-down'} />}
        >
          {expanded ? 'Collapse' : 'Expand'}
        </Button>
      </Box>

      <Divider />

      {/* Content */}
      <Collapse in={expanded}>
        <Box sx={{ p: 3 }}>
          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
              <AlertTitle>Analysis Error</AlertTitle>
              {error}
            </Alert>
          )}

          {/* Job Description Input */}
          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              multiline
              rows={6}
              label="Job Description"
              placeholder="Paste a job description here to get AI-powered filter suggestions...

Example:
Senior Python Developer with 5+ years experience in Django and AWS. Must have strong SQL skills and experience with microservices. Remote position, bachelor's degree preferred."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              disabled={disabled || loading}
              helperText="The AI will analyze the job description and suggest relevant search filters"
            />
          </Box>

          {/* Action Buttons */}
          <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
            <Button
              variant="contained"
              onClick={handleAnalyze}
              disabled={disabled || loading || !jobDescription.trim()}
              startIcon={
                loading ? (
                  <CircularProgress size={16} color="inherit" />
                ) : (
                  <Icon name="sparkles" />
                )
              }
            >
              {loading ? 'Analyzing...' : 'Analyze Job Description'}
            </Button>
            {suggestions && (
              <>
                <Button
                  variant="outlined"
                  onClick={handleClear}
                  disabled={loading}
                  startIcon={<Icon name="x" />}
                >
                  Clear
                </Button>
                <Button
                  variant="contained"
                  color="success"
                  onClick={handleApplyFilters}
                  disabled={loading || selectedFilters.size === 0}
                  startIcon={<Icon name="filter" />}
                >
                  Apply {selectedFilters.size} Filters
                </Button>
              </>
            )}
          </Stack>

          {/* Suggestions Preview */}
          {suggestions && (
            <Box>
              {renderAnalysisSummary()}

              <Divider sx={{ mb: 2 }} />

              <Typography variant="subtitle1" fontWeight={500} gutterBottom>
                Suggested Filters
              </Typography>
              <Typography variant="caption" color="secondary" sx={{ display: 'block', mb: 2 }}>
                Click on filters to select/deselect them. Filters with higher confidence are
                pre-selected.
              </Typography>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  {renderSkillsSection()}
                  {renderLanguagesSection()}
                </Grid>
                <Grid item xs={12} md={6}>
                  {renderExperienceSection()}
                  {renderLocationSection()}
                  {renderEducationSection()}
                </Grid>
              </Grid>

              {/* All Filters (Advanced) */}
              {suggestions.all_filters.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Divider sx={{ mb: 2 }} />
                  <Typography variant="subtitle2" color="secondary" gutterBottom>
                    <Icon name="list" size={16} sx={{ mr: 0.5, verticalAlign: 'middle' }} />
                    All Extracted Filters ({suggestions.all_filters.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {suggestions.all_filters.map((filter, idx) => (
                      <Chip
                        key={idx}
                        label={`${filter.filter_type}: ${String(filter.value)}`}
                        size="small"
                        variant="outlined"
                        deleteIcon={
                          <Typography variant="caption" sx={{ fontSize: '0.6rem' }}>
                            {getSourceLabel(filter.source)}
                          </Typography>
                        }
                        onDelete={undefined}
                        sx={{
                          '& .MuiChip-deleteIcon': {
                            color: 'text.secondary',
                          },
                        }}
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </Box>
          )}

          {/* Loading State */}
          {loading && (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                py: 4,
              }}
            >
              <CircularProgress size={48} sx={{ mb: 2 }} />
              <Typography variant="body2" color="secondary">
                Analyzing job description...
              </Typography>
              <Typography variant="caption" color="secondary">
                This may take a few seconds
              </Typography>
            </Box>
          )}

          {/* Empty State */}
          {!loading && !suggestions && !error && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Icon name="file-text" size={48} color="disabled" sx={{ mb: 2 }} />
              <Typography variant="body2" color="secondary">
                Paste a job description above and click "Analyze" to get started
              </Typography>
            </Box>
          )}
        </Box>
      </Collapse>
    </Paper>
  );
};

export default AIFilterSuggestions;
