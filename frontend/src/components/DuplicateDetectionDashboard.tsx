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
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  FileCopy as DuplicateIcon,
  Info as InfoIcon,
  MergeType as MergeIcon,
} from '@mui/icons-material';
import { duplicatesClient } from '@/api/duplicates';
import type { DuplicateResumeItem, DuplicateListResponse } from '@/api/duplicates';

/**
 * DuplicateDetectionDashboard Component Props
 */
interface DuplicateDetectionDashboardProps {
  /** Organization ID for filtering duplicates */
  organizationId: string;
  /** Callback when merge action is triggered */
  onMergeRequest?: (duplicate: DuplicateResumeItem) => void;
  /** Show detailed information */
  showDetails?: boolean;
}

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
const formatTimestamp = (timestamp: string): string => {
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
 * DuplicateDetectionDashboard Component
 *
 * Displays a dashboard showing potential duplicate resumes with confidence scores.
 * Features include:
 * - List of duplicate pairs with original and duplicate filenames
 * - Confidence score indicators
 * - Detection timestamps
 * - Pagination support
 * - Refresh functionality
 * - Merge action buttons
 *
 * @example
 * ```tsx
 * <DuplicateDetectionDashboard
 *   organizationId="org-123"
 *   onMergeRequest={(duplicate) => handleMerge(duplicate)}
 *   showDetails={true}
 * />
 * ```
 */
const DuplicateDetectionDashboard: React.FC<DuplicateDetectionDashboardProps> = ({
  organizationId,
  onMergeRequest,
  showDetails = false,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<DuplicateListResponse | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  /**
   * Fetch duplicate detection data from backend
   */
  const fetchDuplicates = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await duplicatesClient.listDuplicates(
        organizationId,
        page * rowsPerPage,
        rowsPerPage
      );
      setData(result);
    } catch (err: any) {
      const errorMessage = err?.detail || err?.message || 'Failed to load duplicate detection data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [organizationId, page, rowsPerPage]);

  /**
   * Initial data fetch
   */
  useEffect(() => {
    if (organizationId) {
      fetchDuplicates();
    } else {
      setError('Organization ID is required');
      setLoading(false);
    }
  }, [organizationId, fetchDuplicates]);

  /**
   * Handle page change
   */
  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  /**
   * Handle rows per page change
   */
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  /**
   * Handle refresh button click
   */
  const handleRefresh = () => {
    fetchDuplicates();
  };

  /**
   * Handle merge button click
   */
  const handleMergeClick = (duplicate: DuplicateResumeItem) => {
    if (onMergeRequest) {
      onMergeRequest(duplicate);
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          Загрузка дубликатов...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Анализ резюме для организации
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" size="small" onClick={handleRefresh} startIcon={<RefreshIcon />}>
            Повторить
          </Button>
        }
        sx={{ mb: 3 }}
      >
        <Typography variant="body2" fontWeight={600}>
          Ошибка загрузки данных
        </Typography>
        <Typography variant="body2">{error}</Typography>
      </Alert>
    );
  }

  /**
   * Render empty state
   */
  if (!data || data.duplicates.length === 0) {
    return (
      <Paper sx={{ p: 6, textAlign: 'center' }}>
        <Box
          sx={{
            width: 80,
            height: 80,
            borderRadius: '50%',
            bgcolor: 'success.light',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 3,
          }}
        >
          <DuplicateIcon sx={{ fontSize: 40, color: 'success.dark' }} />
        </Box>
        <Typography variant="h6" gutterBottom>
          Дубликаты не найдены
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          В системе не обнаружено потенциальных дубликатов резюме
        </Typography>
        <Button variant="outlined" startIcon={<RefreshIcon />} onClick={handleRefresh}>
          Обновить
        </Button>
      </Paper>
    );
  }

  /**
   * Render main dashboard
   */
  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h5" fontWeight={700} gutterBottom>
            Обнаружение дубликатов
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Найдено {data.total_count} пар потенциальных дубликатов резюме
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={loading}
        >
          Обновить
        </Button>
      </Box>

      {/* Summary Card */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: 'info.light' }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <InfoIcon sx={{ color: 'info.dark' }} />
          <Box>
            <Typography variant="body1" fontWeight={600}>
              Обнаружено дубликатов: {data.total_count}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Проверьте потенциальные совпадения и выполните слияние для устранения дубликатов
            </Typography>
          </Box>
        </Stack>
      </Paper>

      {/* Duplicates Table */}
      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }} aria-label="duplicate detection table">
          <TableHead>
            <TableRow>
              <TableCell>Оригинальное резюме</TableCell>
              <TableCell>Дубликат резюме</TableCell>
              <TableCell align="center">Уверенность</TableCell>
              <TableCell>Время обнаружения</TableCell>
              {showDetails && <TableCell>Хеш содержимого</TableCell>}
              <TableCell align="right">Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.duplicates.map((duplicate) => (
              <TableRow
                key={duplicate.id}
                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
              >
                {/* Original Resume */}
                <TableCell>
                  <Stack spacing={0.5}>
                    <Typography variant="body2" fontWeight={600}>
                      {duplicate.original_filename || 'Неизвестный файл'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ID: {duplicate.original_resume_id.substring(0, 8)}...
                    </Typography>
                  </Stack>
                </TableCell>

                {/* Duplicate Resume */}
                <TableCell>
                  <Stack spacing={0.5}>
                    <Typography variant="body2" fontWeight={600}>
                      {duplicate.duplicate_filename || 'Неизвестный файл'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ID: {duplicate.duplicate_resume_id.substring(0, 8)}...
                    </Typography>
                  </Stack>
                </TableCell>

                {/* Confidence Score - using 1.0 for exact hash matches */}
                <TableCell align="center">
                  <Chip
                    label="100%"
                    color={getConfidenceColor(1.0)}
                    size="small"
                    sx={{ fontWeight: 600 }}
                  />
                </TableCell>

                {/* Detection Timestamp */}
                <TableCell>
                  <Typography variant="body2">
                    {formatTimestamp(duplicate.detection_timestamp)}
                  </Typography>
                </TableCell>

                {/* Content Hash (Optional) */}
                {showDetails && (
                  <TableCell>
                    <Tooltip title={duplicate.content_hash}>
                      <Typography
                        variant="caption"
                        sx={{
                          fontFamily: 'monospace',
                          maxWidth: 120,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: 'block',
                        }}
                      >
                        {duplicate.content_hash.substring(0, 16)}...
                      </Typography>
                    </Tooltip>
                  </TableCell>
                )}

                {/* Actions */}
                <TableCell align="right">
                  <Tooltip title="Объединить профили">
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={() => handleMergeClick(duplicate)}
                      disabled={!onMergeRequest}
                    >
                      <MergeIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {/* Pagination */}
        <TablePagination
          rowsPerPageOptions={[10, 25, 50, 100]}
          component="div"
          count={data.total_count}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Строк на странице:"
          labelDisplayedRows={({ from, to, count }) =>
            `${from}-${to} из ${count !== -1 ? count : `более чем ${to}`}`
          }
        />
      </TableContainer>
    </Box>
  );
};

export default DuplicateDetectionDashboard;
