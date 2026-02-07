/**
 * API Key List Component
 *
 * Displays a list of API keys with actions for viewing, revoking, and managing them.
 *
 * @module components/developer/APIKeyList
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
  AlertTitle,
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
  Link,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  Delete as DeleteIcon,
  ContentCopy as ContentCopyIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { apiKeysClient, type APIKey } from '@/api/apiKeys';

interface APIKeyListProps {
  refreshTrigger?: number;
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
 * Format scopes for display
 */
const formatScopes = (scopes: string[]): string => {
  return scopes.map((s) => s.replace(/:/g, ' ').replace(/(^\w|\s\w)/g, (match) => match.toUpperCase())).join(', ');
};

/**
 * Check if key is expired
 */
const isExpired = (expiresAt: string | null): boolean => {
  if (!expiresAt) return false;
  return new Date(expiresAt) < new Date();
};

/**
 * APIKeyList Component
 *
 * Displays a grid/list of API keys with their metadata and actions:
 * - Key name and prefix
 * - Active/Revoked status
 * - Scopes
 * - Rate limits
 * - Last used and created dates
 * - Revoke action
 *
 * @example
 * ```tsx
 * <APIKeyList refreshTrigger={timestamp} />
 * ```
 */
const APIKeyList: React.FC<APIKeyListProps> = ({ refreshTrigger = 0 }) => {
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedKey, setSelectedKey] = useState<APIKey | null>(null);
  const [revokeDialogOpen, setRevokeDialogOpen] = useState(false);
  const [revokingKeyId, setRevokingKeyId] = useState<string | null>(null);
  const [showKeyPrefix, setShowKeyPrefix] = useState<Record<string, boolean>>({});
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);

  const fetchAPIKeys = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const keys = await apiKeysClient.listAPIKeys();
      setApiKeys(keys);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load API keys');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAPIKeys();
  }, [fetchAPIKeys, refreshTrigger]);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, key: APIKey) => {
    setAnchorEl(event.currentTarget);
    setSelectedKey(key);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedKey(null);
  };

  const handleRevokeClick = () => {
    setRevokeDialogOpen(true);
    handleMenuClose();
  };

  const handleRevokeConfirm = async () => {
    if (!selectedKey) return;

    setRevokingKeyId(selectedKey.id);
    setRevokeDialogOpen(false);

    try {
      await apiKeysClient.revokeAPIKey(selectedKey.id);
      await fetchAPIKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke API key');
    } finally {
      setRevokingKeyId(null);
      setSelectedKey(null);
    }
  };

  const handleCopyPrefix = (key: APIKey) => {
    const prefix = key.key_prefix;
    navigator.clipboard.writeText(prefix).then(() => {
      setCopiedKeyId(key.id);
      setTimeout(() => setCopiedKeyId(null), 2000);
    });
  };

  const toggleKeyVisibility = (keyId: string) => {
    setShowKeyPrefix((prev) => ({ ...prev, [keyId]: !prev[keyId] }));
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <Stack alignItems="center" spacing={2}>
          <CircularProgress size={48} />
          <Typography variant="body2" color="text.secondary">
            Loading API keys...
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
          <Button color="inherit" onClick={fetchAPIKeys} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Error Loading API Keys</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (apiKeys.length === 0) {
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
            No API Keys Yet
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create your first API key to start integrating with AgentHR
          </Typography>
        </Box>
      </Paper>
    );
  }

  const activeKeys = apiKeys.filter((k) => k.is_active && !isExpired(k.expires_at));
  const revokedKeys = apiKeys.filter((k) => !k.is_active);
  const expiredKeys = apiKeys.filter((k) => k.is_active && isExpired(k.expires_at));

  return (
    <Stack spacing={4}>
      {/* Active Keys Section */}
      {activeKeys.length > 0 && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" fontWeight={600}>
              Active Keys ({activeKeys.length})
            </Typography>
            <Button
              size="small"
              onClick={fetchAPIKeys}
              startIcon={<RefreshIcon />}
            >
              Refresh
            </Button>
          </Box>

          <Grid container spacing={2}>
            {activeKeys.map((key) => (
              <Grid item xs={12} md={6} key={key.id}>
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
                          <Typography variant="h6" fontWeight={600}>
                            {key.name}
                          </Typography>
                          <Chip
                            icon={<CheckCircleIcon fontSize="small" />}
                            label="Active"
                            color="success"
                            size="small"
                          />
                        </Box>

                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              fontFamily: 'monospace',
                              bgcolor: 'background.paper',
                              px: 1,
                              py: 0.5,
                              borderRadius: 0.5,
                            }}
                          >
                            {key.key_prefix}••••••••
                          </Typography>
                          <Tooltip
                            title={copiedKeyId === key.id ? 'Copied!' : 'Copy prefix'}
                          >
                            <IconButton
                              size="small"
                              onClick={() => handleCopyPrefix(key)}
                              color={copiedKeyId === key.id ? 'success' : 'default'}
                            >
                              <ContentCopyIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </Box>

                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, key)}
                      >
                        <MoreVertIcon />
                      </IconButton>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Stack spacing={1.5}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Scopes
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                          {formatScopes(key.scopes)}
                        </Typography>
                      </Box>

                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Created
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 0.5 }}>
                            {formatDate(key.created_at)}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Last Used
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 0.5 }}>
                            {formatDate(key.last_used_at)}
                          </Typography>
                        </Box>
                      </Box>

                      {key.expires_at && (
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Expires
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 0.5 }}>
                            {formatDate(key.expires_at)}
                          </Typography>
                        </Box>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Revoked Keys Section */}
      {revokedKeys.length > 0 && (
        <Box>
          <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
            Revoked Keys ({revokedKeys.length})
          </Typography>

          <Grid container spacing={2}>
            {revokedKeys.map((key) => (
              <Grid item xs={12} md={6} key={key.id}>
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
                          <Typography variant="h6" fontWeight={600}>
                            {key.name}
                          </Typography>
                          <Chip
                            icon={<CancelIcon fontSize="small" />}
                            label="Revoked"
                            color="error"
                            size="small"
                          />
                        </Box>

                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: 'monospace',
                            color: 'text.secondary',
                          }}
                        >
                          {key.key_prefix}••••••••
                        </Typography>
                      </Box>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Typography variant="caption" color="text.secondary">
                      Revoked on {formatDate(key.updated_at)}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Expired Keys Section */}
      {expiredKeys.length > 0 && (
        <Box>
          <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
            Expired Keys ({expiredKeys.length})
          </Typography>

          <Grid container spacing={2}>
            {expiredKeys.map((key) => (
              <Grid item xs={12} md={6} key={key.id}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    opacity: 0.7,
                    borderColor: 'warning.main',
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Typography variant="h6" fontWeight={600}>
                            {key.name}
                          </Typography>
                          <Chip label="Expired" color="warning" size="small" />
                        </Box>

                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: 'monospace',
                            color: 'text.secondary',
                          }}
                        >
                          {key.key_prefix}••••••••
                        </Typography>
                      </Box>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Typography variant="caption" color="text.secondary">
                      Expired on {formatDate(key.expires_at)}
                    </Typography>
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
        <MenuItem onClick={handleRevokeClick} sx={{ color: 'error.main' }}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          Revoke Key
        </MenuItem>
      </Menu>

      {/* Revoke Confirmation Dialog */}
      <Dialog open={revokeDialogOpen} onClose={() => setRevokeDialogOpen(false)}>
        <DialogTitle>Revoke API Key?</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to revoke <strong>"{selectedKey?.name}"</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            This action will immediately invalidate the API key. Any applications using this key
            will no longer be able to access the API. This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRevokeDialogOpen(false)} disabled={!!revokingKeyId}>
            Cancel
          </Button>
          <Button
            onClick={handleRevokeConfirm}
            color="error"
            variant="contained"
            disabled={!!revokingKeyId}
            startIcon={revokingKeyId ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {revokingKeyId ? 'Revoking...' : 'Revoke Key'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default APIKeyList;
