// Импорт хуков для управления состоянием
import { useState } from 'react';
// Импорт компонентов MUI для UI
import {
  Container,       // Контейнер для ограничения ширины содержимого
  Typography,      // Компонент для текста с различными стилями
  Box,             // Универсальный контейнер для верстки
  Grid,            // Сетка для адаптивной верстки
  Paper,           // Контейнер с эффектом elevated (карточка)
  Chip,            // Метки/теги
  Button,          // Кнопки
  CircularProgress, // Индикатор загрузки
} from '@mui/material';
// Импорт иконок из MUI
import {
  Recommend as RecommendIcon,
  AutoAwesome as AIIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
// Импорт хуков для работы с данными
import { useQuery } from '@tanstack/react-query';
// Импорт API клиента
import { apiClient } from '../../api/client';
// Импорт компонента карточки вакансии
import { JobCard } from '../../components/jobs/JobCard';
// Импорт MUI компонентов
import { PageTransition } from '@components/mui/PageTransition';
import { LoadingState } from '@components/mui/LoadingState';
import { ErrorState } from '@components/mui/ErrorState';

// Интерфейс описывающий структуру вакансии
interface Job {
  id: string;
  title: string;
  description: string;
  company: string;
  location: string;
  work_format: string;
  salary_min?: number;
  salary_max?: number;
  skills: string[];
  match_score?: number; // Оценка соответствия профилю
}

// Интерфейс ответа API с рекомендациями
interface RecommendationsResponse {
  jobs: Job[];
  total: number;
  insights: {
    top_skills: string[];          // Топ навыков пользователя
    recommended_industries: string[]; // Рекомендуемые индустрии
  };
}

/**
 * Страница рекомендуемых вакансий
 * Отображает AI-рекомендации вакансий на основе профиля пользователя
 */
export function RecommendedJobsPage() {
  // Состояние фильтрации вакансий
  const [filter, setFilter] = useState<'all' | 'high-match'>('all');

  // Получение рекомендаций с сервера
  const { data, isLoading, error } = useQuery({
    queryKey: ['recommended-jobs', filter],
    queryFn: async () => {
      const response = await apiClient.getAxiosInstance().get<RecommendationsResponse>(
        `/api/v1/jobs/recommendations?min_match=${filter === 'high-match' ? 70 : 0}`
      );
      return response.data;
    },
  });

  // Фильтрация вакансий по выбранному критерию
  const filteredJobs = data?.jobs.filter(job =>
    filter === 'all' || (job.match_score && job.match_score >= 70)
  ) ?? [];

  return (
    <PageTransition>
      <Container maxWidth="xl" sx={{ py: 2 }}>
        {/* Заголовок страницы */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <RecommendIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" fontWeight={700}>
                Recommended Jobs
              </Typography>
              <Typography variant="body1" color="text.secondary">
                AI-powered recommendations based on your profile
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Секция AI-инсайтов */}
        {data?.insights && (
          <Paper sx={{ p: 3, mb: 4, bgcolor: 'primary.50', border: '1px solid', borderColor: 'primary.200' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <AIIcon color="primary" />
              <Typography variant="h6" fontWeight={600}>
                AI Insights
              </Typography>
            </Box>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Your Top Skills
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {data.insights.top_skills.map((skill) => (
                    <Chip key={skill} label={skill} size="small" variant="outlined" />
                  ))}
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Recommended Industries
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {data.insights.recommended_industries.map((industry) => (
                    <Chip key={industry} label={industry} size="small" color="primary" variant="filled" />
                  ))}
                </Box>
              </Grid>
            </Grid>
          </Paper>
        )}

        {/* Панель фильтров */}
        <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
          <Button
            variant={filter === 'all' ? 'contained' : 'outlined'}
            onClick={() => setFilter('all')}
            startIcon={<RecommendIcon />}
          >
            All Recommendations
          </Button>
          <Button
            variant={filter === 'high-match' ? 'contained' : 'outlined'}
            onClick={() => setFilter('high-match')}
            startIcon={<TrendingUpIcon />}
          >
            High Match (70%+)
          </Button>
        </Box>

        {/* Состояния загрузки, ошибки и список вакансий */}
        {isLoading ? (
          <LoadingState message="Loading recommendations..." />
        ) : error ? (
          <ErrorState
            title="Error"
            message="Failed to load recommendations. Please try again later."
            onRetry={() => window.location.reload()}
          />
        ) : filteredJobs.length === 0 ? (
          // Состояние: нет рекомендаций
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <RecommendIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No recommendations yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Complete your profile and upload your resume to get personalized job recommendations
            </Typography>
            <Button variant="contained" component="a" href="/jobs/upload">
              Upload Resume
            </Button>
          </Box>
        ) : (
          // Сетка с карточками вакансий
          <Grid container spacing={2}>
            {filteredJobs.map((job) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={job.id}>
                <Box sx={{ position: 'relative' }}>
                  {/* Бейдж соответствия вакансии */}
                  {job.match_score && (
                    <Chip
                      label={`${job.match_score}% match`}
                      size="small"
                      color="primary"
                      sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        zIndex: 1,
                        fontWeight: 600,
                      }}
                    />
                  )}
                  <JobCard job={job} />
                </Box>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>
    </PageTransition>
  );
}
