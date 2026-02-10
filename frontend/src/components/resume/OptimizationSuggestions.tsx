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
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import type {
  OptimizationFeedback,
  OptimizationSuggestion,
  OptimizationPriority,
  OptimizationCategory,
} from '@/types/api';

/**
 * OptimizationSuggestions Component Props
 */
interface OptimizationSuggestionsProps {
  /** Optimization feedback data from API */
  optimizationData: OptimizationFeedback | null;
  /** Loading state */
  loading?: boolean;
  /** Error message */
  error?: string | null;
  /** Component title */
  title?: string;
  /** Maximum number of suggestions to display */
  maxDisplay?: number;
  /** Callback when applying a suggestion */
  onApplySuggestion?: (suggestion: OptimizationSuggestion) => void;
  /** Disabled state */
  disabled?: boolean;
}

/**
 * Priority configuration for display
 */
const getPriorityConfig = (priority: OptimizationPriority) => {
  switch (priority) {
    case 'high':
      return {
        label: 'High',
        iconName: 'alert-circle',
        color: 'error' as const,
        bgColor: 'error.light' as const,
        description: 'Important improvement',
      };
    case 'medium':
      return {
        label: 'Medium',
        iconName: 'zap',
        color: 'warning' as const,
        bgColor: 'warning.light' as const,
        description: 'Recommended improvement',
      };
    case 'low':
      return {
        label: 'Low',
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
 * Get score color based on value
 */
const getScoreColor = (score: number): 'success' | 'warning' | 'error' => {
  if (score >= 80) return 'success';
  if (score >= 60) return 'warning';
  return 'error';
};

/**
 * Get priority-based color config
 */
const getPriorityColors = (priority: OptimizationPriority) => {
  switch (priority) {
    case 'high':
      return {
        bg: 'error.light',
        border: 'error.dark',
        bgHover: 'background.paper',
      };
    case 'medium':
      return {
        bg: 'warning.light',
        border: 'warning.dark',
        bgHover: 'background.paper',
      };
    case 'low':
      return {
        bg: 'info.light',
        border: 'info.dark',
        bgHover: 'background.paper',
      };
    default:
      return {
        bg: 'grey.100',
        border: 'grey.300',
        bgHover: 'grey.200',
      };
  }
};

/**
 * OptimizationSuggestions Component
 *
 * Displays AI-powered resume optimization suggestions with:
 * - Overall optimization score visualization
 * - Priority-based suggestion grouping
 * - Expandable suggestion details
 * - Category and type indicators
 * - Actionable examples and recommendations
 *
 * @example
 * ```tsx
 * <OptimizationSuggestions
 *   optimizationData={optimizationFeedback}
 *   loading={false}
 *   onApplySuggestion={(suggestion) => console.log('Apply:', suggestion)}
 * />
 * ```
 */
const OptimizationSuggestions: React.FC<OptimizationSuggestionsProps> = ({
  optimizationData,
  loading = false,
  error = null,
  title = 'Resume Optimization Suggestions',
  maxDisplay = 50,
  onApplySuggestion,
  disabled = false,
}) => {
  const [expandedSuggestions, setExpandedSuggestions] = React.useState<Set<number>>(new Set());
  const [filterType, setFilterType] = React.useState<'all' | OptimizationPriority>('all');

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
   * Render loading state
   */
  if (loading) {
    return (
      <Box css={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
        <Typography css={{ ml: 2 }}>
          Analyzing resume for optimization opportunities...
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert severity="error" css={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  /**
   * Render empty state
   */
  if (!optimizationData || !optimizationData.suggestions || optimizationData.suggestions.length === 0) {
    return (
      <Box css={{ textAlign: 'center', py: 4 }}>
        <Icon name="check-circle" css={{ fontSize: 48, color: 'success.main', mb: 2 }} />
        <Typography color="text.secondary" fontWeight={600}>
          No Optimization Suggestions
        </Typography>
        <Typography color="text.secondary">
          Your resume looks great! No immediate improvements needed.
        </Typography>
      </Box>
    );
  }

  const scoreColor = getScoreColor(optimizationData.score);

  // Filter suggestions by priority
  const filteredSuggestions = React.useMemo(() => {
    if (filterType === 'all') return optimizationData.suggestions;
    return optimizationData.suggestions.filter((s) => s.priority === filterType);
  }, [optimizationData.suggestions, filterType]);

  const displaySuggestions = filteredSuggestions.slice(0, maxDisplay);
  const hasMore = filteredSuggestions.length > maxDisplay;

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
            <Icon name="sparkles" css={{ color: 'primary.main' }} />
            <Typography fontWeight={600}>{title}</Typography>
          </Box>

          {/* Score Display */}
          <Box
            css={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              px: 2,
              py: 1,
              borderRadius: 1,
              backgroundColor: `${scoreColor}.light`,
            }}
          >
            <Typography
              fontWeight={700}
              color={scoreColor}
              css={{ fontSize: '1.25rem' }}
            >
              {optimizationData.score}
            </Typography>
            <Typography color="text.secondary" css={{ fontSize: '0.875rem' }}>
              /100
            </Typography>
          </Box>
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
            label={`${optimizationData.total_suggestions} suggestions`}
            size="small"
            color="primary"
            variant="outlined"
          />
          {optimizationData.high_priority_count > 0 && (
            <Chip
              label={`${optimizationData.high_priority_count} high`}
              size="small"
              color="error"
              variant="outlined"
            />
          )}
          {optimizationData.medium_priority_count > 0 && (
            <Chip
              label={`${optimizationData.medium_priority_count} medium`}
              size="small"
              color="warning"
              variant="outlined"
            />
          )}
          {optimizationData.low_priority_count > 0 && (
            <Chip
              label={`${optimizationData.low_priority_count} low`}
              size="small"
              color="info"
              variant="outlined"
            />
          )}
        </Box>

        {/* Filter Tabs */}
        <Stack direction="row" spacing={1} css={{ mb: 2, flexWrap: 'wrap' }}>
          <Chip
            label="All"
            onClick={() => setFilterType('all')}
            color={filterType === 'all' ? 'primary' : 'default'}
            variant={filterType === 'all' ? 'filled' : 'outlined'}
            size="small"
            css={{ cursor: 'pointer' }}
          />
          <Chip
            label="High Priority"
            onClick={() => setFilterType('high')}
            color={filterType === 'high' ? 'error' : 'default'}
            variant={filterType === 'high' ? 'filled' : 'outlined'}
            size="small"
            css={{ cursor: 'pointer' }}
          />
          <Chip
            label="Medium Priority"
            onClick={() => setFilterType('medium')}
            color={filterType === 'medium' ? 'warning' : 'default'}
            variant={filterType === 'medium' ? 'filled' : 'outlined'}
            size="small"
            css={{ cursor: 'pointer' }}
          />
          <Chip
            label="Low Priority"
            onClick={() => setFilterType('low')}
            color={filterType === 'low' ? 'info' : 'default'}
            variant={filterType === 'low' ? 'filled' : 'outlined'}
            size="small"
            css={{ cursor: 'pointer' }}
          />
        </Stack>

        {/* Missing Keywords Section */}
        {optimizationData.missing_keywords && optimizationData.missing_keywords.length > 0 && (
          <>
            <Box
              css={{
                mt: 2,
                mb: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <Icon name="tag" css={{ color: 'warning.main', fontSize: '1rem' }} />
              <Typography fontWeight={600} color="text.secondary">
                Missing Keywords
              </Typography>
            </Box>
            <Box
              css={{
                display: 'flex',
                gap: 1,
                flexWrap: 'wrap',
                mb: 2,
              }}
            >
              {optimizationData.missing_keywords.map((keyword, idx) => (
                <Chip
                  key={idx}
                  label={keyword}
                  size="small"
                  color="warning"
                  variant="outlined"
                />
              ))}
            </Box>
          </>
        )}

        {/* Suggestions List */}
        <Stack spacing={1.5}>
          {displaySuggestions.map((suggestion, index) => {
            const isExpanded = expandedSuggestions.has(index);
            const priorityConfig = getPriorityConfig(suggestion.priority);
            const categoryIcon = getCategoryIcon(suggestion.category);
            const categoryLabel = getCategoryLabel(suggestion.category);
            const hasExamples = suggestion.examples && suggestion.examples.length > 0;

            return (
              <Box
                key={index}
                css={{
                  p: 1.5,
                  borderRadius: 1,
                  backgroundColor: getPriorityColors(suggestion.priority).bg,
                  border: '1px solid',
                  borderColor: getPriorityColors(suggestion.priority).border,
                  transition: 'background-color 0.2s',
                  '&:hover': {
                    backgroundColor: getPriorityColors(suggestion.priority).bgHover,
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
                  <Box css={{ flex: 1 }}>
                    <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                      <Icon name={categoryIcon} css={{ fontSize: '1rem', color: 'primary.main' }} />
                      <Typography
                        css={{ fontWeight: 600, fontSize: '0.95rem' }}
                        color="text.primary"
                      >
                        {suggestion.title}
                      </Typography>
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
                    </Stack>
                  </Box>

                  {/* Expand/Collapse Button */}
                  <IconButton
                    size="small"
                    onClick={() => toggleExpanded(index)}
                    disabled={disabled}
                    css={{ ml: 1 }}
                  >
                    <Icon name={isExpanded ? 'chevron-up' : 'chevron-down'} />
                  </IconButton>
                </Box>

                {/* Expanded Content */}
                <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                  <Box css={{ mt: 1.5 }}>
                    {/* Description */}
                    <Typography color="text.secondary" css={{ mb: 1, fontSize: '0.875rem' }}>
                      {suggestion.description}
                    </Typography>

                    {/* Current State */}
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

                    {/* Recommendation */}
                    <Box
                      css={{
                        p: 1,
                        borderRadius: 0.75,
                        backgroundColor: 'success.light',
                        border: '1px solid',
                        borderColor: 'success.main',
                        mb: hasExamples ? 1 : 0,
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

                    {/* Examples */}
                    {hasExamples && (
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
      </CardContent>
    </Card>
  );
};

export default OptimizationSuggestions;
