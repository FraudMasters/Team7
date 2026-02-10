import React, { useState } from 'react';
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
} from '@mui/material';
import {
  DescriptionOutlined,
  WorkOutline,
  School,
  Code,
  BusinessCenter,
  Star,
} from '@mui/icons-material';

/**
 * Resume template configuration
 */
interface ResumeTemplate {
  id: string;
  name: string;
  description: string;
  category: 'professional' | 'creative' | 'technical' | 'entry-level';
  previewImage: string;
  features: string[];
  recommendedFor: string[];
  color: string;
}

/**
 * Available resume templates
 */
const RESUME_TEMPLATES: ResumeTemplate[] = [
  {
    id: 'modern-professional',
    name: 'Modern Professional',
    description: 'Clean and contemporary design for corporate roles',
    category: 'professional',
    previewImage: '/templates/modern-professional.png',
    features: ['ATS-Friendly', 'Clean Layout', 'Professional Font'],
    recommendedFor: ['Business Analyst', 'Project Manager', 'Consultant'],
    color: '#1976d2',
  },
  {
    id: 'executive',
    name: 'Executive',
    description: 'Sophisticated layout for senior professionals',
    category: 'professional',
    previewImage: '/templates/executive.png',
    features: ['Elegant Design', 'Leadership Focus', 'Strategic Layout'],
    recommendedFor: ['CEO', 'Director', 'VP', 'Senior Manager'],
    color: '#2e7d32',
  },
  {
    id: 'creative-designer',
    name: 'Creative Designer',
    description: 'Bold and artistic template for creative industries',
    category: 'creative',
    previewImage: '/templates/creative-designer.png',
    features: ['Visual Layout', 'Portfolio Section', 'Color Options'],
    recommendedFor: ['Graphic Designer', 'Art Director', 'UX Designer'],
    color: '#9c27b0',
  },
  {
    id: 'tech-developer',
    name: 'Tech Developer',
    description: 'Optimized for software engineering roles',
    category: 'technical',
    previewImage: '/templates/tech-developer.png',
    features: ['Skills Highlight', 'Projects Section', 'GitHub Integration'],
    recommendedFor: ['Software Engineer', 'Full Stack Developer', 'DevOps'],
    color: '#f57c00',
  },
  {
    id: 'data-scientist',
    name: 'Data Scientist',
    description: 'Perfect for analytics and ML roles',
    category: 'technical',
    previewImage: '/templates/data-scientist.png',
    features: ['Quantitative Focus', 'Research Section', 'Publication Area'],
    recommendedFor: ['Data Scientist', 'ML Engineer', 'Research Analyst'],
    color: '#0097a7',
  },
  {
    id: 'entry-level',
    name: 'Entry Level',
    description: 'Great template for recent graduates',
    category: 'entry-level',
    previewImage: '/templates/entry-level.png',
    features: ['Education Focus', 'Simple Layout', 'Internship Section'],
    recommendedFor: ['Recent Graduate', 'Intern', 'Junior Associate'],
    color: '#546e7a',
  },
];

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

  const [selectedCategory, setSelectedCategory] = useState<
    ResumeTemplate['category'] | 'all'
  >('all');
  const [hoveredTemplate, setHoveredTemplate] = useState<string | null>(null);

  /**
   * Get unique categories from templates
   */
  const categories: Array<(ResumeTemplate['category'] | 'all')> = [
    'all',
    ...Array.from(new Set(RESUME_TEMPLATES.map((t) => t.category))),
  ];

  /**
   * Filter templates by selected category
   */
  const filteredTemplates =
    selectedCategory === 'all'
      ? RESUME_TEMPLATES
      : RESUME_TEMPLATES.filter((t) => t.category === selectedCategory);

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

      {/* Category Filter */}
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

      {/* Templates Grid */}
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
