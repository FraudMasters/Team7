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
  const [oauthError, setOauthError] = useState<string | null>(null);
  const [oauthSuccess, setOauthSuccess] = useState<boolean>(false);

  const open = controlledOpen !== undefined ? controlledOpen : internalOpen;

  // Check for OAuth callback on mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const success = urlParams.get('success');

    if (error) {
      setOauthError(decodeURIComponent(error));
      setConnectingProvider(null);
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
    }

    if (success === 'true') {
      setOauthSuccess(true);
      setConnectingProvider(null);
      // Refetch connections to show new connection
      refetchConnections();
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  // Fetch calendar connections
  const {
    data: connectionsData,
    isLoading: isLoadingConnections,
    error: connectionsError,
    refetch: refetchConnections,
  } = useQuery({
    queryKey: ['calendarConnections', recruiterId],
    queryFn: async () => {
      const response = await calendarClient.listConnections(
        recruiterId ? { recruiter_id: recruiterId } : undefined
      );
      return {
        connections: Array.isArray(response) ? response : response.connections || [],
        total_count: Array.isArray(response) ? response.length : response.total_count || 0,
      };
    },
    enabled: open,
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

    // Build OAuth authorization URL
    const apiBaseUrl = import.meta.env.VITE_API_URL || '';
    const oauthUrl = `${apiBaseUrl}/api/oauth/${provider}/authorize`;

    // Add recruiter_id as query parameter
    const params = new URLSearchParams();
    if (recruiterId) {
      params.append('recruiter_id', recruiterId);
    } else {
      // If no recruiter ID is provided, use a default or current user
      // TODO: Get current user ID from auth context
      params.append('recruiter_id', 'default-recruiter-id');
    }

    // Redirect to OAuth authorization endpoint
    const fullUrl = `${oauthUrl}?${params.toString()}`;
    window.location.href = fullUrl;
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
          {/* OAuth Success Alert */}
          {oauthSuccess && (
            <Alert severity="success" onClose={() => setOauthSuccess(false)}>
              Calendar connected successfully! Your calendar is now linked to AgentHR.
            </Alert>
          )}

          {/* OAuth Error Alert */}
          {oauthError && (
            <Alert severity="error" onClose={() => setOauthError(null)}>
              Failed to connect calendar: {oauthError}
            </Alert>
          )}

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
                startIcon={connectingProvider === 'google' ? <CircularProgress size={16} /> : <LinkIcon />}
                onClick={() => handleConnect('google')}
                disabled={connectingProvider !== null || getProviderConnections('google').length > 0}
                size="small"
              >
                {connectingProvider === 'google' ? 'Connecting...' : 'Connect'}
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
                startIcon={connectingProvider === 'outlook' ? <CircularProgress size={16} /> : <LinkIcon />}
                onClick={() => handleConnect('outlook')}
                disabled={connectingProvider !== null || getProviderConnections('outlook').length > 0}
                size="small"
              >
                {connectingProvider === 'outlook' ? 'Connecting...' : 'Connect'}
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
        <Button onClick={handleClose} disabled={connectingProvider !== null}>
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
