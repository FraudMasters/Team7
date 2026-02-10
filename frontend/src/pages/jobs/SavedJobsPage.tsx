// Импорт хуков для управления состоянием
import { useState, useMemo, useCallback } from 'react';
// Импорт компонентов MUI для UI
import {
  Container,
  Typography,
  TextField,
  Grid,
  Paper,
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  IconButton,
  Chip,
} from '@mui/material';
// Импорт иконок MUI
import { Search as SearchIcon, Bookmark as BookmarkIcon, Close as CloseIcon } from '@mui/icons-material';
// Импорт хука для работы с сохранёнными вакансиями
import { useSavedJobs, useUnsaveJob } from '../../hooks/useSavedJobs';
// Импорт хука авторизации
import { useAuth } from '../../hooks/useAuth';
// Импорт клиента запросов для инвалидации кэша
import { useQueryClient } from '@tanstack/react-query';
// Импорт MUI компонентов
import { PageTransition } from '@components/mui/PageTransition';
import { LoadingState } from '@components/mui/LoadingState';
import { ErrorState } from '@components/mui/ErrorState';
// React Router для навигации
import { Link } from 'react-router-dom';

/**
 * Страница сохранённых вакансий
 * Отображает список вакансий, добавленных в закладки пользователем
 */
export function SavedJobsPage() {
  // Состояние для поиска по сохранённым вакансиям
  const [searchTerm, setSearchTerm] = useState('');
  // Получаем пользователя из auth контекста
  const { user } = useAuth();
  // Клиент для управления кэшем React Query
  const queryClient = useQueryClient();
  // Получение сохранённых вакансий с сервера
  const { data, isLoading, error } = useSavedJobs(user?.id ?? '');
  // Мутация для удаления вакансии из сохранённых
  const unsaveJob = useUnsaveJob();

  // Фильтрация вакансий по поисковому запросу
  const filteredJobs = useMemo(() => {
    if (!data?.saved_jobs) return [];
    return data.saved_jobs.filter((job) => {
      const title = job.vacancy_title ?? '';
      const description = job.vacancy_description ?? '';
      const searchLower = searchTerm.toLowerCase();
      return (
        searchTerm === '' ||
        title.toLowerCase().includes(searchLower) ||
        description.toLowerCase().includes(searchLower)
      );
    });
  }, [data, searchTerm]);

  /**
   * Обработчик удаления вакансии из сохранённых
   * @param savedJobId - ID сохранённой вакансии
   * @param vacancyId - ID вакансии (для альтернативного удаления)
   */
  const handleRemoveSavedJob = useCallback((savedJobId: string, vacancyId: string) => {
    unsaveJob.mutate(
      { savedJobId, vacancyId, userId: user?.id ?? '' },
      {
        onSuccess: () => {
          // Инвалидируем кэш после успешного удаления
          queryClient.invalidateQueries({ queryKey: ['saved-jobs', user?.id] });
        },
      }
    );
  }, [unsaveJob, queryClient, user?.id]);

  return (
    <PageTransition>
      <Container maxWidth="xl" sx={{ py: 2 }}>
        {/* Заголовок страницы */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Saved Jobs
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Your bookmarked job opportunities
          </Typography>
        </Box>

        {/* Панель поиска */}
        <Paper
          sx={{
            p: 2,
            mb: 4,
            display: 'flex',
            gap: 2,
            alignItems: 'center',
          }}
        >
          <TextField
            placeholder="Search saved jobs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              endAdornment: searchTerm && (
                <IconButton
                  size="small"
                  onClick={() => setSearchTerm('')}
                  sx={{ mr: -0.5 }}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              ),
            }}
            sx={{ flexGrow: 1, minWidth: 200 }}
          />
          {/* Счётчик сохранённых вакансий */}
          <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
            <BookmarkIcon color="primary" />
            <Typography variant="body2" color="text.secondary">
              {data?.total ?? 0} saved
            </Typography>
          </Box>
        </Paper>

        {/* Состояния загрузки, ошибки и пустого списка */}
        {isLoading ? (
          <LoadingState message="Loading saved jobs..." />
        ) : error ? (
          <ErrorState
            title="Error"
            message="Failed to load saved jobs. Please try again later."
            onRetry={() => queryClient.invalidateQueries({ queryKey: ['saved-jobs', user?.id] })}
          />
        ) : filteredJobs.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            {/* Состояние: нет сохранённых вакансий */}
            <BookmarkIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {searchTerm ? 'No saved jobs match your search' : 'No saved jobs yet'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {searchTerm
                ? 'Try adjusting your search terms'
                : 'Start bookmarking jobs to see them here'}
            </Typography>
            {!searchTerm && (
              <Button variant="contained" component={Link} to="/jobs">
                Browse Jobs
              </Button>
            )}
          </Box>
        ) : (
          <Grid container spacing={2}>
            {/* Сетка с карточками сохранённых вакансий */}
            {filteredJobs.map((job) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={job.id}>
                <Card
                  component={Link}
                  to={`/jobs/${job.vacancy_id}`}
                  sx={{
                    textDecoration: 'none',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'transform 0.2s ease-out, box-shadow 0.2s ease-out',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    },
                  }}
                >
                  <CardContent sx={{ flexGrow: 1, p: 3 }}>
                    {/* Заголовок с названием и закладкой */}
                    <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="h6" fontWeight={600} color="text.primary" gutterBottom>
                          {job.vacancy_title || 'Untitled Position'}
                        </Typography>
                      </Box>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.preventDefault();
                          handleRemoveSavedJob(job.id, job.vacancy_id);
                        }}
                        sx={{ ml: 1 }}
                        aria-label="Remove from saved"
                      >
                        <Bookmark color="primary" />
                      </IconButton>
                    </Stack>

                    {/* Описание, обрезанное до 2 строк */}
                    {job.vacancy_description && (
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          mb: 2,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }}
                      >
                        {job.vacancy_description}
                      </Typography>
                    )}

                    {/* Дата сохранения */}
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Chip
                        label={`Saved ${new Date(job.created_at).toLocaleDateString()}`}
                        size="small"
                        variant="outlined"
                        sx={{
                          borderRadius: 1,
                          fontSize: '0.75rem',
                          height: 24,
                        }}
                      />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>
    </PageTransition>
  );
}
