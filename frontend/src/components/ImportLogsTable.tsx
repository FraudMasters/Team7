import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  AlertTitle,
  Stack,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  IconButton,
  Tooltip,
  TextField,
  MenuItem,
  TablePagination,
  Collapse,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as CheckIcon,
  Refresh as RefreshIcon,
  Replay as RetryIcon,
  KeyboardArrowDown as ExpandMoreIcon,
  KeyboardArrowUp as ExpandLessIcon,
  Schedule as ScheduleIcon,
  CloudUpload as CloudUploadIcon,
} from '@mui/icons-material';
import { jobIntegrationsClient } from '@/api/jobIntegrations';
import type { ImportLogResponse, ApiError } from '@/types/api';

/**
 * ImportLogsTable Component Props
 */
interface ImportLogsTableProps {
  /** API endpoint URL for fetching import logs */
  apiUrl?: string;
  /** Initial status filter to apply */
  initialStatusFilter?: string;
}

/**
 * Get status icon for display
 */
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'success':
      return <CheckIcon fontSize="small" />;
    case 'failed':
      return <ErrorIcon fontSize="small" />;
    case 'partial':
      return <WarningIcon fontSize="small" />;
    case 'in_progress':
      return <CircularProgress size={16} />;
    case 'skipped':
      return <InfoIcon fontSize="small" />;
    default:
      return <InfoIcon fontSize="small" />;
  }
};

/**
 * Get status color for display
 */
const getStatusColor = (status: string): 'success' | 'warning' | 'error' | 'info' | 'default' => {
  switch (status) {
    case 'success':
      return 'success';
    case 'failed':
      return 'error';
    case 'partial':
      return 'warning';
    case 'in_progress':
      return 'info';
    case 'skipped':
      return 'default';
    default:
      return 'default';
  }
};

/**
 * Format duration in human-readable format
 */
const formatDuration = (startedAt: string | null, completedAt: string | null): string => {
  if (!startedAt || !completedAt) return 'N/A';

  const start = new Date(startedAt).getTime();
  const end = new Date(completedAt).getTime();
  const durationSeconds = Math.round((end - start) / 1000);

  if (durationSeconds < 60) {
    return `${durationSeconds}s`;
  } else if (durationSeconds < 3600) {
    const minutes = Math.floor(durationSeconds / 60);
    const seconds = durationSeconds % 60;
    return `${minutes}m ${seconds}s`;
  } else {
    const hours = Math.floor(durationSeconds / 3600);
    const minutes = Math.floor((durationSeconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
};

/**
 * ImportLogsTable Component
 *
 * Displays import history for job board integrations including:
 * - Status badges (success, failed, partial, in_progress, skipped)
 * - Records processed/succeeded/failed counts
 * - Duration and timestamps
 * - Error messages for failed imports
 * - Retry functionality for failed imports
 * - Filtering by status
 * - Pagination
 *
 * @example
 * ```tsx
 * <ImportLogsTable />
 * ```
 */
const ImportLogsTable: React.FC<ImportLogsTableProps> = ({
  initialStatusFilter = '',
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [retrying, setRetrying] = useState<Record<string, boolean>>({});
  const [data, setData] = useState<ImportLogResponse[]>([]);
  const [total, setTotal] = useState(0);

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Filter state
  const [statusFilter, setStatusFilter] = useState(initialStatusFilter);

  // Expanded row state
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  /**
   * Fetch import logs from backend
   */
  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await jobIntegrationsClient.listImportLogs(
        page * rowsPerPage,
        rowsPerPage,
        statusFilter || undefined
      );

      setData(response.logs);
      setTotal(response.total);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load import logs';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage, statusFilter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  /**
   * Handle retrying a failed import
   */
  const handleRetry = useCallback(async (logId: string) => {
    try {
      setRetrying((prev) => ({ ...prev, [logId]: true }));
      setError(null);

      const response = await fetch(`/api/integrations/logs/${logId}/retry`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData: ApiError = await response.json();
        throw new Error(errorData.detail || 'Failed to retry import');
      }

      setSuccessMessage('Import retry initiated successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);

      // Refresh logs after retry
      await fetchLogs();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to retry import';
      setError(errorMessage);
    } finally {
      setRetrying((prev) => ({ ...prev, [logId]: false }));
    }
  }, [fetchLogs]);

  /**
   * Handle page change
   */
  const handleChangePage = useCallback((event: unknown, newPage: number) => {
    setPage(newPage);
  }, []);

  /**
   * Handle rows per page change
   */
  const handleChangeRowsPerPage = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  }, []);

  /**
   * Handle status filter change
   */
  const handleStatusFilterChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setStatusFilter(event.target.value);
    setPage(0);
  }, []);

  /**
   * Toggle row expansion
   */
  const handleToggleRow = useCallback((logId: string) => {
    setExpandedRow((prev) => (prev === logId ? null : logId));
  }, []);

  /**
   * Render loading state
   */
  if (loading && data.length === 0) {
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
          Loading Import Logs
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Please wait while we fetch the import history...
        </Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Error Message */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Message */}
      {successMessage && (
        <Alert
          severity="success"
          icon={<CheckIcon fontSize="inherit" />}
          onClose={() => setSuccessMessage(null)}
        >
          {successMessage}
        </Alert>
      )}

      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h5" fontWeight={600}>
              Import Logs
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {total} {total === 1 ? 'import' : 'imports'} logged
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            {/* Status Filter */}
            <TextField
              select
              label="Filter by Status"
              value={statusFilter}
              onChange={handleStatusFilterChange}
              size="small"
              sx={{ minWidth: 150 }}
            >
              <MenuItem value="">All Statuses</MenuItem>
              <MenuItem value="success">Success</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
              <MenuItem value="partial">Partial</MenuItem>
              <MenuItem value="in_progress">In Progress</MenuItem>
              <MenuItem value="skipped">Skipped</MenuItem>
            </TextField>

            {/* Refresh Button */}
            <Button
              variant="outlined"
              startIcon={loading ? <CircularProgress size={16} /> : <RefreshIcon />}
              onClick={fetchLogs}
              disabled={loading}
              size="small"
            >
              Refresh
            </Button>
          </Box>
        </Box>

        {/* Table */}
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell />
                <TableCell>Source</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Processed</TableCell>
                <TableCell align="right">Succeeded</TableCell>
                <TableCell align="right">Failed</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Started</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} sx={{ py: 8, textAlign: 'center' }}>
                    <CloudUploadIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      No Import Logs Found
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {statusFilter
                        ? `No imports with status "${statusFilter}" found.`
                        : 'No imports have been run yet.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                data.map((log) => {
                  const isExpanded = expandedRow === log.id;
                  const canRetry = log.status === 'failed' || log.status === 'partial';

                  return (
                    <React.Fragment key={log.id}>
                      <TableRow hover>
                        {/* Expand/Collapse Button */}
                        <TableCell sx={{ width: 50 }}>
                          {(log.error_message || log.error_details || log.import_metadata) && (
                            <IconButton
                              size="small"
                              onClick={() => handleToggleRow(log.id)}
                              aria-label="Show details"
                            >
                              {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                            </IconButton>
                          )}
                        </TableCell>

                        {/* Job Board Name */}
                        <TableCell>
                          <Typography variant="body2" fontWeight={500}>
                            {log.job_board_name || 'Unknown Source'}
                          </Typography>
                        </TableCell>

                        {/* Status Badge */}
                        <TableCell>
                          <Chip
                            icon={getStatusIcon(log.status)}
                            label={log.status.replace('_', ' ').toUpperCase()}
                            color={getStatusColor(log.status)}
                            size="small"
                            variant="filled"
                          />
                        </TableCell>

                        {/* Records Processed */}
                        <TableCell align="right">
                          <Typography variant="body2">
                            {log.records_processed ?? 0}
                          </Typography>
                        </TableCell>

                        {/* Records Succeeded */}
                        <TableCell align="right">
                          <Typography variant="body2" color="success.main">
                            {log.records_succeeded ?? 0}
                          </Typography>
                        </TableCell>

                        {/* Records Failed */}
                        <TableCell align="right">
                          <Typography
                            variant="body2"
                            color={log.records_failed && log.records_failed > 0 ? 'error.main' : 'text.secondary'}
                          >
                            {log.records_failed ?? 0}
                          </Typography>
                        </TableCell>

                        {/* Duration */}
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <ScheduleIcon fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary">
                              {formatDuration(log.started_at, log.completed_at)}
                            </Typography>
                          </Box>
                        </TableCell>

                        {/* Started At */}
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {log.started_at
                              ? new Date(log.started_at).toLocaleString()
                              : 'N/A'}
                          </Typography>
                        </TableCell>

                        {/* Actions */}
                        <TableCell align="right">
                          {canRetry && (
                            <Tooltip title="Retry import">
                              <IconButton
                                size="small"
                                onClick={() => handleRetry(log.id)}
                                disabled={retrying[log.id]}
                                color="primary"
                                aria-label="Retry import"
                              >
                                {retrying[log.id] ? (
                                  <CircularProgress size={16} />
                                ) : (
                                  <RetryIcon />
                                )}
                              </IconButton>
                            </Tooltip>
                          )}
                        </TableCell>
                      </TableRow>

                      {/* Expanded Row Details */}
                      {(log.error_message || log.error_details || log.import_metadata) && (
                        <TableRow>
                          <TableCell colSpan={9} sx={{ py: 0, border: 'none' }}>
                            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                              <Box sx={{ p: 3, bgcolor: 'action.hover' }}>
                                {/* Error Message */}
                                {log.error_message && (
                                  <Alert severity="error" sx={{ mb: log.error_details ? 2 : 0 }}>
                                    <AlertTitle>Error</AlertTitle>
                                    <Typography variant="body2">
                                      {log.error_message}
                                    </Typography>
                                  </Alert>
                                )}

                                {/* Error Details */}
                                {log.error_details && (
                                  <Box sx={{ mb: 2 }}>
                                    <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                                      Error Details:
                                    </Typography>
                                    <Box
                                      sx={{
                                        p: 2,
                                        bgcolor: 'background.paper',
                                        borderRadius: 1,
                                        fontFamily: 'monospace',
                                        fontSize: '0.875rem',
                                        overflow: 'auto',
                                        maxHeight: 200,
                                      }}
                                    >
                                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                        {JSON.stringify(log.error_details, null, 2)}
                                      </pre>
                                    </Box>
                                  </Box>
                                )}

                                {/* Import Metadata */}
                                {log.import_metadata && (
                                  <Box>
                                    <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                                      Import Metadata:
                                    </Typography>
                                    <Box
                                      sx={{
                                        p: 2,
                                        bgcolor: 'background.paper',
                                        borderRadius: 1,
                                        fontFamily: 'monospace',
                                        fontSize: '0.875rem',
                                        overflow: 'auto',
                                        maxHeight: 200,
                                      }}
                                    >
                                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                        {JSON.stringify(log.import_metadata, null, 2)}
                                      </pre>
                                    </Box>
                                  </Box>
                                )}

                                {/* Retry Count */}
                                {log.retry_count !== null && log.retry_count > 0 && (
                                  <Box sx={{ mt: 2 }}>
                                    <Chip
                                      label={`Retried ${log.retry_count} time${log.retry_count > 1 ? 's' : ''}`}
                                      color="warning"
                                      size="small"
                                      variant="outlined"
                                    />
                                  </Box>
                                )}
                              </Box>
                            </Collapse>
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[10, 25, 50, 100]}
          labelRowsPerPage="Rows per page:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} of ${count !== -1 ? count : `more than ${to}`}`}
        />
      </Paper>
    </Stack>
  );
};

export default ImportLogsTable;
