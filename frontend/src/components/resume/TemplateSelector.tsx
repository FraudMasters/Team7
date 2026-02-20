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
  Grid,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import type {
  ResumeTemplateResponse,
  ResumeTemplateType,
} from '@/types/resume-templates';

/**
 * TemplateSelector Component Props
 */
interface TemplateSelectorProps {
  /** Available templates data */
  templates: ResumeTemplateResponse[];
  /** Currently selected template ID */
  selectedTemplateId?: string;
  /** Callback when a template is selected */
  onSelectTemplate?: (template: ResumeTemplateResponse) => void;
  /** Loading state */
  loading?: boolean;
  /** Error message */
  error?: string | null;
  /** Component title */
  title?: string;
  /** Number of columns in the grid (1-4) */
  columns?: 1 | 2 | 3 | 4;
  /** Disabled state */
  disabled?: boolean;
  /** Show ATS compliance badge */
  showAtsBadge?: boolean;
  /** Filter by template type */
  filterType?: ResumeTemplateType | 'all';
}

/**
 * Template type configuration for display
 */
const getTemplateTypeConfig = (templateType: string) => {
  const configs: Record<string, { label: string; iconName: string; color: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'default' }> = {
    modern: { label: 'Modern', iconName: 'zap', color: 'primary' },
    classic: { label: 'Classic', iconName: 'book', color: 'secondary' },
    creative: { label: 'Creative', iconName: 'palette', color: 'info' },
    ats_friendly: { label: 'ATS-Optimized', iconName: 'check-circle', color: 'success' },
    professional: { label: 'Professional', iconName: 'briefcase', color: 'default' },
    minimal: { label: 'Minimal', iconName: 'minus', color: 'secondary' },
    elegant: { label: 'Elegant', iconName: 'award', color: 'info' },
    bold: { label: 'Bold', iconName: 'star', color: 'warning' },
  };
  return configs[templateType] || { label: templateType, iconName: 'file', color: 'default' as const };
};

/**
 * Get column width based on columns count
 */
const getGridColumns = (columns: number): number => {
  const columnMap: Record<number, number> = {
    1: 12,
    2: 6,
    3: 4,
    4: 3,
  };
  return columnMap[columns] || 4;
};

/**
 * Template Card Component
 */
interface TemplateCardProps {
  template: ResumeTemplateResponse;
  isSelected: boolean;
  onSelect: () => void;
  disabled: boolean;
  showAtsBadge: boolean;
}

const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  isSelected,
  onSelect,
  disabled,
  showAtsBadge,
}) => {
  const typeConfig = getTemplateTypeConfig(template.template_type);

  return (
    <Card
      css={{
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.6 : 1,
        transition: 'all 0.2s ease-in-out',
        height: '100%',
        border: isSelected ? '2px solid' : '1px solid',
        borderColor: isSelected ? 'primary.main' : 'divider',
        '&:hover': disabled
          ? {}
          : {
              boxShadow: 3,
              transform: 'translateY(-2px)',
            },
      }}
      onClick={() => !disabled && onSelect()}
    >
      {/* Template Preview */}
      <Box
        css={{
          position: 'relative',
          height: 160,
          backgroundColor: 'grey.100',
          overflow: 'hidden',
        }}
      >
        {template.preview_url ? (
          <Box
            component="img"
            src={template.preview_url}
            alt={template.name}
            css={{
              height: '100%',
              width: '100%',
              objectFit: 'cover',
            }}
          />
        ) : (
          <Box
            css={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'grey.50',
            }}
          >
            <Icon name="file-text" css={{ fontSize: 48, color: 'grey.400' }} />
          </Box>
        )}

        {/* Selection indicator */}
        {isSelected && (
          <Box
            css={{
              position: 'absolute',
              top: 8,
              right: 8,
              backgroundColor: 'primary.main',
              borderRadius: '50%',
              width: 24,
              height: 24,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Icon name="check" css={{ color: 'white', fontSize: 16 }} />
          </Box>
        )}

        {/* Default badge */}
        {template.is_default && (
          <Chip
            label="Default"
            size="small"
            color="primary"
            css={{
              position: 'absolute',
              top: 8,
              left: 8,
              fontSize: '0.7rem',
            }}
          />
        )}
      </Box>

      <CardContent css={{ py: 1.5, px: 2 }}>
        {/* Template name and type */}
        <Box css={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography
            fontWeight={600}
            css={{
              fontSize: '0.95rem',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              flex: 1,
            }}
          >
            {template.name}
          </Typography>
          <Tooltip title={typeConfig.label} arrow>
            <Icon name={typeConfig.iconName} size={18} css={{ color: `${typeConfig.color}.main`, ml: 0.5 }} />
          </Tooltip>
        </Box>

        {/* Description */}
        {template.description && (
          <Typography
            color="text.secondary"
            css={{
              fontSize: '0.8rem',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              mb: 1,
            }}
          >
            {template.description}
          </Typography>
        )}

        {/* Badges */}
        <Stack direction="row" spacing={0.5} css={{ flexWrap: 'wrap' }}>
          <Chip
            label={typeConfig.label}
            size="small"
            color={typeConfig.color}
            variant="outlined"
            css={{ fontSize: '0.65rem', height: 20 }}
          />
          {showAtsBadge && template.is_ats_compliant && (
            <Tooltip title="Optimized for Applicant Tracking Systems" arrow>
              <Chip
                icon={<Icon name="shield" size={12} />}
                label="ATS"
                size="small"
                color="success"
                variant="outlined"
                css={{ fontSize: '0.65rem', height: 20 }}
              />
            </Tooltip>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};

/**
 * TemplateSelector Component
 *
 * Displays a grid of resume templates for selection with:
 * - Visual template previews
 * - Template type indicators
 * - ATS compliance badges
 * - Selection state visualization
 * - Loading and error states
 *
 * @example
 * ```tsx
 * <TemplateSelector
 *   templates={templatesList}
 *   selectedTemplateId="template-123"
 *   onSelectTemplate={(template) => console.log('Selected:', template)}
 *   loading={false}
 *   columns={3}
 *   showAtsBadge
 * />
 * ```
 */
const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  templates,
  selectedTemplateId,
  onSelectTemplate,
  loading = false,
  error = null,
  title = 'Choose a Template',
  columns = 3,
  disabled = false,
  showAtsBadge = true,
  filterType = 'all',
}) => {
  /**
   * Filter templates by type
   */
  const filteredTemplates = React.useMemo(() => {
    if (filterType === 'all') {
      return templates.filter((t) => t.is_active);
    }
    return templates.filter((t) => t.is_active && t.template_type === filterType);
  }, [templates, filterType]);

  /**
   * Handle template selection
   */
  const handleSelect = (template: ResumeTemplateResponse) => {
    if (!disabled && onSelectTemplate) {
      onSelectTemplate(template);
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box css={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
        <CircularProgress />
        <Typography css={{ mt: 2 }} color="text.secondary">
          Loading templates...
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
  if (!templates || templates.length === 0) {
    return (
      <Box css={{ textAlign: 'center', py: 4 }}>
        <Icon name="layout" css={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography color="text.secondary" fontWeight={600}>
          No Templates Available
        </Typography>
        <Typography color="text.secondary">
          Please check back later for available resume templates.
        </Typography>
      </Box>
    );
  }

  /**
   * Render filtered empty state
   */
  if (filteredTemplates.length === 0) {
    return (
      <Box css={{ textAlign: 'center', py: 4 }}>
        <Icon name="search" css={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography color="text.secondary" fontWeight={600}>
          No Templates Found
        </Typography>
        <Typography color="text.secondary">
          No templates match the selected filter. Try selecting a different category.
        </Typography>
      </Box>
    );
  }

  const gridSize = getGridColumns(columns);

  return (
    <Card>
      <CardContent>
        {/* Header Section */}
        <Box
          css={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
            flexWrap: 'wrap',
            gap: 1,
          }}
        >
          <Box css={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Icon name="layout" css={{ color: 'primary.main' }} />
            <Typography fontWeight={600}>{title}</Typography>
          </Box>

          {/* Template count */}
          <Box
            css={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <Chip
              label={`${filteredTemplates.length} template${filteredTemplates.length !== 1 ? 's' : ''}`}
              size="small"
              color="primary"
              variant="outlined"
            />
            {selectedTemplateId && (
              <Chip
                label="1 selected"
                size="small"
                color="success"
                variant="outlined"
                icon={<Icon name="check" size={14} />}
              />
            )}
          </Box>
        </Box>

        <Divider css={{ mb: 2 }} />

        {/* Template Grid */}
        <Grid container spacing={2}>
          {filteredTemplates.map((template) => (
            <Grid item xs={12} sm={6} md={gridSize} key={template.id}>
              <TemplateCard
                template={template}
                isSelected={selectedTemplateId === template.id}
                onSelect={() => handleSelect(template)}
                disabled={disabled}
                showAtsBadge={showAtsBadge}
              />
            </Grid>
          ))}
        </Grid>

        {/* Selection hint */}
        {!selectedTemplateId && (
          <Box css={{ mt: 2, textAlign: 'center' }}>
            <Typography color="text.secondary" css={{ fontSize: '0.85rem' }}>
              <Icon name="info" size={14} css={{ verticalAlign: 'middle', mr: 0.5 }} />
              Click on a template to select it for your resume
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default TemplateSelector;
