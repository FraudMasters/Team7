import React, { useState } from 'react';
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
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const steps = ['Базовая информация', 'Навыки', 'Дополнительно', 'Обязанности'];

interface VacancyWizardProps {
  onComplete?: (vacancy: any) => void;
  initialData?: any;
}

const VacancyWizard: React.FC<VacancyWizardProps> = ({ onComplete, initialData }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    // Step 1: Basic Info
    title: initialData?.title || '',
    min_experience_months: initialData?.min_experience_months || 0,
    salary_min: initialData?.salary_min || null,
    salary_max: initialData?.salary_max || null,

    // Step 2: Skills
    required_skills: initialData?.required_skills || [],
    additional_requirements: initialData?.additional_requirements || [],

    // Step 3: Additional
    industry: initialData?.industry || '',
    work_format: initialData?.work_format || '',
    location: initialData?.location || '',
    english_level: initialData?.english_level || '',
    employment_type: initialData?.employment_type || '',

    // Step 4: Description
    description: initialData?.description || '',
  });

  // Temp state for skill input
  const [skillInput, setSkillInput] = useState('');
  const [additionalSkillInput, setAdditionalSkillInput] = useState('');

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
          setError('Укажите название должности');
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
        if (formData.description.length < 50) {
          setError('Описание должно содержать минимум 50 символов');
          return false;
        }
        return true;
      default:
        return true;
    }
  };

  const handleSubmit = async () => {
    if (!validateStep(activeStep)) return;

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
        navigate('/vacancies');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create vacancy');
    }
  };

  const addRequiredSkill = () => {
    if (skillInput.trim() && !formData.required_skills.includes(skillInput.trim())) {
      setFormData({
        ...formData,
        required_skills: [...formData.required_skills, skillInput.trim()],
      });
      setSkillInput('');
    }
  };

  const removeRequiredSkill = (skill: string) => {
    setFormData({
      ...formData,
      required_skills: formData.required_skills.filter((s: string) => s !== skill),
    });
  };

  const addAdditionalSkill = () => {
    if (additionalSkillInput.trim() && !formData.additional_requirements.includes(additionalSkillInput.trim())) {
      setFormData({
        ...formData,
        additional_requirements: [...formData.additional_requirements, additionalSkillInput.trim()],
      });
      setAdditionalSkillInput('');
    }
  };

  const removeAdditionalSkill = (skill: string) => {
    setFormData({
      ...formData,
      additional_requirements: formData.additional_requirements.filter((s: string) => s !== skill),
    });
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Stack spacing={3}>
            <Typography variant="h6">Основная информация</Typography>

            <TextField
              fullWidth
              label="Должность"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Например: Senior Java Developer"
              required
            />

            <Box>
              <Typography gutterBottom>Опыт работы (месяцев): {formData.min_experience_months}</Typography>
              <Slider
                value={formData.min_experience_months}
                onChange={(_, value) => setFormData({ ...formData, min_experience_months: value as number })}
                min={0}
                max={120}
                step={6}
                marks={[
                  { value: 0, label: '0' },
                  { value: 12, label: '1 год' },
                  { value: 36, label: '3 года' },
                  { value: 60, label: '5 лет' },
                  { value: 120, label: '10+ лет' },
                ]}
                valueLabelDisplay="auto"
              />
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Зарплата от ($)"
                  value={formData.salary_min || ''}
                  onChange={(e) => setFormData({ ...formData, salary_min: e.target.value ? parseInt(e.target.value) : null })}
                  placeholder="100000"
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Зарплата до ($)"
                  value={formData.salary_max || ''}
                  onChange={(e) => setFormData({ ...formData, salary_max: e.target.value ? parseInt(e.target.value) : null })}
                  placeholder="150000"
                />
              </Grid>
            </Grid>
          </Stack>
        );

      case 1:
        return (
          <Stack spacing={3}>
            <Typography variant="h6">Технические навыки</Typography>

            <Box>
              <Typography variant="subtitle2" gutterBottom>Обязательные навыки *</Typography>
              <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addRequiredSkill()}
                  placeholder="Добавьте навык (например: Java, Python, React)"
                />
                <Button variant="contained" onClick={addRequiredSkill} startIcon={<AddIcon />}>
                  Добавить
                </Button>
              </Stack>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {formData.required_skills.map((skill: string) => (
                  <Chip
                    key={skill}
                    label={skill}
                    onDelete={() => removeRequiredSkill(skill)}
                    color="primary"
                    deleteIcon={<DeleteIcon />}
                  />
                ))}
              </Box>
            </Box>

            <Box>
              <Typography variant="subtitle2" gutterBottom>Желательные навыки (опционально)</Typography>
              <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  value={additionalSkillInput}
                  onChange={(e) => setAdditionalSkillInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addAdditionalSkill()}
                  placeholder="Дополнительные навыки"
                />
                <Button variant="outlined" onClick={addAdditionalSkill} startIcon={<AddIcon />}>
                  Добавить
                </Button>
              </Stack>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {formData.additional_requirements.map((skill: string) => (
                  <Chip
                    key={skill}
                    label={skill}
                    onDelete={() => removeAdditionalSkill(skill)}
                    color="secondary"
                    deleteIcon={<DeleteIcon />}
                  />
                ))}
              </Box>
            </Box>
          </Stack>
        );

      case 2:
        return (
          <Stack spacing={3}>
            <Typography variant="h6">Дополнительные требования</Typography>

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <FormControl fullWidth>
                  <InputLabel>Тип занятости</InputLabel>
                  <Select
                    value={formData.employment_type}
                    label="Тип занятости"
                    onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
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
                    onChange={(e) => setFormData({ ...formData, work_format: e.target.value })}
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
                    onChange={(e) => setFormData({ ...formData, english_level: e.target.value })}
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
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  placeholder="Москва, Санкт-Петербург и т.д."
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Индустрия"
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  placeholder="IT, Финансы, E-commerce и т.д."
                />
              </Grid>
            </Grid>
          </Stack>
        );

      case 3:
        return (
          <Stack spacing={3}>
            <Typography variant="h6">Обязанности и задачи</Typography>

            <TextField
              fullWidth
              multiline
              rows={8}
              label="Описание вакансии *"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Опишите основные обязанности, задачи, проекты и требования к кандидату..."
              helperText={`Минимум 50 символов (currently: ${formData.description.length})`}
              required
            />

            <Box sx={{ bgcolor: 'info.50', p: 2, borderRadius: 1 }}>
              <Typography variant="subtitle2" color="info.dark">
                Подсказки для хорошего описания:
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Перечислите основные обязанности и задачи
                <br />
                • Укажите, над какими проектами предстоит работать
                <br />
                • Опишите команду и процессы
                <br />
                • Упомяните возможности для роста
              </Typography>
            </Box>
          </Stack>
        );

      default:
        return null;
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate('/vacancies')}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4" component="h1" fontWeight={600}>
            Создать запрос на сотрудника
          </Typography>
        </Box>

        {/* Stepper */}
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
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
            disabled={activeStep === 0}
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
            >
              Создать вакансию
            </Button>
          ) : (
            <Button
              variant="contained"
              onClick={handleNext}
              color="primary"
            >
              Далее
            </Button>
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default VacancyWizard;
