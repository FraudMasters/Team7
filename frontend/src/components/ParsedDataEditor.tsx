import React, { useState, useCallback, useEffect, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
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
  Tabs,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { useTranslation } from 'react-i18next';
import SkillsEditor from './SkillsEditor';
import EducationEditor from './EducationEditor';
import WorkHistoryEditor from './WorkHistoryEditor';
import { parsingCorrectionsClient } from '@/api/parsingCorrections';
import type {
  SkillItem,
  EducationItem,
  WorkHistoryItem,
  ApiError,
} from '@/types/api';
import type {
  CorrectableFieldName,
  CorrectionReason,
  ParsingCorrectionResponse,
  ParsingCorrectionCreate,
} from '@/types/parsingCorrection';

/**
 * Editor section/tab type
 */
type EditorSection = 'skills' | 'education' | 'work_experience' | 'languages';

/**
 * Correction reason configuration
 */
interface CorrectionReasonOption {
  value: CorrectionReason;
  label: string;
  description: string;
}

/**
 * Section configuration
 */
interface SectionConfig {
  id: EditorSection;
  label: string;
  icon: string;
  fieldName: CorrectableFieldName;
}

/**
 * Get correction reason options
 */
const getCorrectionReasonOptions = (t: (key: string, defaultValue?: string) => string): CorrectionReasonOption[] => [
  {
    value: 'position_was_incorrect',
    label: t('parsedDataEditor.reasons.positionIncorrect', 'Position was incorrect'),
    description: t('parsedDataEditor.reasons.positionIncorrectDesc', 'The job title/position was parsed incorrectly'),
  },
  {
    value: 'missing_skill',
    label: t('parsedDataEditor.reasons.missingSkill', 'Missing skill'),
    description: t('parsedDataEditor.reasons.missingSkillDesc', 'A skill was not detected'),
  },
  {
    value: 'incorrect_skill',
    label: t('parsedDataEditor.reasons.incorrectSkill', 'Incorrect skill'),
    description: t('parsedDataEditor.reasons.incorrectSkillDesc', 'A skill was parsed incorrectly'),
  },
  {
    value: 'date_was_incorrect',
    label: t('parsedDataEditor.reasons.dateIncorrect', 'Date was incorrect'),
    description: t('parsedDataEditor.reasons.dateIncorrectDesc', 'A date was parsed incorrectly'),
  },
  {
    value: 'company_was_incorrect',
    label: t('parsedDataEditor.reasons.companyIncorrect', 'Company was incorrect'),
    description: t('parsedDataEditor.reasons.companyIncorrectDesc', 'Company name was parsed incorrectly'),
  },
  {
    value: 'education_was_incorrect',
    label: t('parsedDataEditor.reasons.educationIncorrect', 'Education was incorrect'),
    description: t('parsedDataEditor.reasons.educationIncorrectDesc', 'Education information was parsed incorrectly'),
  },
  {
    value: 'language_was_incorrect',
    label: t('parsedDataEditor.reasons.languageIncorrect', 'Language was incorrect'),
    description: t('parsedDataEditor.reasons.languageIncorrectDesc', 'Language was parsed incorrectly'),
  },
  {
    value: 'field_was_empty',
    label: t('parsedDataEditor.reasons.fieldEmpty', 'Field was empty'),
    description: t('parsedDataEditor.reasons.fieldEmptyDesc', 'A field was not extracted when it should have been'),
  },
  {
    value: 'field_was_incomplete',
    label: t('parsedDataEditor.reasons.fieldIncomplete', 'Field was incomplete'),
    description: t('parsedDataEditor.reasons.fieldIncompleteDesc', 'Only part of the field was extracted'),
  },
  {
    value: 'wrong_field_type',
    label: t('parsedDataEditor.reasons.wrongFieldType', 'Wrong field type'),
    description: t('parsedDataEditor.reasons.wrongFieldTypeDesc', 'Data was assigned to wrong field'),
  },
  {
    value: 'other',
    label: t('parsedDataEditor.reasons.other', 'Other'),
    description: t('parsedDataEditor.reasons.otherDesc', 'Other reason not listed above'),
  },
];

/**
 * Get section configurations
 */
const getSectionConfigs = (t: (key: string, defaultValue?: string) => string): SectionConfig[] => [
  {
    id: 'skills',
    label: t('parsedDataEditor.sections.skills', 'Skills'),
    icon: 'zap',
    fieldName: 'skills',
  },
  {
    id: 'education',
    label: t('parsedDataEditor.sections.education', 'Education'),
    icon: 'graduation-cap',
    fieldName: 'education',
  },
  {
    id: 'work_experience',
    label: t('parsedDataEditor.sections.workExperience', 'Work Experience'),
    icon: 'briefcase',
    fieldName: 'work_experience',
  },
  {
    id: 'languages',
    label: t('parsedDataEditor.sections.languages', 'Languages'),
    icon: 'globe',
    fieldName: 'languages',
  },
];

/**
 * ParsedDataEditor Component Props
 */
interface ParsedDataEditorProps {
  /** Resume ID for tracking corrections */
  resumeId: string;
  /** Parsed skills data */
  skills?: SkillItem[];
  /** Parsed education data */
  education?: EducationItem[];
  /** Parsed work history data */
  workHistory?: WorkHistoryItem[];
  /** Parsed languages data (simplified for now) */
  languages?: Array<{ name: string; proficiency?: string }>;
  /** Existing corrections for this resume */
  existingCorrections?: ParsingCorrectionResponse[];
  /** Callback when data is saved successfully */
  onSave?: (section: EditorSection, data: unknown) => void;
  /** Callback when correction is created */
  onCorrectionCreated?: (correction: ParsingCorrectionResponse) => void;
  /** Callback when edit mode is cancelled */
  onCancel?: () => void;
  /** Whether the editor is in read-only mode */
  readOnly?: boolean;
  /** Loading state for initial data */
  loading?: boolean;
  /** Error message if any */
  error?: string | null;
}

/**
 * Edit item state for tracking what's being edited
 */
interface EditState {
  type: 'skill' | 'education' | 'workHistory' | null;
  index: number | null;
  isNew: boolean;
}

/**
 * ParsedDataEditor Component
 *
 * Unified editor component for managing parsed resume data:
 * - Supports editing skills, education, work experience, and languages
 * - Integrates with existing SkillsEditor, EducationEditor, WorkHistoryEditor
 * - Tracks corrections with reason codes
 * - Provides visual feedback for corrected fields
 * - Handles validation and error states
 *
 * @example
 * ```tsx
 * <ParsedDataEditor
 *   resumeId="resume-123"
 *   skills={parsedSkills}
 *   education={parsedEducation}
 *   workHistory={parsedWorkHistory}
 *   onSave={(section, data) => console.log('Saved:', section, data)}
 *   onCorrectionCreated={(correction) => console.log('Correction:', correction)}
 * />
 * ```
 */
const ParsedDataEditor: React.FC<ParsedDataEditorProps> = ({
  resumeId,
  skills = [],
  education = [],
  workHistory = [],
  languages = [],
  existingCorrections = [],
  onSave,
  onCorrectionCreated,
  onCancel,
  readOnly = false,
  loading = false,
  error: externalError = null,
}) => {
  const { t } = useTranslation();

  // State management
  const [activeSection, setActiveSection] = useState<EditorSection>('skills');
  const [editState, setEditState] = useState<EditState>({
    type: null,
    index: null,
    isNew: false,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(externalError);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Correction dialog state
  const [correctionDialogOpen, setCorrectionDialogOpen] = useState(false);
  const [pendingCorrection, setPendingCorrection] = useState<{
    section: EditorSection;
    fieldName: CorrectableFieldName;
    originalValue: unknown;
    correctedValue: unknown;
  } | null>(null);
  const [selectedReason, setSelectedReason] = useState<CorrectionReason | ''>('');
  const [correctionNote, setCorrectionNote] = useState('');
  const [correctionDialogError, setCorrectionDialogError] = useState<string | null>(null);
  const [savingCorrection, setSavingCorrection] = useState(false);

  // Local data state (for modifications before save)
  const [localSkills, setLocalSkills] = useState<SkillItem[]>(skills);
  const [localEducation, setLocalEducation] = useState<EducationItem[]>(education);
  const [localWorkHistory, setLocalWorkHistory] = useState<WorkHistoryItem[]>(workHistory);
  const [localLanguages, setLocalLanguages] = useState(languages);

  // Get configs
  const sectionConfigs = useMemo(() => getSectionConfigs(t), [t]);
  const correctionReasonOptions = useMemo(() => getCorrectionReasonOptions(t), [t]);

  /**
   * Sync local state with props when they change
   */
  useEffect(() => {
    setLocalSkills(skills);
    setLocalEducation(education);
    setLocalWorkHistory(workHistory);
    setLocalLanguages(languages);
  }, [skills, education, workHistory, languages]);

  /**
   * Sync error state with external error
   */
  useEffect(() => {
    setError(externalError);
  }, [externalError]);

  /**
   * Get corrected field names from existing corrections
   */
  const correctedFields = useMemo(() => {
    return existingCorrections.map(c => c.field_name);
  }, [existingCorrections]);

  /**
   * Check if a field has been corrected
   */
  const isFieldCorrected = useCallback((fieldName: CorrectableFieldName): boolean => {
    return correctedFields.includes(fieldName);
  }, [correctedFields]);

  /**
   * Get current section config
   */
  const currentSection = useMemo(() => {
    return sectionConfigs.find(s => s.id === activeSection) || sectionConfigs[0];
  }, [sectionConfigs, activeSection]);

  /**
   * Handle edit action for an item
   */
  const handleEditItem = useCallback((
    type: 'skill' | 'education' | 'workHistory',
    index: number,
    isNew: boolean = false
  ) => {
    setEditState({ type, index, isNew });
    setError(null);
    setSuccessMessage(null);
  }, []);

  /**
   * Handle cancel edit
   */
  const handleCancelEdit = useCallback(() => {
    setEditState({ type: null, index: null, isNew: false });
    setError(null);
    setSuccessMessage(null);
  }, []);

  /**
   * Handle skill save
   */
  const handleSkillSave = useCallback((item: SkillItem) => {
    const index = editState.index;
    const isNew = editState.isNew;

    if (isNew || index === null) {
      // Add new skill
      const newSkill = { ...item, id: `temp-${Date.now()}` };
      setLocalSkills(prev => [...prev, newSkill]);
      setSuccessMessage(t('parsedDataEditor.success.skillAdded', 'Skill added successfully'));
    } else if (index !== null) {
      // Update existing skill
      setLocalSkills(prev => {
        const updated = [...prev];
        updated[index] = item;
        return updated;
      });
      setSuccessMessage(t('parsedDataEditor.success.skillUpdated', 'Skill updated successfully'));
    }

    // Open correction dialog if this was a modification
    if (!isNew && index !== null) {
      const originalItem = localSkills[index];
      setPendingCorrection({
        section: 'skills',
        fieldName: 'skills',
        originalValue: originalItem,
        correctedValue: item,
      });
      setCorrectionDialogOpen(true);
    } else {
      setEditState({ type: null, index: null, isNew: false });
    }

    onSave?.('skills', localSkills);
  }, [editState, localSkills, onSave, t]);

  /**
   * Handle education save
   */
  const handleEducationSave = useCallback((item: EducationItem) => {
    const index = editState.index;
    const isNew = editState.isNew;

    if (isNew || index === null) {
      const newEducation = { ...item, id: `temp-${Date.now()}` };
      setLocalEducation(prev => [...prev, newEducation]);
      setSuccessMessage(t('parsedDataEditor.success.educationAdded', 'Education added successfully'));
    } else if (index !== null) {
      setLocalEducation(prev => {
        const updated = [...prev];
        updated[index] = item;
        return updated;
      });
      setSuccessMessage(t('parsedDataEditor.success.educationUpdated', 'Education updated successfully'));
    }

    if (!isNew && index !== null) {
      const originalItem = localEducation[index];
      setPendingCorrection({
        section: 'education',
        fieldName: 'education',
        originalValue: originalItem,
        correctedValue: item,
      });
      setCorrectionDialogOpen(true);
    } else {
      setEditState({ type: null, index: null, isNew: false });
    }

    onSave?.('education', localEducation);
  }, [editState, localEducation, onSave, t]);

  /**
   * Handle work history save
   */
  const handleWorkHistorySave = useCallback((item: WorkHistoryItem) => {
    const index = editState.index;
    const isNew = editState.isNew;

    if (isNew || index === null) {
      const newWorkHistory = { ...item, id: `temp-${Date.now()}` };
      setLocalWorkHistory(prev => [...prev, newWorkHistory]);
      setSuccessMessage(t('parsedDataEditor.success.workHistoryAdded', 'Work experience added successfully'));
    } else if (index !== null) {
      setLocalWorkHistory(prev => {
        const updated = [...prev];
        updated[index] = item;
        return updated;
      });
      setSuccessMessage(t('parsedDataEditor.success.workHistoryUpdated', 'Work experience updated successfully'));
    }

    if (!isNew && index !== null) {
      const originalItem = localWorkHistory[index];
      setPendingCorrection({
        section: 'work_experience',
        fieldName: 'work_experience',
        originalValue: originalItem,
        correctedValue: item,
      });
      setCorrectionDialogOpen(true);
    } else {
      setEditState({ type: null, index: null, isNew: false });
    }

    onSave?.('work_experience', localWorkHistory);
  }, [editState, localWorkHistory, onSave, t]);

  /**
   * Validate correction dialog
   */
  const validateCorrectionDialog = useCallback((): boolean => {
    if (!selectedReason) {
      setCorrectionDialogError(t('parsedDataEditor.correctionDialog.reasonRequired', 'Please select a reason for this correction'));
      return false;
    }
    setCorrectionDialogError(null);
    return true;
  }, [selectedReason, t]);

  /**
   * Handle correction dialog confirm
   * Saves the correction to the API and notifies parent component
   */
  const handleCorrectionConfirm = useCallback(async () => {
    if (!pendingCorrection) return;

    // Validate that a reason is selected
    if (!validateCorrectionDialog()) {
      return;
    }

    setSavingCorrection(true);
    setCorrectionDialogError(null);

    try {
      // Build the correction payload
      const correctionPayload: ParsingCorrectionCreate = {
        field_name: pendingCorrection.fieldName,
        original_value: pendingCorrection.originalValue as Record<string, unknown>,
        corrected_value: pendingCorrection.correctedValue as Record<string, unknown>,
        reason: selectedReason as CorrectionReason,
      };

      // Save correction via API
      const response = await parsingCorrectionsClient.createCorrection(
        resumeId,
        correctionPayload
      );

      // Extract the created correction from the response
      const correction: ParsingCorrectionResponse = response.data;

      // Notify parent
      onCorrectionCreated?.(correction);

      // Reset state
      setCorrectionDialogOpen(false);
      setPendingCorrection(null);
      setSelectedReason('');
      setCorrectionNote('');
      setCorrectionDialogError(null);
      setEditState({ type: null, index: null, isNew: false });
    } catch (err) {
      const apiError = err as ApiError;
      setCorrectionDialogError(
        apiError.detail || t('parsedDataEditor.correctionDialog.saveError', 'Failed to save correction. Please try again.')
      );
    } finally {
      setSavingCorrection(false);
    }
  }, [pendingCorrection, resumeId, selectedReason, onCorrectionCreated, validateCorrectionDialog, t]);

  /**
   * Handle correction dialog cancel
   */
  const handleCorrectionCancel = useCallback(() => {
    // Prevent canceling while saving
    if (savingCorrection) return;

    setCorrectionDialogOpen(false);
    setPendingCorrection(null);
    setSelectedReason('');
    setCorrectionNote('');
    setCorrectionDialogError(null);
    setEditState({ type: null, index: null, isNew: false });
  }, [savingCorrection]);

  /**
   * Handle delete item
   */
  const handleDeleteItem = useCallback((type: 'skill' | 'education' | 'workHistory', index: number) => {
    switch (type) {
      case 'skill':
        setLocalSkills(prev => prev.filter((_, i) => i !== index));
        break;
      case 'education':
        setLocalEducation(prev => prev.filter((_, i) => i !== index));
        break;
      case 'workHistory':
        setLocalWorkHistory(prev => prev.filter((_, i) => i !== index));
        break;
    }
  }, []);

  /**
   * Clear success message after timeout
   */
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Paper variant="outlined" sx={{ p: 4 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            py: 4,
          }}
        >
          <CircularProgress size={48} sx={{ mb: 2 }} />
          <Typography variant="body1" color="text.secondary">
            {t('parsedDataEditor.loading', 'Loading parsed data...')}
          </Typography>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack spacing={2.5}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h6" fontWeight={600}>
              {t('parsedDataEditor.title', 'Edit Parsed Data')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('parsedDataEditor.subtitle', 'Review and correct the parsed resume information')}
            </Typography>
          </Box>
          {correctedFields.length > 0 && (
            <Chip
              icon={<Icon name="check-circle" size={16} />}
              label={t('parsedDataEditor.correctedCount', '{{count}} corrections', { count: correctedFields.length })}
              color="success"
              size="small"
              variant="outlined"
            />
          )}
        </Box>

        <Divider />

        {/* Error Message */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Success Message */}
        {successMessage && (
          <Alert
            severity="success"
            icon={<Icon name="check-circle" size={20} />}
            onClose={() => setSuccessMessage(null)}
          >
            {successMessage}
          </Alert>
        )}

        {/* Section Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeSection}
            onChange={(_, newValue) => setActiveSection(newValue as EditorSection)}
            variant="scrollable"
            items={sectionConfigs.map(section => ({
              id: section.id,
              label: section.label,
              icon: <Icon name={section.icon} size={16} />,
            }))}
          />
        </Box>

        {/* Section Content */}
        <Box sx={{ minHeight: 400 }}>
          {/* Skills Section */}
          {activeSection === 'skills' && (
            <Stack spacing={2}>
              {/* Skills List */}
              {localSkills.length > 0 ? (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
                    {t('parsedDataEditor.skillsList', 'Skills ({{count}})', { count: localSkills.length })}
                  </Typography>
                  <Stack spacing={1.5}>
                    {localSkills.map((skill, index) => (
                      <Box key={skill.id || index}>
                        {editState.type === 'skill' && editState.index === index ? (
                          <SkillsEditor
                            skillItem={skill}
                            onSave={handleSkillSave}
                            onCancel={handleCancelEdit}
                            readOnly={readOnly}
                          />
                        ) : (
                          <Paper
                            variant="outlined"
                            sx={{
                              p: 2,
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              borderLeft: isFieldCorrected('skills') ? 3 : 0,
                              borderColor: 'success.main',
                            }}
                          >
                            <Box>
                              <Typography variant="subtitle1" fontWeight={500}>
                                {skill.name}
                              </Typography>
                              <Stack direction="row" spacing={1} alignItems="center">
                                {skill.category && (
                                  <Typography variant="caption" color="text.secondary">
                                    {skill.category}
                                  </Typography>
                                )}
                                {skill.proficiency_level && (
                                  <Chip
                                    label={skill.proficiency_level}
                                    size="small"
                                    variant="outlined"
                                  />
                                )}
                                {skill.years_of_experience && (
                                  <Typography variant="caption" color="text.secondary">
                                    {skill.years_of_experience} {t('parsedDataEditor.years', 'years')}
                                  </Typography>
                                )}
                              </Stack>
                            </Box>
                            {!readOnly && (
                              <Stack direction="row" spacing={1}>
                                <Tooltip title={t('common.edit', 'Edit')}>
                                  <IconButton
                                    size="small"
                                    onClick={() => handleEditItem('skill', index)}
                                  >
                                    <Icon name="edit" size={18} />
                                  </IconButton>
                                </Tooltip>
                                <Tooltip title={t('common.delete', 'Delete')}>
                                  <IconButton
                                    size="small"
                                    color="error"
                                    onClick={() => handleDeleteItem('skill', index)}
                                  >
                                    <Icon name="trash" size={18} />
                                  </IconButton>
                                </Tooltip>
                              </Stack>
                            )}
                          </Paper>
                        )}
                      </Box>
                    ))}
                  </Stack>
                </Box>
              ) : (
                <Alert severity="info">
                  {t('parsedDataEditor.noSkills', 'No skills were extracted from the resume.')}
                </Alert>
              )}

              {/* Add Skill Button */}
              {!readOnly && editState.type !== 'skill' && (
                <Button
                  variant="outlined"
                  startIcon={<Icon name="plus" size={16} />}
                  onClick={() => handleEditItem('skill', localSkills.length, true)}
                  sx={{ alignSelf: 'flex-start' }}
                >
                  {t('parsedDataEditor.addSkill', 'Add Skill')}
                </Button>
              )}

              {/* New Skill Editor */}
              {editState.type === 'skill' && editState.isNew && (
                <SkillsEditor
                  onSave={handleSkillSave}
                  onCancel={handleCancelEdit}
                  readOnly={readOnly}
                />
              )}
            </Stack>
          )}

          {/* Education Section */}
          {activeSection === 'education' && (
            <Stack spacing={2}>
              {localEducation.length > 0 ? (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
                    {t('parsedDataEditor.educationList', 'Education ({{count}})', { count: localEducation.length })}
                  </Typography>
                  <Stack spacing={1.5}>
                    {localEducation.map((edu, index) => (
                      <Box key={edu.id || index}>
                        {editState.type === 'education' && editState.index === index ? (
                          <EducationEditor
                            educationItem={edu}
                            onSave={handleEducationSave}
                            onCancel={handleCancelEdit}
                            readOnly={readOnly}
                          />
                        ) : (
                          <Paper
                            variant="outlined"
                            sx={{
                              p: 2,
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'flex-start',
                              borderLeft: isFieldCorrected('education') ? 3 : 0,
                              borderColor: 'success.main',
                            }}
                          >
                            <Box>
                              <Typography variant="subtitle1" fontWeight={500}>
                                {edu.degree}
                              </Typography>
                              <Typography variant="body2" color="primary">
                                {edu.institution_name}
                              </Typography>
                              <Stack direction="row" spacing={2} sx={{ mt: 0.5 }}>
                                <Typography variant="caption" color="text.secondary">
                                  {edu.start_date} - {edu.end_date || t('parsedDataEditor.present', 'Present')}
                                </Typography>
                                {edu.field_of_study && (
                                  <Typography variant="caption" color="text.secondary">
                                    {edu.field_of_study}
                                  </Typography>
                                )}
                              </Stack>
                            </Box>
                            {!readOnly && (
                              <Stack direction="row" spacing={1}>
                                <Tooltip title={t('common.edit', 'Edit')}>
                                  <IconButton
                                    size="small"
                                    onClick={() => handleEditItem('education', index)}
                                  >
                                    <Icon name="edit" size={18} />
                                  </IconButton>
                                </Tooltip>
                                <Tooltip title={t('common.delete', 'Delete')}>
                                  <IconButton
                                    size="small"
                                    color="error"
                                    onClick={() => handleDeleteItem('education', index)}
                                  >
                                    <Icon name="trash" size={18} />
                                  </IconButton>
                                </Tooltip>
                              </Stack>
                            )}
                          </Paper>
                        )}
                      </Box>
                    ))}
                  </Stack>
                </Box>
              ) : (
                <Alert severity="info">
                  {t('parsedDataEditor.noEducation', 'No education was extracted from the resume.')}
                </Alert>
              )}

              {!readOnly && editState.type !== 'education' && (
                <Button
                  variant="outlined"
                  startIcon={<Icon name="plus" size={16} />}
                  onClick={() => handleEditItem('education', localEducation.length, true)}
                  sx={{ alignSelf: 'flex-start' }}
                >
                  {t('parsedDataEditor.addEducation', 'Add Education')}
                </Button>
              )}

              {editState.type === 'education' && editState.isNew && (
                <EducationEditor
                  onSave={handleEducationSave}
                  onCancel={handleCancelEdit}
                  readOnly={readOnly}
                />
              )}
            </Stack>
          )}

          {/* Work Experience Section */}
          {activeSection === 'work_experience' && (
            <Stack spacing={2}>
              {localWorkHistory.length > 0 ? (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
                    {t('parsedDataEditor.workHistoryList', 'Work Experience ({{count}})', { count: localWorkHistory.length })}
                  </Typography>
                  <Stack spacing={1.5}>
                    {localWorkHistory.map((work, index) => (
                      <Box key={work.id || index}>
                        {editState.type === 'workHistory' && editState.index === index ? (
                          <WorkHistoryEditor
                            workHistoryItem={work}
                            onSave={handleWorkHistorySave}
                            onCancel={handleCancelEdit}
                            readOnly={readOnly}
                          />
                        ) : (
                          <Paper
                            variant="outlined"
                            sx={{
                              p: 2,
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'flex-start',
                              borderLeft: isFieldCorrected('work_experience') ? 3 : 0,
                              borderColor: 'success.main',
                            }}
                          >
                            <Box>
                              <Typography variant="subtitle1" fontWeight={500}>
                                {work.position_title}
                              </Typography>
                              <Typography variant="body2" color="primary">
                                {work.company_name}
                              </Typography>
                              <Stack direction="row" spacing={2} sx={{ mt: 0.5 }}>
                                <Typography variant="caption" color="text.secondary">
                                  {work.start_date} - {work.end_date || t('parsedDataEditor.present', 'Present')}
                                </Typography>
                                {work.location && (
                                  <Typography variant="caption" color="text.secondary">
                                    {work.location}
                                  </Typography>
                                )}
                                {work.employment_type && (
                                  <Chip
                                    label={work.employment_type.replace('_', ' ')}
                                    size="small"
                                    variant="outlined"
                                  />
                                )}
                              </Stack>
                            </Box>
                            {!readOnly && (
                              <Stack direction="row" spacing={1}>
                                <Tooltip title={t('common.edit', 'Edit')}>
                                  <IconButton
                                    size="small"
                                    onClick={() => handleEditItem('workHistory', index)}
                                  >
                                    <Icon name="edit" size={18} />
                                  </IconButton>
                                </Tooltip>
                                <Tooltip title={t('common.delete', 'Delete')}>
                                  <IconButton
                                    size="small"
                                    color="error"
                                    onClick={() => handleDeleteItem('workHistory', index)}
                                  >
                                    <Icon name="trash" size={18} />
                                  </IconButton>
                                </Tooltip>
                              </Stack>
                            )}
                          </Paper>
                        )}
                      </Box>
                    ))}
                  </Stack>
                </Box>
              ) : (
                <Alert severity="info">
                  {t('parsedDataEditor.noWorkHistory', 'No work experience was extracted from the resume.')}
                </Alert>
              )}

              {!readOnly && editState.type !== 'workHistory' && (
                <Button
                  variant="outlined"
                  startIcon={<Icon name="plus" size={16} />}
                  onClick={() => handleEditItem('workHistory', localWorkHistory.length, true)}
                  sx={{ alignSelf: 'flex-start' }}
                >
                  {t('parsedDataEditor.addWorkHistory', 'Add Work Experience')}
                </Button>
              )}

              {editState.type === 'workHistory' && editState.isNew && (
                <WorkHistoryEditor
                  onSave={handleWorkHistorySave}
                  onCancel={handleCancelEdit}
                  readOnly={readOnly}
                />
              )}
            </Stack>
          )}

          {/* Languages Section */}
          {activeSection === 'languages' && (
            <Stack spacing={2}>
              {localLanguages.length > 0 ? (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
                    {t('parsedDataEditor.languagesList', 'Languages ({{count}})', { count: localLanguages.length })}
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    {localLanguages.map((lang, index) => (
                      <Chip
                        key={index}
                        label={lang.proficiency ? `${lang.name} (${lang.proficiency})` : lang.name}
                        variant={isFieldCorrected('languages') ? 'filled' : 'outlined'}
                        color={isFieldCorrected('languages') ? 'success' : 'default'}
                        onDelete={!readOnly ? () => {
                          setLocalLanguages(prev => prev.filter((_, i) => i !== index));
                        } : undefined}
                      />
                    ))}
                  </Stack>
                </Box>
              ) : (
                <Alert severity="info">
                  {t('parsedDataEditor.noLanguages', 'No languages were extracted from the resume.')}
                </Alert>
              )}
            </Stack>
          )}
        </Box>

        {/* Action Buttons */}
        {!readOnly && onCancel && (
          <Stack direction="row" spacing={1.5} justifyContent="flex-end" sx={{ pt: 1 }}>
            <Button
              variant="outlined"
              onClick={onCancel}
              disabled={submitting}
            >
              {t('common.cancel', 'Cancel')}
            </Button>
          </Stack>
        )}
      </Stack>

      {/* Correction Reason Dialog */}
      <Dialog
        open={correctionDialogOpen}
        onClose={savingCorrection ? undefined : handleCorrectionCancel}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Stack direction="row" alignItems="center" spacing={1}>
            <Icon name="alert-circle" size={20} />
            <Typography variant="h6">
              {t('parsedDataEditor.correctionDialog.title', 'Why are you making this correction?')}
            </Typography>
          </Stack>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('parsedDataEditor.correctionDialog.description', 'This information helps us improve our parsing accuracy.')}
          </Typography>

          {/* Correction Dialog Error */}
          {correctionDialogError && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setCorrectionDialogError(null)}>
              {correctionDialogError}
            </Alert>
          )}

          <FormControl fullWidth sx={{ mb: 2 }} error={!selectedReason && !!correctionDialogError}>
            <InputLabel>
              {t('parsedDataEditor.correctionDialog.reason', 'Reason')}
            </InputLabel>
            <Select
              value={selectedReason}
              onChange={(e) => {
                setSelectedReason(e.target.value as CorrectionReason);
                // Clear error when user selects a reason
                if (correctionDialogError) {
                  setCorrectionDialogError(null);
                }
              }}
              label={t('parsedDataEditor.correctionDialog.reason', 'Reason')}
            >
              <MenuItem value="" disabled>
                <Typography variant="body2" color="text.secondary">
                  {t('parsedDataEditor.correctionDialog.selectReason', 'Select a reason...')}
                </Typography>
              </MenuItem>
              {correctionReasonOptions.map(option => (
                <MenuItem key={option.value} value={option.value}>
                  <Box>
                    <Typography variant="body2">{option.label}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {option.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
            {!selectedReason && correctionDialogError && (
              <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 1.75 }}>
                {correctionDialogError}
              </Typography>
            )}
          </FormControl>

          <TextField
            label={t('parsedDataEditor.correctionDialog.note', 'Additional notes (optional)')}
            value={correctionNote}
            onChange={(e) => setCorrectionNote(e.target.value)}
            multiline
            rows={2}
            fullWidth
            placeholder={t('parsedDataEditor.correctionDialog.notePlaceholder', 'Any additional context about this correction...')}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCorrectionCancel} color="inherit" disabled={savingCorrection}>
            {t('common.cancel', 'Cancel')}
          </Button>
          <Button
            onClick={handleCorrectionConfirm}
            variant="contained"
            startIcon={savingCorrection ? <CircularProgress size={16} color="inherit" /> : <Icon name="check" size={16} />}
            disabled={!selectedReason || savingCorrection}
          >
            {savingCorrection
              ? t('parsedDataEditor.correctionDialog.saving', 'Saving...')
              : t('parsedDataEditor.correctionDialog.confirm', 'Confirm Correction')}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default ParsedDataEditor;
export type {
  ParsedDataEditorProps,
  EditorSection,
  EditState,
  CorrectionReasonOption,
  SectionConfig,
};
