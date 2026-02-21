import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Stack,
  CircularProgress,
  Alert,
  Divider,
  Tooltip,
  Collapse,
  IconButton,
  Button,
  LinearProgress,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import type {
  OptimizationSuggestion,
  OptimizationPriority,
  OptimizationCategory,
} from '@/types/api';

/**
 * AI Suggestion item with additional AI-specific metadata
 */
export interface AISuggestionItem extends OptimizationSuggestion {
  /** Unique identifier for the suggestion */
  id?: string;
  /** Confidence score (0-100) */
  confidence_score?: number;
  /** Whether the suggestion has been applied */
  applied?: boolean;
  /** Auto-applicable flag */
  auto_applicable?: boolean;
  /** Impact prediction */
  impact_prediction?: 'high' | 'medium' | 'low';
  /** Section of resume this applies to */
  target_section?: string;
}

/**
 * AI Suggestions Panel data structure
 */
export interface AISuggestionsData {
  /** Resume ID */
  resume_id: string;
  /** Overall AI score */
  ai_score: number;
  /** List of AI suggestions */
  suggestions: AISuggestionItem[];
  /** Total count */
  total_suggestions: number;
  /** Generation timestamp */
  generated_at?: string;
  /** Model used for suggestions */
  model_used?: string;
}

/**
 * AISuggestionsPanel Component Props
 */
interface AISuggestionsPanelProps {
  /** AI suggestions data */
  suggestionsData: AISuggestionsData | null;
  /** Loading state */
  loading?: boolean;
  /** Error message */
  error?: string | null;
  /** Component title */
  title?: string;
  /** Maximum suggestions to display */
  maxDisplay?: number;
  /** Callback when applying a suggestion */
  onApplySuggestion?: (suggestion: AISuggestionItem) => void;
  /** Callback when dismissing a suggestion */
  onDismissSuggestion?: (suggestion: AISuggestionItem) => void;
  /** Callback to regenerate suggestions */
  onRegenerate?: () => void;
  /** Show regenerate button */
  showRegenerate?: boolean;
  /** Disabled state */
  disabled?: boolean;
  /** Compact mode */
  compact?: boolean;
}

/**
 * Impact level configuration
 */
const getImpactConfig = (impact: 'high' | 'medium' | 'low') => {
  switch (impact) {
    case 'high':
      return {
        label: 'High Impact',
        iconName: 'trending-up',
        color: 'success' as const,
        description: 'Will significantly improve your resume',
      };
    case 'medium':
      return {
        label: 'Medium Impact',
        iconName: 'minus',
        color: 'warning' as const,
        description: 'Will moderately improve your resume',
      };
    case 'low':
      return {
        label: 'Low Impact',
        iconName: 'trending-down',
        color: 'info' as const,
        description: 'Minor improvement suggested',
      };
    default:
      return {
        label: 'Suggestion',
        iconName: 'lightbulb',
        color: 'default' as const,
        description: 'Improvement suggestion',
      };
  }
};

/**
 * Priority configuration for display
 */
const getPriorityConfig = (priority: OptimizationPriority) => {
  switch (priority) {
    case 'high':
      return {
        label: 'High Priority',
        iconName: 'alert-circle',
        color: 'error' as const,
        bgColor: 'error.light' as const,
        description: 'Address this issue first',
      };
    case 'medium':
      return {
        label: 'Medium Priority',
        iconName: 'zap',
        color: 'warning' as const,
        bgColor: 'warning.light' as const,
        description: 'Recommended improvement',
      };
    case 'low':
      return {
        label: 'Low Priority',
        iconName: 'info',
        color: 'info' as const,
        bgColor: 'info.light' as const,
        description: 'Nice to have',
      };
    default:
      return {
        label: 'Suggestion',
        iconName: 'lightbulb',
        color: 'default' as const,
        bgColor: 'grey.100' as const,
        description: 'Improvement suggestion',
      };
  }
};

/**
 * Category icon mapping
 */
const getCategoryIcon = (category: OptimizationCategory): string => {
  const iconMap: Record<OptimizationCategory, string> = {
    keywords: 'tag',
    structure: 'layout',
    readability: 'eye',
    impact: 'trending-up',
    action_verbs: 'zap',
    summary: 'file-text',
    active_language: 'message-square',
    achievements: 'award',
  };
  return iconMap[category] || 'lightbulb';
};

/**
 * Category label mapping
 */
const getCategoryLabel = (category: OptimizationCategory): string => {
  const labelMap: Record<OptimizationCategory, string> = {
    keywords: 'Keywords',
    structure: 'Structure',
    readability: 'Readability',
    impact: 'Impact',
    action_verbs: 'Action Verbs',
    summary: 'Summary',
    active_language: 'Active Language',
    achievements: 'Achievements',
  };
  return labelMap[category] || category;
};

/**
 * Section label mapping
 */
const getSectionLabel = (section: string): string => {
  const sectionLabels: Record<string, string> = {
    summary: 'Professional Summary',
    experience: 'Work Experience',
    education: 'Education',
    skills: 'Skills',
    projects: 'Projects',
    certifications: 'Certifications',
    header: 'Header',
    contact: 'Contact Information',
  };
  return sectionLabels[section] || section;
};

/**
 * Get score color based on value
 */
const getScoreColor = (score: number): 'success' | 'warning' | 'error' => {
  if (score >= 80) return 'success';
  if (score >= 60) return 'warning';
  return 'error';
};

/**
 * Get confidence level label
 */
const getConfidenceLabel = (confidence: number): string => {
  if (confidence >= 90) return 'Very High';
  if (confidence >= 70) return 'High';
  if (confidence >= 50) return 'Medium';
  return 'Low';
};

/**
 * AISuggestionsPanel Component
 *
 * Displays AI-powered resume improvement suggestions with:
 * - Overall AI score visualization with progress bar
 * - Confidence scores for each suggestion
 * - Impact predictions
 * - Apply/dismiss actions
 * - Regenerate functionality
 * - Target section indicators
 *
 * @example
 * ```tsx
 * <AISuggestionsPanel
 *   suggestionsData={aiSuggestions}
 *   loading={isGenerating}
 *   onApplySuggestion={(suggestion) => handleApply(suggestion)}
 *   onRegenerate={() => regenerateSuggestions()}
 * />
 * ```
 */
const AISuggestionsPanel: React.FC<AISuggestionsPanelProps> = ({
  suggestionsData,
  loading = false,
  error = null,
  title = 'AI Improvement Suggestions',
  maxDisplay = 10,
  onApplySuggestion,
  onDismissSuggestion,
  onRegenerate,
  showRegenerate = true,
  disabled = false,
  compact = false,
}) => {
  const [expandedSuggestions, setExpandedSuggestions] = React.useState<Set<number>>(new Set());
  const [filterPriority, setFilterPriority] = React.useState<'all' | OptimizationPriority>('all');
  const [appliedIds, setAppliedIds] = React.useState<Set<string>>(new Set());

  /**
   * Toggle suggestion expansion
   */
  const toggleExpanded = (index: number) => {
    setExpandedSuggestions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  /**
   * Handle applying a suggestion
   */
  const handleApply = (suggestion: AISuggestionItem, index: number) => {
    if (suggestion.id) {
      setAppliedIds((prev) => new Set(prev).add(suggestion.id!));
    }
    onApplySuggestion?.(suggestion);
  };

  /**
   * Check if suggestion is applied
   */
  const isApplied = (suggestion: AISuggestionItem): boolean => {
    return appliedIds.has(suggestion.id || '') || suggestion.applied || false;
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box css={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
            <CircularProgress size={48} />
            <Typography css={{ mt: 2 }} color="text.secondary">
              Generating AI suggestions...
            </Typography>
            <Typography color="text.secondary" css={{ fontSize: '0.875rem', mt: 1 }}>
              This may take a few seconds
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
          <Alert
            severity="error"
            action={
              showRegenerate && onRegenerate && (
                <Button color="inherit" size="small" onClick={onRegenerate} disabled={disabled}>
                  Retry
                </Button>
              )
            }
          >
            {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  /**
   * Render empty state
   */
  if (!suggestionsData || !suggestionsData.suggestions || suggestionsData.suggestions.length === 0) {
    return (
      <Card>
        <CardContent>
          <Box css={{ textAlign: 'center', py: 4 }}>
            <Icon name="sparkles" css={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography color="text.primary" fontWeight={600}>
              No Suggestions Available
            </Typography>
            <Typography color="text.secondary" css={{ mt: 1 }}>
              Your resume looks great! Click regenerate to get fresh suggestions.
            </Typography>
            {showRegenerate && onRegenerate && (
              <Button
                variant="outlined"
                startIcon={<Icon name="refresh-cw" />}
                onClick={onRegenerate}
                disabled={disabled}
                css={{ mt: 2 }}
              >
                Generate Suggestions
              </Button>
            )}
          </Box>
        </CardContent>
      </Card>
    );
  }

  const scoreColor = getScoreColor(suggestionsData.ai_score);

  // Filter suggestions by priority
  const filteredSuggestions = React.useMemo(() => {
    if (filterPriority === 'all') return suggestionsData.suggestions;
    return suggestionsData.suggestions.filter((s) => s.priority === filterPriority);
  }, [suggestionsData.suggestions, filterPriority]);

  const displaySuggestions = filteredSuggestions.slice(0, maxDisplay);
  const hasMore = filteredSuggestions.length > maxDisplay;
  const appliedCount = displaySuggestions.filter(isApplied).length;

  return (
    <Card>
      <CardContent>
        {/* Header Section */}
        <Box
          css={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            mb: 2,
            flexWrap: 'wrap',
            gap: 1,
          }}
        >
          <Box css={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Icon name="brain" css={{ color: 'primary.main' }} />
            <Typography fontWeight={600}>{title}</Typography>
            {suggestionsData.model_used && (
              <Chip
                label={suggestionsData.model_used}
                size="small"
                variant="outlined"
                css={{ fontSize: '0.65rem', height: 20 }}
              />
            )}
          </Box>

          {showRegenerate && onRegenerate && (
            <Button
              size="small"
              variant="outlined"
              startIcon={<Icon name="refresh-cw" />}
              onClick={onRegenerate}
              disabled={disabled || loading}
            >
              Regenerate
            </Button>
          )}
        </Box>

        {/* AI Score Section */}
        <Box css={{ mb: 2 }}>
          <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography color="text.secondary" css={{ fontSize: '0.875rem' }}>
              AI Score
            </Typography>
            <Box css={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography
                fontWeight={700}
                color={scoreColor}
                css={{ fontSize: '1.5rem' }}
              >
                {suggestionsData.ai_score}
              </Typography>
              <Typography color="text.secondary" css={{ fontSize: '0.875rem' }}>
                /100
              </Typography>
            </Box>
          </Box>
          <LinearProgress
            variant="determinate"
            value={suggestionsData.ai_score}
            color={scoreColor}
            css={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        <Divider css={{ mb: 2 }} />

        {/* Summary Stats */}
        <Box
          css={{
            display: 'flex',
            gap: 2,
            mb: 2,
            flexWrap: 'wrap',
          }}
        >
          <Chip
            label={`${suggestionsData.total_suggestions} suggestions`}
            size="small"
            color="primary"
            variant="outlined"
          />
          {appliedCount > 0 && (
            <Chip
              label={`${appliedCount} applied`}
              size="small"
              color="success"
              variant="outlined"
              icon={<Icon name="check" css={{ fontSize: '0.875rem' }} />}
            />
          )}
        </Box>

        {/* Filter Tabs */}
        <Stack direction="row" spacing={1} css={{ mb: 2, flexWrap: 'wrap' }}>
          <Chip
            label="All"
            onClick={() => setFilterPriority('all')}
            color={filterPriority === 'all' ? 'primary' : 'default'}
            variant={filterPriority === 'all' ? 'filled' : 'outlined'}
            size="small"
            css={{ cursor: 'pointer' }}
          />
          <Chip
            label="High Priority"
            onClick={() => setFilterPriority('high')}
            color={filterPriority === 'high' ? 'error' : 'default'}
            variant={filterPriority === 'high' ? 'filled' : 'outlined'}
            size="small"
            css={{ cursor: 'pointer' }}
          />
          <Chip
            label="Medium Priority"
            onClick={() => setFilterPriority('medium')}
            color={filterPriority === 'medium' ? 'warning' : 'default'}
            variant={filterPriority === 'medium' ? 'filled' : 'outlined'}
            size="small"
            css={{ cursor: 'pointer' }}
          />
          <Chip
            label="Low Priority"
            onClick={() => setFilterPriority('low')}
            color={filterPriority === 'low' ? 'info' : 'default'}
            variant={filterPriority === 'low' ? 'filled' : 'outlined'}
            size="small"
            css={{ cursor: 'pointer' }}
          />
        </Stack>

        {/* Suggestions List */}
        <Stack spacing={1.5}>
          {displaySuggestions.map((suggestion, index) => {
            const isExpanded = expandedSuggestions.has(index);
            const priorityConfig = getPriorityConfig(suggestion.priority);
            const categoryIcon = getCategoryIcon(suggestion.category);
            const categoryLabel = getCategoryLabel(suggestion.category);
            const applied = isApplied(suggestion);
            const impactConfig = suggestion.impact_prediction
              ? getImpactConfig(suggestion.impact_prediction)
              : null;

            return (
              <Box
                key={index}
                css={{
                  p: compact ? 1 : 1.5,
                  borderRadius: 1,
                  backgroundColor: applied ? 'success.light' : 'background.default',
                  border: '1px solid',
                  borderColor: applied ? 'success.main' : 'divider',
                  opacity: applied ? 0.8 : 1,
                  transition: 'all 0.2s',
                  '&:hover': {
                    borderColor: applied ? 'success.main' : 'primary.light',
                  },
                }}
              >
                {/* Suggestion Header */}
                <Box
                  css={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                  }}
                >
                  <Box css={{ flex: 1, minWidth: 0 }}>
                    <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                      <Icon name={categoryIcon} css={{ fontSize: '1rem', color: 'primary.main' }} />
                      <Typography
                        css={{ fontWeight: 600, fontSize: '0.95rem' }}
                        color={applied ? 'success.dark' : 'text.primary'}
                      >
                        {suggestion.title}
                      </Typography>
                      {applied && (
                        <Icon name="check-circle" css={{ fontSize: '1rem', color: 'success.main' }} />
                      )}
                    </Box>

                    <Stack direction="row" spacing={0.5} css={{ flexWrap: 'wrap', mt: 0.5 }}>
                      <Tooltip title={priorityConfig.description} arrow>
                        <Chip
                          label={priorityConfig.label}
                          size="small"
                          color={priorityConfig.color}
                          variant="outlined"
                          css={{ fontSize: '0.65rem', height: 20 }}
                        />
                      </Tooltip>
                      <Chip
                        label={categoryLabel}
                        size="small"
                        color="default"
                        variant="outlined"
                        css={{ fontSize: '0.65rem', height: 20 }}
                      />
                      {suggestion.confidence_score !== undefined && (
                        <Tooltip title={`AI confidence: ${suggestion.confidence_score}%`} arrow>
                          <Chip
                            label={`${getConfidenceLabel(suggestion.confidence_score)} confidence`}
                            size="small"
                            color="default"
                            variant="outlined"
                            css={{ fontSize: '0.65rem', height: 20 }}
                          />
                        </Tooltip>
                      )}
                      {impactConfig && (
                        <Tooltip title={impactConfig.description} arrow>
                          <Chip
                            label={impactConfig.label}
                            size="small"
                            color={impactConfig.color}
                            variant="outlined"
                            icon={<Icon name={impactConfig.iconName} css={{ fontSize: '0.75rem' }} />}
                            css={{ fontSize: '0.65rem', height: 20 }}
                          />
                        </Tooltip>
                      )}
                      {suggestion.target_section && (
                        <Chip
                          label={getSectionLabel(suggestion.target_section)}
                          size="small"
                          color="secondary"
                          variant="outlined"
                          css={{ fontSize: '0.65rem', height: 20 }}
                        />
                      )}
                    </Stack>
                  </Box>

                  {/* Actions */}
                  <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 1 }}>
                    {!applied && onApplySuggestion && (
                      <Tooltip title="Apply suggestion" arrow>
                        <IconButton
                          size="small"
                          onClick={() => handleApply(suggestion, index)}
                          disabled={disabled}
                          color="primary"
                        >
                          <Icon name="check" />
                        </IconButton>
                      </Tooltip>
                    )}
                    {!applied && onDismissSuggestion && (
                      <Tooltip title="Dismiss suggestion" arrow>
                        <IconButton
                          size="small"
                          onClick={() => onDismissSuggestion(suggestion)}
                          disabled={disabled}
                          color="default"
                        >
                          <Icon name="x" />
                        </IconButton>
                      </Tooltip>
                    )}
                    <IconButton
                      size="small"
                      onClick={() => toggleExpanded(index)}
                      disabled={disabled}
                    >
                      <Icon name={isExpanded ? 'chevron-up' : 'chevron-down'} />
                    </IconButton>
                  </Box>
                </Box>

                {/* Expanded Content */}
                <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                  <Box css={{ mt: 1.5 }}>
                    {/* Description */}
                    <Typography color="text.secondary" css={{ mb: 1, fontSize: '0.875rem' }}>
                      {suggestion.description}
                    </Typography>

                    {/* Current State */}
                    {suggestion.current_state && (
                      <Box
                        css={{
                          p: 1,
                          borderRadius: 0.75,
                          backgroundColor: 'error.light',
                          border: '1px solid',
                          borderColor: 'error.main',
                          mb: 1,
                        }}
                      >
                        <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                          <Icon name="x-circle" css={{ fontSize: '0.875rem', color: 'error.main' }} />
                          <Typography fontWeight={600} css={{ fontSize: '0.8rem' }} color="error.dark">
                            Current:
                          </Typography>
                        </Box>
                        <Typography color="text.secondary" css={{ fontSize: '0.85rem', pl: 2 }}>
                          {suggestion.current_state}
                        </Typography>
                      </Box>
                    )}

                    {/* Recommendation */}
                    {suggestion.recommendation && (
                      <Box
                        css={{
                          p: 1,
                          borderRadius: 0.75,
                          backgroundColor: 'success.light',
                          border: '1px solid',
                          borderColor: 'success.main',
                          mb: suggestion.examples && suggestion.examples.length > 0 ? 1 : 0,
                        }}
                      >
                        <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                          <Icon name="check-circle" css={{ fontSize: '0.875rem', color: 'success.main' }} />
                          <Typography fontWeight={600} css={{ fontSize: '0.8rem' }} color="success.dark">
                            Recommended:
                          </Typography>
                        </Box>
                        <Typography color="text.secondary" css={{ fontSize: '0.85rem', pl: 2 }}>
                          {suggestion.recommendation}
                        </Typography>
                      </Box>
                    )}

                    {/* Examples */}
                    {suggestion.examples && suggestion.examples.length > 0 && (
                      <>
                        <Typography
                          color="text.secondary"
                          css={{ display: 'block', mt: 1, mb: 0.5, fontWeight: 500 }}
                        >
                          Examples:
                        </Typography>
                        <Stack spacing={0.5}>
                          {suggestion.examples.map((example, idx) => (
                            <Box
                              key={idx}
                              css={{
                                p: 1,
                                borderRadius: 0.5,
                                backgroundColor: 'background.paper',
                                border: '1px solid',
                                borderColor: 'divider',
                                fontSize: '0.85rem',
                              }}
                            >
                              <Typography color="text.primary">{example}</Typography>
                            </Box>
                          ))}
                        </Stack>
                      </>
                    )}

                    {/* Apply Button */}
                    {!applied && onApplySuggestion && suggestion.auto_applicable && (
                      <Button
                        variant="contained"
                        color="primary"
                        size="small"
                        startIcon={<Icon name="wand" />}
                        onClick={() => handleApply(suggestion, index)}
                        disabled={disabled}
                        css={{ mt: 1.5 }}
                      >
                        Apply Automatically
                      </Button>
                    )}
                  </Box>
                </Collapse>
              </Box>
            );
          })}
        </Stack>

        {/* Show More Indicator */}
        {hasMore && (
          <Box css={{ mt: 2, textAlign: 'center' }}>
            <Typography color="text.secondary" css={{ fontSize: '0.85rem' }}>
              Showing {maxDisplay} of {filteredSuggestions.length} suggestions
            </Typography>
          </Box>
        )}

        {/* Generation Timestamp */}
        {suggestionsData.generated_at && (
          <Box css={{ mt: 2, textAlign: 'right' }}>
            <Typography color="text.secondary" css={{ fontSize: '0.75rem' }}>
              Generated: {new Date(suggestionsData.generated_at).toLocaleString()}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default AISuggestionsPanel;
