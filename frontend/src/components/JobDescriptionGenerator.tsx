import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Chip,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Grid,
  Alert,
  IconButton,
  Card,
  CardContent,
  Divider,
  CircularProgress,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ErrorBoundary from './ErrorBoundary';
import ErrorMessage, { ErrorType, ErrorAction } from './ErrorMessage';
import { jobDescriptionsClient } from '@/api/jobDescriptions';
import type {
  JobDescriptionGenerateRequest,
  JobDescriptionResponse,
} from '@/types/api';

interface JobDescriptionGeneratorProps {
  onComplete?: (description: JobDescriptionResponse) => void;
  initialData?: Partial<JobDescriptionGenerateRequest>;
  embedded?: boolean;
}

// Memoized skill chip component
const SkillChip = React.memo<{
  skill: string;
  onDelete: () => void;
  color?: 'primary' | 'secondary' | 'default';
}>(({ skill, onDelete, color = 'default' }) => (
  <Chip
    label={skill}
    onDelete={onDelete}
    color={color}
    deleteIcon={<Icon name="trash-2" size="small" />}
    size="small"
  />
));

SkillChip.displayName = 'SkillChip';

const JobDescriptionGenerator: React.FC<JobDescriptionGeneratorProps> = ({
  onComplete,
  initialData,
  embedded = false,
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [error, setError] = useState<Error | ErrorType | string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedDescription, setGeneratedDescription] = useState<JobDescriptionResponse | null>(null);

  // Form state
  const [formData, setFormData] = useState<JobDescriptionGenerateRequest>({
    title: initialData?.title || '',
    required_skills: initialData?.required_skills || [],
    min_experience_months: initialData?.min_experience_months || 0,
    seniority_level: initialData?.seniority_level || '',
    industry: initialData?.industry || '',
    work_format: initialData?.work_format || '',
    location: initialData?.location || '',
    employment_type: initialData?.employment_type || '',
    salary_range: initialData?.salary_range || '',
    additional_requirements: initialData?.additional_requirements || [],
    tone: initialData?.tone || 'professional',
    language: initialData?.language || 'en',
  });

  // Temp state for skill input
  const [skillInput, setSkillInput] = useState('');
  const [additionalSkillInput, setAdditionalSkillInput] = useState('');

  const experienceLabel = useMemo(() => {
    if (formData.min_experience_months === 0) return t('jobDescriptionGenerator.fields.experience.noExperience');
    if (formData.min_experience_months < 12) {
      return `${formData.min_experience_months} ${t('jobDescriptionGenerator.fields.experience.months')}`;
    }
    const years = Math.floor(formData.min_experience_months / 12);
    const months = formData.min_experience_months % 12;
    if (months === 0) {
      return t('jobDescriptionGenerator.fields.experience.years', { years, plural: years > 1 ? 's' : '' });
    }
    return t('jobDescriptionGenerator.fields.experience.yearsMonths', { years, months });
  }, [formData.min_experience_months, t]);

  const handleGenerate = async () => {
    // Validation
    if (!formData.title.trim()) {
      setError(t('jobDescriptionGenerator.error.jobTitleRequired'));
      return;
    }
    if (formData.required_skills.length === 0) {
      setError(t('jobDescriptionGenerator.error.atLeastOneSkill'));
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const description = await jobDescriptionsClient.generateDescription(formData);
      setGeneratedDescription(description);
      if (onComplete) {
        onComplete(description);
      }
    } catch (err) {
      setError(err instanceof Error ? err : t('jobDescriptionGenerator.error.generationFailed'));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRegenerate = async () => {
    setGeneratedDescription(null);
    await handleGenerate();
  };

  const handleReset = () => {
    setGeneratedDescription(null);
    setError(null);
  };

  const addRequiredSkill = useCallback(() => {
    if (skillInput.trim() && !formData.required_skills.includes(skillInput.trim())) {
      setFormData({
        ...formData,
        required_skills: [...formData.required_skills, skillInput.trim()],
      });
      setSkillInput('');
    }
  }, [formData, skillInput]);

  const removeRequiredSkill = useCallback((skill: string) => {
    setFormData({
      ...formData,
      required_skills: formData.required_skills.filter((s: string) => s !== skill),
    });
  }, [formData]);

  const addAdditionalSkill = useCallback(() => {
    if (additionalSkillInput.trim() && !formData.additional_requirements?.includes(additionalSkillInput.trim())) {
      setFormData({
        ...formData,
        additional_requirements: [...(formData.additional_requirements || []), additionalSkillInput.trim()],
      });
      setAdditionalSkillInput('');
    }
  }, [formData, additionalSkillInput]);

  const removeAdditionalSkill = useCallback((skill: string) => {
    setFormData({
      ...formData,
      additional_requirements: formData.additional_requirements?.filter((s: string) => s !== skill) || [],
    });
  }, [formData]);

  // Error handler for ErrorBoundary
  const handleError = useCallback((error: Error, errorInfo: React.ErrorInfo) => {
    console.error('ErrorBoundary caught an error in JobDescriptionGenerator:', error);
    console.error('Error Info:', errorInfo);
  }, []);

  const renderGeneratedDescription = () => {
    if (!generatedDescription) return null;

    return (
      <Box sx={{ mt: 4 }}>
        <Divider sx={{ mb: 3 }} />
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h5" fontWeight={600}>
            {t('jobDescriptionGenerator.results.title')}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              onClick={handleRegenerate}
              startIcon={<Icon name="refresh-cw" size={16} />}
              disabled={isGenerating}
            >
              {t('jobDescriptionGenerator.buttons.regenerate')}
            </Button>
            <Button
              variant="outlined"
              onClick={handleReset}
              startIcon={<Icon name="edit" size={16} />}
            >
              {t('jobDescriptionGenerator.buttons.editInputs')}
            </Button>
            <Button
              variant="contained"
              onClick={() => {
                if (onComplete) {
                  onComplete(generatedDescription);
                }
              }}
              startIcon={<Icon name="check" size={16} />}
            >
              {t('jobDescriptionGenerator.buttons.useDescription')}
            </Button>
          </Box>
        </Box>

        <Card variant="outlined">
          <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Title and Summary */}
            <Box>
              <Typography variant="h4" fontWeight={600} gutterBottom>
                {generatedDescription.title}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {generatedDescription.summary}
              </Typography>
            </Box>

            {/* Responsibilities */}
            <Box>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                {t('jobDescriptionGenerator.results.responsibilities')}
              </Typography>
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                {generatedDescription.responsibilities.map((resp, idx) => (
                  <Typography component="li" key={idx} variant="body1" sx={{ mb: 1 }}>
                    {resp}
                  </Typography>
                ))}
              </Box>
            </Box>

            {/* Requirements */}
            <Box>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                {t('jobDescriptionGenerator.results.requirements')}
              </Typography>
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                {generatedDescription.requirements.map((req, idx) => (
                  <Typography component="li" key={idx} variant="body1" sx={{ mb: 1 }}>
                    {req}
                  </Typography>
                ))}
              </Box>
            </Box>

            {/* Benefits */}
            {generatedDescription.benefits.length > 0 && (
              <Box>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  {t('jobDescriptionGenerator.results.benefits')}
                </Typography>
                <Box component="ul" sx={{ pl: 2, m: 0 }}>
                  {generatedDescription.benefits.map((benefit, idx) => (
                    <Typography component="li" key={idx} variant="body1" sx={{ mb: 1 }}>
                      {benefit}
                    </Typography>
                  ))}
                </Box>
              </Box>
            )}

            {/* Company Culture */}
            <Box>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                {t('jobDescriptionGenerator.results.companyCulture')}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {generatedDescription.company_culture}
              </Typography>
            </Box>

            {/* Interview Process */}
            <Box>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                {t('jobDescriptionGenerator.results.interviewProcess')}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {generatedDescription.interview_process}
              </Typography>
            </Box>

            {/* Bias Warnings */}
            {generatedDescription.bias_warnings && generatedDescription.bias_warnings.length > 0 && (
              <Box>
                <Alert severity="warning">
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    {t('jobDescriptionGenerator.results.biasWarnings.title')}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    {t('jobDescriptionGenerator.results.biasWarnings.description')}
                  </Typography>
                  <Box component="ul" sx={{ pl: 2, m: 0 }}>
                    {generatedDescription.bias_warnings.map((warning, idx) => (
                      <Typography component="li" key={idx} variant="body2" sx={{ mb: 0.5 }}>
                        {warning}
                      </Typography>
                    ))}
                  </Box>
                </Alert>
              </Box>
            )}

            {/* Inclusive Language Score */}
            {generatedDescription.inclusive_language_score !== undefined && generatedDescription.inclusive_language_score !== null && (
              <Box>
                {generatedDescription.bias_warnings && generatedDescription.bias_warnings.length === 0 ? (
                  <Alert severity="success">
                    <Typography variant="body2">
                      {t('jobDescriptionGenerator.results.biasWarnings.noWarnings')}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1, fontWeight: 600 }}>
                      {t('jobDescriptionGenerator.results.biasWarnings.inclusiveScore', {
                        score: Math.round(generatedDescription.inclusive_language_score * 100)
                      })}
                    </Typography>
                  </Alert>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    {t('jobDescriptionGenerator.results.biasWarnings.inclusiveScore', {
                      score: Math.round(generatedDescription.inclusive_language_score * 100)
                    })}
                  </Typography>
                )}
              </Box>
            )}

            {/* Metadata */}
            <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Typography variant="caption" color="text.secondary">
                {t('jobDescriptionGenerator.results.metadata', {
                  provider: generatedDescription.provider,
                  model: generatedDescription.model,
                  timestamp: new Date(generatedDescription.generated_at).toLocaleString()
                })}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  };

  return (
    <ErrorBoundary onError={handleError}>
      <Box sx={{ maxWidth: 900, mx: 'auto', p: embedded ? 0 : 3 }}>
        <Paper elevation={embedded ? 0 : 3} sx={{ p: embedded ? 0 : 4 }}>
          {/* Header */}
          {!embedded && (
            <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
              <IconButton onClick={() => navigate('/recruiter/vacancies')} disabled={isGenerating}>
                <Icon name="arrow-left" size={20} />
              </IconButton>
              <Typography variant="h4" component="h1" fontWeight={600}>
                {t('jobDescriptionGenerator.title')}
              </Typography>
            </Box>
          )}

          {/* Info Alert */}
          {!generatedDescription && (
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                {t('jobDescriptionGenerator.subtitle')}
              </Typography>
            </Alert>
          )}

          {/* Error Alert */}
          {error && (
            <ErrorMessage
              error={error}
              title={t('jobDescriptionGenerator.error.title')}
              actions={[
                {
                  label: t('jobDescriptionGenerator.error.retry'),
                  onClick: () => {
                    setError(null);
                    handleGenerate();
                  },
                  primary: true,
                },
                {
                  label: t('jobDescriptionGenerator.error.reset'),
                  onClick: () => setError(null),
                  variant: 'outlined',
                },
              ]}
            />
          )}

          {/* Form - Only show if no generated description */}
          {!generatedDescription && (
            <Stack spacing={3}>
              {/* Basic Information Section */}
              <Box>
                <Typography variant="h6" gutterBottom>
                  {t('jobDescriptionGenerator.sections.basicInfo')}
                </Typography>

                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label={`${t('jobDescriptionGenerator.fields.jobTitle')} *`}
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      placeholder={t('jobDescriptionGenerator.fields.jobTitlePlaceholder')}
                      required
                      disabled={isGenerating}
                    />
                  </Grid>

                  <Grid item xs={6}>
                    <FormControl fullWidth>
                      <InputLabel>{t('jobDescriptionGenerator.fields.seniorityLevel')}</InputLabel>
                      <Select
                        value={formData.seniority_level}
                        label={t('jobDescriptionGenerator.fields.seniorityLevel')}
                        onChange={(e) => setFormData({ ...formData, seniority_level: e.target.value })}
                        disabled={isGenerating}
                      >
                        <MenuItem value="">{t('jobDescriptionGenerator.fields.seniorityLevels.notSpecified')}</MenuItem>
                        <MenuItem value="junior">{t('jobDescriptionGenerator.fields.seniorityLevels.junior')}</MenuItem>
                        <MenuItem value="mid">{t('jobDescriptionGenerator.fields.seniorityLevels.mid')}</MenuItem>
                        <MenuItem value="senior">{t('jobDescriptionGenerator.fields.seniorityLevels.senior')}</MenuItem>
                        <MenuItem value="lead">{t('jobDescriptionGenerator.fields.seniorityLevels.lead')}</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={6}>
                    <FormControl fullWidth>
                      <InputLabel>{t('jobDescriptionGenerator.fields.employmentType')}</InputLabel>
                      <Select
                        value={formData.employment_type}
                        label={t('jobDescriptionGenerator.fields.employmentType')}
                        onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                        disabled={isGenerating}
                      >
                        <MenuItem value="">{t('jobDescriptionGenerator.fields.employmentTypes.notSpecified')}</MenuItem>
                        <MenuItem value="full-time">{t('jobDescriptionGenerator.fields.employmentTypes.fullTime')}</MenuItem>
                        <MenuItem value="part-time">{t('jobDescriptionGenerator.fields.employmentTypes.partTime')}</MenuItem>
                        <MenuItem value="contract">{t('jobDescriptionGenerator.fields.employmentTypes.contract')}</MenuItem>
                        <MenuItem value="freelance">{t('jobDescriptionGenerator.fields.employmentTypes.freelance')}</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12}>
                    <Box>
                      <Typography gutterBottom>
                        {t('jobDescriptionGenerator.fields.experienceRequired')}: {experienceLabel}
                      </Typography>
                      <Slider
                        value={formData.min_experience_months}
                        onChange={(_, value) => setFormData({ ...formData, min_experience_months: value as number })}
                        min={0}
                        max={120}
                        step={6}
                        marks={[
                          { value: 0, label: '0' },
                          { value: 12, label: '1y' },
                          { value: 36, label: '3y' },
                          { value: 60, label: '5y' },
                          { value: 120, label: '10y+' },
                        ]}
                        valueLabelDisplay="off"
                        disabled={isGenerating}
                      />
                    </Box>
                  </Grid>

                  <Grid item xs={6}>
                    <FormControl fullWidth>
                      <InputLabel>{t('jobDescriptionGenerator.fields.workFormat')}</InputLabel>
                      <Select
                        value={formData.work_format}
                        label={t('jobDescriptionGenerator.fields.workFormat')}
                        onChange={(e) => setFormData({ ...formData, work_format: e.target.value })}
                        disabled={isGenerating}
                      >
                        <MenuItem value="">{t('jobDescriptionGenerator.fields.workFormats.notSpecified')}</MenuItem>
                        <MenuItem value="remote">{t('jobDescriptionGenerator.fields.workFormats.remote')}</MenuItem>
                        <MenuItem value="office">{t('jobDescriptionGenerator.fields.workFormats.office')}</MenuItem>
                        <MenuItem value="hybrid">{t('jobDescriptionGenerator.fields.workFormats.hybrid')}</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label={t('jobDescriptionGenerator.fields.location')}
                      value={formData.location}
                      onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                      placeholder={t('jobDescriptionGenerator.fields.locationPlaceholder')}
                      disabled={isGenerating}
                    />
                  </Grid>

                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label={t('jobDescriptionGenerator.fields.industry')}
                      value={formData.industry}
                      onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                      placeholder={t('jobDescriptionGenerator.fields.industryPlaceholder')}
                      disabled={isGenerating}
                    />
                  </Grid>

                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label={t('jobDescriptionGenerator.fields.salaryRange')}
                      value={formData.salary_range}
                      onChange={(e) => setFormData({ ...formData, salary_range: e.target.value })}
                      placeholder={t('jobDescriptionGenerator.fields.salaryRangePlaceholder')}
                      disabled={isGenerating}
                    />
                  </Grid>
                </Grid>
              </Box>

              <Divider />

              {/* Skills Section */}
              <Box>
                <Typography variant="h6" gutterBottom>
                  {t('jobDescriptionGenerator.sections.skills')}
                </Typography>

                {/* Required Skills */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {`${t('jobDescriptionGenerator.fields.requiredSkills')} *`}
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                    <TextField
                      fullWidth
                      value={skillInput}
                      onChange={(e) => setSkillInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addRequiredSkill())}
                      placeholder={t('jobDescriptionGenerator.fields.requiredSkillsPlaceholder')}
                      disabled={isGenerating}
                    />
                    <Button
                      variant="contained"
                      onClick={addRequiredSkill}
                      startIcon={<Icon name="plus" size={16} />}
                      disabled={isGenerating}
                    >
                      {t('jobDescriptionGenerator.fields.addSkill')}
                    </Button>
                  </Stack>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {formData.required_skills.map((skill: string) => (
                      <SkillChip
                        key={skill}
                        skill={skill}
                        onDelete={() => removeRequiredSkill(skill)}
                        color="primary"
                      />
                    ))}
                    {formData.required_skills.length === 0 && (
                      <Typography variant="body2" color="text.secondary" italic>
                        {t('jobDescriptionGenerator.fields.atLeastOneSkillHint')}
                      </Typography>
                    )}
                  </Box>
                </Box>

                {/* Additional Skills */}
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    {t('jobDescriptionGenerator.fields.additionalSkills')}
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                    <TextField
                      fullWidth
                      value={additionalSkillInput}
                      onChange={(e) => setAdditionalSkillInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addAdditionalSkill())}
                      placeholder={t('jobDescriptionGenerator.fields.additionalSkillsPlaceholder')}
                      disabled={isGenerating}
                    />
                    <Button
                      variant="outlined"
                      onClick={addAdditionalSkill}
                      startIcon={<Icon name="plus" size={16} />}
                      disabled={isGenerating}
                    >
                      {t('jobDescriptionGenerator.fields.addSkill')}
                    </Button>
                  </Stack>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {formData.additional_requirements?.map((skill: string) => (
                      <SkillChip
                        key={skill}
                        skill={skill}
                        onDelete={() => removeAdditionalSkill(skill)}
                        color="secondary"
                      />
                    ))}
                  </Box>
                </Box>
              </Box>

              <Divider />

              {/* Generation Options */}
              <Box>
                <Typography variant="h6" gutterBottom>
                  {t('jobDescriptionGenerator.sections.generationOptions')}
                </Typography>

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <FormControl fullWidth>
                      <InputLabel>{t('jobDescriptionGenerator.fields.tone')}</InputLabel>
                      <Select
                        value={formData.tone}
                        label={t('jobDescriptionGenerator.fields.tone')}
                        onChange={(e) => setFormData({ ...formData, tone: e.target.value as 'professional' | 'casual' | 'formal' | 'friendly' })}
                        disabled={isGenerating}
                      >
                        <MenuItem value="professional">{t('jobDescriptionGenerator.fields.tones.professional')}</MenuItem>
                        <MenuItem value="casual">{t('jobDescriptionGenerator.fields.tones.casual')}</MenuItem>
                        <MenuItem value="formal">{t('jobDescriptionGenerator.fields.tones.formal')}</MenuItem>
                        <MenuItem value="friendly">{t('jobDescriptionGenerator.fields.tones.friendly')}</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={6}>
                    <FormControl fullWidth>
                      <InputLabel>{t('jobDescriptionGenerator.fields.language')}</InputLabel>
                      <Select
                        value={formData.language}
                        label={t('jobDescriptionGenerator.fields.language')}
                        onChange={(e) => setFormData({ ...formData, language: e.target.value as 'en' | 'ru' })}
                        disabled={isGenerating}
                      >
                        <MenuItem value="en">{t('jobDescriptionGenerator.fields.languages.en')}</MenuItem>
                        <MenuItem value="ru">{t('jobDescriptionGenerator.fields.languages.ru')}</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
              </Box>

              {/* Generate Button */}
              <Box sx={{ display: 'flex', justifyContent: 'center', pt: 2 }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  startIcon={isGenerating ? <CircularProgress size={20} /> : <Icon name="sparkles" size={20} />}
                  sx={{ minWidth: 200 }}
                >
                  {isGenerating ? t('jobDescriptionGenerator.buttons.generating') : t('jobDescriptionGenerator.buttons.generate')}
                </Button>
              </Box>
            </Stack>
          )}

          {/* Generated Description */}
          {renderGeneratedDescription()}
        </Paper>
      </Box>
    </ErrorBoundary>
  );
};

export default JobDescriptionGenerator;
