import { Container, Box, Typography, Grid, Paper, CircularProgress, Alert } from '@mui/material';
import { Speed as SpeedIcon, People as PeopleIcon, Work as WorkIcon, TrendingUp as TrendingIcon } from '@mui/icons-material';
import { BentoCard } from '../../components/dashboard/BentoCard';
import { useRecruiterAnalytics, useCandidates, useRecruiterVacancies } from '../../hooks/useRecruiterData';

/**
 * Страница дашборда рекрутера
 *
 * Отображает ключевые метрики рекрутера: активные вакансии, количество кандидатов,
 * время найма и количество заявок. Использует MUI компоненты для отображения
 * карточек метрик в стиле Bento Grid.
 */
export function DashboardPage() {
  // Получаем аналитические данные рекрутера
  const { data: analytics, isLoading: analyticsLoading, isError: analyticsError } = useRecruiterAnalytics();

  // Получаем данные о кандидатах
  const { data: candidatesData, isLoading: candidatesLoading } = useCandidates();

  // Получаем данные о вакансиях
  const { data: vacanciesData, isLoading: vacanciesLoading } = useRecruiterVacancies();

  // Вычисляем количество кандидатов
  const candidateCount = candidatesData?.candidates?.length || 0;

  // Вычисляем количество вакансий
  const vacancyCount = vacanciesData?.vacancies?.length || 0;

  // Вычисляем среднее количество заявок на вакансию
  const applicationsPerJob = vacancyCount > 0 ? (candidateCount / vacancyCount).toFixed(1) : '--';

  // Проверяем состояние загрузки
  const isLoading = analyticsLoading || candidatesLoading || vacanciesLoading;

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Заголовок дашборда */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700}>
          Recruiter Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back! Here's what's happening today.
        </Typography>
      </Box>

      {/* Показываем ошибку если не удалось загрузить аналитику */}
      {analyticsError && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Unable to load analytics data. Displaying available metrics.
        </Alert>
      )}

      {/* Показываем индикатор загрузки */}
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Сетка метрик в стиле Bento Grid */}
          <Grid container spacing={2} sx={{ mb: 4 }}>
            {/* Карточка с количеством активных вакансий */}
            <Grid item xs={12} sm={6} lg={3}>
              <BentoCard
                title="Active Jobs"
                value={vacancyCount}
                subtitle="Open positions"
                icon={<WorkIcon sx={{ color: 'white' }} />}
                color="primary"
              />
            </Grid>

            {/* Карточка с общим количеством кандидатов */}
            <Grid item xs={12} sm={6} lg={3}>
              <BentoCard
                title="Total Candidates"
                value={candidateCount}
                subtitle="In pipeline"
                icon={<PeopleIcon sx={{ color: 'white' }} />}
                color="secondary"
              />
            </Grid>

            {/* Карточка со средним временем найма */}
            <Grid item xs={12} sm={6} lg={3}>
              <BentoCard
                title="Time to Hire"
                value={analytics?.time_to_hire?.average_days ? `${Math.round(analytics.time_to_hire.average_days)}d` : '--'}
                subtitle="Average days"
                icon={<SpeedIcon sx={{ color: 'white' }} />}
                color="success"
              />
            </Grid>

            {/* Карточка с количеством заявок на вакансию */}
            <Grid item xs={12} sm={6} lg={3}>
              <BentoCard
                title="Applications/Job"
                value={applicationsPerJob}
                subtitle="Current average"
                icon={<TrendingIcon sx={{ color: 'white' }} />}
                color="warning"
              />
            </Grid>
          </Grid>

          {/* Воронка найма (Pipeline Funnel) */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Pipeline Funnel
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Pipeline metrics will be displayed here...
                </Typography>
              </Box>
            </Paper>
          </Grid>
        </>
      )}
    </Container>
  );
}
