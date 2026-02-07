import React, { useState, useCallback } from 'react';
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  Typography,
  Alert,
  AlertTitle,
  IconButton,
  Tooltip,
  Stack,
  Card,
  CardContent,
} from '@mui/material';
import {
  Close as CloseIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { integrationsClient } from '@/api/integrations';
import type {
  SyncHistoryItem,
  SyncHistoryResponse,
  ApiError,
} from '@/types/api';
import { format } from 'date-fns';

/**
 * SyncHistory Component Props
 */
interface SyncHistoryProps {
  /** Integration ID to fetch sync history for */
  integrationId: string;
  /** Integration name for display */
  integrationName: string;
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog is closed */
  onClose: () => void;
}

/**
 * Get sync status display configuration
 */
const getSyncStatusDisplay = (status: string) => {
  const displays: Record<string, { color: 'success' | 'info' | 'error' | 'warning' | 'default'; icon: React.ReactNode; label: string }> = {
    pending: {
      icon: <ScheduleIcon sx={{ fontSize: 16 }} />,
      color: 'info',
      label: 'Pending',
    },
    running: {
      icon: <ScheduleIcon sx={{ fontSize: 16 }} />,
      color: 'info',
      label: 'Running',
    },
    completed: {
      icon: <CheckCircleIcon sx={{ fontSize: 16 }} />,
      color: 'success',
      label: 'Completed',
    },
    failed: {
      icon: <ErrorIcon sx={{ fontSize: 16 }} />,
      color: 'error',
      label: 'Failed',
    },
  };

  return (
    displays[status] || {
      icon: <InfoIcon sx={{ fontSize: 16 }} />,
      color: 'default',
      label: status,
    }
  );
};

/**
 * SyncHistory Component
 *
 * Displays sync history for an integration including:
 * - Sync operation status (pending, running, completed, failed)
 * - Records processed, successful, and failed counts
 * - Duration and timestamps
 * - Error details for failed syncs
 *
 * Displays in a dialog with a table showing recent sync operations.
 * Error details can be expanded to view full error messages.
 *
 * @example
 * ```tsx
 * <SyncHistory
 *   integrationId="integration-uuid"
 *   integrationName="Workday Production"
 *   open={historyDialogOpen}
 *   onClose={() => setHistoryDialogOpen(false)}
 * />
 * ```
 */
const SyncHistory: React.FC<SyncHistoryProps> = ({
  integrationId,
  integrationName,
  open,
  onClose,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncHistory, setSyncHistory] = useState<SyncHistoryResponse | null>(null);
  const [expandedError, setExpandedError] = useState<string | null>(null);

  /**
   * Fetch sync history data from backend
   */
  const fetchSyncHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response: SyncHistoryResponse = await integrationsClient.getSyncHistory(
        integrationId,
        0,
        50
      );

      setSyncHistory(response);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load sync history. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [integrationId]);

  /**
   * Fetch history when dialog opens
   */
  const handleEnter = () => {
    fetchSyncHistory();
  };

  /**
   * Toggle error details expansion
   */
  const toggleErrorExpansion = (syncId: string) => {
    setExpandedError((prev) => (prev === syncId ? null : syncId));
  };

  /**
   * Format duration for display
   */
  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  };

  /**
   * Render loading state
   */
  const renderLoading = () => (
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
        Loading sync history...
      </Typography>
    </Box>
  );

  /**
   * Render error state
   */
  const renderError = () => (
    <Alert
      severity="error"
      action={
        <Button color="inherit" onClick={fetchSyncHistory} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      }
    >
      <AlertTitle>Error Loading Sync History</AlertTitle>
      {error}
    </Alert>
  );

  /**
   * Render empty state
   */
  const renderEmpty = () => (
    <Alert severity="info">
      <AlertTitle>No Sync History</AlertTitle>
      No sync operations have been performed for this integration yet. Trigger a sync to see history here.
    </Alert>
  );

  /**
   * Render sync history table
   */
  const renderTable = () => {
    if (!syncHistory || syncHistory.syncs.length === 0) {
      return renderEmpty();
    }

    return (
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Status</TableCell>
              <TableCell>Sync Type</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Records</TableCell>
              <TableCell>Success/Failed</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {syncHistory.syncs.map((sync) => {
              const statusDisplay = getSyncStatusDisplay(sync.status);
              const hasError = sync.status === 'failed' && sync.error_message;

              return (
                <React.Fragment key={sync.sync_id}>
                  <TableRow
                    hover
                    sx={{
                      cursor: hasError ? 'pointer' : 'default',
                      ...(hasError && {
                        '&:hover': {
                          backgroundColor: 'action.hover',
                        },
                      }),
                    }}
                    onClick={() => hasError && toggleErrorExpansion(sync.sync_id)}
                  >
                    <TableCell>
                      <Chip
                        icon={statusDisplay.icon}
                        label={statusDisplay.label}
                        color={statusDisplay.color}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                        {sync.sync_type}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {sync.started_at
                          ? format(new Date(sync.started_at), 'MMM dd, HH:mm:ss')
                          : '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDuration(sync.duration_seconds)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {sync.records_processed.toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Typography variant="body2" color="success.main">
                          {sync.records_successful.toLocaleString()}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          /
                        </Typography>
                        <Typography
                          variant="body2"
                          color={sync.records_failed > 0 ? 'error.main' : 'text.secondary'}
                        >
                          {sync.records_failed.toLocaleString()}
                        </Typography>
                        {hasError && (
                          <Tooltip title={expandedError === sync.sync_id ? 'Hide details' : 'View details'}>
                            <IconButton size="small" sx={{ p: 0.5 }}>
                              {expandedError === sync.sync_id ? (
                                <ExpandLessIcon fontSize="small" />
                              ) : (
                                <ExpandMoreIcon fontSize="small" />
                              )}
                            </IconButton>
                          </Tooltip>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                  {hasError && expandedError === sync.sync_id && (
                    <TableRow>
                      <TableCell colSpan={6} sx={{ backgroundColor: 'error.lighter' }}>
                        <Card variant="outlined" sx={{ borderColor: 'error.main' }}>
                          <CardContent sx={{ py: 2, px: 2 }}>
                            <Typography variant="subtitle2" color="error" gutterBottom>
                              Error Details
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                              {sync.error_message}
                            </Typography>
                            {sync.metadata && Object.keys(sync.metadata).length > 0 && (
                              <Box sx={{ mt: 2 }}>
                                <Typography variant="caption" color="text.secondary">
                                  Metadata:
                                </Typography>
                                <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace', display: 'block', mt: 0.5 }}>
                                  {JSON.stringify(sync.metadata, null, 2)}
                                </Typography>
                              </Box>
                            )}
                          </CardContent>
                        </Card>
                      </TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      onEnter={handleEnter}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '80vh' },
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h6" component="div">
              Sync History
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {integrationName}
            </Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ pb: 2 }}>
        {syncHistory && (
          <Box sx={{ mb: 2 }}>
            <Stack direction="row" spacing={2} alignItems="center">
              <Typography variant="body2" color="text.secondary">
                Total Syncs: <strong>{syncHistory.total_syncs}</strong>
              </Typography>
              <Typography variant="body2" color="success.main">
                Completed: <strong>{syncHistory.completed_syncs}</strong>
              </Typography>
              <Typography variant="body2" color="error.main">
                Failed: <strong>{syncHistory.failed_syncs}</strong>
              </Typography>
            </Stack>
          </Box>
        )}

        {loading && renderLoading()}
        {!loading && error && renderError()}
        {!loading && !error && renderTable()}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          onClick={fetchSyncHistory}
          startIcon={<RefreshIcon />}
          disabled={loading}
        >
          Refresh
        </Button>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SyncHistory;
