import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  CircularProgress,
  Alert,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  InputAdornment,
  IconButton,
  Tab,
  Tabs,
  Card,
  CardContent,
  Collapse,
  Tooltip,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import type {
  ResumeContent,
  PersonalInfo,
  WorkExperienceEntry,
  EducationEntry,
  SkillEntry,
  CertificationEntry,
  LanguageEntry,
  ProjectEntry,
} from '@/types/resumeBuilder';
import {
  createEmptyResumeContent,
  createEmptyWorkExperience,
  createEmptyEducation,
  createEmptySkill,
  createEmptyCertification,
  createEmptyLanguage,
  createEmptyProject,
} from '@/types/resumeBuilder';

/**
 * Resume section tab identifiers
 */
type ResumeSection = 'personal' | 'summary' | 'work' | 'education' | 'skills' | 'certifications' | 'languages' | 'projects';

/**
 * ResumeEditor Component Props
 */
interface ResumeEditorProps {
  /** Initial resume content to edit */
  initialContent?: ResumeContent;
  /** Callback when resume content changes */
  onChange?: (content: ResumeContent) => void;
  /** Callback when save is triggered */
  onSave?: (content: ResumeContent) => void | Promise<void>;
  /** Callback when form is cancelled */
  onCancel?: () => void;
  /** Whether the component is in read-only mode */
  readOnly?: boolean;
  /** Loading state for save operation */
  saving?: boolean;
  /** Error message to display */
  error?: string | null;
  /** Success message to display */
  successMessage?: string | null;
  /** Component title */
  title?: string;
}

/**
 * Section configuration for tabs
 */
const SECTION_CONFIG: { id: ResumeSection; label: string; icon: string }[] = [
  { id: 'personal', label: 'Personal Info', icon: 'user' },
  { id: 'summary', label: 'Summary', icon: 'file-text' },
  { id: 'work', label: 'Work Experience', icon: 'briefcase' },
  { id: 'education', label: 'Education', icon: 'graduation-cap' },
  { id: 'skills', label: 'Skills', icon: 'zap' },
  { id: 'certifications', label: 'Certifications', icon: 'award' },
  { id: 'languages', label: 'Languages', icon: 'globe' },
  { id: 'projects', label: 'Projects', icon: 'folder' },
];

/**
 * Skill proficiency level options
 */
const SKILL_LEVEL_OPTIONS = [
  { value: 'basic', label: 'Basic' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
  { value: 'expert', label: 'Expert' },
];

/**
 * Skill category options
 */
const SKILL_CATEGORY_OPTIONS = [
  { value: 'technical', label: 'Technical' },
  { value: 'soft', label: 'Soft Skills' },
  { value: 'language', label: 'Language' },
  { value: 'tool', label: 'Tools & Software' },
  { value: 'methodology', label: 'Methodology' },
  { value: 'other', label: 'Other' },
];

/**
 * Language proficiency options
 */
const LANGUAGE_PROFICIENCY_OPTIONS = [
  { value: 'native', label: 'Native' },
  { value: 'fluent', label: 'Fluent' },
  { value: 'advanced', label: 'Advanced' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'basic', label: 'Basic' },
];

/**
 * ResumeEditor Component
 *
 * Comprehensive form component for editing all resume sections:
 * - Personal information (name, contact, links)
 * - Professional summary
 * - Work experience entries
 * - Education entries
 * - Skills with categories and proficiency
 * - Certifications
 * - Languages
 * - Projects
 *
 * Features:
 * - Tab-based navigation between sections
 * - Add/edit/delete entries for list sections
 * - Form validation with error display
 * - Loading and error states
 * - Read-only mode support
 *
 * @example
 * ```tsx
 * // Editing existing resume
 * <ResumeEditor
 *   initialContent={resumeContent}
 *   onChange={(content) => console.log('Changed:', content)}
 *   onSave={async (content) => await saveResume(content)}
 * />
 *
 * // Creating new resume
 * <ResumeEditor
 *   onSave={async (content) => await createResume(content)}
 *   onCancel={() => navigate('/resumes')}
 * />
 *
 * // Read-only view
 * <ResumeEditor
 *   initialContent={resumeContent}
 *   readOnly
 * />
 * ```
 */
const ResumeEditor: React.FC<ResumeEditorProps> = ({
  initialContent,
  onChange,
  onSave,
  onCancel,
  readOnly = false,
  saving = false,
  error = null,
  successMessage = null,
  title = 'Edit Resume',
}) => {
  // Initialize content state
  const [content, setContent] = useState<ResumeContent>(
    initialContent || createEmptyResumeContent()
  );
  const [activeSection, setActiveSection] = useState<ResumeSection>('personal');
  const [internalError, setInternalError] = useState<string | null>(null);
  const [internalSuccess, setInternalSuccess] = useState<string | null>(null);

  // Track expanded items for collapsible sections
  const [expandedWorkItems, setExpandedWorkItems] = useState<Set<string>>(new Set());
  const [expandedEducationItems, setExpandedEducationItems] = useState<Set<string>>(new Set());
  const [expandedCertificationItems, setExpandedCertificationItems] = useState<Set<string>>(new Set());
  const [expandedProjectItems, setExpandedProjectItems] = useState<Set<string>>(new Set());

  /**
   * Update content and notify parent
   */
  const updateContent = useCallback(
    (updates: Partial<ResumeContent>) => {
      const newContent = { ...content, ...updates };
      setContent(newContent);
      onChange?.(newContent);
    },
    [content, onChange]
  );

  /**
   * Update personal info field
   */
  const updatePersonalInfo = useCallback(
    (field: keyof PersonalInfo) => (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value;
      updateContent({
        personal_info: {
          ...content.personal_info,
          [field]: value,
        },
      });
    },
    [content.personal_info, updateContent]
  );

  /**
   * Update summary field
   */
  const updateSummary = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      updateContent({ summary: event.target.value });
    },
    [updateContent]
  );

  // ==================== Work Experience Methods ====================

  /**
   * Add new work experience entry
   */
  const addWorkExperience = useCallback(() => {
    const newEntry = createEmptyWorkExperience();
    const updatedEntries = [...content.work_experience, newEntry];
    updateContent({ work_experience: updatedEntries });
    setExpandedWorkItems((prev) => new Set([...prev, newEntry.id!]));
  }, [content.work_experience, updateContent]);

  /**
   * Update work experience entry
   */
  const updateWorkExperience = useCallback(
    (id: string, field: keyof WorkExperienceEntry, value: string | boolean | string[]) => {
      const updatedEntries = content.work_experience.map((entry) =>
        entry.id === id ? { ...entry, [field]: value } : entry
      );
      updateContent({ work_experience: updatedEntries });
    },
    [content.work_experience, updateContent]
  );

  /**
   * Delete work experience entry
   */
  const deleteWorkExperience = useCallback(
    (id: string) => {
      const updatedEntries = content.work_experience.filter((entry) => entry.id !== id);
      updateContent({ work_experience: updatedEntries });
      setExpandedWorkItems((prev) => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    },
    [content.work_experience, updateContent]
  );

  /**
   * Toggle work experience expansion
   */
  const toggleWorkExpansion = useCallback((id: string) => {
    setExpandedWorkItems((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);

  // ==================== Education Methods ====================

  /**
   * Add new education entry
   */
  const addEducation = useCallback(() => {
    const newEntry = createEmptyEducation();
    const updatedEntries = [...content.education, newEntry];
    updateContent({ education: updatedEntries });
    setExpandedEducationItems((prev) => new Set([...prev, newEntry.id!]));
  }, [content.education, updateContent]);

  /**
   * Update education entry
   */
  const updateEducation = useCallback(
    (id: string, field: keyof EducationEntry, value: string | string[]) => {
      const updatedEntries = content.education.map((entry) =>
        entry.id === id ? { ...entry, [field]: value } : entry
      );
      updateContent({ education: updatedEntries });
    },
    [content.education, updateContent]
  );

  /**
   * Delete education entry
   */
  const deleteEducation = useCallback(
    (id: string) => {
      const updatedEntries = content.education.filter((entry) => entry.id !== id);
      updateContent({ education: updatedEntries });
      setExpandedEducationItems((prev) => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    },
    [content.education, updateContent]
  );

  /**
   * Toggle education expansion
   */
  const toggleEducationExpansion = useCallback((id: string) => {
    setExpandedEducationItems((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);

  // ==================== Skills Methods ====================

  /**
   * Add new skill entry
   */
  const addSkill = useCallback(() => {
    const newEntry = createEmptySkill();
    const updatedEntries = [...content.skills, newEntry];
    updateContent({ skills: updatedEntries });
  }, [content.skills, updateContent]);

  /**
   * Update skill entry
   */
  const updateSkill = useCallback(
    (index: number, field: keyof SkillEntry, value: string | number | undefined) => {
      const updatedEntries = content.skills.map((entry, i) =>
        i === index ? { ...entry, [field]: value } : entry
      );
      updateContent({ skills: updatedEntries });
    },
    [content.skills, updateContent]
  );

  /**
   * Delete skill entry
   */
  const deleteSkill = useCallback(
    (index: number) => {
      const updatedEntries = content.skills.filter((_, i) => i !== index);
      updateContent({ skills: updatedEntries });
    },
    [content.skills, updateContent]
  );

  // ==================== Certifications Methods ====================

  /**
   * Add new certification entry
   */
  const addCertification = useCallback(() => {
    const newEntry = createEmptyCertification();
    const updatedEntries = [...content.certifications, newEntry];
    updateContent({ certifications: updatedEntries });
    setExpandedCertificationItems((prev) => new Set([...prev, newEntry.id!]));
  }, [content.certifications, updateContent]);

  /**
   * Update certification entry
   */
  const updateCertification = useCallback(
    (id: string, field: keyof CertificationEntry, value: string) => {
      const updatedEntries = content.certifications.map((entry) =>
        entry.id === id ? { ...entry, [field]: value } : entry
      );
      updateContent({ certifications: updatedEntries });
    },
    [content.certifications, updateContent]
  );

  /**
   * Delete certification entry
   */
  const deleteCertification = useCallback(
    (id: string) => {
      const updatedEntries = content.certifications.filter((entry) => entry.id !== id);
      updateContent({ certifications: updatedEntries });
      setExpandedCertificationItems((prev) => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    },
    [content.certifications, updateContent]
  );

  /**
   * Toggle certification expansion
   */
  const toggleCertificationExpansion = useCallback((id: string) => {
    setExpandedCertificationItems((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);

  // ==================== Languages Methods ====================

  /**
   * Add new language entry
   */
  const addLanguage = useCallback(() => {
    const newEntry = createEmptyLanguage();
    const updatedEntries = [...content.languages, newEntry];
    updateContent({ languages: updatedEntries });
  }, [content.languages, updateContent]);

  /**
   * Update language entry
   */
  const updateLanguage = useCallback(
    (index: number, field: keyof LanguageEntry, value: string) => {
      const updatedEntries = content.languages.map((entry, i) =>
        i === index ? { ...entry, [field]: value } : entry
      );
      updateContent({ languages: updatedEntries });
    },
    [content.languages, updateContent]
  );

  /**
   * Delete language entry
   */
  const deleteLanguage = useCallback(
    (index: number) => {
      const updatedEntries = content.languages.filter((_, i) => i !== index);
      updateContent({ languages: updatedEntries });
    },
    [content.languages, updateContent]
  );

  // ==================== Projects Methods ====================

  /**
   * Add new project entry
   */
  const addProject = useCallback(() => {
    const newEntry = createEmptyProject();
    const updatedEntries = [...content.projects, newEntry];
    updateContent({ projects: updatedEntries });
    setExpandedProjectItems((prev) => new Set([...prev, newEntry.id!]));
  }, [content.projects, updateContent]);

  /**
   * Update project entry
   */
  const updateProject = useCallback(
    (id: string, field: keyof ProjectEntry, value: string | string[]) => {
      const updatedEntries = content.projects.map((entry) =>
        entry.id === id ? { ...entry, [field]: value } : entry
      );
      updateContent({ projects: updatedEntries });
    },
    [content.projects, updateContent]
  );

  /**
   * Delete project entry
   */
  const deleteProject = useCallback(
    (id: string) => {
      const updatedEntries = content.projects.filter((entry) => entry.id !== id);
      updateContent({ projects: updatedEntries });
      setExpandedProjectItems((prev) => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    },
    [content.projects, updateContent]
  );

  /**
   * Toggle project expansion
   */
  const toggleProjectExpansion = useCallback((id: string) => {
    setExpandedProjectItems((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);

  // ==================== Save Handler ====================

  /**
   * Handle save button click
   */
  const handleSave = useCallback(async () => {
    if (onSave) {
      try {
        setInternalError(null);
        await onSave(content);
        setInternalSuccess('Resume saved successfully!');
        setTimeout(() => setInternalSuccess(null), 3000);
      } catch (err) {
        setInternalError(err instanceof Error ? err.message : 'Failed to save resume');
      }
    }
  }, [content, onSave]);

  /**
   * Handle cancel button click
   */
  const handleCancel = useCallback(() => {
    onCancel?.();
  }, [onCancel]);

  // ==================== Render Section Content ====================

  /**
   * Render personal info section
   */
  const renderPersonalInfoSection = () => (
    <Stack spacing={2.5}>
      <Typography fontWeight={600} color="text.secondary">
        Contact Information
      </Typography>

      <Stack direction="row" spacing={2}>
        <TextField
          label="First Name"
          value={content.personal_info?.full_name?.split(' ')[0] || ''}
          onChange={updatePersonalInfo('full_name')}
          placeholder="John"
          disabled={saving || readOnly}
          fullWidth
          size="small"
        />
        <TextField
          label="Last Name"
          value={content.personal_info?.full_name?.split(' ').slice(1).join(' ') || ''}
          onChange={(e) => {
            const firstName = content.personal_info?.full_name?.split(' ')[0] || '';
            updateContent({
              personal_info: {
                ...content.personal_info,
                full_name: `${firstName} ${e.target.value}`.trim(),
              },
            });
          }}
          placeholder="Doe"
          disabled={saving || readOnly}
          fullWidth
          size="small"
        />
      </Stack>

      <Stack direction="row" spacing={2}>
        <TextField
          label="Email"
          type="email"
          value={content.personal_info?.email || ''}
          onChange={updatePersonalInfo('email')}
          placeholder="john.doe@example.com"
          disabled={saving || readOnly}
          fullWidth
          size="small"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Icon name="mail" size={18} />
              </InputAdornment>
            ),
          }}
        />
        <TextField
          label="Phone"
          value={content.personal_info?.phone || ''}
          onChange={updatePersonalInfo('phone')}
          placeholder="+1 (555) 123-4567"
          disabled={saving || readOnly}
          fullWidth
          size="small"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Icon name="phone" size={18} />
              </InputAdornment>
            ),
          }}
        />
      </Stack>

      <TextField
        label="Location"
        value={content.personal_info?.location || ''}
        onChange={updatePersonalInfo('location')}
        placeholder="San Francisco, CA"
        disabled={saving || readOnly}
        fullWidth
        size="small"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Icon name="map-pin" size={18} />
            </InputAdornment>
          ),
        }}
      />

      <Divider />

      <Typography fontWeight={600} color="text.secondary">
        Professional Title
      </Typography>

      <TextField
        label="Professional Title"
        value={content.personal_info?.title || ''}
        onChange={updatePersonalInfo('title')}
        placeholder="Senior Software Engineer"
        disabled={saving || readOnly}
        fullWidth
        size="small"
        helperText="Your current or target job title"
      />

      <Divider />

      <Typography fontWeight={600} color="text.secondary">
        Online Profiles
      </Typography>

      <TextField
        label="LinkedIn URL"
        value={content.personal_info?.linkedin_url || ''}
        onChange={updatePersonalInfo('linkedin_url')}
        placeholder="https://linkedin.com/in/johndoe"
        disabled={saving || readOnly}
        fullWidth
        size="small"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Icon name="linkedin" size={18} />
            </InputAdornment>
          ),
        }}
      />

      <TextField
        label="GitHub URL"
        value={content.personal_info?.github_url || ''}
        onChange={updatePersonalInfo('github_url')}
        placeholder="https://github.com/johndoe"
        disabled={saving || readOnly}
        fullWidth
        size="small"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Icon name="github" size={18} />
            </InputAdornment>
          ),
        }}
      />

      <TextField
        label="Personal Website"
        value={content.personal_info?.website_url || ''}
        onChange={updatePersonalInfo('website_url')}
        placeholder="https://johndoe.com"
        disabled={saving || readOnly}
        fullWidth
        size="small"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Icon name="globe" size={18} />
            </InputAdornment>
          ),
        }}
      />
    </Stack>
  );

  /**
   * Render summary section
   */
  const renderSummarySection = () => (
    <Stack spacing={2.5}>
      <Typography fontWeight={600} color="text.secondary">
        Professional Summary
      </Typography>

      <TextField
        multiline
        rows={6}
        label="Summary"
        value={content.summary || ''}
        onChange={updateSummary}
        placeholder="Write a compelling summary of your professional background, key achievements, and career goals..."
        disabled={saving || readOnly}
        fullWidth
        helperText="2-4 sentences highlighting your experience, skills, and what you bring to a potential employer"
      />

      <Box css={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Chip
          size="small"
          label={`${(content.summary || '').length} characters`}
          variant="outlined"
          color={(content.summary?.length || 0) > 500 ? 'warning' : 'default'}
        />
        <Chip
          size="small"
          label="Recommended: 200-500 characters"
          variant="outlined"
        />
      </Box>
    </Stack>
  );

  /**
   * Render work experience section
   */
  const renderWorkExperienceSection = () => (
    <Stack spacing={2}>
      <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography fontWeight={600} color="text.secondary">
          Work Experience ({content.work_experience.length})
        </Typography>
        {!readOnly && (
          <Button
            variant="outlined"
            size="small"
            startIcon={<Icon name="plus" size={16} />}
            onClick={addWorkExperience}
            disabled={saving}
          >
            Add Position
          </Button>
        )}
      </Box>

      {content.work_experience.length === 0 ? (
        <Box css={{ textAlign: 'center', py: 4 }}>
          <Icon name="briefcase" css={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography color="text.secondary">No work experience added yet</Typography>
          {!readOnly && (
            <Button
              variant="text"
              startIcon={<Icon name="plus" size={16} />}
              onClick={addWorkExperience}
              disabled={saving}
              css={{ mt: 1 }}
            >
              Add your first position
            </Button>
          )}
        </Box>
      ) : (
        <Stack spacing={1.5}>
          {content.work_experience.map((entry) => {
            const isExpanded = expandedWorkItems.has(entry.id!);
            return (
              <Card
                key={entry.id}
                variant="outlined"
                css={{
                  cursor: 'pointer',
                  transition: 'box-shadow 0.2s',
                  '&:hover': { boxShadow: 2 },
                }}
              >
                <CardContent>
                  <Box
                    css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}
                    onClick={() => toggleWorkExpansion(entry.id!)}
                  >
                    <Box>
                      <Typography fontWeight={600}>{entry.position || 'Position Title'}</Typography>
                      <Typography color="primary" variant="body2">
                        {entry.company || 'Company Name'}
                      </Typography>
                      <Typography color="text.secondary" variant="caption">
                        {entry.start_date || 'Start'} - {entry.is_current ? 'Present' : entry.end_date || 'End'}
                      </Typography>
                    </Box>
                    <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      {!readOnly && (
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteWorkExperience(entry.id!);
                            }}
                            disabled={saving}
                          >
                            <Icon name="trash-2" size={16} />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Icon name={isExpanded ? 'chevron-up' : 'chevron-down'} size={20} />
                    </Box>
                  </Box>

                  <Collapse in={isExpanded} timeout="auto">
                    <Divider css={{ my: 2 }} />
                    <Stack spacing={2}>
                      <Stack direction="row" spacing={2}>
                        <TextField
                          label="Company"
                          value={entry.company || ''}
                          onChange={(e) => updateWorkExperience(entry.id!, 'company', e.target.value)}
                          placeholder="Company Name"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                        <TextField
                          label="Position"
                          value={entry.position || ''}
                          onChange={(e) => updateWorkExperience(entry.id!, 'position', e.target.value)}
                          placeholder="Job Title"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                      </Stack>

                      <TextField
                        label="Location"
                        value={entry.location || ''}
                        onChange={(e) => updateWorkExperience(entry.id!, 'location', e.target.value)}
                        placeholder="City, Country"
                        disabled={saving || readOnly}
                        fullWidth
                        size="small"
                        InputProps={{
                          startAdornment: (
                            <InputAdornment position="start">
                              <Icon name="map-pin" size={18} />
                            </InputAdornment>
                          ),
                        }}
                      />

                      <Stack direction="row" spacing={2}>
                        <TextField
                          label="Start Date"
                          value={entry.start_date || ''}
                          onChange={(e) => updateWorkExperience(entry.id!, 'start_date', e.target.value)}
                          placeholder="YYYY-MM"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                        <TextField
                          label="End Date"
                          value={entry.end_date || ''}
                          onChange={(e) => updateWorkExperience(entry.id!, 'end_date', e.target.value)}
                          placeholder="YYYY-MM or Present"
                          disabled={saving || readOnly || entry.is_current}
                          fullWidth
                          size="small"
                        />
                      </Stack>

                      <FormControl size="small" disabled={saving || readOnly}>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={entry.is_current}
                              onChange={(e) => updateWorkExperience(entry.id!, 'is_current', e.target.checked)}
                              disabled={saving || readOnly}
                            />
                          }
                          label="I currently work here"
                        />
                      </FormControl>

                      <TextField
                        multiline
                        rows={4}
                        label="Description"
                        value={entry.description || ''}
                        onChange={(e) => updateWorkExperience(entry.id!, 'description', e.target.value)}
                        placeholder="Describe your responsibilities and achievements..."
                        disabled={saving || readOnly}
                        fullWidth
                        helperText="Use bullet points to highlight key achievements"
                      />
                    </Stack>
                  </Collapse>
                </CardContent>
              </Card>
            );
          })}
        </Stack>
      )}
    </Stack>
  );

  /**
   * Render education section
   */
  const renderEducationSection = () => (
    <Stack spacing={2}>
      <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography fontWeight={600} color="text.secondary">
          Education ({content.education.length})
        </Typography>
        {!readOnly && (
          <Button
            variant="outlined"
            size="small"
            startIcon={<Icon name="plus" size={16} />}
            onClick={addEducation}
            disabled={saving}
          >
            Add Education
          </Button>
        )}
      </Box>

      {content.education.length === 0 ? (
        <Box css={{ textAlign: 'center', py: 4 }}>
          <Icon name="graduation-cap" css={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography color="text.secondary">No education added yet</Typography>
          {!readOnly && (
            <Button
              variant="text"
              startIcon={<Icon name="plus" size={16} />}
              onClick={addEducation}
              disabled={saving}
              css={{ mt: 1 }}
            >
              Add your first education
            </Button>
          )}
        </Box>
      ) : (
        <Stack spacing={1.5}>
          {content.education.map((entry) => {
            const isExpanded = expandedEducationItems.has(entry.id!);
            return (
              <Card
                key={entry.id}
                variant="outlined"
                css={{
                  cursor: 'pointer',
                  transition: 'box-shadow 0.2s',
                  '&:hover': { boxShadow: 2 },
                }}
              >
                <CardContent>
                  <Box
                    css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}
                    onClick={() => toggleEducationExpansion(entry.id!)}
                  >
                    <Box>
                      <Typography fontWeight={600}>{entry.degree || 'Degree'}</Typography>
                      <Typography color="primary" variant="body2">
                        {entry.institution || 'Institution Name'}
                      </Typography>
                      <Typography color="text.secondary" variant="caption">
                        {entry.field_of_study || 'Field of Study'} • {entry.start_date || 'Start'} - {entry.end_date || 'End'}
                      </Typography>
                    </Box>
                    <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      {!readOnly && (
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteEducation(entry.id!);
                            }}
                            disabled={saving}
                          >
                            <Icon name="trash-2" size={16} />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Icon name={isExpanded ? 'chevron-up' : 'chevron-down'} size={20} />
                    </Box>
                  </Box>

                  <Collapse in={isExpanded} timeout="auto">
                    <Divider css={{ my: 2 }} />
                    <Stack spacing={2}>
                      <Stack direction="row" spacing={2}>
                        <TextField
                          label="Institution"
                          value={entry.institution || ''}
                          onChange={(e) => updateEducation(entry.id!, 'institution', e.target.value)}
                          placeholder="University Name"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                        <TextField
                          label="Degree"
                          value={entry.degree || ''}
                          onChange={(e) => updateEducation(entry.id!, 'degree', e.target.value)}
                          placeholder="Bachelor of Science"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                      </Stack>

                      <Stack direction="row" spacing={2}>
                        <TextField
                          label="Field of Study"
                          value={entry.field_of_study || ''}
                          onChange={(e) => updateEducation(entry.id!, 'field_of_study', e.target.value)}
                          placeholder="Computer Science"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                        <TextField
                          label="GPA"
                          value={entry.gpa || ''}
                          onChange={(e) => updateEducation(entry.id!, 'gpa', e.target.value)}
                          placeholder="3.8/4.0"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                      </Stack>

                      <Stack direction="row" spacing={2}>
                        <TextField
                          label="Start Date"
                          value={entry.start_date || ''}
                          onChange={(e) => updateEducation(entry.id!, 'start_date', e.target.value)}
                          placeholder="YYYY-MM"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                        <TextField
                          label="End Date"
                          value={entry.end_date || ''}
                          onChange={(e) => updateEducation(entry.id!, 'end_date', e.target.value)}
                          placeholder="YYYY-MM"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                      </Stack>

                      <TextField
                        label="Location"
                        value={entry.location || ''}
                        onChange={(e) => updateEducation(entry.id!, 'location', e.target.value)}
                        placeholder="City, Country"
                        disabled={saving || readOnly}
                        fullWidth
                        size="small"
                        InputProps={{
                          startAdornment: (
                            <InputAdornment position="start">
                              <Icon name="map-pin" size={18} />
                            </InputAdornment>
                          ),
                        }}
                      />

                      <TextField
                        multiline
                        rows={3}
                        label="Additional Information"
                        value={entry.description || ''}
                        onChange={(e) => updateEducation(entry.id!, 'description', e.target.value)}
                        placeholder="Honors, activities, thesis..."
                        disabled={saving || readOnly}
                        fullWidth
                      />
                    </Stack>
                  </Collapse>
                </CardContent>
              </Card>
            );
          })}
        </Stack>
      )}
    </Stack>
  );

  /**
   * Render skills section
   */
  const renderSkillsSection = () => (
    <Stack spacing={2}>
      <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography fontWeight={600} color="text.secondary">
          Skills ({content.skills.length})
        </Typography>
        {!readOnly && (
          <Button
            variant="outlined"
            size="small"
            startIcon={<Icon name="plus" size={16} />}
            onClick={addSkill}
            disabled={saving}
          >
            Add Skill
          </Button>
        )}
      </Box>

      {content.skills.length === 0 ? (
        <Box css={{ textAlign: 'center', py: 4 }}>
          <Icon name="zap" css={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography color="text.secondary">No skills added yet</Typography>
          {!readOnly && (
            <Button
              variant="text"
              startIcon={<Icon name="plus" size={16} />}
              onClick={addSkill}
              disabled={saving}
              css={{ mt: 1 }}
            >
              Add your first skill
            </Button>
          )}
        </Box>
      ) : (
        <Stack spacing={1.5}>
          {content.skills.map((skill, index) => (
            <Card key={index} variant="outlined">
              <CardContent>
                <Stack direction="row" spacing={2} alignItems="center">
                  <TextField
                    label="Skill Name"
                    value={skill.name}
                    onChange={(e) => updateSkill(index, 'name', e.target.value)}
                    placeholder="JavaScript"
                    disabled={saving || readOnly}
                    size="small"
                    css={{ flex: 2 }}
                  />
                  <FormControl size="small" disabled={saving || readOnly} css={{ flex: 1 }}>
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={skill.category || ''}
                      onChange={(e) => updateSkill(index, 'category', e.target.value)}
                      label="Category"
                    >
                      {SKILL_CATEGORY_OPTIONS.map((opt) => (
                        <MenuItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <FormControl size="small" disabled={saving || readOnly} css={{ flex: 1 }}>
                    <InputLabel>Level</InputLabel>
                    <Select
                      value={skill.level || ''}
                      onChange={(e) => updateSkill(index, 'level', e.target.value)}
                      label="Level"
                    >
                      {SKILL_LEVEL_OPTIONS.map((opt) => (
                        <MenuItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <TextField
                    label="Years"
                    type="number"
                    value={skill.years_of_experience || ''}
                    onChange={(e) => updateSkill(index, 'years_of_experience', parseInt(e.target.value) || undefined)}
                    disabled={saving || readOnly}
                    size="small"
                    css={{ width: 80 }}
                  />
                  {!readOnly && (
                    <IconButton
                      size="small"
                      onClick={() => deleteSkill(index)}
                      disabled={saving}
                    >
                      <Icon name="trash-2" size={16} />
                    </IconButton>
                  )}
                </Stack>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}
    </Stack>
  );

  /**
   * Render certifications section
   */
  const renderCertificationsSection = () => (
    <Stack spacing={2}>
      <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography fontWeight={600} color="text.secondary">
          Certifications ({content.certifications.length})
        </Typography>
        {!readOnly && (
          <Button
            variant="outlined"
            size="small"
            startIcon={<Icon name="plus" size={16} />}
            onClick={addCertification}
            disabled={saving}
          >
            Add Certification
          </Button>
        )}
      </Box>

      {content.certifications.length === 0 ? (
        <Box css={{ textAlign: 'center', py: 4 }}>
          <Icon name="award" css={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography color="text.secondary">No certifications added yet</Typography>
          {!readOnly && (
            <Button
              variant="text"
              startIcon={<Icon name="plus" size={16} />}
              onClick={addCertification}
              disabled={saving}
              css={{ mt: 1 }}
            >
              Add your first certification
            </Button>
          )}
        </Box>
      ) : (
        <Stack spacing={1.5}>
          {content.certifications.map((entry) => {
            const isExpanded = expandedCertificationItems.has(entry.id!);
            return (
              <Card
                key={entry.id}
                variant="outlined"
                css={{
                  cursor: 'pointer',
                  transition: 'box-shadow 0.2s',
                  '&:hover': { boxShadow: 2 },
                }}
              >
                <CardContent>
                  <Box
                    css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}
                    onClick={() => toggleCertificationExpansion(entry.id!)}
                  >
                    <Box>
                      <Typography fontWeight={600}>{entry.name || 'Certification Name'}</Typography>
                      <Typography color="primary" variant="body2">
                        {entry.issuer || 'Issuing Organization'}
                      </Typography>
                      <Typography color="text.secondary" variant="caption">
                        Issued: {entry.issue_date || 'N/A'}
                      </Typography>
                    </Box>
                    <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      {!readOnly && (
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteCertification(entry.id!);
                            }}
                            disabled={saving}
                          >
                            <Icon name="trash-2" size={16} />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Icon name={isExpanded ? 'chevron-up' : 'chevron-down'} size={20} />
                    </Box>
                  </Box>

                  <Collapse in={isExpanded} timeout="auto">
                    <Divider css={{ my: 2 }} />
                    <Stack spacing={2}>
                      <Stack direction="row" spacing={2}>
                        <TextField
                          label="Certification Name"
                          value={entry.name}
                          onChange={(e) => updateCertification(entry.id!, 'name', e.target.value)}
                          placeholder="AWS Solutions Architect"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                        <TextField
                          label="Issuing Organization"
                          value={entry.issuer || ''}
                          onChange={(e) => updateCertification(entry.id!, 'issuer', e.target.value)}
                          placeholder="Amazon Web Services"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                      </Stack>

                      <Stack direction="row" spacing={2}>
                        <TextField
                          label="Issue Date"
                          value={entry.issue_date || ''}
                          onChange={(e) => updateCertification(entry.id!, 'issue_date', e.target.value)}
                          placeholder="YYYY-MM"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                        <TextField
                          label="Expiry Date"
                          value={entry.expiry_date || ''}
                          onChange={(e) => updateCertification(entry.id!, 'expiry_date', e.target.value)}
                          placeholder="YYYY-MM or 'Does not expire'"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                      </Stack>

                      <Stack direction="row" spacing={2}>
                        <TextField
                          label="Credential ID"
                          value={entry.credential_id || ''}
                          onChange={(e) => updateCertification(entry.id!, 'credential_id', e.target.value)}
                          placeholder="ABC123XYZ"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                        <TextField
                          label="Credential URL"
                          value={entry.credential_url || ''}
                          onChange={(e) => updateCertification(entry.id!, 'credential_url', e.target.value)}
                          placeholder="https://..."
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                      </Stack>
                    </Stack>
                  </Collapse>
                </CardContent>
              </Card>
            );
          })}
        </Stack>
      )}
    </Stack>
  );

  /**
   * Render languages section
   */
  const renderLanguagesSection = () => (
    <Stack spacing={2}>
      <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography fontWeight={600} color="text.secondary">
          Languages ({content.languages.length})
        </Typography>
        {!readOnly && (
          <Button
            variant="outlined"
            size="small"
            startIcon={<Icon name="plus" size={16} />}
            onClick={addLanguage}
            disabled={saving}
          >
            Add Language
          </Button>
        )}
      </Box>

      {content.languages.length === 0 ? (
        <Box css={{ textAlign: 'center', py: 4 }}>
          <Icon name="globe" css={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography color="text.secondary">No languages added yet</Typography>
          {!readOnly && (
            <Button
              variant="text"
              startIcon={<Icon name="plus" size={16} />}
              onClick={addLanguage}
              disabled={saving}
              css={{ mt: 1 }}
            >
              Add your first language
            </Button>
          )}
        </Box>
      ) : (
        <Stack spacing={1.5}>
          {content.languages.map((language, index) => (
            <Card key={index} variant="outlined">
              <CardContent>
                <Stack direction="row" spacing={2} alignItems="center">
                  <TextField
                    label="Language"
                    value={language.name}
                    onChange={(e) => updateLanguage(index, 'name', e.target.value)}
                    placeholder="English"
                    disabled={saving || readOnly}
                    size="small"
                    css={{ flex: 2 }}
                  />
                  <FormControl size="small" disabled={saving || readOnly} css={{ flex: 1 }}>
                    <InputLabel>Proficiency</InputLabel>
                    <Select
                      value={language.proficiency || ''}
                      onChange={(e) => updateLanguage(index, 'proficiency', e.target.value)}
                      label="Proficiency"
                    >
                      {LANGUAGE_PROFICIENCY_OPTIONS.map((opt) => (
                        <MenuItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <TextField
                    label="Certification"
                    value={language.certification || ''}
                    onChange={(e) => updateLanguage(index, 'certification', e.target.value)}
                    placeholder="IELTS, TOEFL..."
                    disabled={saving || readOnly}
                    size="small"
                    css={{ flex: 1 }}
                  />
                  {!readOnly && (
                    <IconButton
                      size="small"
                      onClick={() => deleteLanguage(index)}
                      disabled={saving}
                    >
                      <Icon name="trash-2" size={16} />
                    </IconButton>
                  )}
                </Stack>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}
    </Stack>
  );

  /**
   * Render projects section
   */
  const renderProjectsSection = () => (
    <Stack spacing={2}>
      <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography fontWeight={600} color="text.secondary">
          Projects ({content.projects.length})
        </Typography>
        {!readOnly && (
          <Button
            variant="outlined"
            size="small"
            startIcon={<Icon name="plus" size={16} />}
            onClick={addProject}
            disabled={saving}
          >
            Add Project
          </Button>
        )}
      </Box>

      {content.projects.length === 0 ? (
        <Box css={{ textAlign: 'center', py: 4 }}>
          <Icon name="folder" css={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography color="text.secondary">No projects added yet</Typography>
          {!readOnly && (
            <Button
              variant="text"
              startIcon={<Icon name="plus" size={16} />}
              onClick={addProject}
              disabled={saving}
              css={{ mt: 1 }}
            >
              Add your first project
            </Button>
          )}
        </Box>
      ) : (
        <Stack spacing={1.5}>
          {content.projects.map((entry) => {
            const isExpanded = expandedProjectItems.has(entry.id!);
            return (
              <Card
                key={entry.id}
                variant="outlined"
                css={{
                  cursor: 'pointer',
                  transition: 'box-shadow 0.2s',
                  '&:hover': { boxShadow: 2 },
                }}
              >
                <CardContent>
                  <Box
                    css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}
                    onClick={() => toggleProjectExpansion(entry.id!)}
                  >
                    <Box>
                      <Typography fontWeight={600}>{entry.name || 'Project Name'}</Typography>
                      <Typography color="text.secondary" variant="body2">
                        {entry.description?.substring(0, 100) || 'Project description...'}
                        {(entry.description?.length || 0) > 100 ? '...' : ''}
                      </Typography>
                    </Box>
                    <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      {!readOnly && (
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteProject(entry.id!);
                            }}
                            disabled={saving}
                          >
                            <Icon name="trash-2" size={16} />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Icon name={isExpanded ? 'chevron-up' : 'chevron-down'} size={20} />
                    </Box>
                  </Box>

                  <Collapse in={isExpanded} timeout="auto">
                    <Divider css={{ my: 2 }} />
                    <Stack spacing={2}>
                      <TextField
                        label="Project Name"
                        value={entry.name}
                        onChange={(e) => updateProject(entry.id!, 'name', e.target.value)}
                        placeholder="My Awesome Project"
                        disabled={saving || readOnly}
                        fullWidth
                        size="small"
                      />

                      <TextField
                        label="Project URL"
                        value={entry.url || ''}
                        onChange={(e) => updateProject(entry.id!, 'url', e.target.value)}
                        placeholder="https://github.com/..."
                        disabled={saving || readOnly}
                        fullWidth
                        size="small"
                        InputProps={{
                          startAdornment: (
                            <InputAdornment position="start">
                              <Icon name="link" size={18} />
                            </InputAdornment>
                          ),
                        }}
                      />

                      <Stack direction="row" spacing={2}>
                        <TextField
                          label="Start Date"
                          value={entry.start_date || ''}
                          onChange={(e) => updateProject(entry.id!, 'start_date', e.target.value)}
                          placeholder="YYYY-MM"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                        <TextField
                          label="End Date"
                          value={entry.end_date || ''}
                          onChange={(e) => updateProject(entry.id!, 'end_date', e.target.value)}
                          placeholder="YYYY-MM"
                          disabled={saving || readOnly}
                          fullWidth
                          size="small"
                        />
                      </Stack>

                      <TextField
                        multiline
                        rows={4}
                        label="Description"
                        value={entry.description || ''}
                        onChange={(e) => updateProject(entry.id!, 'description', e.target.value)}
                        placeholder="Describe what the project does, your role, and the technologies used..."
                        disabled={saving || readOnly}
                        fullWidth
                      />
                    </Stack>
                  </Collapse>
                </CardContent>
              </Card>
            );
          })}
        </Stack>
      )}
    </Stack>
  );

  /**
   * Render active section content
   */
  const renderSectionContent = () => {
    switch (activeSection) {
      case 'personal':
        return renderPersonalInfoSection();
      case 'summary':
        return renderSummarySection();
      case 'work':
        return renderWorkExperienceSection();
      case 'education':
        return renderEducationSection();
      case 'skills':
        return renderSkillsSection();
      case 'certifications':
        return renderCertificationsSection();
      case 'languages':
        return renderLanguagesSection();
      case 'projects':
        return renderProjectsSection();
      default:
        return null;
    }
  };

  return (
    <Paper variant="outlined" css={{ p: 3 }}>
      <Stack spacing={3}>
        {/* Header */}
        <Box css={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" fontWeight={600}>
            {title}
          </Typography>
          {saving && (
            <Box css={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={16} />
              <Typography variant="body2" color="text.secondary">
                Saving...
              </Typography>
            </Box>
          )}
        </Box>

        <Divider />

        {/* Error Message */}
        {(error || internalError) && (
          <Alert severity="error" onClose={() => setInternalError(null)}>
            {error || internalError}
          </Alert>
        )}

        {/* Success Message */}
        {successMessage && (
          <Alert
            severity="success"
            icon={<Icon name="check-circle" size={20} />}
            onClose={() => setInternalSuccess(null)}
          >
            {successMessage}
          </Alert>
        )}

        {/* Section Tabs */}
        <Box css={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeSection}
            onChange={(_, newValue) => setActiveSection(newValue)}
            variant="scrollable"
            scrollButtons="auto"
          >
            {SECTION_CONFIG.map((section) => (
              <Tab
                key={section.id}
                value={section.id}
                label={
                  <Box css={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Icon name={section.icon} size={16} />
                    <span>{section.label}</span>
                  </Box>
                }
                css={{ minHeight: 48 }}
              />
            ))}
          </Tabs>
        </Box>

        {/* Section Content */}
        <Box css={{ minHeight: 400 }}>{renderSectionContent()}</Box>

        {/* Action Buttons */}
        {!readOnly && (
          <>
            <Divider />
            <Stack direction="row" spacing={1.5} justifyContent="flex-end">
              {onCancel && (
                <Button
                  variant="outlined"
                  onClick={handleCancel}
                  disabled={saving}
                  size="small"
                >
                  Cancel
                </Button>
              )}
              {onSave && (
                <Button
                  variant="contained"
                  onClick={handleSave}
                  disabled={saving}
                  startIcon={saving ? <CircularProgress size={16} /> : <Icon name="save" size={16} />}
                  size="small"
                >
                  {saving ? 'Saving...' : 'Save Resume'}
                </Button>
              )}
            </Stack>
          </>
        )}
      </Stack>
    </Paper>
  );
};

export default ResumeEditor;
