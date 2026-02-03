/**
 * Job Board Integrations Page
 *
 * Manage job board integrations for automatic resume importing.
 * Supports Indeed, ZipRecruiter, Glassdoor, and custom webhook integrations.
 */

import { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Stack,
  Grid2,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Alert,
  CircularProgress,
  Menu,
  MenuItem,
  Switch,
  Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  CloudUpload as CloudUploadIcon,
  Sync as SyncIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobIntegrationsClient } from '../../api/jobIntegrations';
import { useBreakpoints } from '../../hooks/useBreakpoints';
import { JobIntegrationForm } from '../../components/JobIntegrationForm';
import type { JobBoardIntegrationResponse } from '../../types/api';

export function JobIntegrationsPage() {
  const queryClient = useQueryClient();
  const { isMobile } = useBreakpoints();

  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<JobBoardIntegrationResponse | null>(null);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const {
    data: integrationsData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['job-integrations'],
    queryFn: async () => {
      return await jobIntegrationsClient.listIntegrations(0, 100);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await jobIntegrationsClient.deleteIntegration(id);
    },
    onSuccess: () => {
      setDeleteDialogOpen(false);
      setSelectedIntegration(null);
      queryClient.invalidateQueries({ queryKey: ['job-integrations'] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: async (id: string) => {
      return await jobIntegrationsClient.toggleIntegration(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-integrations'] });
    },
  });

  const importMutation = useMutation({
    mutationFn: async (id: string) => {
      return await jobIntegrationsClient.triggerManualImport(id);
    },
    onSuccess: (data) => {
      setSnackbar({
        open: true,
        message: `Import triggered for ${data.integration_name}. Task ID: ${data.task_id}`,
        severity: 'success',
      });
      queryClient.invalidateQueries({ queryKey: ['job-integrations'] });
    },
    onError: (error: { detail?: string }) => {
      setSnackbar({
        open: true,
        message: error.detail || 'Failed to trigger import',
        severity: 'error',
      });
    },
  });

  const integrations = integrationsData?.integrations || [];
  const total = integrationsData?.total || 0;

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, integration: JobBoardIntegrationResponse) => {
    setMenuAnchor(event.currentTarget);
    setSelectedIntegration(integration);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedIntegration(null);
  };

  const handleEdit = () => {
    handleMenuClose();
    setFormDialogOpen(true);
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleToggle = () => {
    handleMenuClose();
    if (selectedIntegration) {
      toggleMutation.mutate(selectedIntegration.id);
    }
  };

  const handleCreateNew = () => {
    setSelectedIntegration(null);
    setFormDialogOpen(true);
  };

  const handleFormSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['job-integrations'] });
  };

  const handleDeleteConfirm = () => {
    if (selectedIntegration) {
      deleteMutation.mutate(selectedIntegration.id);
    }
  };

  const handleTriggerImport = (integrationId: string) => {
    importMutation.mutate(integrationId);
  };

  const maskApiKey = (key: string): string => {
    if (!key || key.length < 8) return '****';
    return `${key.substring(0, 4)}${'*'.repeat(8)}${key.substring(key.length - 4)}`;
  };

  const getBoardType = (name: string): string => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('indeed')) return 'Indeed';
    if (lowerName.includes('ziprecruiter')) return 'ZipRecruiter';
    if (lowerName.includes('glassdoor')) return 'Glassdoor';
    if (lowerName.includes('webhook')) return 'Webhook';
    return 'Custom';
  };

  const getBoardColor = (name: string): 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning' => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('indeed')) return 'primary';
    if (lowerName.includes('ziprecruiter')) return 'success';
    if (lowerName.includes('glassdoor')) return 'secondary';
    if (lowerName.includes('webhook')) return 'info';
    return 'default';
  };

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant={isMobile ? 'h5' : 'h4'} fontWeight={700}>
            Job Board Integrations
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {total} {total === 1 ? 'integration' : 'integrations'} configured
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateNew}
        >
          {isMobile ? 'Add' : 'Add Integration'}
        </Button>
      </Stack>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {(error as { detail?: string }).detail || 'Failed to load integrations.'}
        </Alert>
      )}

      {/* Empty State */}
      {!isLoading && integrations.length === 0 && (
        <Paper sx={{ p: 8, textAlign: 'center' }}>
          <CloudUploadIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No integrations configured
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Connect job boards to automatically import resumes
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateNew}
            sx={{ mt: 3 }}
          >
            Add Integration
          </Button>
        </Paper>
      )}

      {/* Loading State */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Integrations Grid */}
      {!isLoading && integrations.length > 0 && (
        <Grid2 container spacing={3}>
          {integrations.map((integration) => (
            <Grid2 key={integration.id} size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
              <Paper
                sx={{
                  p: 3,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
              >
                {/* Header with Menu */}
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 2 }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6" noWrap>
                      {integration.name}
                    </Typography>
                    <Chip
                      label={getBoardType(integration.name)}
                      color={getBoardColor(integration.name)}
                      size="small"
                      sx={{ mt: 1 }}
                    />
                  </Box>
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuOpen(e, integration)}
                    aria-label="Options"
                  >
                    <MoreVertIcon />
                  </IconButton>
                </Box>

                {/* API Endpoint */}
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    mb: 2,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                  }}
                >
                  {integration.api_endpoint}
                </Typography>

                {/* Status */}
                <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
                  <Chip
                    label={integration.enabled ? 'Active' : 'Disabled'}
                    color={integration.enabled ? 'success' : 'default'}
                    size="small"
                  />
                  {integration.last_sync_at && (
                    <Typography variant="caption" color="text.secondary">
                      Last sync: {new Date(integration.last_sync_at).toLocaleDateString()}
                    </Typography>
                  )}
                </Stack>

                {/* Actions */}
                <Box sx={{ mt: 2 }}>
                  <Button
                    fullWidth
                    variant="outlined"
                    size="small"
                    startIcon={<SyncIcon />}
                    onClick={() => handleTriggerImport(integration.id)}
                    disabled={!integration.enabled || importMutation.isPending}
                  >
                    {importMutation.isPending ? 'Importing...' : 'Import Now'}
                  </Button>
                </Box>

                {/* API Key (masked) */}
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    API Key: {maskApiKey(integration.api_key)}
                  </Typography>
                </Box>
              </Paper>
            </Grid2>
          ))}
        </Grid2>
      )}

      {/* Options Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleToggle}>
          <Switch checked={selectedIntegration?.enabled} size="small" sx={{ mr: 1 }} />
          {selectedIntegration?.enabled ? 'Disable' : 'Enable'}
        </MenuItem>
        <MenuItem onClick={handleEdit}>
          <EditIcon fontSize="small" sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Edit/Create Form Dialog */}
      <JobIntegrationForm
        open={formDialogOpen}
        onClose={() => setFormDialogOpen(false)}
        onSuccess={handleFormSuccess}
        integration={selectedIntegration}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Delete Integration</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Are you sure you want to delete "{selectedIntegration?.name}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This action cannot be undone. Import history will be preserved.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        message={snackbar.message}
      />
    </Container>
  );
}

export default JobIntegrationsPage;
