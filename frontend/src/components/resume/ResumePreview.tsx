import React, { useMemo, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Stack,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  IconButton,
  Button,
  Tooltip,
  Link,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import type {
  ResumeContent,
  WorkExperienceEntry,
  EducationEntry,
  SkillEntry,
  CertificationEntry,
  LanguageEntry,
  ProjectEntry,
} from '@/types/resumeBuilder';

/**
 * ResumePreview Component Props
 */
interface ResumePreviewProps {
  /** Resume content to preview */
  content: ResumeContent | null;
  /** Loading state */
  loading?: boolean;
  /** Error message */
  error?: string | null;
  /** Component title */
  title?: string;
  /** Show zoom controls */
  showZoomControls?: boolean;
  /** Show print button */
  showPrintButton?: boolean;
  /** Callback when print is triggered */
  onPrint?: () => void;
  /** Template style (affects colors) */
  templateStyle?: 'modern' | 'classic' | 'minimal' | 'professional';
  /** Custom class name for the preview container */
  className?: string;
  /** Whether preview is in compact mode */
  compact?: boolean;
}

/**
 * Template style configurations
 */
const TEMPLATE_STYLES = {
  modern: {
    primaryColor: '#2563eb',
    secondaryColor: '#64748b',
    headerBg: '#f1f5f9',
    accentColor: '#3b82f6',
  },
  classic: {
    primaryColor: '#1f2937',
    secondaryColor: '#6b7280',
    headerBg: '#f9fafb',
    accentColor: '#374151',
  },
  minimal: {
    primaryColor: '#000000',
    secondaryColor: '#525252',
    headerBg: '#ffffff',
    accentColor: '#171717',
  },
  professional: {
    primaryColor: '#1e40af',
    secondaryColor: '#475569',
    headerBg: '#f8fafc',
    accentColor: '#2563eb',
  },
};

/**
 * Format date range for display
 */
const formatDateRange = (startDate?: string, endDate?: string, isCurrent?: boolean): string => {
  const start = startDate || '';
  const end = isCurrent ? 'Present' : endDate || '';
  if (!start && !end) return '';
  return `${start} - ${end}`;
};

/**
 * Get proficiency badge color
 */
const getProficiencyColor = (level?: string): 'success' | 'primary' | 'secondary' | 'default' => {
  switch (level) {
    case 'expert':
    case 'native':
      return 'success';
    case 'advanced':
    case 'fluent':
      return 'primary';
    case 'intermediate':
      return 'secondary';
    default:
      return 'default';
  }
};

/**
 * ResumePreview Component
 *
 * Displays a live preview of a resume with:
 * - Professional formatting for all sections
 * - Template style options
 * - Zoom controls
 * - Print-ready layout
 * - Responsive design
 * - Empty state handling
 *
 * @example
 * ```tsx
 * <ResumePreview
 *   content={resumeContent}
 *   loading={false}
 *   showZoomControls
 *   onPrint={() => window.print()}
 *   templateStyle="modern"
 * />
 * ```
 */
const ResumePreview: React.FC<ResumePreviewProps> = ({
  content,
  loading = false,
  error = null,
  title = 'Resume Preview',
  showZoomControls = true,
  showPrintButton = true,
  onPrint,
  templateStyle = 'modern',
  className,
  compact = false,
}) => {
  const [zoom, setZoom] = React.useState(100);

  const style = TEMPLATE_STYLES[templateStyle];

  /**
   * Handle zoom in
   */
  const handleZoomIn = useCallback(() => {
    setZoom((prev) => Math.min(prev + 10, 150));
  }, []);

  /**
   * Handle zoom out
   */
  const handleZoomOut = useCallback(() => {
    setZoom((prev) => Math.max(prev - 10, 50));
  }, []);

  /**
   * Handle reset zoom
   */
  const handleZoomReset = useCallback(() => {
    setZoom(100);
  }, []);

  /**
   * Handle print
   */
  const handlePrint = useCallback(() => {
    if (onPrint) {
      onPrint();
    } else {
      window.print();
    }
  }, [onPrint]);

  /**
   * Check if content is empty
   */
  const isEmpty = useMemo(() => {
    if (!content) return true;

    const hasPersonalInfo = content.personal_info && (
      content.personal_info.full_name ||
      content.personal_info.email ||
      content.personal_info.phone
    );
    const hasSummary = content.summary && content.summary.trim().length > 0;
    const hasWork = content.work_experience && content.work_experience.length > 0;
    const hasEducation = content.education && content.education.length > 0;
    const hasSkills = content.skills && content.skills.length > 0;
    const hasCertifications = content.certifications && content.certifications.length > 0;
    const hasLanguages = content.languages && content.languages.length > 0;
    const hasProjects = content.projects && content.projects.length > 0;

    return !hasPersonalInfo && !hasSummary && !hasWork && !hasEducation &&
           !hasSkills && !hasCertifications && !hasLanguages && !hasProjects;
  }, [content]);

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box css={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
        <CircularProgress size={48} />
        <Typography color="text.secondary" css={{ mt: 2 }}>
          Loading resume preview...
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
  if (isEmpty) {
    return (
      <Box
        css={{
          textAlign: 'center',
          py: 8,
          px: 4,
          border: '2px dashed',
          borderColor: 'divider',
          borderRadius: 2,
        }}
      >
        <Icon name="file-text" css={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
        <Typography fontWeight={600} color="text.secondary" gutterBottom>
          No Resume Content
        </Typography>
        <Typography color="text.secondary" variant="body2">
          Start adding your information to see a preview of your resume.
        </Typography>
      </Box>
    );
  }

  /**
   * Render contact links
   */
  const renderContactLinks = () => {
    const links = [];
    if (content?.personal_info?.linkedin_url) {
      links.push(
        <Link
          key="linkedin"
          href={content.personal_info.linkedin_url}
          target="_blank"
          rel="noopener noreferrer"
          css={{ display: 'flex', alignItems: 'center', gap: 0.5, color: style.primaryColor }}
        >
          <Icon name="linkedin" size={14} />
          LinkedIn
        </Link>
      );
    }
    if (content?.personal_info?.github_url) {
      links.push(
        <Link
          key="github"
          href={content.personal_info.github_url}
          target="_blank"
          rel="noopener noreferrer"
          css={{ display: 'flex', alignItems: 'center', gap: 0.5, color: style.primaryColor }}
        >
          <Icon name="github" size={14} />
          GitHub
        </Link>
      );
    }
    if (content?.personal_info?.website_url) {
      links.push(
        <Link
          key="website"
          href={content.personal_info.website_url}
          target="_blank"
          rel="noopener noreferrer"
          css={{ display: 'flex', alignItems: 'center', gap: 0.5, color: style.primaryColor }}
        >
          <Icon name="globe" size={14} />
          Website
        </Link>
      );
    }
    return links.length > 0 ? (
      <Stack direction="row" spacing={2} css={{ flexWrap: 'wrap' }}>
        {links}
      </Stack>
    ) : null;
  };

  /**
   * Render work experience item
   */
  const renderWorkExperienceItem = (entry: WorkExperienceEntry, index: number) => (
    <Box key={entry.id || index} css={{ mb: 2 }}>
      <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.5 }}>
        <Box>
          <Typography fontWeight={600} css={{ color: style.primaryColor }}>
            {entry.position || 'Position'}
          </Typography>
          <Typography variant="body2" css={{ color: style.secondaryColor }}>
            {entry.company || 'Company'}
            {entry.location && ` • ${entry.location}`}
          </Typography>
        </Box>
        <Typography
          variant="caption"
          css={{ color: style.secondaryColor, whiteSpace: 'nowrap', ml: 2 }}
        >
          {formatDateRange(entry.start_date, entry.end_date, entry.is_current)}
        </Typography>
      </Box>
      {entry.description && (
        <Typography
          variant="body2"
          css={{
            mt: 1,
            whiteSpace: 'pre-line',
            lineHeight: 1.6,
          }}
        >
          {entry.description}
        </Typography>
      )}
      {entry.skills && entry.skills.length > 0 && (
        <Box css={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
          {entry.skills.map((skill, idx) => (
            <Chip
              key={idx}
              label={skill}
              size="small"
              variant="outlined"
              css={{
                fontSize: '0.7rem',
                height: 20,
                borderColor: style.accentColor,
                color: style.secondaryColor,
              }}
            />
          ))}
        </Box>
      )}
    </Box>
  );

  /**
   * Render education item
   */
  const renderEducationItem = (entry: EducationEntry, index: number) => (
    <Box key={entry.id || index} css={{ mb: 2 }}>
      <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.5 }}>
        <Box>
          <Typography fontWeight={600} css={{ color: style.primaryColor }}>
            {entry.degree || 'Degree'}
            {entry.field_of_study && ` in ${entry.field_of_study}`}
          </Typography>
          <Typography variant="body2" css={{ color: style.secondaryColor }}>
            {entry.institution || 'Institution'}
            {entry.location && ` • ${entry.location}`}
          </Typography>
        </Box>
        <Typography
          variant="caption"
          css={{ color: style.secondaryColor, whiteSpace: 'nowrap', ml: 2 }}
        >
          {formatDateRange(entry.start_date, entry.end_date)}
        </Typography>
      </Box>
      {entry.gpa && (
        <Typography variant="body2" css={{ color: style.secondaryColor, mt: 0.5 }}>
          GPA: {entry.gpa}
        </Typography>
      )}
      {entry.honors && entry.honors.length > 0 && (
        <Typography variant="body2" css={{ color: style.secondaryColor, mt: 0.5 }}>
          Honors: {entry.honors.join(', ')}
        </Typography>
      )}
    </Box>
  );

  /**
   * Render skill item
   */
  const renderSkillItem = (skill: SkillEntry, index: number) => (
    <Box
      key={index}
      css={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        py: 0.5,
      }}
    >
      <Typography variant="body2" css={{ flex: 1 }}>
        {skill.name}
      </Typography>
      {skill.level && (
        <Chip
          label={skill.level}
          size="small"
          color={getProficiencyColor(skill.level)}
          variant="outlined"
          css={{ fontSize: '0.65rem', height: 18 }}
        />
      )}
      {skill.years_of_experience && (
        <Typography variant="caption" css={{ color: style.secondaryColor }}>
          {skill.years_of_experience} yrs
        </Typography>
      )}
    </Box>
  );

  /**
   * Render certification item
   */
  const renderCertificationItem = (entry: CertificationEntry, index: number) => (
    <Box key={entry.id || index} css={{ mb: 1.5 }}>
      <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography fontWeight={600} css={{ color: style.primaryColor, fontSize: '0.9rem' }}>
            {entry.name}
          </Typography>
          <Typography variant="body2" css={{ color: style.secondaryColor }}>
            {entry.issuer}
          </Typography>
        </Box>
        <Typography variant="caption" css={{ color: style.secondaryColor }}>
          {entry.issue_date}
          {entry.expiry_date && ` - ${entry.expiry_date}`}
        </Typography>
      </Box>
      {entry.credential_id && (
        <Typography variant="caption" css={{ color: style.secondaryColor, display: 'block', mt: 0.25 }}>
          Credential ID: {entry.credential_id}
        </Typography>
      )}
    </Box>
  );

  /**
   * Render language item
   */
  const renderLanguageItem = (language: LanguageEntry, index: number) => (
    <Box
      key={index}
      css={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        py: 0.5,
      }}
    >
      <Typography variant="body2">{language.name}</Typography>
      <Stack direction="row" spacing={1} alignItems="center">
        {language.proficiency && (
          <Chip
            label={language.proficiency}
            size="small"
            color={getProficiencyColor(language.proficiency)}
            variant="outlined"
            css={{ fontSize: '0.65rem', height: 18 }}
          />
        )}
        {language.certification && (
          <Typography variant="caption" css={{ color: style.secondaryColor }}>
            ({language.certification})
          </Typography>
        )}
      </Stack>
    </Box>
  );

  /**
   * Render project item
   */
  const renderProjectItem = (entry: ProjectEntry, index: number) => (
    <Box key={entry.id || index} css={{ mb: 2 }}>
      <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.5 }}>
        <Box css={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography fontWeight={600} css={{ color: style.primaryColor }}>
            {entry.name}
          </Typography>
          {entry.url && (
            <Link
              href={entry.url}
              target="_blank"
              rel="noopener noreferrer"
              css={{ display: 'flex', alignItems: 'center' }}
            >
              <Icon name="external-link" size={14} css={{ color: style.accentColor }} />
            </Link>
          )}
        </Box>
        <Typography variant="caption" css={{ color: style.secondaryColor, whiteSpace: 'nowrap' }}>
          {formatDateRange(entry.start_date, entry.end_date)}
        </Typography>
      </Box>
      {entry.description && (
        <Typography variant="body2" css={{ mt: 0.5, lineHeight: 1.6 }}>
          {entry.description}
        </Typography>
      )}
      {entry.technologies && entry.technologies.length > 0 && (
        <Box css={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
          {entry.technologies.map((tech, idx) => (
            <Chip
              key={idx}
              label={tech}
              size="small"
              variant="outlined"
              css={{
                fontSize: '0.65rem',
                height: 18,
                borderColor: style.accentColor,
                color: style.secondaryColor,
              }}
            />
          ))}
        </Box>
      )}
    </Box>
  );

  /**
   * Render section with title
   */
  const renderSection = (
    title: string,
    icon: string,
    content: React.ReactNode,
    visible: boolean
  ) => {
    if (!visible) return null;
    return (
      <Box css={{ mb: 3 }}>
        <Box
          css={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            mb: 1.5,
            pb: 0.5,
            borderBottom: '2px solid',
            borderColor: style.primaryColor,
          }}
        >
          <Icon name={icon} size={18} css={{ color: style.primaryColor }} />
          <Typography
            fontWeight={700}
            css={{ color: style.primaryColor, textTransform: 'uppercase', fontSize: '0.85rem' }}
          >
            {title}
          </Typography>
        </Box>
        {content}
      </Box>
    );
  };

  return (
    <Box className={className}>
      {/* Header with controls */}
      <Box
        css={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
        }}
      >
        <Typography fontWeight={600}>{title}</Typography>
        <Stack direction="row" spacing={1}>
          {showZoomControls && (
            <>
              <Tooltip title="Zoom Out">
                <IconButton size="small" onClick={handleZoomOut} disabled={zoom <= 50}>
                  <Icon name="zoom-out" size={18} />
                </IconButton>
              </Tooltip>
              <Chip label={`${zoom}%`} size="small" onClick={handleZoomReset} css={{ cursor: 'pointer' }} />
              <Tooltip title="Zoom In">
                <IconButton size="small" onClick={handleZoomIn} disabled={zoom >= 150}>
                  <Icon name="zoom-in" size={18} />
                </IconButton>
              </Tooltip>
            </>
          )}
          {showPrintButton && (
            <Tooltip title="Print">
              <Button
                size="small"
                variant="outlined"
                startIcon={<Icon name="printer" size={16} />}
                onClick={handlePrint}
              >
                Print
              </Button>
            </Tooltip>
          )}
        </Stack>
      </Box>

      {/* Preview Container */}
      <Box
        css={{
          overflow: 'auto',
          maxHeight: compact ? 400 : 'calc(100vh - 250px)',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1,
          backgroundColor: '#f5f5f5',
          p: 2,
        }}
      >
        <Paper
          elevation={3}
          css={{
            transform: `scale(${zoom / 100})`,
            transformOrigin: 'top center',
            transition: 'transform 0.2s ease-in-out',
            width: compact ? '100%' : 612, // A4 width at 72 DPI
            minHeight: compact ? 'auto' : 792, // A4 height at 72 DPI
            mx: 'auto',
            p: compact ? 2 : 4,
            backgroundColor: 'white',
          }}
          id="resume-preview-content"
        >
          {/* Header Section */}
          {content?.personal_info && (
            <Box
              css={{
                textAlign: 'center',
                mb: 3,
                pb: 2,
                borderBottom: '2px solid',
                borderColor: style.primaryColor,
                backgroundColor: style.headerBg,
                mx: compact ? -2 : -4,
                mt: compact ? -2 : -4,
                px: compact ? 2 : 4,
                pt: compact ? 2 : 3,
                pb: 2,
              }}
            >
              <Typography
                variant={compact ? 'h6' : 'h4'}
                fontWeight={700}
                css={{ color: style.primaryColor, mb: 0.5 }}
              >
                {content.personal_info.full_name || 'Your Name'}
              </Typography>
              {content.personal_info.title && (
                <Typography
                  variant={compact ? 'body2' : 'h6'}
                  css={{ color: style.secondaryColor, mb: 1 }}
                >
                  {content.personal_info.title}
                </Typography>
              )}
              <Stack
                direction="row"
                spacing={2}
                justifyContent="center"
                css={{ flexWrap: 'wrap', mb: 1 }}
              >
                {content.personal_info.email && (
                  <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Icon name="mail" size={14} css={{ color: style.secondaryColor }} />
                    <Link
                      href={`mailto:${content.personal_info.email}`}
                      css={{ color: style.secondaryColor, fontSize: '0.85rem' }}
                    >
                      {content.personal_info.email}
                    </Link>
                  </Box>
                )}
                {content.personal_info.phone && (
                  <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Icon name="phone" size={14} css={{ color: style.secondaryColor }} />
                    <Link
                      href={`tel:${content.personal_info.phone}`}
                      css={{ color: style.secondaryColor, fontSize: '0.85rem' }}
                    >
                      {content.personal_info.phone}
                    </Link>
                  </Box>
                )}
                {content.personal_info.location && (
                  <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Icon name="map-pin" size={14} css={{ color: style.secondaryColor }} />
                    <Typography variant="body2" css={{ color: style.secondaryColor }}>
                      {content.personal_info.location}
                    </Typography>
                  </Box>
                )}
              </Stack>
              {renderContactLinks()}
            </Box>
          )}

          {/* Summary Section */}
          {content?.summary && (
            renderSection(
              'Professional Summary',
              'user',
              <Typography variant="body2" css={{ lineHeight: 1.7 }}>
                {content.summary}
              </Typography>,
              true
            )
          )}

          {/* Work Experience Section */}
          {renderSection(
            'Work Experience',
            'briefcase',
            content?.work_experience?.map((entry, index) => renderWorkExperienceItem(entry, index)),
            !!(content?.work_experience && content.work_experience.length > 0)
          )}

          {/* Education Section */}
          {renderSection(
            'Education',
            'graduation-cap',
            content?.education?.map((entry, index) => renderEducationItem(entry, index)),
            !!(content?.education && content.education.length > 0)
          )}

          {/* Skills Section */}
          {renderSection(
            'Skills',
            'zap',
            <Box>
              {content?.skills?.map((skill, index) => renderSkillItem(skill, index))}
            </Box>,
            !!(content?.skills && content.skills.length > 0)
          )}

          {/* Certifications Section */}
          {renderSection(
            'Certifications',
            'award',
            content?.certifications?.map((entry, index) => renderCertificationItem(entry, index)),
            !!(content?.certifications && content.certifications.length > 0)
          )}

          {/* Languages Section */}
          {renderSection(
            'Languages',
            'globe',
            <Box>
              {content?.languages?.map((language, index) => renderLanguageItem(language, index))}
            </Box>,
            !!(content?.languages && content.languages.length > 0)
          )}

          {/* Projects Section */}
          {renderSection(
            'Projects',
            'folder',
            content?.projects?.map((entry, index) => renderProjectItem(entry, index)),
            !!(content?.projects && content.projects.length > 0)
          )}
        </Paper>
      </Box>
    </Box>
  );
};

export default ResumePreview;
