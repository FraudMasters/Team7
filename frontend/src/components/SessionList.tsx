import React, { useState, useEffect } from 'react';
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Avatar,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Computer as DesktopIcon,
  Phone as MobileIcon,
  Tablet as TabletIcon,
  Help as UnknownIcon,
  Delete as DeleteIcon,
  Cancel as CancelIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { formatDistanceToNow, format } from 'date-fns';
import { sessionsClient } from '@/api/sessions';
import type { SessionItem } from '@/types/api';

/**
 * SessionList Component Props
 */
interface SessionListProps {
  /** User ID to filter sessions for (optional) */
  userId?: string;
  /** Whether to show only active sessions */
  isActiveOnly?: boolean;
  /** Auto-refresh interval in milliseconds (0 to disable) */
  refreshInterval?: number;
  /** Callback when session is revoked */
  onSessionRevoked?: (sessionId: string) => void;
}

/**
 * Get device icon for device type
 */
const getDeviceIcon = (deviceType: SessionItem['device_type']) => {
  switch (deviceType) {
    case 'desktop':
      return <DesktopIcon />;
    case 'mobile':
      return <MobileIcon />;
    case 'tablet':
      return <TabletIcon />;
    default:
      return <UnknownIcon />;
  }
};

/**
 * Get device type color
 */
const getDeviceTypeColor = (deviceType: SessionItem['device_type']): 'success' | 'info' | 'warning' | 'default' => {
  switch (deviceType) {
    case 'desktop':
      return 'success';
    case 'mobile':
      return 'info';
    case 'tablet':
      return 'warning';
    default:
      return 'default';
  }
};

/**
 * SessionList Component
 *
 * Displays a list of active user sessions with device information,
 * IP addresses, and activity tracking. Supports revoking sessions
 * and distinguishing the current session from others.
 *
 * @example
 * ```tsx
 * <SessionList
 *   userId="user-123"
 *   isActiveOnly={true}
 *   refreshInterval={30000}
 *   onSessionRevoked={(id) => console.log('Revoked:', id)}
 * />
 * ```
 */
const SessionList: React.FC<SessionListProps> = ({
  userId,
  isActiveOnly = true,
  refreshInterval = 0,
  onSessionRevoked,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [revokeDialogOpen, setRevokeDialogOpen] = useState(false);
  const [sessionToRevoke, setSessionToRevoke] = useState<SessionItem | null>(null);
  const [revokingSessionId, setRevokingSessionId] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({ open: false, message: '', severity: 'success' });

  /**
   * Fetch sessions from API
   */
  const fetchSessions = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await sessionsClient.listSessions({
        user_id: userId,
        is_active: isActiveOnly,
        limit: 100,
      });

      setSessions(response.sessions);
      setTotalCount(response.total_count);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load sessions';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Revoke a session
   */
  const handleRevokeSession = async (session: SessionItem) => {
    setRevokingSessionId(session.id);
    setRevokeDialogOpen(false);

    try {
      await sessionsClient.revokeSession(session.id, 'user_revoked');

      // Remove from local state
      setSessions((prev) => prev.filter((s) => s.id !== session.id));
      setTotalCount((prev) => prev - 1);

      // Show success message
      setSnackbar({
        open: true,
        message: 'Session revoked successfully',
        severity: 'success',
      });

      // Notify parent
      if (onSessionRevoked) {
        onSessionRevoked(session.id);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to revoke session';
      setSnackbar({
        open: true,
        message: errorMessage,
        severity: 'error',
      });
    } finally {
      setRevokingSessionId(null);
      setSessionToRevoke(null);
    }
  };

  /**
   * Open revoke confirmation dialog
   */
  const openRevokeDialog = (session: SessionItem) => {
    if (session.is_current) {
      setSnackbar({
        open: true,
        message: 'Cannot revoke current session',
        severity: 'error',
      });
      return;
    }
    setSessionToRevoke(session);
    setRevokeDialogOpen(true);
  };

  /**
   * Close revoke dialog
   */
  const closeRevokeDialog = () => {
    setRevokeDialogOpen(false);
    setSessionToRevoke(null);
  };

  /**
   * Refresh sessions
   */
  const handleRefresh = () => {
    fetchSessions();
  };

  // Initial fetch and auto-refresh
  useEffect(() => {
    fetchSessions();

    if (refreshInterval > 0) {
      const interval = setInterval(fetchSessions, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [userId, isActiveOnly, refreshInterval]);

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
          Loading sessions...
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
          <Button color="inherit" onClick={fetchSessions} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <Typography variant="subtitle1" fontWeight={600}>
          Failed to Load Sessions
        </Typography>
        <Typography variant="body2">{error}</Typography>
      </Alert>
    );
  }

  /**
   * Render empty state
   */
  if (sessions.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" fontWeight={600}>
          No Active Sessions
        </Typography>
        <Typography variant="body2">
          {isActiveOnly
            ? 'No active sessions found. Sessions appear here when you log in.'
            : 'No sessions found.'}
        </Typography>
      </Alert>
    );
  }

  /**
   * Render session card for mobile view
   */
  const SessionCard: React.FC<{ session: SessionItem }> = ({ session }) => (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        border: session.is_current ? 2 : 1,
        borderColor: session.is_current ? 'success.main' : 'divider',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Avatar
          sx={{
            mr: 2,
            bgcolor: `${getDeviceTypeColor(session.device_type)}.main`,
            width: 48,
            height: 48,
          }}
        >
          {getDeviceIcon(session.device_type)}
        </Avatar>
        <Box sx={{ flex: 1 }}>
          <Typography variant="subtitle1" fontWeight={700}>
            {session.device_name || 'Unknown Device'}
            {session.is_current && (
              <Chip
                label="Current"
                size="small"
                color="success"
                sx={{ ml: 1 }}
              />
            )}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {session.device_type || 'unknown'} • {session.ip_address || 'Unknown IP'}
          </Typography>
        </Box>
      </Box>

      <Stack spacing={1}>
        {/* User Agent */}
        {session.user_agent && (
          <Typography variant="caption" color="text.secondary" noWrap>
            {session.user_agent}
          </Typography>
        )}

        {/* Location */}
        {session.location && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              📍 {session.location}
            </Typography>
          </Box>
        )}

        {/* Activity */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            Last active: {formatDistanceToNow(new Date(session.last_activity_at), { addSuffix: true })}
          </Typography>
        </Box>

        {/* Created */}
        <Typography variant="caption" color="text.secondary">
          Created: {format(new Date(session.created_at), 'MMM d, yyyy HH:mm')}
        </Typography>

        {/* Expires */}
        {session.expires_at && (
          <Typography variant="caption" color="text.secondary">
            Expires: {format(new Date(session.expires_at), 'MMM d, yyyy HH:mm')}
          </Typography>
        )}
      </Stack>

      {/* Revoke Button */}
      {!session.is_current && (
        <Button
          variant="outlined"
          color="error"
          size="small"
          startIcon={<DeleteIcon />}
          onClick={() => openRevokeDialog(session)}
          disabled={revokingSessionId === session.id}
          sx={{ mt: 2 }}
          fullWidth
        >
          {revokingSessionId === session.id ? 'Revoking...' : 'Revoke Session'}
        </Button>
      )}
    </Paper>
  );

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" fontWeight={600}>
              Active Sessions
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {totalCount} session{totalCount !== 1 ? 's' : ''} across all devices
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            size="small"
          >
            Refresh
          </Button>
        </Box>
      </Paper>

      {/* Desktop Table View */}
      <Box sx={{ display: { xs: 'none', md: 'block' } }}>
        <TableContainer component={Paper} elevation={1}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell
                  sx={{
                    fontWeight: 700,
                    bgcolor: 'grey.100',
                    minWidth: 200,
                  }}
                >
                  Device
                </TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>
                  IP Address
                </TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>
                  Location
                </TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 150 }}>
                  Last Activity
                </TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 150 }}>
                  Created
                </TableCell>
                <TableCell sx={{ fontWeight: 700, bgcolor: 'grey.100', minWidth: 120 }}>
                  Status
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 700, bgcolor: 'grey.100' }}>
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sessions.map((session) => (
                <TableRow
                  key={session.id}
                  sx={{
                    '&:nth-of-type(odd)': { bgcolor: 'action.hover' },
                    ...(session.is_current && {
                      bgcolor: 'success.50',
                    }),
                  }}
                >
                  {/* Device */}
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Avatar
                        sx={{
                          width: 32,
                          height: 32,
                          bgcolor: `${getDeviceTypeColor(session.device_type)}.main`,
                        }}
                      >
                        {getDeviceIcon(session.device_type)}
                      </Avatar>
                      <Box>
                        <Typography variant="body2" fontWeight={600}>
                          {session.device_name || 'Unknown Device'}
                        </Typography>
                        {session.user_agent && (
                          <Tooltip title={session.user_agent}>
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              sx={{
                                maxWidth: 150,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                                display: 'block',
                              }}
                            >
                              {session.user_agent}
                            </Typography>
                          </Tooltip>
                        )}
                      </Box>
                    </Box>
                  </TableCell>

                  {/* IP Address */}
                  <TableCell>
                    <Typography variant="body2">
                      {session.ip_address || 'Unknown'}
                    </Typography>
                  </TableCell>

                  {/* Location */}
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {session.location || 'Unknown'}
                    </Typography>
                  </TableCell>

                  {/* Last Activity */}
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {formatDistanceToNow(new Date(session.last_activity_at), {
                        addSuffix: true,
                      })}
                    </Typography>
                  </TableCell>

                  {/* Created */}
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {format(new Date(session.created_at), 'MMM d, yyyy')}
                    </Typography>
                    {session.expires_at && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        Expires: {format(new Date(session.expires_at), 'MMM d')}
                      </Typography>
                    )}
                  </TableCell>

                  {/* Status */}
                  <TableCell>
                    {session.is_current ? (
                      <Chip
                        label="Current"
                        color="success"
                        size="small"
                        icon={<CheckCircleIcon />}
                      />
                    ) : (
                      <Chip
                        label={session.is_active ? 'Active' : 'Inactive'}
                        color={session.is_active ? 'default' : 'default'}
                        size="small"
                      />
                    )}
                  </TableCell>

                  {/* Actions */}
                  <TableCell align="right">
                    {!session.is_current && (
                      <Tooltip title="Revoke this session">
                        <IconButton
                          color="error"
                          onClick={() => openRevokeDialog(session)}
                          disabled={revokingSessionId === session.id}
                        >
                          {revokingSessionId === session.id ? (
                            <CircularProgress size={20} />
                          ) : (
                            <DeleteIcon />
                          )}
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

      {/* Mobile Card View */}
      <Box sx={{ display: { xs: 'block', md: 'none' } }}>
        <Stack spacing={2}>
          {sessions.map((session) => (
            <SessionCard key={session.id} session={session} />
          ))}
        </Stack>
      </Box>

      {/* Revoke Confirmation Dialog */}
      <Dialog open={revokeDialogOpen} onClose={closeRevokeDialog}>
        <DialogTitle>Revoke Session?</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to revoke this session?
          </Typography>
          {sessionToRevoke && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="subtitle2" fontWeight={600}>
                {sessionToRevoke.device_name || 'Unknown Device'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {sessionToRevoke.device_type} • {sessionToRevoke.ip_address}
              </Typography>
              <Typography variant="caption" display="block" color="text.secondary">
                Last active: {formatDistanceToNow(new Date(sessionToRevoke.last_activity_at), { addSuffix: true })}
              </Typography>
            </Box>
          )}
          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body2">
              This will immediately log out the user from this device. They will need to sign in again to continue.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeRevokeDialog} startIcon={<CancelIcon />}>
            Cancel
          </Button>
          <Button
            onClick={() => sessionToRevoke && handleRevokeSession(sessionToRevoke)}
            color="error"
            variant="contained"
            startIcon={<DeleteIcon />}
          >
            Revoke
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Stack>
  );
};

export default SessionList;
