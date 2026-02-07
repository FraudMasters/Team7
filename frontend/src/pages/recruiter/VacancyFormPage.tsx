// Страница создания и редактирования вакансии для рекрутера
// Компонент предоставляет форму для заполнения деталей вакансии
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  Stack,
  Grid,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client';

// Интерфейс данных вакансии
interface Vacancy {
  id: string;
  title: string;
  description: string;
  required_skills: string[];
  min_experience_months?: number;
  industry?: string;
  work_format?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
}

// Списки доступных опций для полей формы
const WORK_FORMATS = ['remote', 'office', 'hybrid'];
const INDUSTRIES = [
  'IT',
  'Finance',
  'Healthcare',
  'Education',
  'Manufacturing',
  'Retail',
  'Other',
];

export function VacancyFormPage() {
  // Хуки для навигации и работы с параметрами URL
  const navigate = useNavigate();
  const { id } = useParams();
  const queryClient = useQueryClient();
  const isEditing = Boolean(id);

  // Локальное состояние для ввода навыков и данных формы
  const [skillInput, setSkillInput] = useState('');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    required_skills: [] as string[],
    min_experience_months: 0,
    industry: '',
    work_format: '',
    location: '',
    salary_min: 0,
    salary_max: 0,
  });

  // Запрос для получения данных вакансии при редактировании
  const { data: vacancyData, isLoading } = useQuery({
    queryKey: ['vacancy', id],
    queryFn: async () => {
      if (!id) return null;
      const response = await apiClient.get<{ vacancy: Vacancy }>(`/vacancies/${id}`);
      return response.data;
    },
    enabled: isEditing,
    onSuccess: (data) => {
      // Заполняем форму полученными данными
      if (data?.vacancy) {
        setFormData({
          title: data.vacancy.title || '',
          description: data.vacancy.description || '',
          required_skills: data.vacancy.required_skills || [],
          min_experience_months: data.vacancy.min_experience_months || 0,
          industry: data.vacancy.industry || '',
          work_format: data.vacancy.work_format || '',
          location: data.vacancy.location || '',
          salary_min: data.vacancy.salary_min || 0,
          salary_max: data.vacancy.salary_max || 0,
        });
      }
    },
  });

  // Мутация для создания новой вакансии
  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await apiClient.post('/vacancies', data);
      return response.data;
    },
    onSuccess: () => {
      // Инвалидируем кеш вакансий и переходим к списку
      queryClient.invalidateQueries({ queryKey: ['vacancies'] });
      navigate('/recruiter/vacancies');
    },
  });

  // Мутация для обновления существующей вакансии
  const updateMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await apiClient.put(`/vacancies/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      // Инвалидируем кеш вакансий и переходим к списку
      queryClient.invalidateQueries({ queryKey: ['vacancies'] });
      navigate('/recruiter/vacancies');
    },
  });

  // Обработчик изменения любого поля формы
  const handleInputChange = (field: string, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // Обработчик добавления навыка в список
  const handleAddSkill = () => {
    if (skillInput.trim() && !formData.required_skills.includes(skillInput.trim())) {
      setFormData((prev) => ({
        ...prev,
        required_skills: [...prev.required_skills, skillInput.trim()],
      }));
      setSkillInput('');
    }
  };

  // Обработчик удаления навыка из списка
  const handleRemoveSkill = (skillToRemove: string) => {
    setFormData((prev) => ({
      ...prev,
      required_skills: prev.required_skills.filter((s) => s !== skillToRemove),
    }));
  };

  // Обработчик отправки формы
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const mutation = isEditing ? updateMutation : createMutation;
    mutation.mutate(formData);
  };

  // Отображаем индикатор загрузки при получении данных
  if (isLoading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Кнопка возврата к списку вакансий */}
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/recruiter/vacancies')}
        sx={{ mb: 3 }}
      >
        Back to Vacancies
      </Button>

      <Paper sx={{ p: 4 }}>
        {/* Заголовок формы */}
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {isEditing ? 'Edit Vacancy' : 'Create New Vacancy'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
          {isEditing ? 'Update vacancy details' : 'Fill in the details to post a new job opening'}
        </Typography>

        {/* Сообщение об ошибке */}
        {createMutation.error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            Failed to {isEditing ? 'update' : 'create'} vacancy. Please try again.
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            {/* Заголовок вакансии */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Job Title"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                required
                placeholder="e.g. Senior Software Engineer"
              />
            </Grid>

            {/* Описание вакансии */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={6}
                label="Job Description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                required
                placeholder="Describe the role, responsibilities, and requirements..."
              />
            </Grid>

            {/* Отрасль и формат работы */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Industry"
                value={formData.industry}
                onChange={(e) => handleInputChange('industry', e.target.value)}
              >
                <MenuItem value="">Select industry</MenuItem>
                {INDUSTRIES.map((ind) => (
                  <MenuItem key={ind} value={ind}>
                    {ind}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Work Format"
                value={formData.work_format}
                onChange={(e) => handleInputChange('work_format', e.target.value)}
              >
                <MenuItem value="">Select format</MenuItem>
                {WORK_FORMATS.map((format) => (
                  <MenuItem key={format} value={format}>
                    {format.charAt(0).toUpperCase() + format.slice(1)}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>

            {/* Местоположение */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Location"
                value={formData.location}
                onChange={(e) => handleInputChange('location', e.target.value)}
                placeholder="e.g. Moscow, Russia or Remote"
              />
            </Grid>

            {/* Диапазон заработной платы */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Minimum Salary (USD/year)"
                value={formData.salary_min || ''}
                onChange={(e) => handleInputChange('salary_min', parseFloat(e.target.value) || 0)}
                InputProps={{ inputProps: { min: 0 } }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Maximum Salary (USD/year)"
                value={formData.salary_max || ''}
                onChange={(e) => handleInputChange('salary_max', parseFloat(e.target.value) || 0)}
                InputProps={{ inputProps: { min: 0 } }}
              />
            </Grid>

            {/* Минимальный опыт работы */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Minimum Experience (months)"
                value={formData.min_experience_months || ''}
                onChange={(e) => handleInputChange('min_experience_months', parseFloat(e.target.value) || 0)}
                InputProps={{ inputProps: { min: 0 } }}
                helperText="e.g. 12 for 1 year, 24 for 2 years"
              />
            </Grid>

            {/* Требуемые навыки */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Required Skills
              </Typography>
              {/* Отображение добавленных навыков как чипов */}
              <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                {formData.required_skills.map((skill) => (
                  <Chip
                    key={skill}
                    label={skill}
                    onDelete={() => handleRemoveSkill(skill)}
                    deleteIcon={<DeleteIcon />}
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Box>
              {/* Поле для добавления нового навыка */}
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  size="small"
                  label="Add skill"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddSkill();
                    }
                  }}
                  placeholder="e.g. Python, React, SQL"
                />
                <Button
                  type="button"
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={handleAddSkill}
                  disabled={!skillInput.trim()}
                >
                  Add
                </Button>
              </Box>
            </Grid>

            {/* Кнопки действий формы */}
            <Grid item xs={12}>
              <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<SaveIcon />}
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {createMutation.isPending || updateMutation.isPending ? (
                    <>
                      <CircularProgress size={16} sx={{ mr: 1 }} />
                      Saving...
                    </>
                  ) : (
                    <>Save {isEditing ? 'Changes' : 'Vacancy'}</>
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outlined"
                  onClick={() => navigate('/recruiter/vacancies')}
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  Cancel
                </Button>
              </Stack>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Container>
  );
}
