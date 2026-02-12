import React, { useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
  Button,
  TextField,
  InputAdornment,
  Tooltip,
  IconButton,
  Collapse,
  Tabs,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import type {
  VisualParsingFeedback as VisualParsingFeedbackType,
  FieldSourceLocation,
  SourceTextLocation,
} from '../types/parsingCorrection';

/**
 * Field category for grouping extracted fields
 */
type FieldCategory = 'personal' | 'skills' | 'experience' | 'education' | 'languages' | 'other';

/**
 * Field category configuration
 */
interface FieldCategoryConfig {
  label: string;
  icon: string;
  fields: string[];
}

/**
 * Get category configuration for a field
 */
const getFieldCategory = (fieldName: string): FieldCategory => {
  const categoryMap: Record<string, FieldCategory> = {
    position: 'personal',
    skills: 'skills',
    work_experience: 'experience',
    education: 'education',
    languages: 'languages',
    age: 'personal',
  };
  return categoryMap[fieldName] || 'other';
};

/**
 * Get all category configurations
 */
const getCategoryConfigs = (t: (key: string, defaultValue?: string) => string): Record<FieldCategory, FieldCategoryConfig> => ({
  personal: {
    label: t('visualParsingFeedback.categories.personal', 'Personal Info'),
    icon: 'user',
    fields: ['position', 'age'],
  },
  skills: {
    label: t('visualParsingFeedback.categories.skills', 'Skills'),
    icon: 'zap',
    fields: ['skills'],
  },
  experience: {
    label: t('visualParsingFeedback.categories.experience', 'Work Experience'),
    icon: 'briefcase',
    fields: ['work_experience'],
  },
  education: {
    label: t('visualParsingFeedback.categories.education', 'Education'),
    icon: 'graduation-cap',
    fields: ['education'],
  },
  languages: {
    label: t('visualParsingFeedback.categories.languages', 'Languages'),
    icon: 'globe',
    fields: ['languages'],
  },
  other: {
    label: t('visualParsingFeedback.categories.other', 'Other'),
    icon: 'file',
    fields: [],
  },
});

/**
 * Format field value for display
 */
const formatFieldValue = (value: string | Record<string, unknown>): string => {
  if (typeof value === 'string') {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map(item => typeof item === 'string' ? item : JSON.stringify(item)).join(', ');
  }
  if (value && typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  return '';
};

/**
 * Highlight text in source based on location
 */
const HighlightedSourceText: React.FC<{
  sourceText: string;
  highlightLocation?: SourceTextLocation | null;
}> = ({ sourceText, highlightLocation }) => {
  if (!highlightLocation?.start && !highlightLocation?.end && !highlightLocation?.text) {
    return (
      <Box
        css={{
          fontFamily: 'monospace',
          fontSize: '0.875rem',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          lineHeight: 1.6,
        }}
      >
        {sourceText}
      </Box>
    );
  }

  // If we have text directly, find and highlight it
  if (highlightLocation.text) {
    const searchText = highlightLocation.text;
    const index = sourceText.indexOf(searchText);

    if (index === -1) {
      return (
        <Box
          css={{
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            lineHeight: 1.6,
          }}
        >
          {sourceText}
        </Box>
      );
    }

    const before = sourceText.slice(0, index);
    const highlighted = searchText;
    const after = sourceText.slice(index + searchText.length);

    return (
      <Box
        css={{
          fontFamily: 'monospace',
          fontSize: '0.875rem',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          lineHeight: 1.6,
        }}
      >
        {before}
        <Box
          component="span"
          css={{
            bgcolor: '$primaryLight',
            color: '$primaryDark',
            px: '$0.5',
            borderRadius: '$0.5',
            fontWeight: 500,
          }}
        >
          {highlighted}
        </Box>
        {after}
      </Box>
    );
  }

  // Use start/end positions if available
  if (highlightLocation.start !== undefined && highlightLocation.end !== undefined) {
    const before = sourceText.slice(0, highlightLocation.start);
    const highlighted = sourceText.slice(highlightLocation.start, highlightLocation.end);
    const after = sourceText.slice(highlightLocation.end);

    return (
      <Box
        css={{
          fontFamily: 'monospace',
          fontSize: '0.875rem',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          lineHeight: 1.6,
        }}
      >
        {before}
        <Box
          component="span"
          css={{
            bgcolor: '$primaryLight',
            color: '$primaryDark',
            px: '$0.5',
            borderRadius: '$0.5',
            fontWeight: 500,
          }}
        >
          {highlighted}
        </Box>
        {after}
      </Box>
    );
  }

  return (
    <Box
      css={{
        fontFamily: 'monospace',
        fontSize: '0.875rem',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        lineHeight: 1.6,
      }}
    >
      {sourceText}
    </Box>
  );
};

/**
 * Individual field item component
 */
interface FieldItemProps {
  field: FieldSourceLocation;
  isSelected: boolean;
  isCorrected: boolean;
  onClick: () => void;
}

const FieldItem: React.FC<FieldItemProps> = ({ field, isSelected, isCorrected, onClick }) => {
  const { t } = useTranslation();

  return (
    <ListItem
      onClick={onClick}
      css={{
        cursor: 'pointer',
        bgcolor: isSelected ? '$primaryLight' : 'transparent',
        borderLeft: 3,
        borderColor: isSelected ? '$primary' : isCorrected ? '$success' : 'transparent',
        borderRadius: '$0.5',
        mb: '$0.5',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          bgcolor: isSelected ? '$primaryLight' : '$grey50',
        },
      }}
    >
      <ListItemIcon css={{ minWidth: 36 }}>
        {isCorrected ? (
          <Icon name="check-circle" color="$success" size={20} />
        ) : (
          <Icon name="file-text" color="$grey500" size={20} />
        )}
      </ListItemIcon>
      <ListItemText
        primary={
          <Box css={{ display: 'flex', alignItems: 'center', gap: '$1' }}>
            <Typography variant="subtitle2" fontWeight={isSelected ? 600 : 500}>
              {field.field_name}
            </Typography>
            {field.confidence !== undefined && (
              <Chip
                label={`${Math.round(field.confidence * 100)}%`}
                size="small"
                variant="outlined"
                css={{
                  fontSize: '0.65rem',
                  height: 18,
                  color: field.confidence >= 0.8 ? '$success' : field.confidence >= 0.5 ? '$warning' : '$error',
                }}
              />
            )}
          </Box>
        }
        secondary={
          <Typography
            variant="caption"
            css={{
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              color: '$grey600',
            }}
          >
            {formatFieldValue(field.extracted_value)}
          </Typography>
        }
      />
      {isSelected && (
        <Icon name="chevron-right" color="$primary" size={20} />
      )}
    </ListItem>
  );
};

/**
 * VisualParsingFeedback Component Props
 */
interface VisualParsingFeedbackProps {
  /** Visual parsing feedback data */
  data: VisualParsingFeedbackType;
  /** Full source text of the resume */
  sourceText: string;
  /** Called when a field is selected */
  onFieldSelect?: (field: FieldSourceLocation | null) => void;
  /** Called when a field is clicked for editing */
  onFieldEdit?: (field: FieldSourceLocation) => void;
  /** Loading state */
  loading?: boolean;
  /** Error message if any */
  error?: string | null;
  /** Default selected field name */
  defaultSelectedField?: string;
}

/**
 * VisualParsingFeedback Component
 *
 * Displays a side-by-side view of source text and extracted fields,
 * allowing users to see which text sections were extracted for each field.
 *
 * @example
 * ```tsx
 * <VisualParsingFeedback
 *   data={feedbackData}
 *   sourceText={resumeText}
 *   onFieldSelect={(field) => console.log('Selected:', field)}
 * />
 * ```
 */
const VisualParsingFeedback: React.FC<VisualParsingFeedbackProps> = ({
  data,
  sourceText,
  onFieldSelect,
  onFieldEdit,
  loading = false,
  error = null,
  defaultSelectedField,
}) => {
  const { t } = useTranslation();
  const [selectedField, setSelectedField] = useState<FieldSourceLocation | null>(() => {
    if (defaultSelectedField) {
      return data.source_locations.find(f => f.field_name === defaultSelectedField) || null;
    }
    return null;
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [isSourceCollapsed, setIsSourceCollapsed] = useState(false);

  const categoryConfigs = useMemo(() => getCategoryConfigs(t), [t]);

  /**
   * Group fields by category
   */
  const fieldsByCategory = useMemo(() => {
    const grouped: Partial<Record<FieldCategory, FieldSourceLocation[]>> = {};

    data.source_locations.forEach(field => {
      const category = getFieldCategory(field.field_name);
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category]!.push(field);
    });

    return grouped;
  }, [data.source_locations]);

  /**
   * Available categories with fields
   */
  const availableCategories = useMemo(() => {
    return Object.keys(fieldsByCategory).filter(
      category => (fieldsByCategory[category as FieldCategory]?.length || 0) > 0
    ) as FieldCategory[];
  }, [fieldsByCategory]);

  /**
   * Active tab - use first available category
   */
  const [activeTab, setActiveTab] = useState<FieldCategory>(() => {
    // Compute initial category from data
    const grouped: Partial<Record<FieldCategory, FieldSourceLocation[]>> = {};
    data.source_locations.forEach(field => {
      const category = getFieldCategory(field.field_name);
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category]!.push(field);
    });
    const categories = Object.keys(grouped).filter(
      cat => (grouped[cat as FieldCategory]?.length || 0) > 0
    ) as FieldCategory[];
    return categories[0] || 'personal';
  });

  /**
   * Filter fields by search query
   */
  const filteredFields = useMemo(() => {
    if (!searchQuery.trim()) {
      return fieldsByCategory[activeTab] || [];
    }

    const query = searchQuery.toLowerCase();
    return (fieldsByCategory[activeTab] || []).filter(field =>
      field.field_name.toLowerCase().includes(query) ||
      formatFieldValue(field.extracted_value).toLowerCase().includes(query)
    );
  }, [fieldsByCategory, activeTab, searchQuery]);

  /**
   * Handle field selection
   */
  const handleFieldSelect = useCallback((field: FieldSourceLocation) => {
    setSelectedField(prev => prev?.field_name === field.field_name ? null : field);
    onFieldSelect?.(selectedField?.field_name === field.field_name ? null : field);
  }, [selectedField, onFieldSelect]);

  /**
   * Handle field edit
   */
  const handleFieldEdit = useCallback((field: FieldSourceLocation) => {
    onFieldEdit?.(field);
  }, [onFieldEdit]);

  /**
   * Scroll to field in source
   */
  const scrollToField = useCallback((field: FieldSourceLocation) => {
    handleFieldSelect(field);
  }, [handleFieldSelect]);

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        css={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: '$8',
        }}
      >
        <CircularProgress size={60} css={{ mb: '$3' }} />
        <Typography variant="h6" color="secondary">
          {t('visualParsingFeedback.loading.title', 'Loading parsing feedback...')}
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert severity="error">
        <Typography variant="subtitle1" fontWeight={600}>
          {t('visualParsingFeedback.error.title', 'Failed to load parsing feedback')}
        </Typography>
        {error}
      </Alert>
    );
  }

  /**
   * Render empty state
   */
  if (!data.source_locations || data.source_locations.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" fontWeight={600}>
          {t('visualParsingFeedback.empty.title', 'No parsing data available')}
        </Typography>
        {t('visualParsingFeedback.empty.message', 'Upload a resume to see visual parsing feedback.')}
      </Alert>
    );
  }

  return (
    <Paper elevation={2} css={{ p: '$3' }}>
      {/* Header */}
      <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: '$3' }}>
        <Typography variant="h6" fontWeight={600}>
          {t('visualParsingFeedback.title', 'Visual Parsing Feedback')}
        </Typography>
        <Box css={{ display: 'flex', alignItems: 'center', gap: '$2' }}>
          <Chip
            label={t('visualParsingFeedback.fieldsCount', '{{count}} fields', { count: data.total_fields })}
            size="small"
            variant="outlined"
          />
          {data.corrected_fields.length > 0 && (
            <Tooltip title={t('visualParsingFeedback.correctedTooltip', '{{count}} fields have been corrected', { count: data.corrected_fields.length })}>
              <Chip
                icon={<Icon name="check-circle" size={16} />}
                label={t('visualParsingFeedback.corrected', '{{count}} corrected', { count: data.corrected_fields.length })}
                size="small"
                color="success"
                variant="outlined"
              />
            </Tooltip>
          )}
        </Box>
      </Box>

      <Divider css={{ mb: '$3' }} />

      {/* Main Content - Side by Side View */}
      <Grid container spacing={3}>
        {/* Left Side - Source Text */}
        <Grid item xs={12} md={6}>
          <Paper
            elevation={0}
            variant="outlined"
            css={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              minHeight: 500,
            }}
          >
            {/* Source Header */}
            <Box
              css={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                p: '$2',
                bgcolor: '$grey50',
                borderBottom: '1px solid',
                borderColor: '$grey200',
              }}
            >
              <Box css={{ display: 'flex', alignItems: 'center', gap: '$1' }}>
                <Icon name="file-text" size={18} />
                <Typography variant="subtitle2" fontWeight={600}>
                  {t('visualParsingFeedback.sourceText.title', 'Source Text')}
                </Typography>
              </Box>
              <Box css={{ display: 'flex', alignItems: 'center', gap: '$1' }}>
                <Typography variant="caption" color="secondary">
                  {sourceText.length} {t('visualParsingFeedback.sourceText.characters', 'characters')}
                </Typography>
                <IconButton
                  size="small"
                  onClick={() => setIsSourceCollapsed(!isSourceCollapsed)}
                  css={{ ml: '$1' }}
                >
                  <Icon name={isSourceCollapsed ? 'maximize-2' : 'minimize-2'} size={18} />
                </IconButton>
              </Box>
            </Box>

            {/* Source Content */}
            <Collapse in={!isSourceCollapsed}>
              <Box
                css={{
                  p: '$2',
                  maxHeight: 600,
                  overflow: 'auto',
                  bgcolor: '$grey25',
                }}
              >
                {selectedField ? (
                  <Box>
                    <Box css={{ mb: '$2', display: 'flex', alignItems: 'center', gap: '$1' }}>
                      <Typography variant="caption" color="primary" fontWeight={600}>
                        {t('visualParsingFeedback.highlighting', 'Highlighting:')} {selectedField.field_name}
                      </Typography>
                      <Button
                        size="small"
                        variant="text"
                        onClick={() => {
                          setSelectedField(null);
                          onFieldSelect?.(null);
                        }}
                        css={{ ml: 'auto', fontSize: '0.75rem' }}
                      >
                        {t('visualParsingFeedback.clearHighlight', 'Clear')}
                      </Button>
                    </Box>
                    <HighlightedSourceText
                      sourceText={sourceText}
                      highlightLocation={selectedField.location}
                    />
                  </Box>
                ) : (
                  <HighlightedSourceText sourceText={sourceText} />
                )}
              </Box>
            </Collapse>
          </Paper>
        </Grid>

        {/* Right Side - Extracted Fields */}
        <Grid item xs={12} md={6}>
          <Paper
            elevation={0}
            variant="outlined"
            css={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              minHeight: 500,
            }}
          >
            {/* Fields Header with Search */}
            <Box
              css={{
                p: '$2',
                bgcolor: '$grey50',
                borderBottom: '1px solid',
                borderColor: '$grey200',
              }}
            >
              <Box css={{ display: 'flex', alignItems: 'center', gap: '$1', mb: '$2' }}>
                <Icon name="layout" size={18} />
                <Typography variant="subtitle2" fontWeight={600}>
                  {t('visualParsingFeedback.extractedFields.title', 'Extracted Fields')}
                </Typography>
              </Box>

              {/* Search */}
              <TextField
                size="small"
                placeholder={t('visualParsingFeedback.searchPlaceholder', 'Search fields...')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                fullWidth
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Icon name="search" size={18} />
                    </InputAdornment>
                  ),
                  endAdornment: searchQuery ? (
                    <InputAdornment position="end">
                      <IconButton size="small" onClick={() => setSearchQuery('')}>
                        <Icon name="x" size={16} />
                      </IconButton>
                    </InputAdornment>
                  ) : undefined,
                }}
                css={{ '& .MuiInputBase-input': { fontSize: '0.875rem', py: '$0.75' } }}
              />
            </Box>

            {/* Category Tabs */}
            {!searchQuery && availableCategories.length > 0 && (
              <Box css={{ borderBottom: '1px solid', borderColor: '$grey200' }}>
                <Tabs
                  value={activeTab}
                  onChange={(_, newValue) => setActiveTab(newValue as FieldCategory)}
                  variant="scrollable"
                  items={availableCategories.map(category => {
                    const config = categoryConfigs[category];
                    const count = fieldsByCategory[category]?.length || 0;
                    return {
                      id: category,
                      label: `${config.label} (${count})`,
                      icon: <Icon name={config.icon} size={16} />,
                    };
                  })}
                />
              </Box>
            )}

            {/* Fields List */}
            <Box css={{ flex: 1, overflow: 'auto', p: '$1' }}>
              {filteredFields.length > 0 ? (
                <List css={{ py: 0 }}>
                  {filteredFields.map((field, index) => (
                    <FieldItem
                      key={`${field.field_name}-${index}`}
                      field={field}
                      isSelected={selectedField?.field_name === field.field_name}
                      isCorrected={data.corrected_fields.includes(field.field_name)}
                      onClick={() => scrollToField(field)}
                    />
                  ))}
                </List>
              ) : (
                <Box css={{ p: '$4', textAlign: 'center' }}>
                  <Icon name="search-x" size={48} color="$grey400" css={{ mb: '$2' }} />
                  <Typography variant="body2" color="secondary">
                    {searchQuery
                      ? t('visualParsingFeedback.noResults', 'No fields matching "{{query}}"', { query: searchQuery })
                      : t('visualParsingFeedback.noFieldsInCategory', 'No fields in this category')}
                  </Typography>
                </Box>
              )}
            </Box>

            {/* Selected Field Details */}
            {selectedField && (
              <Box
                css={{
                  p: '$2',
                  borderTop: 1,
                  borderColor: '$primary',
                  bgcolor: '$primaryLight',
                }}
              >
                <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: '$1' }}>
                  <Typography variant="subtitle2" fontWeight={600}>
                    {selectedField.field_name}
                  </Typography>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<Icon name="edit" size={16} />}
                    onClick={() => handleFieldEdit(selectedField)}
                  >
                    {t('visualParsingFeedback.editField', 'Edit')}
                  </Button>
                </Box>
                <Typography variant="body2" css={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {formatFieldValue(selectedField.extracted_value)}
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default VisualParsingFeedback;
export type {
  VisualParsingFeedbackProps,
  FieldItemProps,
  FieldCategory,
};
