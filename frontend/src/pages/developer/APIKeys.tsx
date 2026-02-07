/**
 * API Keys Management Page
 *
 * Main page for managing API keys used to authenticate requests to the AgentHR API.
 *
 * @module pages/developer/APIKeys
 */

import React, { useState, useCallback } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  Stack,
  Grid,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  AlertTitle,
  Chip,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  VpnKey as VpnKeyIcon,
  ContentCopy as ContentCopyIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import APIKeyList from '@/components/developer/APIKeyList';
import CreateAPIKeyDialog from '@/components/developer/CreateAPIKeyDialog';

/**
 * APIKeys Page Component
 *
 * Provides a comprehensive interface for managing API keys:
 * - View all API keys (active, revoked, expired)
 * - Create new API keys with scopes and rate limits
 * - Revoke existing API keys
 * - Display usage statistics
 *
 * @example
 * ```tsx
 * // Routed at /developer/api-keys
 * import { APIKeys } from '@/pages/developer/APIKeys';
 * ```
 */
const APIKeys: React.FC = () => {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [newKeyDialog, setNewKeyDialog] = useState<{ key: string; message: string } | null>(null);

  const handleCreateKey = useCallback(() => {
    setCreateDialogOpen(true);
  }, []);

  const handleCreateSuccess = useCallback((response: { key: string; message: string }) => {
    setCreateDialogOpen(false);
    setNewKeyDialog(response);
    setRefreshTrigger((prev) => prev + 1);
  }, []);

  const handleCopyKey = useCallback(() => {
    if (newKeyDialog) {
      navigator.clipboard.writeText(newKeyDialog.key);
    }
  }, [newKeyDialog]);

  const handleNewKeyDialogClose = useCallback(() => {
    setNewKeyDialog(null);
  }, []);

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            API Keys
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage API keys for authenticating requests to AgentHR
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateKey}
          size="large"
        >
          Create API Key
        </Button>
      </Stack>

      {/* Info Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
              border: '1px solid',
              borderColor: 'primary.main',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                  }}
                >
                  <VpnKeyIcon />
                </Box>
                <Box>
                  <Typography variant="h5" fontWeight={700}>
                    3
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Keys
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
              border: '1px solid',
              borderColor: 'success.main',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                  }}
                >
                  <CheckCircleIcon />
                </Box>
                <Box>
                  <Typography variant="h5" fontWeight={700}>
                    15K
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Requests Today
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%)',
              border: '1px solid',
              borderColor: 'warning.main',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                  }}
                >
                  <VpnKeyIcon />
                </Box>
                <Box>
                  <Typography variant="h5" fontWeight={700}>
                    2
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Revoked Keys
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              height: '100%',
              background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%)',
              border: '1px solid',
              borderColor: 'error.main',
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                  }}
                >
                  <VpnKeyIcon />
                </Box>
                <Box>
                  <Typography variant="h5" fontWeight={700}>
                    1
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Expired Keys
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Getting Started Section */}
      <Paper sx={{ p: 3, mb: 4, border: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Getting Started with API Keys
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          API keys are used to authenticate your requests to the AgentHR API. Include your key
          in the <code>X-API-Key</code> header with each request.
        </Typography>

        <Box
          sx={{
            bgcolor: 'background.paper',
            p: 2,
            borderRadius: 1,
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            mb: 2,
            border: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Typography variant="body2" component="pre" sx={{ m: 0 }}>
{`curl -X GET "https://api.agenthr.com/api/candidates" \\
  -H "X-API-Key: your_api_key_here"`}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip label="Authentication" size="small" variant="outlined" />
          <Chip label="Rate Limiting" size="small" variant="outlined" />
          <Chip label="Scopes" size="small" variant="outlined" />
        </Box>
      </Paper>

      {/* API Keys List */}
      <APIKeyList refreshTrigger={refreshTrigger} />

      {/* Create API Key Dialog */}
      <CreateAPIKeyDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={handleCreateSuccess}
      />

      {/* New Key Display Dialog */}
      <Dialog open={!!newKeyDialog} onClose={handleNewKeyDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CheckCircleIcon color="success" sx={{ fontSize: 32 }} />
            <Box>
              <Typography variant="h6" fontWeight={600}>
                API Key Created Successfully
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Your new API key is ready to use
              </Typography>
            </Box>
          </Box>
        </DialogTitle>

        <DialogContent>
          <Stack spacing={3}>
            <Alert severity="warning">
              <AlertTitle>Save This Key Now!</AlertTitle>
              {newKeyDialog?.message || 'This key will not be shown again. Make sure to copy and store it securely.'}
            </Alert>

            <Box>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                Your API Key
              </Typography>
              <Box
                sx={{
                  bgcolor: 'background.paper',
                  p: 2,
                  borderRadius: 1,
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  wordBreak: 'break-all',
                  border: '2px solid',
                  borderColor: 'primary.main',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 1,
                }}
              >
                <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                  {newKeyDialog?.key}
                </Typography>
                <Button
                  size="small"
                  variant="contained"
                  onClick={handleCopyKey}
                  startIcon={<ContentCopyIcon />}
                >
                  Copy
                </Button>
              </Box>
            </Box>

            <Divider />

            <Box>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                How to Use Your API Key
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Include this key in the <code>X-API-Key</code> header when making requests to the AgentHR API:
              </Typography>
              <Box
                sx={{
                  bgcolor: 'background.paper',
                  p: 2,
                  borderRadius: 1,
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  border: '1px solid',
                  borderColor: 'divider',
                }}
              >
                <Typography variant="body2" component="pre" sx={{ m: 0 }}>
{`X-API-Key: ${newKeyDialog?.key?.substring(0, 20)}...`}
                </Typography>
              </Box>
            </Box>
          </Stack>
        </DialogContent>

        <DialogActions>
          <Button
            onClick={handleNewKeyDialogClose}
            variant="contained"
            startIcon={<CheckCircleIcon />}
          >
            I've Saved My Key
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default APIKeys;
