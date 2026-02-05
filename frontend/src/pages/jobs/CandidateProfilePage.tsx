// Импорт хуков для управления состоянием
import { useState } from 'react';
// Импорт компонентов MUI для UI
import {
  Box,
  Container,
  Typography,
  Paper,
  Stack,
  Button,
  Divider,
  TextField,
  Chip,
  Grid,
} from '@mui/material';
// Импорт иконок MUI
import {
  Person as PersonIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
  WorkOutline as WorkIcon,
  School as SchoolIcon,
  Edit as EditIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
// Импорт MUI компонентов
import { PageTransition } from '@components/mui/PageTransition';
import { LoadingState } from '@components/mui/LoadingState';
import { ErrorState } from '@components/mui/ErrorState';

/**
 * Интерфейс профиля кандидата
 * Описывает структуру данных профиля пользователя
 */
interface CandidateProfile {
  id: string;
  full_name: string;
  email: string;
  phone?: string;
  location?: string;
  title?: string;
  bio?: string;
  skills: string[];
  experience: Array<{
    company: string;
    position: string;
    duration: string;
  }>;
  education: Array<{
    institution: string;
    degree: string;
    field_of_study: string;
  }>;
}

/**
 * Страница профиля кандидата
 * Отображает персональную информацию, навыки, опыт работы и образование
 * Позволяет редактировать профиль
 */
export function CandidateProfilePage() {
  // Состояние режима редактирования
  const [isEditing, setIsEditing] = useState(false);
  // Состояние загрузки
  const [isLoading, setIsLoading] = useState(false);
  // Состояние ошибки
  const [error, setError] = useState<string | null>(null);
  // Данные профиля пользователя
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  // Форма редактирования профиля
  const [editForm, setEditForm] = useState<CandidateProfile | null>(null);

  // TODO: Заменить на реальный API-вызов
  // const { data: profile, isLoading, error } = useCandidateProfile();

  // Временные данные-заглушка
  const placeholderProfile: CandidateProfile = {
    id: 'candidate-1',
    full_name: 'John Doe',
    email: 'john.doe@example.com',
    phone: '+1 (555) 123-4567',
    location: 'San Francisco, CA',
    title: 'Software Engineer',
    bio: 'Passionate software engineer with 5+ years of experience in building scalable web applications.',
    skills: ['React', 'TypeScript', 'Node.js', 'Python', 'AWS', 'Docker'],
    experience: [
      {
        company: 'Tech Corp',
        position: 'Senior Software Engineer',
        duration: '2021 - Present',
      },
      {
        company: 'StartUp Inc',
        position: 'Software Engineer',
        duration: '2019 - 2021',
      },
    ],
    education: [
      {
        institution: 'University of California',
        degree: 'Bachelor of Science',
        field_of_study: 'Computer Science',
      },
    ],
  };

  // Отображение состояния загрузки
  if (isLoading) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <LoadingState message="Loading profile..." />
        </Container>
      </PageTransition>
    );
  }

  // Отображение состояния ошибки
  if (error) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <ErrorState
            title="Error"
            message={error}
            onRetry={() => window.location.reload()}
          />
        </Container>
      </PageTransition>
    );
  }

  // Текущий профиль (из данных или заглушка)
  const currentProfile = profile || placeholderProfile;
  // Отображаемая форма (в режиме редактирования или просмотра)
  const displayForm = isEditing ? editForm : currentProfile;

  /**
   * Обработчик начала редактирования
   * Копирует текущий профиль в форму редактирования
   */
  const handleEdit = () => {
    setEditForm(currentProfile);
    setIsEditing(true);
  };

  /**
   * Обработчик сохранения изменений
   * TODO: Реализовать сохранение на сервер
   */
  const handleSave = () => {
    setIsLoading(true);
    setTimeout(() => {
      setProfile(editForm);
      setIsEditing(false);
      setIsLoading(false);
    }, 1000);
  };

  /**
   * Обработчик отмены редактирования
   * Сбрасывает форму редактирования
   */
  const handleCancel = () => {
    setIsEditing(false);
    setEditForm(null);
  };

  /**
   * Обработчик изменения поля формы
   * @param field - Имя поля
   * @param value - Новое значение
   */
  const handleFormChange = (field: keyof CandidateProfile, value: any) => {
    if (editForm) {
      setEditForm({ ...editForm, [field]: value });
    }
  };

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Paper sx={{ p: { xs: 3, md: 5 } }}>
          <Stack spacing={4}>
            {/* Заголовок с информацией о кандидате */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ flexGrow: 1 }}>
                <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                  <PersonIcon sx={{ fontSize: 40, color: 'primary.main' }} />
                  <Box>
                    {isEditing ? (
                      <TextField
                        value={displayForm?.full_name || ''}
                        onChange={(e) => handleFormChange('full_name', e.target.value)}
                        variant="outlined"
                        size="small"
                        sx={{ minWidth: 300 }}
                      />
                    ) : (
                      <Typography variant="h3" fontWeight={700}>
                        {displayForm?.full_name}
                      </Typography>
                    )}
                    {displayForm?.title && (
                      <Typography variant="h6" color="text.secondary">
                        {displayForm.title}
                      </Typography>
                    )}
                  </Box>
                </Stack>
              </Box>
              {!isEditing ? (
                <Button
                  variant="outlined"
                  startIcon={<EditIcon />}
                  onClick={handleEdit}
                >
                  Edit Profile
                </Button>
              ) : (
                <Stack direction="row" spacing={2}>
                  <Button
                    variant="outlined"
                    onClick={handleCancel}
                    disabled={isLoading}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<SaveIcon />}
                    onClick={handleSave}
                    disabled={isLoading}
                  >
                    Save
                  </Button>
                </Stack>
              )}
            </Box>

            <Divider />

            {/* Контактная информация */}
            <Box>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Contact Information
              </Typography>
              <Stack spacing={2} sx={{ mt: 2 }}>
                <Stack direction="row" spacing={2} alignItems="center">
                  <EmailIcon sx={{ color: 'text.secondary' }} />
                  {isEditing ? (
                    <TextField
                      value={displayForm?.email || ''}
                      onChange={(e) => handleFormChange('email', e.target.value)}
                      variant="outlined"
                      size="small"
                      fullWidth
                    />
                  ) : (
                    <Typography>{displayForm?.email}</Typography>
                  )}
                </Stack>
                {displayForm?.phone && (
                  <Stack direction="row" spacing={2} alignItems="center">
                    <PhoneIcon sx={{ color: 'text.secondary' }} />
                    {isEditing ? (
                      <TextField
                        value={displayForm.phone}
                        onChange={(e) => handleFormChange('phone', e.target.value)}
                        variant="outlined"
                        size="small"
                        fullWidth
                      />
                    ) : (
                      <Typography>{displayForm.phone}</Typography>
                    )}
                  </Stack>
                )}
                {displayForm?.location && (
                  <Stack direction="row" spacing={2} alignItems="center">
                    <LocationIcon sx={{ color: 'text.secondary' }} />
                    {isEditing ? (
                      <TextField
                        value={displayForm.location}
                        onChange={(e) => handleFormChange('location', e.target.value)}
                        variant="outlined"
                        size="small"
                        fullWidth
                      />
                    ) : (
                      <Typography>{displayForm.location}</Typography>
                    )}
                  </Stack>
                )}
              </Stack>
            </Box>

            <Divider />

            {/* Биография */}
            {displayForm?.bio && (
              <Box>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  About
                </Typography>
                {isEditing ? (
                  <TextField
                    value={displayForm.bio}
                    onChange={(e) => handleFormChange('bio', e.target.value)}
                    multiline
                    rows={4}
                    fullWidth
                    variant="outlined"
                    sx={{ mt: 2 }}
                  />
                ) : (
                  <Typography
                    variant="body1"
                    color="text.secondary"
                    sx={{
                      whiteSpace: 'pre-wrap',
                      lineHeight: 1.8,
                    }}
                  >
                    {displayForm.bio}
                  </Typography>
                )}
              </Box>
            )}

            <Divider />

            {/* Навыки */}
            <Box>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Skills
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" gap={1} sx={{ mt: 2 }}>
                {displayForm?.skills.map((skill) => (
                  <Chip
                    key={skill}
                    label={skill}
                    variant="outlined"
                    sx={{
                      borderRadius: 2,
                      px: 1,
                    }}
                  />
                ))}
              </Stack>
            </Box>

            <Divider />

            {/* Опыт работы */}
            {displayForm?.experience && displayForm.experience.length > 0 && (
              <Box>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Experience
                </Typography>
                <Stack spacing={3} sx={{ mt: 2 }}>
                  {displayForm.experience.map((exp, index) => (
                    <Box key={index}>
                      <Stack direction="row" spacing={2} alignItems="flex-start">
                        <WorkIcon sx={{ color: 'primary.main', mt: 0.5 }} />
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="subtitle1" fontWeight={600}>
                            {exp.position}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {exp.company}
                          </Typography>
                          <Typography variant="body2" color="primary">
                            {exp.duration}
                          </Typography>
                        </Box>
                      </Stack>
                    </Box>
                  ))}
                </Stack>
              </Box>
            )}

            <Divider />

            {/* Образование */}
            {displayForm?.education && displayForm.education.length > 0 && (
              <Box>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Education
                </Typography>
                <Stack spacing={3} sx={{ mt: 2 }}>
                  {displayForm.education.map((edu, index) => (
                    <Box key={index}>
                      <Stack direction="row" spacing={2} alignItems="flex-start">
                        <SchoolIcon sx={{ color: 'primary.main', mt: 0.5 }} />
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="subtitle1" fontWeight={600}>
                            {edu.degree}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {edu.institution}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {edu.field_of_study}
                          </Typography>
                        </Box>
                      </Stack>
                    </Box>
                  ))}
                </Stack>
              </Box>
            )}
          </Stack>
        </Paper>
      </Container>
    </PageTransition>
  );
}
