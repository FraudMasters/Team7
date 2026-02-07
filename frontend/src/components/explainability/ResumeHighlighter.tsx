import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Stack,
  Chip,
  Divider,
  Alert,
  AlertTitle,
  Grid,
  IconButton,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as PositiveIcon,
  Error as NegativeIcon,
  Info as InfoIcon,
  Lightbulb as BulbIcon,
  Visibility as ViewIcon,
  VisibilityOff as HideIcon,
} from '@mui/icons-material';

/**
 * Feature-to-section mapping entry
 */
interface FeatureSectionMapping {
  /** Feature name (e.g., 'experience', 'skills', 'education') */
  featureName: string;
  /** Section content from resume that influenced this feature */
  sectionContent: string;
  /** Impact score (0-100) showing how much this section affected ranking */
  impactScore: number;
  /** Direction of impact (positive or negative) */
  impactDirection: 'positive' | 'neutral' | 'negative';
  /** Optional description of why this section mattered */
  description?: string;
}

/**
 * Resume highlight sections data structure
 * Maps section names to their content with metadata
 */
export interface ResumeHighlightSections {
  [sectionName: string]: string | FeatureSectionMapping;
}

/**
 * ResumeHighlighter Component Props
 */
interface ResumeHighlighterProps {
  /** Mapping of section names to content or detailed feature mappings */
  highlightSections: ResumeHighlightSections;
  /** Optional feature explanations to map sections to features */
  featureExplanations?: Array<{
    feature_name: string;
    contribution: number;
    description: string;
  }>;
  /** Whether to show expanded view by default */
  defaultExpanded?: boolean;
  /** Maximum height for section content before scroll (in pixels) */
  maxContentHeight?: number;
}

/**
 * Get impact configuration based on direction and score
 */
const getImpactConfig = (
  direction: 'positive' | 'neutral' | 'negative',
  score: number
) => {
  if (direction === 'positive') {
    return {
      color: 'success' as const,
      icon: <PositiveIcon />,
      label: 'Positive Impact',
      bgColor: 'success.main',
      textColor: 'success.contrastText',
    };
  }
  if (direction === 'negative') {
    return {
      color: 'error' as const,
      icon: <NegativeIcon />,
      label: 'Negative Impact',
      bgColor: 'error.main',
      textColor: 'error.contrastText',
    };
  }
  return {
    color: 'info' as const,
    icon: <InfoIcon />,
    label: 'Neutral',
    bgColor: 'info.main',
    textColor: 'info.contrastText',
  };
};

/**
 * Normalize section data to FeatureSectionMapping format
 */
const normalizeSectionData = (
  sectionName: string,
  sectionData: string | FeatureSectionMapping
): FeatureSectionMapping => {
  if (typeof sectionData === 'string') {
    // Determine impact based on common section name patterns
    const lowerName = sectionName.toLowerCase();
    const direction: 'positive' | 'neutral' | 'negative' =
      lowerName.includes('missing') || lowerName.includes('weakness')
        ? 'negative'
        : lowerName.includes('strength') || lowerName.includes('matched')
        ? 'positive'
        : 'neutral';

    return {
      featureName: sectionName,
      sectionContent: sectionData,
      impactScore: 50, // Default neutral score
      impactDirection: direction,
    };
  }
  return sectionData;
};

/**
 * ResumeHighlighter Component
 *
 * Displays influential resume sections that affected the ranking with:
 * - Visual highlighting of important sections
 * - Feature-to-section mapping
 * - Impact score visualization
 * - Expandable/collapsible section views
 * - Color-coded positive/negative/neutral impacts
 *
 * @example
 * ```tsx
 * <ResumeHighlighter
 *   highlightSections={{
 *     "Experience": "10 years at Google...",
 *     "Skills": "Python, React, Node.js..."
 *   }}
 * />
 * ```
 */
const ResumeHighlighter: React.FC<ResumeHighlighterProps> = ({
  highlightSections,
  featureExplanations = [],
  defaultExpanded = true,
  maxContentHeight = 300,
}) => {
  const { t } = useTranslation();
  const [expandedSections, setExpandedSections] = React.useState<Set<string>>(
    new Set()
  );

  /**
   * Toggle section expansion
   */
  const toggleSection = (sectionName: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionName)) {
        next.delete(sectionName);
      } else {
        next.add(sectionName);
      }
      return next;
    });
  };

  /**
   * Expand all sections
   */
  const expandAll = () => {
    setExpandedSections(new Set(Object.keys(highlightSections)));
  };

  /**
   * Collapse all sections
   */
  const collapseAll = () => {
    setExpandedSections(new Set());
  };

  // Convert highlight sections to normalized format
  const sections = Object.entries(highlightSections).map(
    ([sectionName, sectionData]) => ({
      sectionName,
      ...normalizeSectionData(sectionName, sectionData),
    })
  );

  // Sort by impact score (highest first)
  const sortedSections = [...sections].sort(
    (a, b) => b.impactScore - a.impactScore
  );

  /**
   * Render empty state
   */
  if (Object.keys(highlightSections).length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>{t('resumeHighlighter.noData.title')}</AlertTitle>
        {t('resumeHighlighter.noData.message')}
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 2,
        }}
      >
        <Box>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            {t('resumeHighlighter.title')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('resumeHighlighter.description', {
              count: sections.length,
            })}
          </Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Chip
            label={t('resumeHighlighter.expandAll')}
            onClick={expandAll}
            clickable
            size="small"
            variant="outlined"
          />
          <Chip
            label={t('resumeHighlighter.collapseAll')}
            onClick={collapseAll}
            clickable
            size="small"
            variant="outlined"
          />
        </Stack>
      </Box>

      {/* Feature-to-Section Mapping Legend */}
      <Paper
        elevation={1}
        sx={{
          p: 2,
          bgcolor: 'info.main',
          bgcolor: 'info.dark',
          color: 'info.contrastText',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <BulbIcon />
          <Typography variant="body2" fontWeight={500}>
            {t('resumeHighlighter.mappingLegend')}
          </Typography>
        </Box>
      </Paper>

      {/* Section Cards */}
      <Grid container spacing={2}>
        {sortedSections.map((section) => {
          const impactConfig = getImpactConfig(
            section.impactDirection,
            section.impactScore
          );
          const isExpanded = expandedSections.has(section.sectionName);

          return (
            <Grid item xs={12} md={6} key={section.sectionName}>
              <Card
                variant="outlined"
                sx={{
                  height: '100%',
                  borderColor: `${impactConfig.color}.main`,
                  borderWidth: 2,
                  transition: 'all 0.2s',
                  '&:hover': {
                    boxShadow: 3,
                  },
                }}
              >
                <CardContent>
                  {/* Section Header */}
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 2,
                    }}
                  >
                    <Box sx={{ flex: 1 }}>
                      <Typography
                        variant="subtitle1"
                        fontWeight={600}
                        color="text.primary"
                      >
                        {section.featureName}
                      </Typography>
                      <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
                        <Chip
                          label={impactConfig.label}
                          size="small"
                          color={impactConfig.color}
                          icon={impactConfig.icon}
                        />
                        <Chip
                          label={`${section.impactScore}% impact`}
                          size="small"
                          variant="outlined"
                        />
                      </Stack>
                    </Box>
                    <Tooltip
                      title={
                        isExpanded
                          ? t('resumeHighlighter.collapse')
                          : t('resumeHighlighter.expand')
                      }
                    >
                      <IconButton
                        size="small"
                        onClick={() => toggleSection(section.sectionName)}
                        color={impactConfig.color}
                      >
                        {isExpanded ? <HideIcon /> : <ViewIcon />}
                      </IconButton>
                    </Tooltip>
                  </Box>

                  {/* Description (if available) */}
                  {section.description && (
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ display: 'block', mb: 1 }}
                    >
                      {section.description}
                    </Typography>
                  )}

                  {/* Section Content */}
                  <Box
                    sx={{
                      bgcolor: 'grey.50',
                      borderRadius: 1,
                      p: 2,
                      borderLeft: 3,
                      borderColor: `${impactConfig.color}.main`,
                    }}
                  >
                    <Typography
                      variant="body2"
                      sx={{
                        maxHeight: isExpanded ? maxContentHeight : 100,
                        overflow: 'auto',
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                      }}
                    >
                      {section.sectionContent}
                    </Typography>
                  </Box>

                  {/* Feature Association */}
                  {featureExplanations.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        fontWeight={600}
                      >
                        {t('resumeHighlighter.associatedFeatures')}:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                        {featureExplanations
                          .filter((feat) =>
                            feat.feature_name
                              .toLowerCase()
                              .includes(section.featureName.toLowerCase())
                          )
                          .slice(0, 3)
                          .map((feat) => (
                            <Chip
                              key={feat.feature_name}
                              label={feat.feature_name}
                              size="small"
                              variant="outlined"
                              color={impactConfig.color}
                            />
                          ))}
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Summary Statistics */}
      <Paper elevation={1} sx={{ p: 2, bgcolor: 'background.default' }}>
        <Grid container spacing={2}>
          <Grid item xs={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="success.main" fontWeight={700}>
                {
                  sections.filter((s) => s.impactDirection === 'positive')
                    .length
                }
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {t('resumeHighlighter.stats.positive')}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="info.main" fontWeight={700}>
                {
                  sections.filter((s) => s.impactDirection === 'neutral')
                    .length
                }
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {t('resumeHighlighter.stats.neutral')}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="error.main" fontWeight={700}>
                {
                  sections.filter((s) => s.impactDirection === 'negative')
                    .length
                }
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {t('resumeHighlighter.stats.negative')}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Stack>
  );
};

export default ResumeHighlighter;
export type { ResumeHighlighterProps, FeatureSectionMapping, ResumeHighlightSections };
