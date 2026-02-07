/**
 * SSO Configuration Page
 *
 * Provides comprehensive SSO provider management functionality including:
 * - List of all configured SAML SSO providers
 * - Add, edit, and delete provider configurations
 * - Enable/disable providers
 * - Provider type filtering (Okta, Azure AD, Google Workspace, Generic SAML)
 * - SAML metadata download
 * - Detailed provider inspection dialog
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Snackbar,
  LinearProgress,
  Tooltip,
  Grid,
  IconButton,
  Stack,
  Pagination,
  Switch,
  FormControlLabel,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  VpnKey as VpnKeyIcon,
  CloudDownload as CloudDownloadIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { ssoClient } from '@/api/sso';
import SSOConfigForm from '@/components/SSOConfigForm';
import type { SSOProviderItem } from '@/types/api';

interface FilterState {
  provider_type: string;
  is_enabled: string;
}

const SSOConfigPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [providers, setProviders] = useState<SSOProviderItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Pagination
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(50);

  // Filters
  const [filters, setFilters] = useState<FilterState>({
    provider_type: '',
    is_enabled: '',
  });

  // Dialog states
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<SSOProviderItem | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [providerToDelete, setProviderToDelete] = useState<SSOProviderItem | null>(null);

  const fetchProviders = useCallback(async () => {
    try {
      setLoading(true);
      const response = await ssoClient.listProviders(
        undefined, // organization_id
        filters.provider_type || undefined,
        filters.is_enabled !== '' ? filters.is_enabled === 'enabled' : undefined,
        rowsPerPage,
        (page - 1) * rowsPerPage
      );
      setProviders(response.providers);
      setTotalCount(response.total_count);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch SSO providers';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [filters, page, rowsPerPage]);

  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  const handleAddProvider = () => {
    setSelectedProvider(null);
    setFormDialogOpen(true);
  };

  const handleEditProvider = (provider: SSOProviderItem) => {
    setSelectedProvider(provider);
    setFormDialogOpen(true);
  };

  const handleDeleteClick = (provider: SSOProviderItem) => {
    setProviderToDelete(provider);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!providerToDelete) return;

    try {
      await ssoClient.deleteProvider(providerToDelete.id);
      setSuccess(`SSO provider "${providerToDelete.provider_name}" has been deleted.`);
      setDeleteDialogOpen(false);
      setProviderToDelete(null);
      fetchProviders();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to delete SSO provider';
      setError(message);
    }
  };

  const handleToggleEnabled = async (provider: SSOProviderItem) => {
    try {
      await ssoClient.updateProvider(provider.id, {
        is_enabled: !provider.is_enabled,
      });
      setSuccess(
        `SSO provider "${provider.provider_name}" has been ${provider.is_enabled ? 'disabled' : 'enabled'}.`
      );
      fetchProviders();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update SSO provider';
      setError(message);
    }
  };

  const handleFormSuccess = () => {
    setFormDialogOpen(false);
    setSelectedProvider(null);
    setSuccess(
      selectedProvider
        ? `SSO provider "${selectedProvider.provider_name}" has been updated.`
        : 'New SSO provider has been created.'
    );
    fetchProviders();
  };

  const handleClearFilters = () => {
    setFilters({
      provider_type: '',
      is_enabled: '',
    });
    setPage(1);
  };

  const getProviderTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      okta: 'Okta',
      azure_ad: 'Azure AD',
      google_workspace: 'Google Workspace',
      generic_saml: 'Generic SAML',
    };
    return labels[type] || type;
  };

  const getProviderTypeColor = (
    type: string
  ): 'primary' | 'info' | 'success' | 'default' => {
    const colors: Record<string, 'primary' | 'info' | 'success' | 'default'> = {
      okta: 'primary',
      azure_ad: 'info',
      google_workspace: 'success',
      generic_saml: 'default',
    };
    return colors[type] || 'default';
  };

  const downloadMetadata = async () => {
    try {
      const response = await ssoClient.getMetadata();
      const blob = new Blob([response.metadata], { type: 'application/xml;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `saml-sp-metadata-${format(new Date(), 'yyyy-MM-dd')}.xml`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setSuccess('SAML metadata has been downloaded.');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to download metadata';
      setError(message);
    }
  };

  if (loading && providers.length === 0) {
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
          <VpnKeyIcon fontSize="large" color="primary" />
          <Typography variant="h4" fontWeight={600}>
            SSO Configuration
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Button variant="outlined" startIcon={<CloudDownloadIcon />} onClick={downloadMetadata}>
            Download Metadata
          </Button>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchProviders} disabled={loading}>
            Refresh
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleAddProvider}>
            Add Provider
          </Button>
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
          Configure SAML 2.0 Single Sign-On (SSO) providers for enterprise authentication. Supported
          providers include Okta, Azure AD, Google Workspace, and generic SAML 2.0 identity
          providers. Download the metadata and import it into your IdP configuration.
        </Typography>
      </Alert>

      {/* Filters Card */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <SettingsIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Filters</Typography>
            {(filters.provider_type || filters.is_enabled) && (
              <Button size="small" onClick={handleClearFilters} sx={{ ml: 'auto' }}>
                Clear All
              </Button>
            )}
          </Box>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Provider Type</InputLabel>
                <Select
                  value={filters.provider_type}
                  onChange={(e) => {
                    setFilters({ ...filters, provider_type: e.target.value });
                    setPage(1);
                  }}
                  label="Provider Type"
                >
                  <MenuItem value="">
                    <em>All Types</em>
                  </MenuItem>
                  <MenuItem value="okta">Okta</MenuItem>
                  <MenuItem value="azure_ad">Azure AD</MenuItem>
                  <MenuItem value="google_workspace">Google Workspace</MenuItem>
                  <MenuItem value="generic_saml">Generic SAML</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={filters.is_enabled}
                  onChange={(e) => {
                    setFilters({ ...filters, is_enabled: e.target.value });
                    setPage(1);
                  }}
                  label="Status"
                >
                  <MenuItem value="">
                    <em>All Status</em>
                  </MenuItem>
                  <MenuItem value="enabled">Enabled</MenuItem>
                  <MenuItem value="disabled">Disabled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <VpnKeyIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Total Providers
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {totalCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CheckCircleIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Enabled
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {providers.filter((p) => p.is_enabled).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CancelIcon color="error" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Disabled
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {providers.filter((p) => !p.is_enabled).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <SettingsIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Showing
                </Typography>
              </Box>
              <Typography variant="body1" fontWeight={500}>
                {providers.length} of {totalCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* SSO Providers Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Provider Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Entity ID</TableCell>
                  <TableCell>SSO URL</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {providers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                      <Typography color="text.secondary">
                        No SSO providers configured. Click "Add Provider" to get started.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  providers.map((provider) => (
                    <TableRow key={provider.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" fontWeight={500}>
                            {provider.provider_name}
                          </Typography>
                          {provider.is_default && (
                            <Chip label="Default" size="small" color="primary" variant="outlined" />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getProviderTypeLabel(provider.provider_type)}
                          size="small"
                          color={getProviderTypeColor(provider.provider_type)}
                        />
                      </TableCell>
                      <TableCell>
                        <Tooltip title={provider.entity_id}>
                          <Typography
                            variant="body2"
                            sx={{
                              maxWidth: 200,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {provider.entity_id}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Tooltip title={provider.sso_url}>
                          <Typography
                            variant="body2"
                            sx={{
                              maxWidth: 200,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {provider.sso_url}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {provider.is_enabled ? (
                            <CheckCircleIcon color="success" fontSize="small" />
                          ) : (
                            <CancelIcon color="error" fontSize="small" />
                          )}
                          <Typography variant="body2">
                            {provider.is_enabled ? 'Enabled' : 'Disabled'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {format(new Date(provider.created_at), 'MMM dd, yyyy')}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                          <Tooltip title={provider.is_enabled ? 'Disable' : 'Enable'}>
                            <IconButton
                              size="small"
                              onClick={() => handleToggleEnabled(provider)}
                              color={provider.is_enabled ? 'success' : 'default'}
                            >
                              <CheckCircleIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit">
                            <IconButton
                              size="small"
                              onClick={() => handleEditProvider(provider)}
                              color="primary"
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteClick(provider)}
                              color="error"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          {totalCount > rowsPerPage && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={Math.ceil(totalCount / rowsPerPage)}
                page={page}
                onChange={(e, newPage) => setPage(newPage)}
                color="primary"
                showFirstButton
                showLastButton
              />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Form Dialog */}
      <SSOConfigForm
        open={formDialogOpen}
        provider={selectedProvider ?? undefined}
        onSuccess={handleFormSuccess}
        onClose={() => {
          setFormDialogOpen(false);
          setSelectedProvider(null);
        }}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => {
          setDeleteDialogOpen(false);
          setProviderToDelete(null);
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Are you sure you want to delete the SSO provider "
            <strong>{providerToDelete?.provider_name}</strong>"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This action cannot be undone. Users will no longer be able to authenticate using this
            provider.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setDeleteDialogOpen(false);
              setProviderToDelete(null);
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
          >
            Delete Provider
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default SSOConfigPage;
