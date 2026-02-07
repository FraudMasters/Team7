/**
 * Webhook List Component
 *
 * Displays a list of webhook subscriptions with actions for viewing, enabling/disabling, and managing them.
 *
 * @module components/developer/WebhookList
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Stack,
  IconButton,
  Menu,
  MenuItem,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
  Link,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  PlayArrow as EnableIcon,
  Pause as DisableIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { webhooksClient, type WebhookSubscription, type WebhookDeliveryLog, WebhookDeliveryStatus } from '@/api/webhooks';

interface WebhookListProps {
  refreshTrigger?: number;
  onStatisticsUpdate?: () => void;
}

/**
 * Format date to readable string
 */
const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'Never';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Get event type label with color
 */
const getEventTypeInfo = (eventType: string): { label: string; color: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' } => {
  if (eventType.startsWith('candidate.')) return { label: 'Candidate', color: 'primary' };
  if (eventType.startsWith('ranking.')) return { label: 'Ranking', color: 'secondary' };
  if (eventType.startsWith('stage.') || eventType.startsWith('status.')) return { label: 'Status', color: 'info' };
  if (eventType.startsWith('resume.')) return { label: 'Resume', color: 'success' };
  if (eventType.startsWith('vacancy.')) return { label: 'Vacancy', color: 'warning' };
  if (eventType.startsWith('match.')) return { label: 'Match', color: 'default' };
  if (eventType.startsWith('workflow.')) return { label: 'Workflow', color: 'error' };
  return { label: 'Other', color: 'default' };
};

/**
 * Get delivery status icon and color
 */
const getDeliveryStatusInfo = (status: string) => {
  switch (status) {
    case WebhookDeliveryStatus.Success:
      return { icon: <CheckCircleIcon fontSize="small" />, color: 'success' as const, label: 'Success' };
    case WebhookDeliveryStatus.Failed:
      return { icon: <ErrorIcon fontSize="small" />, color: 'error' as const, label: 'Failed' };
    case WebhookDeliveryStatus.Retrying:
      return { icon: <ScheduleIcon fontSize="small" />, color: 'warning' as const, label: 'Retrying' };
    default:
      return { icon: <ScheduleIcon fontSize="small" />, color: 'default' as const, label: 'Pending' };
  }
};

/**
 * Delivery Logs Dialog Component
 */
interface DeliveryLogsDialogProps {
  open: boolean;
  onClose: () => void;
  subscriptionId: string;
  subscriptionUrl: string;
}

const DeliveryLogsDialog: React.FC<DeliveryLogsDialogProps> = ({ open, onClose, subscriptionId, subscriptionUrl }) => {
  const [logs, setLogs] = useState<WebhookDeliveryLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = useCallback(async () => {
    if (!open) return;

    setLoading(true);
    setError(null);

    try {
      const data = await webhooksClient.getDeliveryLogs(subscriptionId, 0, 20);
      setLogs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load delivery logs');
    } finally {
      setLoading(false);
    }
  }, [open, subscriptionId]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" fontWeight={600}>
            Delivery Logs
          </Typography>
          <Button
            size="small"
            onClick={fetchLogs}
            startIcon={<RefreshIcon />}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Endpoint: {subscriptionUrl}
        </Typography>
      </DialogTitle>

      <DialogContent>
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <Stack alignItems="center" spacing={2}>
              <CircularProgress size={40} />
              <Typography variant="body2" color="text.secondary">
                Loading delivery logs...
              </Typography>
            </Stack>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!loading && logs.length === 0 && (
          <Paper
            sx={{
              p: 4,
              textAlign: 'center',
              border: '2px dashed',
              borderColor: 'divider',
            }}
          >
            <Typography variant="body2" color="text.secondary">
              No delivery logs yet. Webhooks will be logged here once events are triggered.
            </Typography>
          </Paper>
        )}

        {!loading && logs.length > 0 && (
          <Stack spacing={2}>
            {logs.map((log) => {
              const statusInfo = getDeliveryStatusInfo(log.status);
              return (
                <Card key={log.id} variant="outlined">
                  <CardContent sx={{ py: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          icon={statusInfo.icon}
                          label={statusInfo.label}
                          color={statusInfo.color}
                          size="small"
                        />
                        <Typography variant="caption" color="text.secondary">
                          {formatDate(log.created_at)}
                        </Typography>
                        {log.attempt_count > 1 && (
                          <Chip label={`Attempt ${log.attempt_count}`} size="small" variant="outlined" />
                        )}
                      </Box>
                    </Box>

                    <Box sx={{ mb: 1 }}>
                      <Typography variant="subtitle2" fontWeight={600}>
                        {log.event_type}
                      </Typography>
                    </Box>

                    {log.status_code && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        Status Code: <strong>{log.status_code}</strong>
                      </Typography>
                    )}

                    {log.error_message && (
                      <Alert severity="error" sx={{ mt: 1 }}>
                        <Typography variant="body2">{log.error_message}</Typography>
                      </Alert>
                    )}

                    {log.next_retry_at && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        Next retry: {formatDate(log.next_retry_at)}
                      </Typography>
                    )}

                    <Accordion sx={{ mt: 2 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="caption">View Event Data</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box
                          sx={{
                            bgcolor: 'background.paper',
                            p: 2,
                            borderRadius: 1,
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            overflow: 'auto',
                            maxHeight: 200,
                          }}
                        >
                          <pre>{JSON.stringify(log.event_data, null, 2)}</pre>
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  </CardContent>
                </Card>
              );
            })}
          </Stack>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

/**
 * WebhookList Component
 *
 * Displays a grid/list of webhook subscriptions with their metadata and actions:
 * - Endpoint URL
 * - Active/Inactive status
 * - Subscribed events
 * - Last delivery timestamp
 * - Failure count
 * - Enable/Disable/Delete actions
 * - View delivery logs
 *
 * @example
 * ```tsx
 * <WebhookList refreshTrigger={timestamp} onStatisticsUpdate={fetchStats} />
 * ```
 */
const WebhookList: React.FC<WebhookListProps> = ({ refreshTrigger = 0, onStatisticsUpdate }) => {
  const [webhooks, setWebhooks] = useState<WebhookSubscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedWebhook, setSelectedWebhook] = useState<WebhookSubscription | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingWebhookId, setDeletingWebhookId] = useState<string | null>(null);
  const [togglingWebhookId, setTogglingWebhookId] = useState<string | null>(null);
  const [logsDialogOpen, setLogsDialogOpen] = useState(false);

  const fetchWebhooks = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await webhooksClient.listSubscriptions();
      setWebhooks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load webhooks');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWebhooks();
  }, [fetchWebhooks, refreshTrigger]);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, webhook: WebhookSubscription) => {
    setAnchorEl(event.currentTarget);
    setSelectedWebhook(webhook);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedWebhook(null);
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteConfirm = async () => {
    if (!selectedWebhook) return;

    setDeletingWebhookId(selectedWebhook.id);
    setDeleteDialogOpen(false);

    try {
      await webhooksClient.deleteSubscription(selectedWebhook.id);
      await fetchWebhooks();
      onStatisticsUpdate?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete webhook');
    } finally {
      setDeletingWebhookId(null);
      setSelectedWebhook(null);
    }
  };

  const handleToggle = async (webhook: WebhookSubscription) => {
    setTogglingWebhookId(webhook.id);

    try {
      if (webhook.is_active) {
        await webhooksClient.disableSubscription(webhook.id);
      } else {
        await webhooksClient.enableSubscription(webhook.id);
      }
      await fetchWebhooks();
      onStatisticsUpdate?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle webhook');
    } finally {
      setTogglingWebhookId(null);
    }
  };

  const handleViewLogs = () => {
    setLogsDialogOpen(true);
    handleMenuClose();
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <Stack alignItems="center" spacing={2}>
          <CircularProgress size={48} />
          <Typography variant="body2" color="text.secondary">
            Loading webhooks...
          </Typography>
        </Stack>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" onClick={fetchWebhooks} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Error Loading Webhooks</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (webhooks.length === 0) {
    return (
      <Paper
        sx={{
          p: 6,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: 'divider',
        }}
      >
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Webhooks Yet
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create your first webhook subscription to start receiving event notifications
          </Typography>
        </Box>
      </Paper>
    );
  }

  const activeWebhooks = webhooks.filter((w) => w.is_active);
  const inactiveWebhooks = webhooks.filter((w) => !w.is_active);

  return (
    <Stack spacing={4}>
      {/* Active Webhooks Section */}
      {activeWebhooks.length > 0 && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" fontWeight={600}>
              Active Webhooks ({activeWebhooks.length})
            </Typography>
            <Button
              size="small"
              onClick={fetchWebhooks}
              startIcon={<RefreshIcon />}
            >
              Refresh
            </Button>
          </Box>

          <Grid container spacing={2}>
            {activeWebhooks.map((webhook) => (
              <Grid item xs={12} md={6} key={webhook.id}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    borderColor: 'primary.main',
                    bgcolor: 'primary.50',
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Typography variant="h6" fontWeight={600} noWrap sx={{ maxWidth: 300 }}>
                            {webhook.url}
                          </Typography>
                          <Chip
                            icon={<CheckCircleIcon fontSize="small" />}
                            label="Active"
                            color="success"
                            size="small"
                          />
                        </Box>

                        <Tooltip title={webhook.url}>
                          <Typography
                            variant="body2"
                            sx={{
                              fontFamily: 'monospace',
                              color: 'text.secondary',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {webhook.url}
                          </Typography>
                        </Tooltip>
                      </Box>

                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <Tooltip title="View Delivery Logs">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedWebhook(webhook);
                              setLogsDialogOpen(true);
                            }}
                          >
                            <VisibilityIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={webhook.is_active ? 'Disable' : 'Enable'}>
                          <IconButton
                            size="small"
                            onClick={() => handleToggle(webhook)}
                            disabled={!!togglingWebhookId}
                          >
                            {togglingWebhookId === webhook.id ? (
                              <CircularProgress size={16} />
                            ) : webhook.is_active ? (
                              <PauseIcon fontSize="small" />
                            ) : (
                              <PlayArrowIcon fontSize="small" />
                            )}
                          </IconButton>
                        </Tooltip>
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuOpen(e, webhook)}
                        >
                          <MoreVertIcon />
                        </IconButton>
                      </Box>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Stack spacing={1.5}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Events ({webhook.events.length})
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                          {webhook.events.slice(0, 3).map((event) => {
                            const eventInfo = getEventTypeInfo(event);
                            return (
                              <Chip
                                key={event}
                                label={eventInfo.label}
                                color={eventInfo.color}
                                size="small"
                                variant="outlined"
                              />
                            );
                          })}
                          {webhook.events.length > 3 && (
                            <Chip label={`+${webhook.events.length - 3}`} size="small" variant="outlined" />
                          )}
                        </Box>
                      </Box>

                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Last Delivery
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 0.5 }}>
                            {formatDate(webhook.last_delivery_at)}
                          </Typography>
                        </Box>
                        {webhook.failure_count > 0 && (
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Failures
                            </Typography>
                            <Typography variant="body2" sx={{ mt: 0.5 }} color="error">
                              {webhook.failure_count}
                            </Typography>
                          </Box>
                        )}
                      </Box>

                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Created
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                          {formatDate(webhook.created_at)}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Inactive Webhooks Section */}
      {inactiveWebhooks.length > 0 && (
        <Box>
          <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
            Inactive Webhooks ({inactiveWebhooks.length})
          </Typography>

          <Grid container spacing={2}>
            {inactiveWebhooks.map((webhook) => (
              <Grid item xs={12} md={6} key={webhook.id}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    opacity: 0.7,
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Typography variant="h6" fontWeight={600} noWrap sx={{ maxWidth: 300 }}>
                            {webhook.url}
                          </Typography>
                          <Chip label="Inactive" color="default" size="small" />
                        </Box>

                        <Tooltip title={webhook.url}>
                          <Typography
                            variant="body2"
                            sx={{
                              fontFamily: 'monospace',
                              color: 'text.secondary',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {webhook.url}
                          </Typography>
                        </Tooltip>
                      </Box>

                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <Tooltip title="View Delivery Logs">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedWebhook(webhook);
                              setLogsDialogOpen(true);
                            }}
                          >
                            <VisibilityIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={webhook.is_active ? 'Disable' : 'Enable'}>
                          <IconButton
                            size="small"
                            onClick={() => handleToggle(webhook)}
                            disabled={!!togglingWebhookId}
                          >
                            {togglingWebhookId === webhook.id ? (
                              <CircularProgress size={16} />
                            ) : webhook.is_active ? (
                              <PauseIcon fontSize="small" />
                            ) : (
                              <PlayArrowIcon fontSize="small" />
                            )}
                          </IconButton>
                        </Tooltip>
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuOpen(e, webhook)}
                        >
                          <MoreVertIcon />
                        </IconButton>
                      </Box>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Stack spacing={1.5}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Events ({webhook.events.length})
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                          {webhook.events.slice(0, 3).map((event) => {
                            const eventInfo = getEventTypeInfo(event);
                            return (
                              <Chip
                                key={event}
                                label={eventInfo.label}
                                color={eventInfo.color}
                                size="small"
                                variant="outlined"
                              />
                            );
                          })}
                          {webhook.events.length > 3 && (
                            <Chip label={`+${webhook.events.length - 3}`} size="small" variant="outlined" />
                          )}
                        </Box>
                      </Box>

                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Created
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                          {formatDate(webhook.created_at)}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleViewLogs}>
          <VisibilityIcon fontSize="small" sx={{ mr: 1 }} />
          View Delivery Logs
        </MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          Delete Webhook
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Webhook?</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to delete this webhook subscription?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            This action will immediately stop event deliveries to this endpoint. You will need to
            create a new subscription to resume receiving events. This action cannot be undone.
          </Typography>
          <Box sx={{ mt: 2, p: 1.5, bgcolor: 'background.paper', borderRadius: 1 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              {selectedWebhook?.url}
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={!!deletingWebhookId}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={!!deletingWebhookId}
            startIcon={deletingWebhookId ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {deletingWebhookId ? 'Deleting...' : 'Delete Webhook'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delivery Logs Dialog */}
      {selectedWebhook && (
        <DeliveryLogsDialog
          open={logsDialogOpen}
          onClose={() => setLogsDialogOpen(false)}
          subscriptionId={selectedWebhook.id}
          subscriptionUrl={selectedWebhook.url}
        />
      )}
    </Stack>
  );
};

export default WebhookList;
