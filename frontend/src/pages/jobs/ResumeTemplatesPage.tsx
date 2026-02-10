import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  CardMedia,
  CardActionArea,
  Button,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  DescriptionOutlined,
  WorkOutline,
  School,
  Code,
  BusinessCenter,
  Star,
} from '@mui/icons-material';
import { resumeTemplatesClient, type ResumeTemplateResponse } from '@/api/resume-templates';

/**
 * Resume template configuration with UI properties
 */
interface ResumeTemplate extends ResumeTemplateResponse {
  category: 'professional' | 'creative' | 'technical' | 'entry-level';
  features: string[];
  recommendedFor: string[];
  color: string;
}

/**
 * Map template_type to category
 */
const getTemplateCategory = (templateType: string): ResumeTemplate['category'] => {
  const typeLower = templateType.toLowerCase();
  if (typeLower.includes('creative') || typeLower.includes('designer')) {
    return 'creative';
  } else if (typeLower.includes('tech') || typeLower.includes('developer') || typeLower.includes('data')) {
    return 'technical';
  } else if (typeLower.includes('entry') || typeLower.includes('junior')) {
    return 'entry-level';
  }
  return 'professional';
};

/**
 * Get color for template type
 */
const getTemplateColor = (templateType: string): string => {
  const typeLower = templateType.toLowerCase();
  if (typeLower.includes('creative')) {
    return '#9c27b0';
  } else if (typeLower.includes('tech') || typeLower.includes('developer')) {
    return '#f57c00';
  } else if (typeLower.includes('data')) {
    return '#0097a7';
  } else if (typeLower.includes('entry') || typeLower.includes('junior')) {
    return '#546e7a';
  } else if (typeLower.includes('executive')) {
    return '#2e7d32';
  }
  return '#1976d2';
};

/**
 * Generate features from template config
 */
const getTemplateFeatures = (template: ResumeTemplateResponse): string[] => {
  const features: string[] = [];
  if (template.is_ats_compliant) {
    features.push('ATS-Friendly');
  }
  if (template.style_config?.primary_color) {
    features.push('Custom Colors');
  }
  if (template.layout_config?.margins) {
    features.push('Adjustable Layout');
  }
  if (template.section_config) {
    features.push('Custom Sections');
  }
  // Add default features if none
  if (features.length === 0) {
    features.push('Clean Layout', 'Professional Font');
  }
  return features.slice(0, 3);
};

/**
 * Generate recommended roles based on template type
 */
const getRecommendedRoles = (templateType: string): string[] => {
  const typeLower = templateType.toLowerCase();
  if (typeLower.includes('modern')) {
    return ['Business Analyst', 'Project Manager', 'Consultant'];
  } else if (typeLower.includes('executive')) {
    return ['CEO', 'Director', 'VP', 'Senior Manager'];
  } else if (typeLower.includes('creative')) {
    return ['Graphic Designer', 'Art Director', 'UX Designer'];
  } else if (typeLower.includes('tech') || typeLower.includes('developer')) {
    return ['Software Engineer', 'Full Stack Developer', 'DevOps'];
  } else if (typeLower.includes('data')) {
    return ['Data Scientist', 'ML Engineer', 'Research Analyst'];
  } else if (typeLower.includes('entry') || typeLower.includes('junior')) {
    return ['Recent Graduate', 'Intern', 'Junior Associate'];
  }
  return ['Professional', 'Manager', 'Specialist'];
};

/**
 * Transform API template to UI template
 */
const transformTemplate = (apiTemplate: ResumeTemplateResponse): ResumeTemplate => {
  const category = getTemplateCategory(apiTemplate.template_type);
  return {
    ...apiTemplate,
    category,
    features: getTemplateFeatures(apiTemplate),
    recommendedFor: getRecommendedRoles(apiTemplate.template_type),
    color: getTemplateColor(apiTemplate.template_type),
  };
};

/**
 * Get category icon
 */
const getCategoryIcon = (category: ResumeTemplate['category']) => {
  switch (category) {
    case 'professional':
      return <BusinessCenter />;
    case 'creative':
      return <Star />;
    case 'technical':
      return <Code />;
    case 'entry-level':
      return <School />;
    default:
      return <DescriptionOutlined />;
  }
};

/**
 * Get category color
 */
const getCategoryColor = (category: ResumeTemplate['category']): string => {
  switch (category) {
    case 'professional':
      return '#1976d2';
    case 'creative':
      return '#9c27b0';
    case 'technical':
      return '#f57c00';
    case 'entry-level':
      return '#546e7a';
    default:
      return '#757575';
  }
};

/**
 * Resume Templates Page Component
 *
 * Provides a gallery of resume templates for job seekers to browse and select.
 * Templates are organized by category and include preview images, features,
 * and recommendations for different job roles.
 *
 * Users can select a template to preview and use for resume formatting.
 */
const ResumeTemplatesPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [templates, setTemplates] = useState<ResumeTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<
    ResumeTemplate['category'] | 'all'
  >('all');
  const [hoveredTemplate, setHoveredTemplate] = useState<string | null>(null);

  /**
   * Load templates from API on component mount
   */
  useEffect(() => {
    const loadTemplates = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await resumeTemplatesClient.listResumeTemplates({
          is_active: true,
        });
        const transformedTemplates = data.templates.map(transformTemplate);
        setTemplates(transformedTemplates);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load templates';
        setError(errorMessage);
        console.error('Error loading resume templates:', err);
      } finally {
        setLoading(false);
      }
    };

    loadTemplates();
  }, []);

  /**
   * Get unique categories from loaded templates
   */
  const categories: Array<(ResumeTemplate['category'] | 'all')> = [
    'all',
    ...Array.from(new Set(templates.map((t) => t.category))),
  ];

  /**
   * Filter templates by selected category
   */
  const filteredTemplates =
    selectedCategory === 'all'
      ? templates
      : templates.filter((t) => t.category === selectedCategory);

  /**
   * Handle template selection
   */
  const handleSelectTemplate = (templateId: string) => {
    // Navigate to resume upload with selected template
    navigate(`/jobs/upload?template=${templateId}`);
  };

  /**
   * Handle template preview
   */
  const handlePreviewTemplate = (templateId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    // Open preview modal or navigate to preview page
    // For now, navigate to upload with preview flag
    navigate(`/jobs/upload?template=${templateId}&preview=true`);
  };

  return (
    <Box>
      {/* Page Header */}
      <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
        {t('templates.title') || 'Resume Templates'}
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        {t('templates.subtitle') ||
          'Choose from our professionally designed resume templates to create a standout resume.'}
      </Typography>

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
          <CircularProgress size={40} />
          <Typography sx={{ ml: 2 }} color="text.secondary">
            Loading templates...
          </Typography>
        </Box>
      )}

      {/* Error State */}
      {error && !loading && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* No Templates State */}
      {!loading && !error && templates.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No templates available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Please check back later or contact support.
          </Typography>
        </Paper>
      )}

      {/* Category Filter - Show only when not loading and templates exist */}
      {!loading && !error && templates.length > 0 && (
        <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
            <Typography variant="subtitle2" fontWeight={600} sx={{ mr: 1 }}>
              Filter by:
            </Typography>
            {categories.map((category) => (
              <Chip
                key={category}
                label={
                  category === 'all'
                    ? 'All Templates'
                    : category.charAt(0).toUpperCase() + category.slice(1)
                }
                onClick={() => setSelectedCategory(category)}
                color={selectedCategory === category ? 'primary' : 'default'}
                variant={selectedCategory === category ? 'filled' : 'outlined'}
                icon={category !== 'all' ? getCategoryIcon(category) : undefined}
                sx={{ textTransform: 'capitalize' }}
              />
            ))}
          </Box>
        </Paper>
      )}

      {/* Templates Grid - Show only when not loading and templates exist */}
      {!loading && !error && templates.length > 0 && (
        <Grid container spacing={3}>
          {filteredTemplates.map((template) => (
            <Grid item xs={12} sm={6} md={4} key={template.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  transform: hoveredTemplate === template.id ? 'translateY(-4px)' : 'none',
                  boxShadow:
                    hoveredTemplate === template.id ? 8 : 1,
                  borderLeft: `4px solid ${template.color}`,
                }}
                onMouseEnter={() => setHoveredTemplate(template.id)}
                onMouseLeave={() => setHoveredTemplate(null)}
              >
                <CardActionArea
                  onClick={() => handleSelectTemplate(template.id)}
                  sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}
                >
                  {/* Template Preview */}
                  <CardMedia
                    component="div"
                    sx={{
                      height: 200,
                      bgcolor: template.color + '20',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      position: 'relative',
                    }}
                  >
                    <DescriptionOutlined
                      sx={{ fontSize: 80, color: template.color, opacity: 0.5 }}
                    />
                    <Chip
                      label={template.category}
                      size="small"
                      sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        bgcolor: template.color,
                        color: 'white',
                        textTransform: 'capitalize',
                      }}
                    />
                  </CardMedia>

                  <CardContent sx={{ flexGrow: 1 }}>
                    {/* Template Name */}
                    <Typography variant="h6" fontWeight={600} gutterBottom>
                      {template.name}
                    </Typography>

                    {/* Template Description */}
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      paragraph
                      sx={{ minHeight: 40 }}
                    >
                      {template.description}
                    </Typography>

                    {/* Features */}
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        Features:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {template.features.slice(0, 3).map((feature) => (
                          <Chip
                            key={feature}
                            label={feature}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                          />
                        ))}
                      </Box>
                    </Box>

                    {/* Recommended For */}
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        Recommended for:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {template.recommendedFor.slice(0, 2).map((role) => (
                          <Chip
                            key={role}
                            label={role}
                            size="small"
                            sx={{
                              fontSize: '0.7rem',
                              height: 20,
                              bgcolor: 'action.hover',
                            }}
                          />
                        ))}
                        {template.recommendedFor.length > 2 && (
                          <Chip
                            label={`+${template.recommendedFor.length - 2}`}
                            size="small"
                            sx={{
                              fontSize: '0.7rem',
                              height: 20,
                              bgcolor: 'action.hover',
                            }}
                          />
                        )}
                      </Box>
                    </Box>

                    {/* Action Buttons */}
                    <Box sx={{ display: 'flex', gap: 1, mt: 'auto' }}>
                      <Button
                        variant="contained"
                        size="small"
                        fullWidth
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectTemplate(template.id);
                        }}
                      >
                        Use Template
                      </Button>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={(e) => handlePreviewTemplate(template.id, e)}
                      >
                        Preview
                      </Button>
                    </Box>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Info Section */}
      <Paper
        elevation={0}
        sx={{
          mt: 4,
          p: 3,
          bgcolor: 'info.main',
          color: 'info.contrastText',
        }}
      >
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          💡 Pro Tip
        </Typography>
        <Typography variant="body2">
          {t('templates.proTip') ||
            'Choose a template that best fits your industry and experience level. All templates are ATS-friendly and optimized for both digital and print formats.'}
        </Typography>
      </Paper>
    </Box>
  );
};

export default ResumeTemplatesPage;
export { ResumeTemplatesPage };
