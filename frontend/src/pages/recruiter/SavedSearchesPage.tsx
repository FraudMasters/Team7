/**
 * Страница сохраненных поисковых запросов
 *
 * Управление сохраненными поисками кандидатов с опциями запуска,
 * редактирования и удаления. Использует MUI компоненты для отображения
 * карточек поисков и меню действий.
 */

// Импорт хуков React
import { useState } from 'react';

// Импорт хука React Router для навигации
import { useNavigate } from 'react-router-dom';

// Импорт компонентов MUI
import {
  Box,
  Container,
  Typography,
  Button,
  Stack,
  Grid2,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Alert,
  CircularProgress,
  Menu,
  MenuItem,
} from '@mui/material';

// Импорт иконок MUI
import {
  Add as AddIcon,
  PlayArrow as RunIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';

// Импорт хуков React Query для управления данными
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Импорт API клиента для сохраненных поисков
import { savedSearchesClient } from '../../api/savedSearches';

// Импорт хука для определения размеров экрана
import { useBreakpoints } from '../../hooks';

// Интерфейс сохраненного поиска
interface SavedSearch {
  id: string;
  name: string;
  query: string;
  filters: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export function SavedSearchesPage() {
  // Хук для навигации между страницами
  const navigate = useNavigate();

  // Хук для управления кэшем React Query
  const queryClient = useQueryClient();

  // Определяем, мобильное ли устройство
  const { isMobile } = useBreakpoints();

  // Состояния диалогов и меню
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedSearch, setSelectedSearch] = useState<SavedSearch | null>(null);
  const [editName, setEditName] = useState('');
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);

  // Загружаем сохраненные поиски
  const {
    data: savedSearchesData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['saved-searches'],
    queryFn: async () => {
      return await savedSearchesClient.listSavedSearches(0, 100);
    },
  });

  // Мутация для обновления названия поиска
  const updateMutation = useMutation({
    mutationFn: async ({ id, name }: { id: string; name: string }) => {
      return await savedSearchesClient.updateSavedSearch(id, { name });
    },
    onSuccess: () => {
      setEditDialogOpen(false);
      setSelectedSearch(null);
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] });
    },
  });

  // Мутация для удаления поиска
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await savedSearchesClient.deleteSavedSearch(id);
    },
    onSuccess: () => {
      setDeleteDialogOpen(false);
      setSelectedSearch(null);
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] });
    },
  });

  // Получаем список поисков
  const savedSearches = savedSearchesData?.saved_searches || [];
  const total = savedSearchesData?.total || 0;

  // Обработчик открытия меню
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, search: SavedSearch) => {
    setMenuAnchor(event.currentTarget);
    setSelectedSearch(search);
  };

  // Обработчик закрытия меню
  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedSearch(null);
  };

  // Обработчик редактирования
  const handleEdit = () => {
    if (selectedSearch) {
      setEditName(selectedSearch.name);
      setEditDialogOpen(true);
    }
    handleMenuClose();
  };

  // Обработчик удаления
  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  // Обработчик запуска поиска
  const handleRunSearch = () => {
    handleMenuClose();
    if (selectedSearch) {
      navigate('/recruiter/search', {
        state: {
          query: selectedSearch.query,
          filters: selectedSearch.filters,
        },
      });
    }
  };

  // Сохранить изменения названия
  const handleEditSave = () => {
    if (selectedSearch && editName.trim()) {
      updateMutation.mutate({ id: selectedSearch.id, name: editName });
    }
  };

  // Подтверждение удаления
  const handleDeleteConfirm = () => {
    if (selectedSearch) {
      deleteMutation.mutate(selectedSearch.id);
    }
  };

  // Форматирование фильтров для отображения
  const formatFilters = (filters: Record<string, unknown>): string => {
    const parts: string[] = [];
    if (filters.skills && Array.isArray(filters.skills)) {
      parts.push(`Skills: ${filters.skills.join(', ')}`);
    }
    if (filters.min_match_score && typeof filters.min_match_score === 'number') {
      parts.push(`Min Score: ${filters.min_match_score}%`);
    }
    if (filters.location) {
      parts.push(`Location: ${filters.location}`);
    }
    return parts.join(' • ');
  };

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      {/* Заголовок страницы */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant={isMobile ? 'h5' : 'h4'} fontWeight={700}>
            Saved Searches
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {total} {total === 1 ? 'search' : 'searches'} saved
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/recruiter/search')}
        >
          {isMobile ? 'New' : 'New Search'}
        </Button>
      </Stack>

      {/* Сообщение об ошибке */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {(error as { detail?: string }).detail || 'Failed to load saved searches.'}
        </Alert>
      )}

      {/* Пустое состояние */}
      {!isLoading && savedSearches.length === 0 && (
        <Paper sx={{ p: 8, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            No saved searches yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Create your first saved search to quickly access common queries
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/recruiter/search')}
            sx={{ mt: 3 }}
          >
            Create Search
          </Button>
        </Paper>
      )}

      {/* Состояние загрузки */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Сетка сохраненных поисков */}
      {!isLoading && savedSearches.length > 0 && (
        <Grid2 container spacing={3}>
          {savedSearches.map((search) => (
            <Grid2 key={search.id} size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
              <Paper
                sx={{
                  p: 3,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
              >
                {/* Заголовок с меню */}
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
                  <Typography variant="h6" noWrap sx={{ flex: 1 }}>
                    {search.name}
                  </Typography>
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuOpen(e, search)}
                    aria-label="Options"
                  >
                    <MoreVertIcon />
                  </IconButton>
                </Stack>

                {/* Поисковый запрос */}
                {search.query && (
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      mb: 2,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                    }}
                  >
                    "{search.query}"
                  </Typography>
                )}

                {/* Фильтры */}
                {search.filters && Object.keys(search.filters).length > 0 && (
                  <Box sx={{ mb: 2, flex: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      {formatFilters(search.filters as Record<string, unknown>)}
                    </Typography>
                  </Box>
                )}

                {/* Быстрые действия */}
                <Stack direction="row" spacing={1} sx={{ mt: 'auto' }}>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<RunIcon />}
                    onClick={() => {
                      setSelectedSearch(search);
                      handleRunSearch();
                    }}
                    sx={{ flex: 1 }}
                  >
                    Run
                  </Button>
                </Stack>

                {/* Дата последнего обновления */}
                <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                  Updated {new Date(search.updated_at).toLocaleDateString()}
                </Typography>
              </Paper>
            </Grid2>
          ))}
        </Grid2>
      )}

      {/* Меню опций */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleRunSearch}>
          <RunIcon fontSize="small" sx={{ mr: 1 }} />
          Run Search
        </MenuItem>
        <MenuItem onClick={handleEdit}>
          <EditIcon fontSize="small" sx={{ mr: 1 }} />
          Rename
        </MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Диалог редактирования */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Rename Search</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Search Name"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            sx={{ mt: 2 }}
            slotProps={{
              input: {
                'aria-label': 'Search name',
              },
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleEditSave}
            variant="contained"
            disabled={!editName.trim() || updateMutation.isPending}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог подтверждения удаления */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Delete Saved Search</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Are you sure you want to delete "{selectedSearch?.name}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default SavedSearchesPage;
