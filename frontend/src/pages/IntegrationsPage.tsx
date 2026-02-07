/**
 * Integrations Management Page
 *
 * Provides comprehensive integration management for HRIS/ATS platforms including:
 * - Workday, Greenhouse, Lever, BambooHR, and Ashby
 * - List of configured integrations with status indicators
 * - Actions for testing connections, triggering syncs, viewing history
 * - Integration configuration management
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Tooltip,
  Stack,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  CloudSync as CloudSyncIcon,
  Settings as SettingsIcon,
  History as HistoryIcon,
  Sync as SyncIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { integrationsClient } from '@/api/integrations';
import type { IntegrationResponse } from '@/types/api';
import IntegrationConfig from '@/components/IntegrationConfig';
import SyncHistory from '@/components/SyncHistory';

/**
 * Platform configuration with display properties
 */
const PLATFORM_CONFIG: Record<string, { name: string; category: 'ATS' | 'HRIS'; color: string }> = {
  workday: { name: 'Workday', category: 'HRIS', color: '#f5a623' },
  greenhouse: { name: 'Greenhouse', category: 'ATS', color: '#00a651' },
  lever: { name: 'Lever', category: 'ATS', color: '#00b9f1' },
  bamboohr: { name: 'BambooHR', category: 'HRIS', color: '#e67e22' },
  ashby: { name: 'Ashby', category: 'ATS', color: '#6c5ce7' },
};

/**
 * Get status chip configuration
 */
const getStatusChip = (status: string, syncStatus?: string) => {
  type StatusConfig = { color: 'success' | 'info' | 'default' | 'error' | 'warning'; icon: React.ReactNode; label: string };

  // Prioritize sync status over integration status
  if (syncStatus === 'in_progress') {
    return {
      color: 'info' as const,
      icon: <ScheduleIcon sx={{ fontSize: 16 }} />,
      label: 'Syncing',
    };
  }

  if (syncStatus === 'failed') {
    return {
      color: 'error' as const,
      icon: <ErrorIcon sx={{ fontSize: 16 }} />,
      label: 'Sync Failed',
    };
  }

  const statusConfig: Record<string, StatusConfig> = {
    active: {
      color: 'success',
      icon: <CheckCircleIcon sx={{ fontSize: 16 }} />,
      label: 'Active',
    },
    inactive: {
      color: 'default',
      icon: <ScheduleIcon sx={{ fontSize: 16 }} />,
      label: 'Inactive',
    },
    error: {
      color: 'error',
      icon: <ErrorIcon sx={{ fontSize: 16 }} />,
      label: 'Error',
    },
    pending: {
      color: 'warning',
      icon: <ScheduleIcon sx={{ fontSize: 16 }} />,
      label: 'Pending',
    },
  };

  return statusConfig[status] || statusConfig.inactive;
};

const IntegrationsPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [integrations, setIntegrations] = useState<IntegrationResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [testingConnection, setTestingConnection] = useState<Record<string, boolean>>({});
  const [triggeringSync, setTriggeringSync] = useState<Record<string, boolean>>({});
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [editingIntegration, setEditingIntegration] = useState<IntegrationResponse | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<IntegrationResponse | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await integrationsClient.listIntegrations();
      setIntegrations(response.integrations);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch integrations';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleTestConnection = async (integration: IntegrationResponse) => {
    setTestingConnection((prev) => ({ ...prev, [integration.id]: true }));
    setError(null);
    setSuccess(null);

    try {
      const result = await integrationsClient.testConnection(integration.id);
      if (result.success) {
        setSuccess(`Connection test successful for ${integration.name}: ${result.message}`);
      } else {
        setError(`Connection test failed for ${integration.name}: ${result.message}`);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Connection test failed';
      setError(message);
    } finally {
      setTestingConnection((prev) => ({ ...prev, [integration.id]: false }));
    }
  };

  const handleTriggerSync = async (integration: IntegrationResponse) => {
    setTriggeringSync((prev) => ({ ...prev, [integration.id]: true }));
    setError(null);
    setSuccess(null);

    try {
      await integrationsClient.triggerSync(integration.id, { sync_type: 'incremental' });
      setSuccess(`Sync triggered successfully for ${integration.name}. Check sync history for progress.`);
      fetchData(); // Refresh to show updated status
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to trigger sync';
      setError(message);
    } finally {
      setTriggeringSync((prev) => ({ ...prev, [integration.id]: false }));
    }
  };

  const handleDeleteIntegration = async (integration: IntegrationResponse) => {
    if (!confirm(`Are you sure you want to delete the integration "${integration.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await integrationsClient.deleteIntegration(integration.id);
      setSuccess(`Integration "${integration.name}" deleted successfully.`);
      fetchData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to delete integration';
      setError(message);
    }
  };

  const getPlatformBadge = (platform: string) => {
    const config = PLATFORM_CONFIG[platform.toLowerCase()];
    if (!config) {
      return <Chip label={platform} size="small" variant="outlined" />;
    }

    return (
      <Chip
        label={config.name}
        size="small"
        sx={{
          backgroundColor: config.color,
          color: 'white',
          fontWeight: 600,
        }}
      />
    );
  };

  const handleOpenCreateDialog = () => {
    setEditingIntegration(null);
    setConfigDialogOpen(true);
  };

  const handleOpenEditDialog = (integration: IntegrationResponse) => {
    setEditingIntegration(integration);
    setConfigDialogOpen(true);
  };

  const handleIntegrationSaved = (savedIntegration: IntegrationResponse) => {
    setSuccess(`Integration "${savedIntegration.name}" ${editingIntegration ? 'updated' : 'created'} successfully.`);
    fetchData();
    setConfigDialogOpen(false);
  };

  const handleOpenHistoryDialog = (integration: IntegrationResponse) => {
    setSelectedIntegration(integration);
    setHistoryDialogOpen(true);
  };

  const handleCloseHistoryDialog = () => {
    setHistoryDialogOpen(false);
    setSelectedIntegration(null);
  };

  const getCategoryStats = () => {
    const stats = {
      total: integrations.length,
      active: integrations.filter((i) => i.status === 'active').length,
      ats: integrations.filter((i) => PLATFORM_CONFIG[i.platform]?.category === 'ATS').length,
      hris: integrations.filter((i) => PLATFORM_CONFIG[i.platform]?.category === 'HRIS').length,
    };
    return stats;
  };

  if (loading && integrations.length === 0) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
          <Stack spacing={2} alignItems="center">
            <CircularProgress size={40} />
            <Typography variant="body2" color="text.secondary">
              Loading integrations...
            </Typography>
          </Stack>
        </Box>
      </Container>
    );
  }

  const stats = getCategoryStats();

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={600} gutterBottom>
            Integrations
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your HRIS and ATS platform connections
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchData}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenCreateDialog}
          >
            Add Integration
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
      {info && (
        <Alert severity="info" onClose={() => setInfo(null)} sx={{ mb: 2 }}>
          {info}
        </Alert>
      )}

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CloudSyncIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Total Integrations
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {stats.total}
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
                  Active
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {stats.active}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
                  ATS
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {stats.ats}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Applicant Tracking Systems
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
                  HRIS
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {stats.hris}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                HR Information Systems
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Supported Platforms Info */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Supported Platforms
          </Typography>
          <Grid container spacing={2}>
            {Object.entries(PLATFORM_CONFIG).map(([key, config]) => (
              <Grid item xs={12} sm={6} md={4} key={key}>
                <Box
                  sx={{
                    p: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                  }}
                >
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      backgroundColor: config.color,
                    }}
                  />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" fontWeight={500}>
                      {config.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {config.category}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Integrations Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Configured Integrations
          </Typography>
          {integrations.length === 0 ? (
            <Box sx={{ py: 8, textAlign: 'center' }}>
              <CloudSyncIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No integrations configured
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Get started by adding your first HRIS or ATS integration
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleOpenCreateDialog}
              >
                Add Your First Integration
              </Button>
            </Box>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Platform</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Sync Status</TableCell>
                    <TableCell>Last Sync</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {integrations.map((integration) => {
                    const statusConfig = getStatusChip(integration.status, integration.last_sync_status);
                    return (
                      <TableRow key={integration.id} hover>
                        <TableCell>
                          <Typography variant="body2" fontWeight={500}>
                            {integration.name}
                          </Typography>
                          {integration.error_message && (
                            <Typography variant="caption" color="error" sx={{ display: 'block', mt: 0.5 }}>
                              {integration.error_message}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>{getPlatformBadge(integration.platform)}</TableCell>
                        <TableCell>
                          <Chip
                            icon={statusConfig.icon}
                            label={statusConfig.label}
                            color={statusConfig.color}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {integration.last_sync_status ? (
                            <Chip
                              label={integration.last_sync_status.replace('_', ' ')}
                              color={
                                integration.last_sync_status === 'completed'
                                  ? 'success'
                                  : integration.last_sync_status === 'in_progress'
                                  ? 'info'
                                  : 'error'
                              }
                              size="small"
                              variant="outlined"
                            />
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              Never synced
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {integration.last_sync_at
                              ? format(new Date(integration.last_sync_at), 'MMM dd, HH:mm')
                              : 'Never'}
                          </Typography>
                          {integration.sync_interval_minutes && (
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                              Every {integration.sync_interval_minutes} min
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell align="right">
                          <Tooltip title="Test Connection">
                            <IconButton
                              size="small"
                              onClick={() => handleTestConnection(integration)}
                              disabled={testingConnection[integration.id] || integration.status !== 'active'}
                            >
                              {testingConnection[integration.id] ? (
                                <CircularProgress size={16} />
                              ) : (
                                <CheckCircleIcon fontSize="small" />
                              )}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Trigger Sync">
                            <IconButton
                              size="small"
                              onClick={() => handleTriggerSync(integration)}
                              disabled={
                                triggeringSync[integration.id] ||
                                !integration.sync_enabled ||
                                integration.last_sync_status === 'in_progress'
                              }
                            >
                              {triggeringSync[integration.id] ? (
                                <CircularProgress size={16} />
                              ) : (
                                <SyncIcon fontSize="small" />
                              )}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="View Sync History">
                            <IconButton
                              size="small"
                              onClick={() => handleOpenHistoryDialog(integration)}
                            >
                              <HistoryIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit Integration">
                            <IconButton
                              size="small"
                              onClick={() => handleOpenEditDialog(integration)}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete Integration">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteIntegration(integration)}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Integration Configuration Dialog */}
      <IntegrationConfig
        integration={editingIntegration}
        open={configDialogOpen}
        onClose={() => setConfigDialogOpen(false)}
        onSuccess={handleIntegrationSaved}
      />

      {/* Sync History Dialog */}
      {selectedIntegration && (
        <SyncHistory
          integrationId={selectedIntegration.id}
          integrationName={selectedIntegration.name}
          open={historyDialogOpen}
          onClose={handleCloseHistoryDialog}
        />
      )}
    </Container>
  );
};

export default IntegrationsPage;
