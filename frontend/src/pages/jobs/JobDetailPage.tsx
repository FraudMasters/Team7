// Импорт хука для получения параметров маршрута
import { useParams } from 'react-router-dom';
// Импорт компонентов Material UI
import {
  Box,
  Container,
  Typography,
  Paper,
  Stack,
  Chip,
  Button,
  Divider,
  CircularProgress,
  Grid,
} from '@mui/material';
// Импорт иконок Material UI
import {
  LocationOn,
  WorkOutline,
  AttachMoney,
  Business,
} from '@mui/icons-material';
// Импорт хука для получения данных о вакансии
import { useJob } from '../../hooks/useJobs';

/**
 * Компонент страницы детализации вакансии
 * Отображает полную информацию о вакансии с возможностью подачи заявки
 */
export function JobDetailPage() {
  // Получение ID вакансии из параметров маршрута
  const { id } = useParams<{ id: string }>();
  // Получение данных о вакансии, состояния загрузки и ошибок
  const { data: job, isLoading, error } = useJob(id || '');

  // Отображение индикатора загрузки
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 12 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Отображение состояния ошибки или отсутствия вакансии
  if (error || !job) {
    return (
      <Box sx={{ textAlign: 'center', py: 12 }}>
        <Typography variant="h6">Job not found</Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper
        sx={{
          p: { xs: 3, md: 5 },
          animation: 'fadeInUp 0.5s ease-out both',
          '@keyframes fadeInUp': {
            '0%': {
              opacity: 0,
              transform: 'translateY(20px)',
            },
            '100%': {
              opacity: 1,
              transform: 'translateY(0)',
            },
          },
        }}
      >
        <Stack spacing={4}>
          {/* Заголовок вакансии */}
          <Box>
            <Typography variant="h3" fontWeight={700} gutterBottom>
              {job.title}
            </Typography>
            {/* Метаданные вакансии: индустрия, локация, формат работы, опыт */}
            <Stack direction="row" spacing={2} flexWrap="wrap" color="text.secondary">
              {job.industry && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <Business sx={{ fontSize: 18 }} />
                  <Typography>{job.industry}</Typography>
                </Stack>
              )}
              {job.location && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <LocationOn sx={{ fontSize: 18 }} />
                  <Typography>{job.location}</Typography>
                </Stack>
              )}
              <Stack direction="row" spacing={1} alignItems="center">
                <WorkOutline sx={{ fontSize: 18 }} />
                <Typography>
                  {job.work_format && `${job.work_format}`}
                  {job.min_experience_months > 0 && ` • ${Math.floor(job.min_experience_months / 12)}+ years`}
                </Typography>
              </Stack>
            </Stack>
          </Box>

          <Divider />

          {/* Заработная плата */}
          {job.salary_min && (
            <Stack direction="row" spacing={1} alignItems="center" color="success.main">
              <AttachMoney sx={{ fontSize: 20 }} />
              <Typography variant="h6" fontWeight={600} color="success.main">
                {job.salary_min.toLocaleString()}
                {job.salary_max && ` - ${job.salary_max.toLocaleString()}`}
              </Typography>
            </Stack>
          )}

          {/* Требуемые навыки */}
          <Box>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Required Skills
            </Typography>
            {/* Список навыков в виде чипов */}
            <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
              {job.required_skills.map((skill) => (
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
              {job.description}
            </Typography>
          </Box>

          {/* Кнопки действий */}
          <Stack direction="row" spacing={2} sx={{ pt: 2 }}>
            {/* Кнопка подачи заявки на вакансию */}
            <Button
              variant="contained"
              size="large"
              href={`/jobs/${job.id}/apply`}
              sx={{ flexGrow: 1 }}
            >
              Apply Now
            </Button>
            {/* Кнопка сохранения вакансии */}
            <Button
              variant="outlined"
              size="large"
              sx={{ minWidth: 120 }}
            >
              Save
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Container>
  );
}
