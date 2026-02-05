// Импорт хуков для управления состоянием
import { useState } from 'react';
// Импорт компонентов MUI для UI
import {
  Container,
  Typography,
  TextField,
  Grid,
  Paper,
  Box,
  Button,
} from '@mui/material';
// Импорт иконок MUI
import { Search as SearchIcon, Bookmark as BookmarkIcon } from '@mui/icons-material';
// Импорт кастомных хуков для работы с сохранёнными вакансиями
import { useSavedJobs, useRemoveSavedJob } from '../../hooks/useSavedJobs';
// Импорт карточки вакансии
import { JobCard } from '../../components/jobs/JobCard';
// Импорт клиента запросов для инвалидации кэша
import { useQueryClient } from '@tanstack/react-query';
// Импорт MUI компонентов
import { PageTransition } from '@components/mui/PageTransition';
import { LoadingState } from '@components/mui/LoadingState';
import { ErrorState } from '@components/mui/ErrorState';

/**
 * Страница сохранённых вакансий
 * Отображает список вакансий, добавленных в закладки пользователем
 */
export function SavedJobsPage() {
  // Состояние для поиска по сохранённым вакансиям
  const [searchTerm, setSearchTerm] = useState('');
  // Клиент для управления кэшем React Query
  const queryClient = useQueryClient();
  // Получение сохранённых вакансий с сервера
  const { data, isLoading, error } = useSavedJobs();
  // Мутация для удаления вакансии из сохранённых
  const removeSavedJob = useRemoveSavedJob();

  // Фильтрация вакансий по поисковому запросу
  const filteredJobs = data?.saved_jobs.filter((job) => {
    return (
      searchTerm === '' ||
      job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.description.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }) ?? [];

  /**
   * Обработчик удаления вакансии из сохранённых
   * @param savedJobId - ID сохранённой вакансии
   */
  const handleRemoveSavedJob = (savedJobId: string) => {
    removeSavedJob.mutate(savedJobId, {
      onSuccess: () => {
        // Инвалидируем кэш после успешного удаления
        queryClient.invalidateQueries({ queryKey: ['saved-jobs'] });
      },
    });
  };

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
          }}
          sx={{ flexGrow: 1, minWidth: 200 }}
        />
        {/* Счётчик сохранённых вакансий */}
        <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
          <BookmarkIcon color="primary" />
          <Typography variant="body2" color="text.secondary">
            {data?.total || 0} saved
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
          onRetry={() => queryClient.invalidateQueries({ queryKey: ['saved-jobs'] })}
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
            <Button variant="contained" component="a" href="/jobs">
              Browse Jobs
            </Button>
          )}
        </Box>
      ) : (
        <Grid container spacing={2}>
          {/* Сетка с карточками сохранённых вакансий */}
          {filteredJobs.map((job) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={job.id}>
              <JobCard
                job={job}
                saved={true}
                onSave={() => handleRemoveSavedJob(job.id)}
              />
            </Grid>
          ))}
        </Grid>
      )}
      </Container>
    </PageTransition>
  );
}
