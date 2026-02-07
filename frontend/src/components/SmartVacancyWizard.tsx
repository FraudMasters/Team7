import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stepper,
  Step,
  StepLabel,
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
  Autocomplete,
  Card,
  CardContent,
  ToggleButtonGroup,
  ToggleButton,
  Divider,
  Tooltip,
  InputAdornment,
  CircularProgress,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useKeyboardNavigation } from '@/hooks/useKeyboardNavigation';
import ErrorBoundary from './ErrorBoundary';
import ErrorMessage, { ErrorType, ErrorAction } from './ErrorMessage';
import {
  searchSkills,
  getCanonicalSkillName,
  getAllCategories,
  getSkillsByCategory,
} from '@/data/skillsTaxonomy';
import {
  POSITION_PRESETS,
  findPresetByKeyword,
  getSuggestedPresets,
} from '@/data/positionPresets';

const steps = ['Выбор позиции', 'Навыки', 'Условия', 'Описание'];

// Zod validation schema for vacancy form
const vacancySchema = z.object({
  title: z.string().min(1, 'Укажите название позиции'),
  positionCategory: z.string().optional(),
  min_experience_months: z.number().min(0, 'Опыт работы не может быть отрицательным'),
  salary_min: z.number().nullable().optional(),
  salary_max: z.number().nullable().optional(),
  required_skills: z.array(z.string()).min(1, 'Добавьте хотя бы один обязательный навык'),
  additional_requirements: z.array(z.string()).optional(),
  industry: z.string().optional(),
  work_format: z.string().optional(),
  location: z.string().optional(),
  english_level: z.string().optional(),
  employment_type: z.string().optional(),
  description: z.string().min(30, 'Описание должно содержать минимум 30 символов'),
}).refine((data) => {
  if (data.salary_min && data.salary_max && data.salary_min > data.salary_max) {
    return false;
  }
  return true;
}, {
  message: 'Минимальная зарплата не может быть больше максимальной',
  path: ['salary_min'],
});

type VacancyFormData = z.infer<typeof vacancySchema>;

interface SmartVacancyWizardProps {
  onComplete?: (vacancy: any) => void;
  initialData?: any;
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

// Memoized preset card component
const PresetCard = React.memo<{
  preset: typeof POSITION_PRESETS[0];
  onApply: () => void;
}>(({ preset, onApply }) => (
  <Card
    variant="outlined"
    sx={{
      cursor: 'pointer',
      transition: 'all 0.2s',
      '&:hover': {
        borderColor: 'primary.main',
        boxShadow: 2,
      },
    }}
    onClick={onApply}
  >
    <CardContent>
      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
        {preset.title}
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
        {preset.requiredSkills.slice(0, 4).map((skill) => (
          <Chip key={skill} label={skill} size="small" variant="outlined" />
        ))}
        {preset.requiredSkills.length > 4 && (
          <Chip
            label={`+${preset.requiredSkills.length - 4}`}
            size="small"
            variant="outlined"
          />
        )}
      </Box>
      <Typography variant="caption" color="text.secondary">
        Опыт: {preset.minExperience / 12}+ лет
      </Typography>
    </CardContent>
  </Card>
));

PresetCard.displayName = 'PresetCard';

const SmartVacancyWizard: React.FC<SmartVacancyWizardProps> = ({
  onComplete,
  initialData
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState<Error | ErrorType | string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [suggestedPresets, setSuggestedPresets] = useState<typeof POSITION_PRESETS>([]);
  const [draftRestored, setDraftRestored] = useState(false);

  // React Hook Form setup with Zod validation
  const {
    control,
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isDirty, dirtyFields },
    reset,
  } = useForm<VacancyFormData>({
    resolver: zodResolver(vacancySchema),
    mode: 'onBlur',
    defaultValues: {
      title: initialData?.title || '',
      positionCategory: initialData?.positionCategory || '',
      min_experience_months: initialData?.min_experience_months || 0,
      salary_min: initialData?.salary_min || null,
      salary_max: initialData?.salary_max || null,
      required_skills: initialData?.required_skills || [],
      additional_requirements: initialData?.additional_requirements || [],
      industry: initialData?.industry || '',
      work_format: initialData?.work_format || '',
      location: initialData?.location || '',
      english_level: initialData?.english_level || '',
      employment_type: initialData?.employment_type || '',
      description: initialData?.description || '',
    },
  });

  // Watch form values for auto-save and preset search
  const formValues = watch();

  // Load draft from localStorage on mount
  useEffect(() => {
    const savedDraft = localStorage.getItem('vacancy-draft');
    if (savedDraft) {
      try {
        const draft = JSON.parse(savedDraft);
        // Only restore if we're not editing existing vacancy
        if (!initialData?.title) {
          reset(draft);
          setDraftRestored(true);
          // Auto-hide the draft restored message after 5 seconds
          setTimeout(() => setDraftRestored(false), 5000);
        }
      } catch (err) {
        // Invalid draft, ignore
      }
    }
  }, [reset, initialData]);

  // Auto-save to localStorage when form is dirty
  useEffect(() => {
    if (isDirty) {
      localStorage.setItem('vacancy-draft', JSON.stringify(formValues));
    }
  }, [formValues, isDirty]);

  // Clear draft on successful submission
  const clearDraft = useCallback(() => {
    localStorage.removeItem('vacancy-draft');
  }, []);

  // Debounced preset search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (formValues.title.length >= 2) {
        const suggestions = getSuggestedPresets(formValues.title);
        setSuggestedPresets(suggestions);
      } else {
        setSuggestedPresets([]);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timeoutId);
  }, [formValues.title]);

  const handleNext = async () => {
    // Validate current step fields
    let isValid = false;
    switch (activeStep) {
      case 0:
        // Validate title and salary
        const titleValid = await vacancySchema.shape.title.safeParseAsync(formValues.title);
        const salaryValid = await vacancySchema.safeParseAsync({
          salary_min: formValues.salary_min,
          salary_max: formValues.salary_max,
        });
        if (!titleValid.success) {
          setError(titleValid.error.errors[0].message);
          return;
        }
        if (!salaryValid.success && salaryValid.error.errors.some((e: any) => e.path.includes('salary_min'))) {
          setError('Минимальная зарплата не может быть больше максимальной');
          return;
        }
        isValid = true;
        break;
      case 1:
        const skillsValid = await vacancySchema.shape.required_skills.safeParseAsync(formValues.required_skills);
        if (!skillsValid.success) {
          setError(skillsValid.error.errors[0].message);
          return;
        }
        isValid = true;
        break;
      case 2:
        isValid = true;
        break;
      case 3:
        const descValid = await vacancySchema.shape.description.safeParseAsync(formValues.description);
        if (!descValid.success) {
          setError(descValid.error.errors[0].message);
          return;
        }
        isValid = true;
        break;
      default:
        isValid = true;
    }

    if (isValid) {
      setActiveStep((prevActiveStep) => prevActiveStep + 1);
      setError(null);
    }
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
    setError(null);
  };

  const onSubmit = async (data: VacancyFormData) => {
    setIsSubmitting(true);

    try {
      const response = await fetch('/api/vacancies/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to create vacancy');
      }

      const vacancy = await response.json();

      // Clear draft on success
      clearDraft();

      if (onComplete) {
        onComplete(vacancy);
      } else {
        navigate('/recruiter/vacancies');
      }
    } catch (err) {
      setError(err instanceof Error ? err : 'Failed to create vacancy');
      setIsSubmitting(false);
    }
  };

  const applyPreset = useCallback((preset: typeof POSITION_PRESETS[0]) => {
    setValue('title', preset.title);
    setValue('required_skills', [...preset.requiredSkills]);
    setValue('additional_requirements', [...preset.optionalSkills]);
    setValue('min_experience_months', preset.minExperience);
    setValue('salary_min', preset.suggestedSalary?.min || null);
    setValue('salary_max', preset.suggestedSalary?.max || null);
    setValue('description', preset.description);

    setSuggestedPresets([]);
  }, [setValue]);

  // Keyboard shortcuts for form navigation and actions
  useKeyboardNavigation({
    shortcuts: [
      {
        id: 'vacancy-form.save',
        key: 's',
        modifiers: ['Ctrl'],
        handler: () => handleSubmit(onSubmit)(),
        description: 'Save vacancy form',
        preventDefault: true,
        priority: 10,
      },
      {
        id: 'vacancy-form.cancel',
        key: 'Escape',
        handler: () => {
          // Navigate back on Escape if not on first step
          if (activeStep > 0) {
            handleBack();
          } else {
            // If on first step, navigate back to vacancies list
            navigate('/recruiter/vacancies');
          }
        },
        description: 'Cancel or go back',
        preventDefault: false,
        priority: 5,
        when: () => !isSubmitting, // Disable when submitting
      },
    ],
    priority: 10,
    preventDefault: true,
  });

  const addSkill = useCallback((skill: string, isRequired: boolean) => {
    const canonicalName = getCanonicalSkillName(skill) || skill;
    const targetField = isRequired ? 'required_skills' : 'additional_requirements';
    const currentSkills = isRequired ? formValues.required_skills : formValues.additional_requirements;

    if (!currentSkills.includes(canonicalName)) {
      setValue(targetField, [...currentSkills, canonicalName]);
    }
  }, [formValues.required_skills, formValues.additional_requirements, setValue]);

  const removeSkill = useCallback((skill: string, isRequired: boolean) => {
    const targetField = isRequired ? 'required_skills' : 'additional_requirements';
    const currentSkills = isRequired ? formValues.required_skills : formValues.additional_requirements;

    setValue(targetField, currentSkills.filter((s: string) => s !== skill));
  }, [formValues.required_skills, formValues.additional_requirements, setValue]);

  // Memoized categories
  const allCategories = useMemo(() => getAllCategories(), []);
  const experienceLabel = useMemo(() => {
    if (formValues.min_experience_months === 0) return 'Стажер';
    if (formValues.min_experience_months < 12) {
      return `${formValues.min_experience_months} мес.`;
    }
    const years = Math.floor(formValues.min_experience_months / 12);
    const months = formValues.min_experience_months % 12;
    if (months === 0) {
      return `${years} ${years === 1 ? 'год' : years < 5 ? 'года' : 'лет'}`;
    }
    return `${years} ${years === 1 ? 'год' : 'лет'} ${months} мес.`;
  }, [formValues.min_experience_months]);

  // Error handler for ErrorBoundary
  const handleError = useCallback((error: Error, errorInfo: React.ErrorInfo) => {
    console.error('ErrorBoundary caught an error in SmartVacancyWizard:', error);
    console.error('Error Info:', errorInfo);
  }, []);

  // Step components
  const PositionSelectionStep = () => {
    return (
      <Stack spacing={3}>
        <Typography variant="h6">Выберите или введите позицию</Typography>

        {/* Position Title Input with Suggestions */}
        <Box>
          <Controller
            name="title"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                label="Должность"
                placeholder="Например: Java Developer, Python, DevOps"
                helperText="Мы предложим готовые пресеты навыков для вашей позиции"
                error={!!errors.title}
                inputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Icon name="briefcase" size={20} />
                    </InputAdornment>
                  ),
                }}
              />
            )}
          />
          {errors.title && (
            <Typography variant="caption" color="error" sx={{ mt: 0.5 }}>
              {errors.title.message}
            </Typography>
          )}

          {/* Preset Suggestions */}
          {suggestedPresets.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Icon name="sparkles" size="small" color="primary" />
                Готовые пресеты для вашей позиции:
              </Typography>
              <Grid container spacing={2}>
                {suggestedPresets.map((preset) => (
                  <Grid item xs={12} md={6} key={preset.id}>
                    <PresetCard
                      key={preset.id}
                      preset={preset}
                      onApply={() => applyPreset(preset)}
                    />
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}
        </Box>

        {/* Experience Slider */}
        <Box>
          <Typography gutterBottom>
            Опыт работы: {experienceLabel}
          </Typography>
          <Controller
            name="min_experience_months"
            control={control}
            render={({ field }) => (
              <Slider
                {...field}
                min={0}
                max={120}
                step={6}
                marks={[
                  { value: 0, label: 'Стажер' },
                  { value: 12, label: '1 год' },
                  { value: 36, label: '3 года' },
                  { value: 60, label: '5 лет' },
                  { value: 120, label: '10+ лет' },
                ]}
                valueLabelDisplay="off"
                sx={{ mt: 2 }}
                onChange={(_, value) => field.onChange(value as number)}
              />
            )}
          />
        </Box>

        {/* Salary Range */}
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Controller
              name="salary_min"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  value={field.value || ''}
                  onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : null)}
                  fullWidth
                  type="number"
                  label="Зарплата от ($)"
                  placeholder="100000"
                  error={!!errors.salary_min}
                  helperText={errors.salary_min?.message}
                />
              )}
            />
          </Grid>
          <Grid item xs={6}>
            <Controller
              name="salary_max"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  value={field.value || ''}
                  onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : null)}
                  fullWidth
                  type="number"
                  label="Зарплата до ($)"
                  placeholder="150000"
                  error={!!errors.salary_max}
                  helperText={errors.salary_max?.message}
                />
              )}
            />
          </Grid>
        </Grid>
      </Stack>
    );
  };

  // Skills Selection Step
  const SkillsSelectionStep = () => {
    const [selectedCategory, setSelectedCategory] = useState<string>('');

    const categorySkills = useMemo(
      () => (selectedCategory ? getSkillsByCategory(selectedCategory) : []),
      [selectedCategory]
    );

    return (
      <Stack spacing={3}>
        <Typography variant="h6">Навыки и технологии</Typography>

        {/* Category Quick Selection */}
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Быстрый выбор по категориям:
          </Typography>
          <ToggleButtonGroup
            value={selectedCategory}
            exclusive
            onChange={(e, value) => setSelectedCategory(value || '')}
            sx={{ flexWrap: 'wrap', justifyContent: 'flex-start' }}
          >
            {allCategories.map((cat) => (
              <ToggleButton key={cat.id} value={cat.id} size="small">
                {cat.name}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>

        {/* Show category skills if selected */}
        {selectedCategory && categorySkills.length > 0 && (
          <Box sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              {allCategories.find((c) => c.id === selectedCategory)?.name}:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {categorySkills.slice(0, 12).map((skill) => (
                <Chip
                  key={skill.id}
                  label={skill.name}
                  size="small"
                  variant="outlined"
                  clickable
                  onClick={() => addSkill(skill.name, true)}
                  color={formValues.required_skills.includes(skill.name) ? 'primary' : 'default'}
                />
              ))}
            </Box>
          </Box>
        )}

        <Divider />

        {/* Required Skills with Autocomplete */}
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Обязательные навыки *:
          </Typography>
          <Autocomplete
            fullWidth
            options={[]}
            freeSolo
            disableClearable
            onChange={(_, value) => {
              if (value) {
                addSkill(value as string, true);
              }
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="Навык"
                placeholder="Начните вводить (напр: Java, react, docker)"
                helperText="Автодополнение с синонимами (js → JavaScript)"
                error={!!errors.required_skills}
              />
            )}
          />

          {/* Selected Required Skills */}
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
            {formValues.required_skills.map((skill: string) => (
              <SkillChip
                key={skill}
                skill={skill}
                onDelete={() => removeSkill(skill, true)}
                color="primary"
              />
            ))}
          </Box>
          {errors.required_skills && (
            <Typography variant="caption" color="error" sx={{ mt: 0.5 }}>
              {errors.required_skills.message}
            </Typography>
          )}
        </Box>

        {/* Additional Skills with Autocomplete */}
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Желательные навыки (опционально):
          </Typography>
          <Autocomplete
            fullWidth
            options={[]}
            freeSolo
            disableClearable
            onChange={(_, value) => {
              if (value) {
                addSkill(value as string, false);
              }
            }}
            renderInput={(params) => (
              <TextField {...params} label="Навык" placeholder="Дополнительные навыки" />
            )}
          />

          {/* Selected Additional Skills */}
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
            {formValues.additional_requirements.map((skill: string) => (
              <SkillChip
                key={skill}
                skill={skill}
                onDelete={() => removeSkill(skill, false)}
                color="secondary"
              />
            ))}
          </Box>
        </Box>

        {/* Info Box */}
        <Box sx={{ bgcolor: 'info.50', p: 2, borderRadius: 1, display: 'flex', gap: 1 }}>
          <Icon name="info" size="small" color="info" style={{ marginTop: '2px' }} />
          <Typography variant="body2" color="text.secondary">
            Система автоматически распознает синонимы (например, js → JavaScript, react → React)
          </Typography>
        </Box>
      </Stack>
    );
  };

  // Conditions Step
  const ConditionsStep = () => {
    return (
      <Stack spacing={3}>
        <Typography variant="h6">Условия работы</Typography>

        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Controller
              name="employment_type"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth>
                  <InputLabel>Тип занятости</InputLabel>
                  <Select
                    {...field}
                    label="Тип занятости"
                  >
                    <MenuItem value="">Не указано</MenuItem>
                    <MenuItem value="full-time">Полный день</MenuItem>
                    <MenuItem value="part-time">Частичная занятость</MenuItem>
                    <MenuItem value="contract">Контракт</MenuItem>
                    <MenuItem value="freelance">Фриланс</MenuItem>
                  </Select>
                </FormControl>
              )}
            />
          </Grid>

          <Grid item xs={6}>
            <Controller
              name="work_format"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth>
                  <InputLabel>Формат работы</InputLabel>
                  <Select
                    {...field}
                    label="Формат работы"
                  >
                    <MenuItem value="">Не указано</MenuItem>
                    <MenuItem value="remote">Удаленно</MenuItem>
                    <MenuItem value="office">В офисе</MenuItem>
                    <MenuItem value="hybrid">Гибридный</MenuItem>
                  </Select>
                </FormControl>
              )}
            />
          </Grid>

          <Grid item xs={6}>
            <Controller
              name="english_level"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth>
                  <InputLabel>Уровень английского</InputLabel>
                  <Select
                    {...field}
                    label="Уровень английского"
                  >
                    <MenuItem value="">Не требуется</MenuItem>
                    <MenuItem value="A1">A1 - Beginner</MenuItem>
                    <MenuItem value="A2">A2 - Elementary</MenuItem>
                    <MenuItem value="B1">B1 - Intermediate</MenuItem>
                    <MenuItem value="B2">B2 - Upper-Intermediate</MenuItem>
                    <MenuItem value="C1">C1 - Advanced</MenuItem>
                    <MenuItem value="C2">C2 - Proficiency</MenuItem>
                  </Select>
                </FormControl>
              )}
            />
          </Grid>

          <Grid item xs={6}>
            <Controller
              name="location"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Локация"
                  placeholder="Москва, Санкт-Петербург"
                />
              )}
            />
          </Grid>

          <Grid item xs={12}>
            <Controller
              name="industry"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Индустрия / Компания"
                  placeholder="IT, Финансы, E-commerce, Fintech"
                />
              )}
            />
          </Grid>
        </Grid>
      </Stack>
    );
  };

  // Description Step
  const DescriptionStep = () => {
    const skillsList = formValues.required_skills.slice(0, 3).join(', ');
    const experienceText = formValues.min_experience_months > 0
      ? `${Math.floor(formValues.min_experience_months / 12)}+ лет`
      : '';

    const defaultDescription = `Мы ищем ${formValues.title || 'разработчика'} в команду.

Обязанности:
• Разработка и поддержка сервисов
• Участие в код-ревью и архитектурных решениях
• Работа в команде с другими разработчиками

Наши ожидания:
${skillsList ? `• ${skillsList} на уровне ${experienceText}` : ''}
• Умение работать в команде
• Ответственность и внимательность к деталям`;

    return (
      <Stack spacing={3}>
        <Typography variant="h6">Описание вакансии</Typography>

        <Controller
          name="description"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              multiline
              rows={8}
              label="Опишите обязанности и задачи"
              placeholder={defaultDescription}
              helperText={`Минимум 30 символов (currently: ${field.value?.length || 0})`}
              required
              error={!!errors.description}
            />
          )}
        />
        {errors.description && (
          <Typography variant="caption" color="error">
            {errors.description.message}
          </Typography>
        )}
      </Stack>
    );
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return <PositionSelectionStep />;
      case 1:
        return <SkillsSelectionStep />;
      case 2:
        return <ConditionsStep />;
      case 3:
        return <DescriptionStep />;
      default:
        return null;
    }
  };

  return (
    <ErrorBoundary onError={handleError}>
      <Box sx={{ maxWidth: 900, mx: 'auto', p: 3 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate('/recruiter/vacancies')} disabled={isSubmitting}>
            <Icon name="arrow-left" size={20} />
          </IconButton>
          <Typography variant="h4" component="h1" fontWeight={600}>
            Создать запрос на сотрудника
          </Typography>
        </Box>

        {/* Stepper */}
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label, index) => {
            const stepProps: { completed?: boolean } = {};
            const labelProps: { optional?: React.ReactNode } = {};

            return (
              <Step key={label} {...stepProps}>
                <StepLabel {...labelProps}>{label}</StepLabel>
              </Step>
            );
          })}
        </Stepper>

        {/* Error Alert */}
        {error && (
          <ErrorMessage
            error={error}
            title="Failed to Create Vacancy"
            actions={[
              {
                label: 'Retry',
                onClick: () => {
                  setError(null);
                  handleSubmit(onSubmit)();
                },
                primary: true,
              },
              {
                label: 'Save Draft',
                onClick: () => {
                  setError(null);
                  // Draft is already auto-saved
                },
                variant: 'outlined',
              },
            ]}
          />
        )}

        {/* Draft Restored Alert */}
        {draftRestored && (
          <Alert severity="info" sx={{ mb: 3 }} onClose={() => setDraftRestored(false)}>
            Черновик формы восстановлен из сохраненной версии
          </Alert>
        )}

        {/* Auto-save Indicator */}
        {isDirty && (
          <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
            <CircularProgress size={16} />
            <Typography variant="caption">
              Автосохранение...
            </Typography>
          </Box>
        )}

        {/* Step Content */}
        <Box sx={{ mb: 4 }}>
          {renderStepContent(activeStep)}
        </Box>

        {/* Navigation Buttons */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button
            disabled={activeStep === 0 || isSubmitting}
            onClick={handleBack}
            variant="outlined"
          >
            Назад
          </Button>

          {activeStep === steps.length - 1 ? (
            <Button
              variant="contained"
              onClick={handleSubmit(onSubmit)}
              color="primary"
              startIcon={isSubmitting ? <CircularProgress size={20} /> : <Icon name="sparkles" size={16} />}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Создание...' : 'Создать вакансию'}
            </Button>
          ) : (
            <Button variant="contained" onClick={handleNext} color="primary">
              Далее
            </Button>
          )}
        </Box>
      </Paper>
      </Box>
    </ErrorBoundary>
  );
};

export default SmartVacancyWizard;
