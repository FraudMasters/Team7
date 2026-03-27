import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Stack,
  Button,
  Chip,
  TablePagination,
  IconButton,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Info as InfoIcon,
  Timer as TimerIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { duplicatesClient } from '@/api/duplicates';
import type { ReviewQueueItem, ReviewQueueListResponse } from '@/api/duplicates';

/**
 * DuplicateReviewQueue Component Props
 */
interface DuplicateReviewQueueProps {
  /** Organization ID for filtering review queue */
  organizationId: string;
  /** Callback when review is completed */
  onReviewComplete?: (reviewId: string, status: 'approved' | 'rejected') => void;
  /** Initial status filter */
  initialStatus?: string;
  /** Show all columns including detailed metadata */
  showDetails?: boolean;
  /** Auto-refresh interval in milliseconds (0 to disable) */
  autoRefreshInterval?: number;
}

/**
 * Helper to get status color
 */
const getStatusColor = (
  status: string
): 'default' | 'primary' | 'success' | 'error' | 'warning' | 'info' => {
  switch (status.toLowerCase()) {
    case 'pending':
      return 'warning';
    case 'in_review':
      return 'info';
    case 'approved':
      return 'success';
    case 'rejected':
      return 'error';
    default:
      return 'default';
  }
};

/**
 * Helper to get status label
 */
const getStatusLabel = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'pending':
      return 'Ожидает';
    case 'in_review':
      return 'На проверке';
    case 'approved':
      return 'Одобрено';
    case 'rejected':
      return 'Отклонено';
    default:
      return status;
  }
};

/**
 * Helper to get confidence score color
 */
const getConfidenceColor = (score: number): 'success' | 'warning' | 'error' => {
  if (score >= 0.9) return 'success';
  if (score >= 0.7) return 'warning';
  return 'error';
};

/**
 * Helper to format timestamp
 */
const formatTimestamp = (timestamp?: string): string => {
  if (!timestamp) return '—';
  try {
    const date = new Date(timestamp);
    return new Intl.DateTimeFormat('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  } catch (e) {
    return timestamp;
  }
};

/**
 * Helper to format wait time
 */
const formatWaitTime = (hours?: number): string => {
  if (hours === undefined || hours === null) return '—';
  if (hours < 1) return '< 1 ч';
  if (hours < 24) return `${Math.round(hours)} ч`;
  const days = Math.floor(hours / 24);
  return `${days} д ${Math.round(hours % 24)} ч`;
};

/**
 * DuplicateReviewQueue Component
 *
 * Provides a manual review queue for duplicate candidates:
 * - List of pending duplicate reviews with confidence scores
 * - Filtering by status and confidence score
 * - Sorting by various fields
 * - Approve/reject actions with reason dialog
 * - Wait time indicators
 * - Pagination support
 * - Auto-refresh capability
 * - Detailed view with metadata
 *
 * @example
 * ```tsx
 * <DuplicateReviewQueue
 *   organizationId="org-123"
 *   initialStatus="pending"
 *   onReviewComplete={(id, status) => console.log(`Review ${id} ${status}`)}
 *   autoRefreshInterval={30000}
 *   showDetails={true}
 * />
 * ```
 */
const DuplicateReviewQueue: React.FC<DuplicateReviewQueueProps> = ({
  organizationId,
  onReviewComplete,
  initialStatus = 'pending',
  showDetails = false,
  autoRefreshInterval = 0,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ReviewQueueListResponse | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>(initialStatus);
  const [minConfidence, setMinConfidence] = useState<number | undefined>(undefined);
  const [maxConfidence, setMaxConfidence] = useState<number | undefined>(undefined);
  const [sortBy, setSortBy] = useState<string>('queue_entered_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Action dialog state
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'approve' | 'reject'>('approve');
  const [selectedReview, setSelectedReview] = useState<ReviewQueueItem | null>(null);
  const [actionReason, setActionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  /**
   * Fetch review queue data from API
   */
  const fetchReviewQueue = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await duplicatesClient.listReviewQueue(
        organizationId,
        page * rowsPerPage,
        rowsPerPage,
        statusFilter || undefined,
        minConfidence,
        maxConfidence,
        undefined,
        sortBy,
        sortOrder
      );
      setData(response);
    } catch (err: any) {
      setError(err?.detail || 'Не удалось загрузить очередь проверки');
      console.error('Failed to fetch review queue:', err);
    } finally {
      setLoading(false);
    }
  }, [organizationId, page, rowsPerPage, statusFilter, minConfidence, maxConfidence, sortBy, sortOrder]);

  /**
   * Load data on mount and when dependencies change
   */
  useEffect(() => {
    fetchReviewQueue();
  }, [fetchReviewQueue]);

  /**
   * Auto-refresh if enabled
   */
  useEffect(() => {
    if (autoRefreshInterval > 0) {
      const interval = setInterval(() => {
        fetchReviewQueue();
      }, autoRefreshInterval);

      return () => clearInterval(interval);
    }
  }, [autoRefreshInterval, fetchReviewQueue]);

  /**
   * Handle page change
   */
  const handlePageChange = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  /**
   * Handle rows per page change
   */
  const handleRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  /**
   * Handle refresh button click
   */
  const handleRefresh = () => {
    setPage(0);
    fetchReviewQueue();
  };

  /**
   * Handle status filter change
   */
  const handleStatusFilterChange = (event: any) => {
    setStatusFilter(event.target.value);
    setPage(0);
  };

  /**
   * Open action dialog
   */
  const openActionDialog = (review: ReviewQueueItem, type: 'approve' | 'reject') => {
    setSelectedReview(review);
    setActionType(type);
    setActionReason('');
    setActionDialogOpen(true);
  };

  /**
   * Close action dialog
   */
  const closeActionDialog = () => {
    setActionDialogOpen(false);
    setSelectedReview(null);
    setActionReason('');
    setActionLoading(false);
  };

  /**
   * Execute review action (approve or reject)
   */
  const executeAction = async () => {
    if (!selectedReview) return;

    setActionLoading(true);
    setError(null);

    try {
      if (actionType === 'approve') {
        await duplicatesClient.approveReview(selectedReview.id, {
          decision_reason: actionReason || undefined,
        });
      } else {
        await duplicatesClient.rejectReview(selectedReview.id, {
          decision_reason: actionReason || undefined,
        });
      }

      // Notify parent
      onReviewComplete?.(selectedReview.id, actionType === 'approve' ? 'approved' : 'rejected');

      // Refresh data
      await fetchReviewQueue();

      closeActionDialog();
    } catch (err: any) {
      setError(err?.detail || `Не удалось ${actionType === 'approve' ? 'одобрить' : 'отклонить'} проверку`);
      console.error(`Failed to ${actionType} review:`, err);
      setActionLoading(false);
    }
  };

  /**
   * Apply confidence filter
   */
  const applyConfidenceFilter = (min?: number, max?: number) => {
    setMinConfidence(min);
    setMaxConfidence(max);
    setPage(0);
  };

  /**
   * Clear all filters
   */
  const clearFilters = () => {
    setStatusFilter('');
    setMinConfidence(undefined);
    setMaxConfidence(undefined);
    setPage(0);
  };

  // Calculate stats
  const pendingCount = data?.items.filter((item) => item.status === 'pending').length || 0;
  const inReviewCount = data?.items.filter((item) => item.status === 'in_review').length || 0;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <ScheduleIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Очередь проверки дубликатов
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Ручная проверка потенциальных дубликатов
              </Typography>
            </Box>
          </Box>
          <Tooltip title="Обновить">
            <IconButton onClick={handleRefresh} disabled={loading} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Stats Summary */}
        {data && (
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <Chip
              label={`Всего: ${data.total}`}
              color="default"
              variant="outlined"
              size="medium"
            />
            <Chip
              label={`Ожидает: ${pendingCount}`}
              color="warning"
              variant={statusFilter === 'pending' ? 'filled' : 'outlined'}
              size="medium"
              onClick={() => setStatusFilter('pending')}
            />
            <Chip
              label={`На проверке: ${inReviewCount}`}
              color="info"
              variant={statusFilter === 'in_review' ? 'filled' : 'outlined'}
              size="medium"
              onClick={() => setStatusFilter('in_review')}
            />
          </Box>
        )}

        <Divider sx={{ mb: 2 }} />

        {/* Filters */}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Статус</InputLabel>
              <Select value={statusFilter} onChange={handleStatusFilterChange} label="Статус">
                <MenuItem value="">Все</MenuItem>
                <MenuItem value="pending">Ожидает</MenuItem>
                <MenuItem value="in_review">На проверке</MenuItem>
                <MenuItem value="approved">Одобрено</MenuItem>
                <MenuItem value="rejected">Отклонено</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Сортировка</InputLabel>
              <Select
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value);
                  setPage(0);
                }}
                label="Сортировка"
              >
                <MenuItem value="queue_entered_at">Время добавления</MenuItem>
                <MenuItem value="confidence_score">Оценка уверенности</MenuItem>
                <MenuItem value="wait_time">Время ожидания</MenuItem>
                <MenuItem value="review_started_at">Время начала проверки</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Порядок</InputLabel>
              <Select
                value={sortOrder}
                onChange={(e) => {
                  setSortOrder(e.target.value as 'asc' | 'desc');
                  setPage(0);
                }}
                label="Порядок"
              >
                <MenuItem value="asc">По возрастанию</MenuItem>
                <MenuItem value="desc">По убыванию</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Button variant="outlined" fullWidth onClick={clearFilters} disabled={loading}>
              Сбросить фильтры
            </Button>
          </Grid>
        </Grid>

        {/* Confidence Filter Presets */}
        <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
          <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'center', mr: 1 }}>
            Уверенность:
          </Typography>
          <Chip
            label="Все"
            size="small"
            onClick={() => applyConfidenceFilter(undefined, undefined)}
            variant={minConfidence === undefined && maxConfidence === undefined ? 'filled' : 'outlined'}
          />
          <Chip
            label="Высокая (≥90%)"
            size="small"
            color="success"
            onClick={() => applyConfidenceFilter(0.9, undefined)}
            variant={minConfidence === 0.9 ? 'filled' : 'outlined'}
          />
          <Chip
            label="Средняя (70-90%)"
            size="small"
            color="warning"
            onClick={() => applyConfidenceFilter(0.7, 0.9)}
            variant={minConfidence === 0.7 && maxConfidence === 0.9 ? 'filled' : 'outlined'}
          />
          <Chip
            label="Низкая (<70%)"
            size="small"
            color="error"
            onClick={() => applyConfidenceFilter(undefined, 0.7)}
            variant={maxConfidence === 0.7 ? 'filled' : 'outlined'}
          />
        </Box>
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Empty State */}
      {!loading && data && data.items.length === 0 && (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <InfoIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Нет элементов в очереди
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {statusFilter
              ? 'Попробуйте изменить фильтры для отображения большего количества элементов'
              : 'В очереди проверки пока нет потенциальных дубликатов'}
          </Typography>
        </Paper>
      )}

      {/* Review Queue Table */}
      {!loading && data && data.items.length > 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Оригинал</TableCell>
                <TableCell>Дубликат</TableCell>
                <TableCell align="center">Уверенность</TableCell>
                <TableCell align="center">Статус</TableCell>
                <TableCell align="center">Время ожидания</TableCell>
                <TableCell align="center">Добавлено в очередь</TableCell>
                {showDetails && (
                  <>
                    <TableCell align="center">Начало проверки</TableCell>
                    <TableCell align="center">Завершение</TableCell>
                  </>
                )}
                <TableCell align="center">Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.items.map((item) => (
                <TableRow key={item.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={500}>
                      {item.original_filename || 'Неизвестный файл'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ID: {item.original_resume_id.substring(0, 8)}...
                    </Typography>
                  </TableCell>

                  <TableCell>
                    <Typography variant="body2" fontWeight={500}>
                      {item.duplicate_filename || 'Неизвестный файл'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ID: {item.duplicate_resume_id.substring(0, 8)}...
                    </Typography>
                  </TableCell>

                  <TableCell align="center">
                    <Chip
                      label={`${Math.round(item.confidence_score * 100)}%`}
                      color={getConfidenceColor(item.confidence_score)}
                      size="small"
                    />
                  </TableCell>

                  <TableCell align="center">
                    <Chip
                      label={getStatusLabel(item.status)}
                      color={getStatusColor(item.status)}
                      size="small"
                    />
                  </TableCell>

                  <TableCell align="center">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                      <TimerIcon fontSize="small" color="action" />
                      <Typography variant="body2">{formatWaitTime(item.wait_time_hours)}</Typography>
                    </Box>
                  </TableCell>

                  <TableCell align="center">
                    <Typography variant="body2">{formatTimestamp(item.queue_entered_at)}</Typography>
                  </TableCell>

                  {showDetails && (
                    <>
                      <TableCell align="center">
                        <Typography variant="body2">
                          {formatTimestamp(item.review_started_at)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2">
                          {formatTimestamp(item.review_completed_at)}
                        </Typography>
                      </TableCell>
                    </>
                  )}

                  <TableCell align="center">
                    <Stack direction="row" spacing={1} justifyContent="center">
                      {item.status === 'pending' || item.status === 'in_review' ? (
                        <>
                          <Tooltip title="Одобрить">
                            <IconButton
                              size="small"
                              color="success"
                              onClick={() => openActionDialog(item, 'approve')}
                            >
                              <ApproveIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Отклонить">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => openActionDialog(item, 'reject')}
                            >
                              <RejectIcon />
                            </IconButton>
                          </Tooltip>
                        </>
                      ) : (
                        <Chip
                          label={item.decision_reason || 'Без причины'}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Pagination */}
          <TablePagination
            component="div"
            count={data.total}
            page={page}
            onPageChange={handlePageChange}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={handleRowsPerPageChange}
            rowsPerPageOptions={[10, 25, 50, 100]}
            labelRowsPerPage="Строк на странице:"
            labelDisplayedRows={({ from, to, count }) =>
              `${from}–${to} из ${count !== -1 ? count : `более ${to}`}`
            }
          />
        </TableContainer>
      )}

      {/* Action Dialog */}
      <Dialog open={actionDialogOpen} onClose={closeActionDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {actionType === 'approve' ? (
            <>
              <ApproveIcon sx={{ verticalAlign: 'middle', mr: 1, color: 'success.main' }} />
              Одобрить дубликат
            </>
          ) : (
            <>
              <RejectIcon sx={{ verticalAlign: 'middle', mr: 1, color: 'error.main' }} />
              Отклонить дубликат
            </>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedReview && (
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Детали проверки
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Оригинал:
                      </Typography>
                      <Typography variant="body2" fontWeight={500}>
                        {selectedReview.original_filename || 'Неизвестный файл'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Дубликат:
                      </Typography>
                      <Typography variant="body2" fontWeight={500}>
                        {selectedReview.duplicate_filename || 'Неизвестный файл'}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Уверенность:
                      </Typography>
                      <Chip
                        label={`${Math.round(selectedReview.confidence_score * 100)}%`}
                        color={getConfidenceColor(selectedReview.confidence_score)}
                        size="small"
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Время ожидания:
                      </Typography>
                      <Typography variant="body2">
                        {formatWaitTime(selectedReview.wait_time_hours)}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>

              <TextField
                fullWidth
                multiline
                rows={3}
                label="Причина решения (опционально)"
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                placeholder={
                  actionType === 'approve'
                    ? 'Например: Подтверждено, один и тот же кандидат'
                    : 'Например: Разные люди с похожими именами'
                }
              />

              <Alert severity={actionType === 'approve' ? 'info' : 'warning'}>
                {actionType === 'approve'
                  ? 'Одобрение дубликата переместит его в очередь на слияние. Профили можно будет объединить позже.'
                  : 'Отклонение дубликата пометит эту пару как не являющуюся дубликатом. Это решение можно изменить позже.'}
              </Alert>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeActionDialog} disabled={actionLoading}>
            Отмена
          </Button>
          <Button
            onClick={executeAction}
            disabled={actionLoading}
            variant="contained"
            color={actionType === 'approve' ? 'success' : 'error'}
            startIcon={actionLoading ? <CircularProgress size={16} /> : null}
          >
            {actionLoading
              ? 'Обработка...'
              : actionType === 'approve'
              ? 'Одобрить'
              : 'Отклонить'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default DuplicateReviewQueue;
