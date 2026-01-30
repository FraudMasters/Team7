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
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon,
  AutoAwesome as AutoAwesomeIcon,
  Work as WorkIcon,
  School as SchoolIcon,
  BusinessCenter as BusinessCenterIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
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
    deleteIcon={<DeleteIcon />}
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
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [suggestedPresets, setSuggestedPresets] = useState<typeof POSITION_PRESETS>([]);

  // Form state
  const [formData, setFormData] = useState({
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
  });

  // Debounced preset search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (formData.title.length >= 2) {
        const suggestions = getSuggestedPresets(formData.title);
        setSuggestedPresets(suggestions);
      } else {
        setSuggestedPresets([]);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timeoutId);
  }, [formData.title]);

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prevActiveStep) => prevActiveStep + 1);
      setError(null);
    }
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
    setError(null);
  };

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 0:
        if (!formData.title.trim()) {
          setError('Укажите название позиции');
          return false;
        }
        if (formData.salary_min && formData.salary_max && formData.salary_min > formData.salary_max) {
          setError('Минимальная зарплата не может быть больше максимальной');
          return false;
        }
        return true;
      case 1:
        if (formData.required_skills.length === 0) {
          setError('Добавьте хотя бы один обязательный навык');
          return false;
        }
        return true;
      case 2:
        return true;
      case 3:
        if (!formData.description.trim()) {
          setError('Опишите обязанности и задачи');
          return false;
        }
        if (formData.description.length < 30) {
          setError('Описание должно содержать минимум 30 символов');
          return false;
        }
        return true;
      default:
        return true;
    }
  };

  const handleSubmit = async () => {
    if (!validateStep(activeStep)) return;

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/vacancies/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Failed to create vacancy');
      }

      const vacancy = await response.json();

      if (onComplete) {
        onComplete(vacancy);
      } else {
        navigate('/recruiter/vacancies');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create vacancy');
      setIsSubmitting(false);
    }
  };

  const applyPreset = useCallback((preset: typeof POSITION_PRESETS[0]) => {
    setFormData((prev) => ({
      ...prev,
      title: preset.title,
      required_skills: [...preset.requiredSkills],
      additional_requirements: [...preset.optionalSkills],
      min_experience_months: preset.minExperience,
      salary_min: preset.suggestedSalary?.min || null,
      salary_max: preset.suggestedSalary?.max || null,
      description: preset.description,
    }));

    setSuggestedPresets([]);
  }, []);

  const addSkill = useCallback((skill: string, isRequired: boolean) => {
    const canonicalName = getCanonicalSkillName(skill) || skill;
    const targetArray = isRequired ? 'required_skills' : 'additional_requirements';

    setFormData((prev) => {
      if (prev[targetArray].includes(canonicalName)) {
        return prev;
      }
      return {
        ...prev,
        [targetArray]: [...prev[targetArray], canonicalName],
      };
    });
  }, []);

  const removeSkill = useCallback((skill: string, isRequired: boolean) => {
    const targetArray = isRequired ? 'required_skills' : 'additional_requirements';
    setFormData((prev) => ({
      ...prev,
      [targetArray]: prev[targetArray].filter((s: string) => s !== skill),
    }));
  }, []);

  // Memoized categories
  const allCategories = useMemo(() => getAllCategories(), []);
  const experienceLabel = useMemo(() => {
    if (formData.min_experience_months === 0) return 'Стажер';
    if (formData.min_experience_months < 12) {
      return `${formData.min_experience_months} мес.`;
    }
    const years = Math.floor(formData.min_experience_months / 12);
    const months = formData.min_experience_months % 12;
    if (months === 0) {
      return `${years} ${years === 1 ? 'год' : years < 5 ? 'года' : 'лет'}`;
    }
    return `${years} ${years === 1 ? 'год' : 'лет'} ${months} мес.`;
  }, [formData.min_experience_months]);

  // Step components
  const PositionSelectionStep = () => {
    const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setFormData((prev) => ({ ...prev, title: e.target.value }));
    };

    const handleSalaryMinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setFormData((prev) => ({
        ...prev,
        salary_min: e.target.value ? parseInt(e.target.value) : null,
      }));
    };

    const handleSalaryMaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setFormData((prev) => ({
        ...prev,
        salary_max: e.target.value ? parseInt(e.target.value) : null,
      }));
    };

    const handleExperienceChange = (_: Event, value: number | number[]) => {
      setFormData((prev) => ({
        ...prev,
        min_experience_months: value as number,
      }));
    };

    return (
      <Stack spacing={3}>
        <Typography variant="h6">Выберите или введите позицию</Typography>

        {/* Position Title Input with Suggestions */}
        <Box>
          <TextField
            fullWidth
            label="Должность"
            value={formData.title}
            onChange={handleTitleChange}
            placeholder="Например: Java Developer, Python, DevOps"
            helperText="Мы предложим готовые пресеты навыков для вашей позиции"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <WorkIcon />
                </InputAdornment>
              ),
            }}
          />

          {/* Preset Suggestions */}
          {suggestedPresets.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AutoAwesomeIcon color="primary" fontSize="small" />
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
          <Slider
            value={formData.min_experience_months}
            onChange={handleExperienceChange}
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
          />
        </Box>

        {/* Salary Range */}
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <TextField
              fullWidth
              type="number"
              label="Зарплата от ($)"
              value={formData.salary_min || ''}
              onChange={handleSalaryMinChange}
              placeholder="100000"
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              fullWidth
              type="number"
              label="Зарплата до ($)"
              value={formData.salary_max || ''}
              onChange={handleSalaryMaxChange}
              placeholder="150000"
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
                  color={formData.required_skills.includes(skill.name) ? 'primary' : 'default'}
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
              />
            )}
          />

          {/* Selected Required Skills */}
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
            {formData.required_skills.map((skill: string) => (
              <SkillChip
                key={skill}
                skill={skill}
                onDelete={() => removeSkill(skill, true)}
                color="primary"
              />
            ))}
          </Box>
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
            {formData.additional_requirements.map((skill: string) => (
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
          <InfoIcon color="info" fontSize="small" sx={{ mt: 0.25 }} />
          <Typography variant="body2" color="text.secondary">
            Система автоматически распознает синонимы (например, js → JavaScript, react → React)
          </Typography>
        </Box>
      </Stack>
    );
  };

  // Conditions Step
  const ConditionsStep = () => {
    const handleChange = (field: string) => (e: any) => {
      setFormData((prev) => ({ ...prev, [field]: e.target.value }));
    };

    return (
      <Stack spacing={3}>
        <Typography variant="h6">Условия работы</Typography>

        <Grid container spacing={2}>
          <Grid item xs={6}>
            <FormControl fullWidth>
              <InputLabel>Тип занятости</InputLabel>
              <Select
                value={formData.employment_type}
                label="Тип занятости"
                onChange={handleChange('employment_type')}
              >
                <MenuItem value="">Не указано</MenuItem>
                <MenuItem value="full-time">Полный день</MenuItem>
                <MenuItem value="part-time">Частичная занятость</MenuItem>
                <MenuItem value="contract">Контракт</MenuItem>
                <MenuItem value="freelance">Фриланс</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={6}>
            <FormControl fullWidth>
              <InputLabel>Формат работы</InputLabel>
              <Select
                value={formData.work_format}
                label="Формат работы"
                onChange={handleChange('work_format')}
              >
                <MenuItem value="">Не указано</MenuItem>
                <MenuItem value="remote">Удаленно</MenuItem>
                <MenuItem value="office">В офисе</MenuItem>
                <MenuItem value="hybrid">Гибридный</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={6}>
            <FormControl fullWidth>
              <InputLabel>Уровень английского</InputLabel>
              <Select
                value={formData.english_level}
                label="Уровень английского"
                onChange={handleChange('english_level')}
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
          </Grid>

          <Grid item xs={6}>
            <TextField
              fullWidth
              label="Локация"
              value={formData.location}
              onChange={handleChange('location')}
              placeholder="Москва, Санкт-Петербург"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Индустрия / Компания"
              value={formData.industry}
              onChange={handleChange('industry')}
              placeholder="IT, Финансы, E-commerce, Fintech"
            />
          </Grid>
        </Grid>
      </Stack>
    );
  };

  // Description Step
  const DescriptionStep = () => {
    const handleChange = (field: string) => (e: any) => {
      setFormData((prev) => ({ ...prev, [field]: e.target.value }));
    };

    const skillsList = formData.required_skills.slice(0, 3).join(', ');
    const experienceText = formData.min_experience_months > 0
      ? `${Math.floor(formData.min_experience_months / 12)}+ лет`
      : '';

    const defaultDescription = `Мы ищем ${formData.title || 'разработчика'} в команду.

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

        <TextField
          fullWidth
          multiline
          rows={8}
          label="Опишите обязанности и задачи"
          value={formData.description}
          onChange={handleChange('description')}
          placeholder={defaultDescription}
          helperText={`Минимум 30 символов (currently: ${formData.description.length})`}
          required
        />
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
    <Box sx={{ maxWidth: 900, mx: 'auto', p: 3 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate('/recruiter/vacancies')} disabled={isSubmitting}>
            <ArrowBackIcon />
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
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
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
              onClick={handleSubmit}
              color="primary"
              startIcon={isSubmitting ? <CircularProgress size={20} /> : <AutoAwesomeIcon />}
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
  );
};

export default SmartVacancyWizard;
