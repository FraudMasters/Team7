import { useState } from 'react';
// MUI компоненты для UI
import {
  Container,
  Typography,
  TextField,
  Grid,
  Paper,
  Box,
  Stack,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
} from '@mui/material';
// Иконки MUI
import { Search as SearchIcon, WorkOutline as WorkIcon } from '@mui/icons-material';
// Хуки для получения данных
import { useApplications } from '../../hooks/useApplications';
// Компоненты
import { ApplicationCard } from '../../components/jobs/ApplicationCard';
import { PageTransition } from '@components/mui/PageTransition';
import { LoadingState } from '@components/mui/LoadingState';
import { ErrorState } from '@components/mui/ErrorState';

export function MyApplicationsPage() {
  // Состояние для поискового запроса
  const [searchTerm, setSearchTerm] = useState('');
  // Состояние для фильтрации по статусу
  const [filters, setFilters] = useState<{
    status?: string;
  }>({});

  // Получаем данные о заявках
  const { data, isLoading, error } = useApplications();

  // Фильтрация заявок по поиску и статусу
  const filteredApplications = data?.applications.filter((application) => {
    // Проверка соответствия поисковому запросу
    const matchesSearch =
      searchTerm === '' ||
      application.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      application.description?.toLowerCase().includes(searchTerm.toLowerCase());

    // Проверка соответствия статусу
    const matchesStatus = !filters.status || application.status === filters.status;

    return matchesSearch && matchesStatus;
  }) ?? [];

  // Функция для подсчета заявок по статусу
  const getStatusCount = (status: string) => {
    return data?.applications.filter((app) => app.status === status).length ?? 0;
  };

  return (
    <PageTransition>
      <Container maxWidth="xl" sx={{ py: 2 }}>
        {/* Заголовок страницы */}
        <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          My Applications
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Track your job application progress
        </Typography>
      </Box>

      {/* Поиск и фильтры */}
      <Paper
        sx={{
          p: 2,
          mb: 4,
          display: 'flex',
          gap: 2,
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <TextField
          placeholder="Search applications..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
          sx={{ flexGrow: 1, minWidth: 200 }}
        />
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={filters.status || ''}
            label="Status"
            onChange={(e) => setFilters({ ...filters, status: e.target.value || undefined })}
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="under_review">Under Review</MenuItem>
            <MenuItem value="interview">Interview</MenuItem>
            <MenuItem value="offered">Offered</MenuItem>
            <MenuItem value="rejected">Rejected</MenuItem>
          </Select>
        </FormControl>
        {/* Отображение общего количества заявок */}
        <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
          <WorkIcon color="primary" />
          <Typography variant="body2" color="text.secondary">
            {data?.total || 0} total
          </Typography>
        </Box>
      </Paper>

      {/* Сводка по статусам */}
      {data && data.applications.length > 0 && (
        <Paper sx={{ p: 2, mb: 4 }}>
          <Stack direction="row" spacing={2} flexWrap="wrap">
            <Typography variant="body2" color="text.secondary">
              Summary:
            </Typography>
            <Typography variant="body2" sx={{ minWidth: 80 }}>
              Pending: {getStatusCount('pending')}
            </Typography>
            <Typography variant="body2" sx={{ minWidth: 100 }}>
              Under Review: {getStatusCount('under_review')}
            </Typography>
            <Typography variant="body2" sx={{ minWidth: 70 }}>
              Interview: {getStatusCount('interview')}
            </Typography>
            <Typography variant="body2" sx={{ minWidth: 60 }}>
              Offered: {getStatusCount('offered')}
            </Typography>
            <Typography variant="body2" sx={{ minWidth: 70 }}>
              Rejected: {getStatusCount('rejected')}
            </Typography>
          </Stack>
        </Paper>
      )}

      {/* Состояния загрузки, ошибки, пустого списка и сетка заявок */}
      {isLoading ? (
        <LoadingState message="Loading applications..." />
      ) : error ? (
        <ErrorState
          title="Error"
          message="Failed to load applications. Please try again later."
          onRetry={() => window.location.reload()}
        />
      ) : filteredApplications.length === 0 ? (
        // Состояние пустого списка
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <WorkIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {searchTerm || filters.status ? 'No applications match your search' : 'No applications yet'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {searchTerm || filters.status
              ? 'Try adjusting your search terms'
              : 'Start applying to jobs to track them here'}
          </Typography>
          {!searchTerm && !filters.status && (
            <Typography
              variant="body2"
              color="primary"
              sx={{ cursor: 'pointer', textDecoration: 'underline' }}
              component="a"
              href="/jobs"
            >
              Browse Jobs
            </Typography>
          )}
        </Box>
      ) : (
        // Сетка карточек заявок
        <Grid container spacing={2}>
          {filteredApplications.map((application) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={application.id}>
              <ApplicationCard application={application} />
            </Grid>
          ))}
        </Grid>
      )}
      </Container>
    </PageTransition>
  );
}
