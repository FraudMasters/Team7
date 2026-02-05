/**
 * Страница деталей вакансии
 *
 * Отображает подробную информацию о вакансии: заголовок, местоположение,
 * зарплату, требуемые навыки и описание. Использует MUI компоненты для
 * отображения информации и кнопок навигации.
 */

// Импорт хуков React Router для навигации и получения параметров URL
import { useParams, useNavigate } from 'react-router-dom';

// Импорт компонентов MUI для верстки и отображения контента
import {
  Box,
  Container,
  Typography,
  Paper,
  Stack,
  Chip,
  Button,
  Divider,
} from '@mui/material';

// Импорт иконок MUI для визуализации информации
import {
  LocationOn,
  WorkOutline,
  AttachMoney,
  Business,
  Edit,
  People,
} from '@mui/icons-material';

// Импорт кастомных хуков для получения данных о вакансии
import { useJob } from '../../hooks/useJobs';

// Импорт MUI компонентов для анимации переходов и состояний загрузки
import { PageTransition } from '@components/mui/PageTransition';
import { LoadingState } from '@components/mui/LoadingState';
import { ErrorState } from '@components/mui/ErrorState';

export function VacancyDetailPage() {
  // Получаем ID вакансии из параметров URL
  const { id } = useParams<{ id: string }>();

  // Хук для навигации между страницами
  const navigate = useNavigate();

  // Загружаем данные о вакансии
  const { data: vacancy, isLoading, error } = useJob(id || '');

  // Отображаем состояние загрузки
  if (isLoading) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <LoadingState message="Loading vacancy details..." />
        </Container>
      </PageTransition>
    );
  }

  // Отображаем состояние ошибки
  if (error || !vacancy) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <ErrorState
            title="Vacancy Not Found"
            message="The vacancy you're looking for doesn't exist or you don't have permission to view it."
            onRetry={() => navigate('/recruiter/vacancies')}
          />
        </Container>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Paper sx={{ p: { xs: 3, md: 5 } }}>
          <Stack spacing={4}>
          {/* Заголовок вакансии с метаданными */}
          <Box>
            <Typography variant="h3" fontWeight={700} gutterBottom>
              {vacancy.title}
            </Typography>
            <Stack direction="row" spacing={2} flexWrap="wrap" color="text.secondary">
              {vacancy.industry && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <Business sx={{ fontSize: 18 }} />
                  <Typography>{vacancy.industry}</Typography>
                </Stack>
              )}
              {vacancy.location && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <LocationOn sx={{ fontSize: 18 }} />
                  <Typography>{vacancy.location}</Typography>
                </Stack>
              )}
              <Stack direction="row" spacing={1} alignItems="center">
                <WorkOutline sx={{ fontSize: 18 }} />
                <Typography>
                  {vacancy.work_format && `${vacancy.work_format}`}
                  {vacancy.min_experience_months > 0 && ` • ${Math.floor(vacancy.min_experience_months / 12)}+ years`}
                </Typography>
              </Stack>
            </Stack>
          </Box>

          <Divider />

          {/* Информация о зарплате */}
          {vacancy.salary_min && (
            <Stack direction="row" spacing={1} alignItems="center" color="success.main">
              <AttachMoney sx={{ fontSize: 20 }} />
              <Typography variant="h6" fontWeight={600} color="success.main">
                {vacancy.salary_min.toLocaleString()}
                {vacancy.salary_max && ` - ${vacancy.salary_max.toLocaleString()}`}
              </Typography>
            </Stack>
          )}

          {/* Требуемые навыки */}
          <Box>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Required Skills
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
              {vacancy.required_skills.map((skill) => (
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

          {/* Описание вакансии */}
          <Box>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Description
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              sx={{
                whiteSpace: 'pre-wrap',
                lineHeight: 1.8,
              }}
            >
              {vacancy.description}
            </Typography>
          </Box>

          {/* Кнопки действий */}
          <Stack direction="row" spacing={2} sx={{ pt: 2 }}>
            <Button
              variant="contained"
              size="large"
              startIcon={<People />}
              onClick={() => navigate('/recruiter/candidates')}
              sx={{ flexGrow: 1 }}
            >
              View Candidates
            </Button>
            <Button
              variant="outlined"
              size="large"
              startIcon={<Edit />}
              onClick={() => navigate(`/recruiter/vacancies/${vacancy.id}/edit`)}
            >
              Edit Vacancy
            </Button>
          </Stack>
        </Stack>
      </Paper>
      </Container>
    </PageTransition>
  );
}
