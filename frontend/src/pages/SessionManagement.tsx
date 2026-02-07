/**
 * Session Management Page
 *
 * Provides comprehensive session management functionality including:
 * - List of all active user sessions
 * - Device information and last activity timestamps
 * - Revoke individual sessions
 * - Revoke all sessions (with option to exclude current)
 * - Current session highlighting
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
  LinearProgress,
  Tooltip,
  Grid,
  IconButton,
  Stack,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  ExitToApp as RevokeIcon,
  DeleteForever as DeleteAllIcon,
  Security as SecurityIcon,
  Computer as DesktopIcon,
  Phone as MobileIcon,
  Tablet as TabletIcon,
  Help as UnknownIcon,
  LocationOn as LocationIcon,
  AccessTime as TimeIcon,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';
import sessionApi from '../services/sessionApi';
import type { SessionItem } from '@/types/api';

const SessionManagementPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentUserId, setCurrentUserId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Dialog states
  const [revokeDialogOpen, setRevokeDialogOpen] = useState(false);
  const [revokeAllDialogOpen, setRevokeAllDialogOpen] = useState(false);
  const [selectedSession, setSelectedSession] = useState<SessionItem | null>(null);

  const fetchSessions = useCallback(async () => {
    try {
      setLoading(true);
      const response = await sessionApi.getSessions({
        is_active: true,
        limit: 100,
      });
      setSessions(response.sessions);
      setTotalCount(response.total_count);

      // Store current user ID for revoke all functionality
      if (response.sessions.length > 0) {
        setCurrentUserId(response.sessions[0].user_id);
      }

      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch sessions';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleRevokeSession = async () => {
    if (!selectedSession) return;

    try {
      await sessionApi.revokeSession(selectedSession.id, 'user_revoked');
      setSuccess(`Session from ${selectedSession.device_name || 'Unknown Device'} has been revoked.`);
      setRevokeDialogOpen(false);
      setSelectedSession(null);
      fetchSessions();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to revoke session';
      setError(message);
    }
  };

  const handleRevokeAll = async () => {
    if (!currentUserId) return;

    try {
      const result = await sessionApi.revokeAllSessions({
        user_id: currentUserId,
        exclude_current: true,
        reason: 'user_revoked_all',
      });
      setSuccess(`Successfully revoked ${result.revoked_count} session(s). Your current session remains active.`);
      setRevokeAllDialogOpen(false);
      fetchSessions();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to revoke all sessions';
      setError(message);
    }
  };

  const openRevokeDialog = (session: SessionItem) => {
    setSelectedSession(session);
    setRevokeDialogOpen(true);
  };

  const getDeviceIcon = (deviceType: string | null) => {
    switch (deviceType) {
      case 'desktop':
        return <DesktopIcon fontSize="small" />;
      case 'mobile':
        return <MobileIcon fontSize="small" />;
      case 'tablet':
        return <TabletIcon fontSize="small" />;
      default:
        return <UnknownIcon fontSize="small" />;
    }
  };

  const getDeviceTypeColor = (deviceType: string | null): 'success' | 'info' | 'warning' | 'error' | 'default' => {
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

  if (loading && sessions.length === 0) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ width: '100%', mt: 4 }}>
          <LinearProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <SecurityIcon fontSize="large" color="primary" />
          <Typography variant="h4" fontWeight={600}>
            Session Management
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchSessions}
            disabled={loading}
          >
            Refresh
          </Button>
          {sessions.length > 1 && (
            <Button
              variant="contained"
              color="error"
              startIcon={<DeleteAllIcon />}
              onClick={() => setRevokeAllDialogOpen(true)}
              disabled={loading || totalCount <= 1}
            >
              Revoke All Other Sessions
            </Button>
          )}
        </Stack>
      </Box>

      {/* Error/Success Messages */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Info Alert */}
      <Alert severity="info" sx={{ mb: 4 }}>
        <Typography variant="body2">
          Manage your active sessions across all devices. You can revoke individual sessions or sign out from all other devices at once.
        </Typography>
      </Alert>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <SecurityIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Active Sessions
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {totalCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <DesktopIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Desktop Sessions
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {sessions.filter((s) => s.device_type === 'desktop').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <MobileIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Mobile Sessions
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {sessions.filter((s) => s.device_type === 'mobile' || s.device_type === 'tablet').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Sessions Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Device</TableCell>
                  <TableCell>Location</TableCell>
                  <TableCell>Last Activity</TableCell>
                  <TableCell>Expires</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sessions.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                      <Typography color="text.secondary">
                        No active sessions found.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  sessions.map((session) => (
                    <TableRow
                      key={session.id}
                      hover
                      sx={{
                        backgroundColor: session.is_current ? 'action.selected' : 'inherit',
                      }}
                    >
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box sx={{ color: 'text.secondary' }}>
                            {getDeviceIcon(session.device_type)}
                          </Box>
                          <Box>
                            <Typography variant="body2" fontWeight={500}>
                              {session.device_name || 'Unknown Device'}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <Chip
                                label={session.device_type || 'Unknown'}
                                size="small"
                                color={getDeviceTypeColor(session.device_type)}
                              />
                              {session.is_current && (
                                <Chip
                                  label="Current"
                                  size="small"
                                  color="primary"
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {session.location ? (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <LocationIcon fontSize="small" color="disabled" />
                            <Typography variant="body2">{session.location}</Typography>
                          </Box>
                        ) : (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <LocationIcon fontSize="small" color="disabled" />
                            <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                              {session.ip_address || '-'}
                            </Typography>
                          </Box>
                        )}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <TimeIcon fontSize="small" color="disabled" />
                          <Box>
                            <Typography variant="body2">
                              {formatDistanceToNow(new Date(session.last_activity_at), {
                                addSuffix: true,
                              })}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {format(new Date(session.last_activity_at), 'MMM dd, HH:mm')}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {session.expires_at ? (
                          <Typography variant="body2">
                            {format(new Date(session.expires_at), 'MMM dd, HH:mm')}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Never
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={session.is_active ? 'Active' : 'Inactive'}
                          size="small"
                          color={session.is_active ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        {!session.is_current && (
                          <Tooltip title="Revoke this session">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => openRevokeDialog(session)}
                            >
                              <RevokeIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Revoke Session Dialog */}
      <Dialog
        open={revokeDialogOpen}
        onClose={() => {
          setRevokeDialogOpen(false);
          setSelectedSession(null);
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Revoke Session?</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to revoke the session from:
          </Typography>
          {selectedSession && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" fontWeight={500}>
                {selectedSession.device_name || 'Unknown Device'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {selectedSession.location || selectedSession.ip_address || 'Unknown Location'}
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block">
                Last active: {formatDistanceToNow(new Date(selectedSession.last_activity_at), { addSuffix: true })}
              </Typography>
            </Box>
          )}
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            This will sign out the user from this device immediately. They will need to log in again to access their account.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setRevokeDialogOpen(false);
              setSelectedSession(null);
            }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleRevokeSession}
            startIcon={<RevokeIcon />}
          >
            Revoke Session
          </Button>
        </DialogActions>
      </Dialog>

      {/* Revoke All Sessions Dialog */}
      <Dialog
        open={revokeAllDialogOpen}
        onClose={() => setRevokeAllDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Revoke All Other Sessions?</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to revoke all other active sessions?
          </Typography>
          <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
            <Typography variant="body2" color="info.dark">
              This will revoke <strong>{totalCount - 1}</strong> other session(s).
            </Typography>
            <Typography variant="body2" color="info.dark" sx={{ mt: 1 }}>
              Your current session will remain active, and you will stay signed in on this device.
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            All other devices will be signed out immediately. Users will need to log in again to access their accounts.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRevokeAllDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleRevokeAll}
            startIcon={<DeleteAllIcon />}
          >
            Revoke All Sessions
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default SessionManagementPage;
