/**
 * Learning Recommendations Card Component
 *
 * Displays learning resources organized by skill with filtering options.
 */

import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  CardActions,
  Chip,
  Stack,
  Button,
  Grid,
  IconButton,
  Collapse,
  Badge,
  ToggleButton,
  ToggleButtonGroup,
  Link,
  Divider,
  Rating,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  School as CourseIcon,
  Verified as CertificationIcon,
  MenuBook as BookIcon,
  PlayCircle as VideoIcon,
  Work as WorkshopIcon,
  Code as TutorialIcon,
  Launch as LaunchIcon,
  AttachMoney as CostIcon,
  FreeBreakfast as FreeIcon,
} from '@mui/icons-material';
import type { LearningRecommendationsResponse, LearningResource } from '@/types/api';

interface LearningRecommendationsCardProps {
  recommendations: LearningRecommendationsResponse;
  onResourceClick?: (resource: LearningResource) => void;
}

/**
 * Get resource icon based on type
 */
function getResourceIcon(type: string) {
  switch (type) {
    case 'course':
      return <CourseIcon />;
    case 'certification':
      return <CertificationIcon />;
    case 'book':
      return <BookIcon />;
    case 'video':
      return <VideoIcon />;
    case 'workshop':
      return <WorkshopIcon />;
    case 'tutorial':
      return <TutorialIcon />;
    default:
      return <CourseIcon />;
  }
}

/**
 * Get resource type label
 */
function getResourceTypeLabel(type: string, t: any): string {
  const labels: Record<string, string> = {
    course: t('skillGap.resourceType.course', { defaultValue: 'Course' }),
    certification: t('skillGap.resourceType.certification', { defaultValue: 'Certification' }),
    book: t('skillGap.resourceType.book', { defaultValue: 'Book' }),
    tutorial: t('skillGap.resourceType.tutorial', { defaultValue: 'Tutorial' }),
    video: t('skillGap.resourceType.video', { defaultValue: 'Video' }),
    bootcamp: t('skillGap.resourceType.bootcamp', { defaultValue: 'Bootcamp' }),
    workshop: t('skillGap.resourceType.workshop', { defaultValue: 'Workshop' }),
    other: t('skillGap.resourceType.other', { defaultValue: 'Other' }),
  };
  return labels[type] || type;
}

/**
 * Skill Recommendations Section
 */
interface SkillSectionProps {
  skill: string;
  resources: LearningResource[];
  onResourceClick?: (resource: LearningResource) => void;
}

function SkillSection({ skill, resources, onResourceClick }: SkillSectionProps) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(true);

  return (
    <Paper sx={{ mb: 2 }} variant="outlined">
      <Box
        sx={{
          p: 2,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          bgcolor: 'action.hover',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <Box display="flex" alignItems="center" gap={1}>
          <Typography variant="subtitle1" fontWeight="medium">
            {skill}
          </Typography>
          <Badge badgeContent={resources.length} color="primary" />
        </Box>
        {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
      </Box>

      <Collapse in={expanded}>
        <Box sx={{ p: 2 }}>
          <Grid container spacing={2}>
            {resources.map((resource, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    {/* Resource Type Badge */}
                    <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
                      <Chip
                        icon={getResourceIcon(resource.resource_type)}
                        label={getResourceTypeLabel(resource.resource_type, t)}
                        size="small"
                        variant="outlined"
                      />
                      {resource.certificate_offered && (
                        <Tooltip title={t('skillGap.offersCertificate', { defaultValue: 'Offers Certificate' })}>
                          <CertificationIcon color="primary" fontSize="small" />
                        </Tooltip>
                      )}
                    </Box>

                    {/* Title */}
                    <Typography variant="subtitle2" fontWeight="medium" gutterBottom>
                      {resource.title}
                    </Typography>

                    {/* Description */}
                    {resource.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {resource.description.length > 100
                          ? `${resource.description.substring(0, 100)}...`
                          : resource.description}
                      </Typography>
                    )}

                    {/* Provider */}
                    {resource.provider && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {t('skillGap.provider', { defaultValue: 'Provider' })}: {resource.provider}
                      </Typography>
                    )}

                    {/* Rating */}
                    {resource.rating && (
                      <Box display="flex" alignItems="center" gap={0.5} mt={1}>
                        <Rating
                          value={resource.rating}
                          precision={0.1}
                          readOnly
                          size="small"
                        />
                        <Typography variant="caption" color="text.secondary">
                          ({resource.rating_count || 0})
                        </Typography>
                      </Box>
                    )}

                    {/* Details */}
                    <Stack direction="row" spacing={1} mt={1} flexWrap="wrap">
                      {resource.skill_level && (
                        <Chip label={resource.skill_level} size="small" variant="outlined" />
                      )}
                      <Chip
                        icon={resource.access_type === 'free' ? <FreeIcon fontSize="small" /> : <CostIcon fontSize="small" />}
                        label={resource.access_type === 'free' ? t('skillGap.free', { defaultValue: 'Free' }) : `$${resource.cost_amount || 0}`}
                        size="small"
                        color={resource.access_type === 'free' ? 'success' : 'default'}
                      />
                      {resource.duration_hours && (
                        <Chip
                          label={`${resource.duration_hours}h`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Stack>

                    {/* Scores (hidden by default, can be toggled) */}
                    <Box mt={1}>
                      <Typography variant="caption" color="text.secondary">
                        {t('skillGap.relevance', { defaultValue: 'Relevance' })}: {(resource.relevance_score * 100).toFixed(0)}% |
                        {t('skillGap.quality', { defaultValue: 'Quality' })}: {(resource.quality_score * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                  </CardContent>

                  <CardActions>
                    {resource.url ? (
                      <Button
                        size="small"
                        href={resource.url}
                        LinkComponent={'a' as const}
                        target="_blank"
                        rel="noopener noreferrer"
                        startIcon={<LaunchIcon />}
                        onClick={() => onResourceClick?.(resource)}
                      >
                        {t('skillGap.viewResource', { defaultValue: 'View' })}
                      </Button>
                    ) : (
                      <Button
                        size="small"
                        startIcon={<LaunchIcon />}
                        disabled
                      >
                        {t('skillGap.viewResource', { defaultValue: 'View' })}
                      </Button>
                    )}
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      </Collapse>
    </Paper>
  );
}

/**
 * Learning Recommendations Card Component
 */
export function LearningRecommendationsCard({
  recommendations,
  onResourceClick,
}: LearningRecommendationsCardProps) {
  const { t } = useTranslation();
  const [filter, setFilter] = useState<'all' | 'free' | 'paid'>('all');
  const [sortBy, setSortBy] = useState<'priority' | 'duration' | 'cost'>('priority');

  // Filter and sort recommendations
  const filteredRecommendations = useMemo(() => {
    const result: Record<string, LearningResource[]> = {};

    for (const [skill, resources] of Object.entries(recommendations.recommendations)) {
      let filtered = resources;

      // Apply cost filter
      if (filter === 'free') {
        filtered = filtered.filter((r) => r.access_type === 'free');
      } else if (filter === 'paid') {
        filtered = filtered.filter((r) => r.access_type !== 'free');
      }

      // Apply sorting
      filtered = [...filtered].sort((a, b) => {
        if (sortBy === 'duration') {
          return (a.duration_hours || 0) - (b.duration_hours || 0);
        }
        if (sortBy === 'cost') {
          return (a.cost_amount || 0) - (b.cost_amount || 0);
        }
        return b.priority_score - a.priority_score;
      });

      if (filtered.length > 0) {
        result[skill] = filtered;
      }
    }

    return result;
  }, [recommendations.recommendations, filter, sortBy]);

  const totalResources = Object.values(filteredRecommendations).reduce(
    (sum, resources) => sum + resources.length,
    0
  );

  return (
    <Stack spacing={2}>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={2}>
        <Typography variant="h6">
          {t('skillGap.recommendationsTitle', { defaultValue: 'Learning Recommendations' })}
        </Typography>

        {/* Filters */}
        <Box display="flex" gap={1}>
          <ToggleButtonGroup
            value={filter}
            exclusive
            size="small"
            onChange={(_, value) => value && setFilter(value)}
          >
            <ToggleButton value="all">
              {t('skillGap.filter.all', { defaultValue: 'All' })}
            </ToggleButton>
            <ToggleButton value="free">
              {t('skillGap.filter.freeOnly', { defaultValue: 'Free Only' })}
            </ToggleButton>
            <ToggleButton value="paid">
              {t('skillGap.filter.paid', { defaultValue: 'Paid' })}
            </ToggleButton>
          </ToggleButtonGroup>

          <ToggleButtonGroup
            value={sortBy}
            exclusive
            size="small"
            onChange={(_, value) => value && setSortBy(value)}
          >
            <ToggleButton value="priority">
              {t('skillGap.sort.priority', { defaultValue: 'Priority' })}
            </ToggleButton>
            <ToggleButton value="duration">
              {t('skillGap.sort.duration', { defaultValue: 'Duration' })}
            </ToggleButton>
            <ToggleButton value="cost">
              {t('skillGap.sort.cost', { defaultValue: 'Cost' })}
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </Box>

      {/* Summary */}
      <Paper sx={{ p: 2 }} variant="outlined">
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Typography variant="h4" color="primary">
              {totalResources}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('skillGap.totalResources', { defaultValue: 'Total Resources' })}
            </Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="h4" color="success.main">
              {recommendations.alternative_free_resources}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('skillGap.freeResources', { defaultValue: 'Free Resources' })}
            </Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="h4">
              {recommendations.total_cost > 0 ? `$${recommendations.total_cost.toFixed(0)}` : '-'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('skillGap.totalCost', { defaultValue: 'Total Cost (Paid)' })}
            </Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="h4">
              {recommendations.total_duration_hours > 0
                ? `${recommendations.total_duration_hours.toFixed(0)}h`
                : '-'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('skillGap.totalDuration', { defaultValue: 'Total Duration' })}
            </Typography>
          </Grid>
        </Grid>

        {recommendations.skills_with_certifications.length > 0 && (
          <Box mt={2}>
            <Typography variant="caption" color="text.secondary">
              {t('skillGap.certificationsAvailable', {
                defaultValue: 'Certifications available for: {{skills}}',
                skills: recommendations.skills_with_certifications.join(', '),
              })}
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Skill Sections */}
      {Object.entries(filteredRecommendations).length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            {t('skillGap.noRecommendations', {
              defaultValue: 'No recommendations match the current filters.',
            })}
          </Typography>
        </Paper>
      ) : (
        <Box>
          {recommendations.priority_ordering
            .filter((skill) => filteredRecommendations[skill] !== undefined)
            .map((skill) => (
              <SkillSection
                key={skill}
                skill={skill}
                resources={filteredRecommendations[skill]!}
                onResourceClick={onResourceClick}
              />
            ))}
        </Box>
      )}

      {/* Summary Text */}
      <Typography variant="caption" color="text.secondary" align="center" display="block">
        {recommendations.summary}
      </Typography>
    </Stack>
  );
}

export default LearningRecommendationsCard;
