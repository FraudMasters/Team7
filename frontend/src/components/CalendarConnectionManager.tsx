/**
 * Calendar Connection Manager Component
 *
 * Manage calendar connections for interview scheduling.
 * Supports Google Calendar and Microsoft Outlook integration.
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
  Divider,
} from '@mui/material';
import {
  Event as EventIcon,
  Close as CloseIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  Link as LinkIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { calendarClient } from '../api/calendar';
import type {
  CalendarConnectionResponse,
  CalendarConnectionListResponse,
  CalendarProvider,
} from '../types/api';

interface CalendarConnectionManagerProps {
  recruiterId?: string;
  open?: boolean;
  onClose?: () => void;
  onSuccess?: (connection: CalendarConnectionResponse) => void;
}

const PROVIDER_CONFIG: Record<
  CalendarProvider,
  { label: string; icon: string; color: string; scopes: string[] }
> = {
  google: {
    label: 'Google Calendar',
    icon: 'G',
    color: '#4285F4',
    scopes: ['https://www.googleapis.com/auth/calendar.events'],
  },
  outlook: {
    label: 'Microsoft Outlook',
    icon: 'O',
    color: '#0078D4',
    scopes: ['Calendars.ReadWrite'],
  },
};

export function CalendarConnectionManager({
  recruiterId,
  open: controlledOpen,
  onClose,
  onSuccess,
}: CalendarConnectionManagerProps) {
  const queryClient = useQueryClient();
  const [internalOpen, setInternalOpen] = useState(true);
  const [connectingProvider, setConnectingProvider] = useState<CalendarProvider | null>(null);

  const open = controlledOpen !== undefined ? controlledOpen : internalOpen;

  // Fetch calendar connections
  const {
    data: connectionsData,
    isLoading: isLoadingConnections,
    error: connectionsError,
    refetch: refetchConnections,
  } = useQuery({
    queryKey: ['calendarConnections', recruiterId],
    queryFn: async () => {
      return await calendarClient.listConnections(
        recruiterId ? { recruiter_id: recruiterId } : undefined
      );
    },
    enabled: open,
  });

  // Create connection mutation (for OAuth callback handling)
  const createConnectionMutation = useMutation({
    mutationFn: async (provider: CalendarProvider) => {
      // Initiate OAuth flow by redirecting to backend OAuth endpoint
      const params = new URLSearchParams({
        provider,
        redirect_uri: window.location.origin + '/calendar/callback',
        state: JSON.stringify({ provider, recruiterId }),
      });

      // This would typically redirect to the OAuth provider
      // For now, we'll simulate the flow
      window.location.href = `/api/calendar/authorize?${params.toString()}`;

      // Return a placeholder (in real flow, this would be handled by callback)
      return {} as CalendarConnectionResponse;
    },
    onSuccess: (connection) => {
      queryClient.invalidateQueries({ queryKey: ['calendarConnections'] });
      if (onSuccess) {
        onSuccess(connection);
      }
    },
  });

  // Delete connection mutation
  const deleteConnectionMutation = useMutation({
    mutationFn: async (connectionId: string) => {
      await calendarClient.deleteConnection(connectionId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendarConnections'] });
    },
  });

  // Update connection mutation (for re-syncing)
  const updateConnectionMutation = useMutation({
    mutationFn: async (connectionId: string) => {
      return await calendarClient.updateConnection(connectionId, {
        status: 'active',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendarConnections'] });
    },
  });

  const handleClose = () => {
    if (onClose) {
      onClose();
    } else {
      setInternalOpen(false);
    }
  };

  const handleConnect = (provider: CalendarProvider) => {
    setConnectingProvider(provider);
    createConnectionMutation.mutate(provider);
  };

  const handleDisconnect = (connectionId: string, provider: CalendarProvider) => {
    if (window.confirm(`Are you sure you want to disconnect your ${PROVIDER_CONFIG[provider].label} account?`)) {
      deleteConnectionMutation.mutate(connectionId);
    }
  };

  const handleResync = (connectionId: string) => {
    updateConnectionMutation.mutate(connectionId);
  };

  const connections = connectionsData?.connections || [];

  const getProviderConnections = (provider: CalendarProvider) => {
    return connections.filter((c) => c.provider === provider);
  };

  const getConnectionStatus = (connection: CalendarConnectionResponse) => {
    const statusConfig = {
      active: { label: 'Connected', color: 'success' as const, icon: <CheckIcon /> },
      expired: { label: 'Expired', color: 'error' as const, icon: <ErrorIcon /> },
      error: { label: 'Error', color: 'error' as const, icon: <ErrorIcon /> },
      disconnected: { label: 'Disconnected', color: 'default' as const, icon: null },
    };

    return statusConfig[connection.status] || statusConfig.disconnected;
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={1}>
            <EventIcon color="primary" />
            <Typography variant="h6">Calendar Connections</Typography>
          </Stack>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Connect your calendar to enable interview scheduling, availability checking, and automatic
          event creation.
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {/* Google Calendar Section */}
          <Paper sx={{ p: 2 }}>
            <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
              <Stack direction="row" alignItems="center" spacing={1}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    bgcolor: PROVIDER_CONFIG.google.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: 'bold',
                  }}
                >
                  {PROVIDER_CONFIG.google.icon}
                </Box>
                <Typography variant="subtitle1" fontWeight="medium">
                  {PROVIDER_CONFIG.google.label}
                </Typography>
              </Stack>
              <Button
                variant="outlined"
                startIcon={<LinkIcon />}
                onClick={() => handleConnect('google')}
                disabled={createConnectionMutation.isPending || getProviderConnections('google').length > 0}
                size="small"
              >
                {createConnectionMutation.isPending && connectingProvider === 'google'
                  ? 'Connecting...'
                  : 'Connect'}
              </Button>
            </Stack>

            {getProviderConnections('google').length > 0 ? (
              <Stack spacing={1}>
                {getProviderConnections('google').map((connection) => {
                  const status = getConnectionStatus(connection);
                  return (
                    <Box
                      key={connection.id}
                      sx={{
                        p: 1.5,
                        bgcolor: 'grey.50',
                        borderRadius: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <Chip
                          label={status.label}
                          color={status.color}
                          size="small"
                          icon={status.icon}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {connection.calendar_email}
                        </Typography>
                        {connection.last_sync_at && (
                          <Typography variant="caption" color="text.secondary">
                            Synced {new Date(connection.last_sync_at).toLocaleDateString()}
                          </Typography>
                        )}
                      </Stack>
                      <Stack direction="row" spacing={0.5}>
                        <IconButton
                          size="small"
                          onClick={() => handleResync(connection.id)}
                          disabled={updateConnectionMutation.isPending}
                          title="Re-sync"
                        >
                          <RefreshIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDisconnect(connection.id, 'google')}
                          disabled={deleteConnectionMutation.isPending}
                          color="error"
                          title="Disconnect"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Stack>
                    </Box>
                  );
                })}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No Google Calendar account connected
              </Typography>
            )}
          </Paper>

          {/* Outlook Calendar Section */}
          <Paper sx={{ p: 2 }}>
            <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
              <Stack direction="row" alignItems="center" spacing={1}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    bgcolor: PROVIDER_CONFIG.outlook.color,
                    color: 'white',
                    fontWeight: 'bold',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {PROVIDER_CONFIG.outlook.icon}
                </Box>
                <Typography variant="subtitle1" fontWeight="medium">
                  {PROVIDER_CONFIG.outlook.label}
                </Typography>
              </Stack>
              <Button
                variant="outlined"
                startIcon={<LinkIcon />}
                onClick={() => handleConnect('outlook')}
                disabled={createConnectionMutation.isPending || getProviderConnections('outlook').length > 0}
                size="small"
              >
                {createConnectionMutation.isPending && connectingProvider === 'outlook'
                  ? 'Connecting...'
                  : 'Connect'}
              </Button>
            </Stack>

            {getProviderConnections('outlook').length > 0 ? (
              <Stack spacing={1}>
                {getProviderConnections('outlook').map((connection) => {
                  const status = getConnectionStatus(connection);
                  return (
                    <Box
                      key={connection.id}
                      sx={{
                        p: 1.5,
                        bgcolor: 'grey.50',
                        borderRadius: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <Chip
                          label={status.label}
                          color={status.color}
                          size="small"
                          icon={status.icon}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {connection.calendar_email}
                        </Typography>
                        {connection.last_sync_at && (
                          <Typography variant="caption" color="text.secondary">
                            Synced {new Date(connection.last_sync_at).toLocaleDateString()}
                          </Typography>
                        )}
                      </Stack>
                      <Stack direction="row" spacing={0.5}>
                        <IconButton
                          size="small"
                          onClick={() => handleResync(connection.id)}
                          disabled={updateConnectionMutation.isPending}
                          title="Re-sync"
                        >
                          <RefreshIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDisconnect(connection.id, 'outlook')}
                          disabled={deleteConnectionMutation.isPending}
                          color="error"
                          title="Disconnect"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Stack>
                    </Box>
                  );
                })}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No Outlook account connected
              </Typography>
            )}
          </Paper>

          {/* Loading State */}
          {isLoadingConnections && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
              <CircularProgress />
            </Box>
          )}

          {/* Error State */}
          {connectionsError && (
            <Alert severity="error">
              Failed to load calendar connections. Please try again.
            </Alert>
          )}

          {/* Info Alert */}
          <Alert severity="info">
            <Typography variant="body2">
              Connecting your calendar allows the system to:
            </Typography>
            <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
              <li>Check interviewer availability when scheduling interviews</li>
              <li>Automatically create calendar events for scheduled interviews</li>
              <li>Detect scheduling conflicts before booking</li>
              <li>Send calendar invites to all participants</li>
            </ul>
          </Alert>
        </Stack>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={createConnectionMutation.isPending}>
          Close
        </Button>
        <Button
          onClick={() => refetchConnections()}
          startIcon={<RefreshIcon />}
          disabled={isLoadingConnections}
          variant="outlined"
        >
          Refresh
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default CalendarConnectionManager;
