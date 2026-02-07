/**
 * Страница поиска кандидатов
 *
 * Расширенный поиск кандидатов с фильтрацией, AI-ранжированием и возможностью сохранения.
 * Использует MUI компоненты для отображения формы поиска, фильтров и результатов.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Stack,
  Grid2,
  Paper,
  TextField,
  Slider,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  Save as SaveIcon,
  Close as CloseIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { candidateSearchClient } from '../../api/search';
import { savedSearchesClient } from '../../api/savedSearches';
import { useBreakpoints } from '../../hooks';
import { useKeyboardNavigation } from '../../hooks/useKeyboardNavigation';

// Интерфейс кандидата
interface Candidate {
  id: string;
  filename: string;
  name?: string;
  email?: string;
  match_percentage: number;
  ai_ranking_score?: number;
  skills: string[];
  experience_years?: number;
  location?: string;
}

export function SearchPage() {
  // Хуки для навигации и управления кэшем
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isMobile, isTablet } = useBreakpoints();

  // Состояния для поиска и фильтров
  const [searchQuery, setSearchQuery] = useState('');
  const [skillsFilter, setSkillsFilter] = useState('');
  const [minMatchScore, setMinMatchScore] = useState([0]);
  const [aiRankingEnabled, setAiRankingEnabled] = useState(true);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [saveSearchName, setSaveSearchName] = useState('');

  // Горячие клавиши для быстрого доступа к функциям поиска
  useKeyboardNavigation([
    { key: 'Ctrl+K', action: () => document.getElementById('search-input')?.focus(), priority: 10 },
    { key: 'Ctrl+S', action: () => setSaveDialogOpen(true), priority: 10 },
    { key: 'Escape', action: () => setSaveDialogOpen(false), priority: 5 },
  ]);

  // Загружаем результаты поиска
  const {
    data: searchResults,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['candidate-search', searchQuery, skillsFilter, minMatchScore, aiRankingEnabled],
    queryFn: async () => {
      const filters: Record<string, unknown> = {};
      if (minMatchScore[0] > 0) filters.min_match_score = minMatchScore[0];
      if (skillsFilter) filters.skills = skillsFilter.split(',').map(s => s.trim());

      return await candidateSearchClient.searchCandidates({
        query: searchQuery || undefined,
        filters: Object.keys(filters).length > 0 ? filters : undefined,
        limit: 50,
        sort_by: aiRankingEnabled ? 'ai_ranking' : 'relevance',
      });
    },
    enabled: searchQuery.length > 0 || skillsFilter.length > 0 || minMatchScore[0] > 0,
  });

  // Мутация для сохраненного поиска
  const saveSearchMutation = useMutation({
    mutationFn: async () => {
      await savedSearchesClient.createSavedSearch({
        name: saveSearchName,
        query: searchQuery,
        filters: {
          skills: skillsFilter,
          min_match_score: minMatchScore[0],
        },
      });
    },
    onSuccess: () => {
      setSaveDialogOpen(false);
      setSaveSearchName('');
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] });
    },
  });

  // Вычисляем статистику по результатам
  const candidates = searchResults?.candidates || [];
  const highMatchCount = candidates.filter(c => c.match_percentage >= 80).length;
  const mediumMatchCount = candidates.filter(c => c.match_percentage >= 60 && c.match_percentage < 80).length;
  const avgMatchScore = candidates.length > 0
    ? Math.round(candidates.reduce((sum, c) => sum + c.match_percentage, 0) / candidates.length)
    : 0;

  // Обработчик поиска
  const handleSearch = () => {
    refetch();
  };

  // Обработчик сохранения поиска
  const handleSaveSearch = () => {
    if (saveSearchName.trim()) {
      saveSearchMutation.mutate();
    }
  };

  // Переход к детали кандидата
  const handleCandidateClick = (candidateId: string) => {
    navigate(`/recruiter/candidates/${candidateId}`);
  };

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      {/* Заголовок страницы */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant={isMobile ? 'h5' : 'h4'} fontWeight={700}>
            Candidate Search
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Find the perfect candidate with advanced filters
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<SaveIcon />}
          onClick={() => setSaveDialogOpen(true)}
          disabled={!searchQuery && !skillsFilter && minMatchScore[0] === 0}
        >
          {isMobile ? 'Save' : 'Save Search'}
        </Button>
      </Stack>

      {/* Форма поиска и фильтры */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid2 container spacing={3}>
          {/* Поле поиска */}
          <Grid2 size={{ xs: 12, md: 6 }}>
            <TextField
              id="search-input"
              fullWidth
              placeholder="Search by name, skills, or keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              InputProps={{
                endAdornment: searchQuery && (
                  <IconButton onClick={() => setSearchQuery('')} size="small">
                    <CloseIcon />
                  </IconButton>
                ),
              }}
              slotProps={{
                input: {
                  'aria-label': 'Search candidates',
                },
              }}
            />
          </Grid2>

          {/* Фильтр по навыкам */}
          <Grid2 size={{ xs: 12, md: 4 }}>
            <TextField
              fullWidth
              placeholder="Skills (comma-separated)"
              value={skillsFilter}
              onChange={(e) => setSkillsFilter(e.target.value)}
              helperText="e.g., Python, Django, PostgreSQL"
              slotProps={{
                input: {
                  'aria-label': 'Filter by skills',
                },
              }}
            />
          </Grid2>

          {/* Кнопка поиска */}
          <Grid2 size={{ xs: 12, md: 2 }}>
            <Button
              fullWidth
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={handleSearch}
              sx={{ height: '56px' }}
            >
              Search
            </Button>
          </Grid2>

          {/* Слайдер минимального соответствия */}
          <Grid2 size={{ xs: 12, md: 6 }}>
            <Typography variant="body2" gutterBottom>
              Minimum Match Score: {minMatchScore[0]}%
            </Typography>
            <Slider
              value={minMatchScore}
              onChange={(_, value) => setMinMatchScore(value as number[])}
              min={0}
              max={100}
              marks={[
                { value: 0, label: '0%' },
                { value: 50, label: '50%' },
                { value: 80, label: '80%' },
                { value: 100, label: '100%' },
              ]}
              valueLabelDisplay="auto"
              aria-label="Minimum match score"
            />
          </Grid2>

          {/* Переключатель AI-ранжирования */}
          <Grid2 size={{ xs: 12, md: 6 }}>
            <Stack direction="row" alignItems="center" justifyContent="flex-end">
              <Typography variant="body2" sx={{ mr: 2 }}>
                AI Ranking
              </Typography>
              <Button
                variant={aiRankingEnabled ? 'contained' : 'outlined'}
                startIcon={<TrendingUpIcon />}
                onClick={() => setAiRankingEnabled(!aiRankingEnabled)}
              >
                {aiRankingEnabled ? 'Enabled' : 'Disabled'}
              </Button>
            </Stack>
          </Grid2>
        </Grid2>
      </Paper>

      {/* Сообщение об ошибке */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {(error as { detail?: string }).detail || 'Search failed. Please try again.'}
        </Alert>
      )}

      {/* Сводка результатов */}
      {candidates.length > 0 && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.default' }}>
          <Grid2 container spacing={2}>
            <Grid2 size={{ xs: 6, md: 3 }}>
              <Typography variant="h6">{candidates.length}</Typography>
              <Typography variant="body2" color="text.secondary">Candidates</Typography>
            </Grid2>
            <Grid2 size={{ xs: 6, md: 3 }}>
              <Typography variant="h6" color="success.main">{highMatchCount}</Typography>
              <Typography variant="body2" color="text.secondary">High Match</Typography>
            </Grid2>
            <Grid2 size={{ xs: 6, md: 3 }}>
              <Typography variant="h6" color="warning.main">{mediumMatchCount}</Typography>
              <Typography variant="body2" color="text.secondary">Medium Match</Typography>
            </Grid2>
            <Grid2 size={{ xs: 6, md: 3 }}>
              <Typography variant="h6">{avgMatchScore}%</Typography>
              <Typography variant="body2" color="text.secondary">Avg Score</Typography>
            </Grid2>
          </Grid2>
        </Paper>
      )}

      {/* Сетка кандидатов */}
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : candidates.length > 0 ? (
        <Grid2 container spacing={3}>
          {candidates.map((candidate) => (
            <Grid2 key={candidate.id} size={{ xs: 12, sm: 6, lg: 4 }}>
              <Paper
                sx={{
                  p: 3,
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
                onClick={() => handleCandidateClick(candidate.id)}
                role="button"
                tabIndex={0}
                aria-label={`View ${candidate.name || candidate.filename}`}
                onKeyPress={(e) => e.key === 'Enter' && handleCandidateClick(candidate.id)}
              >
                {/* Бейдж соответствия */}
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
                  <Chip
                    label={`${candidate.match_percentage}%`}
                    color={candidate.match_percentage >= 80 ? 'success' : candidate.match_percentage >= 60 ? 'warning' : 'default'}
                    size="small"
                  />
                  {aiRankingEnabled && candidate.ai_ranking_score && (
                    <Chip
                      icon={<TrendingUpIcon fontSize="small" />}
                      label={`AI: ${candidate.ai_ranking_score}`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  )}
                </Stack>

                {/* Информация о кандидате */}
                <Typography variant="h6" noWrap sx={{ mb: 1 }}>
                  {candidate.name || candidate.filename}
                </Typography>
                {candidate.email && (
                  <Typography variant="body2" color="text.secondary" noWrap sx={{ mb: 2 }}>
                    {candidate.email}
                  </Typography>
                )}

                {/* Навыки */}
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 2 }}>
                  {candidate.skills.slice(0, 5).map((skill) => (
                    <Chip key={skill} label={skill} size="small" variant="outlined" />
                  ))}
                  {candidate.skills.length > 5 && (
                    <Chip label={`+${candidate.skills.length - 5}`} size="small" />
                  )}
                </Box>

                {/* Бейдж TOP рекомендации */}
                {candidate.match_percentage >= 90 && (
                  <Chip
                    label="TOP"
                    color="primary"
                    size="small"
                    sx={{ mt: 2 }}
                  />
                )}
              </Paper>
            </Grid2>
          ))}
        </Grid2>
      ) : searchQuery || skillsFilter || minMatchScore[0] > 0 ? (
        <Paper sx={{ p: 8, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No candidates found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Try adjusting your search criteria
          </Typography>
        </Paper>
      ) : (
        <Paper sx={{ p: 8, textAlign: 'center' }}>
          <SearchIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Start your search
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Enter keywords or select filters to find candidates
          </Typography>
        </Paper>
      )}

      {/* Диалог сохранения поиска */}
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Save Search</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Search Name"
            value={saveSearchName}
            onChange={(e) => setSaveSearchName(e.target.value)}
            sx={{ mt: 2 }}
            slotProps={{
              input: {
                'aria-label': 'Search name',
              },
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSaveSearch}
            variant="contained"
            disabled={!saveSearchName.trim() || saveSearchMutation.isPending}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default SearchPage;
