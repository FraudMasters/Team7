/**
 * Backup Management Page
 *
 * Provides comprehensive backup and restore functionality including:
 * - Backup status overview with metrics cards
 * - List of all backups with actions
 * - Create new backup dialog
 * - Restore from backup dialog
 * - Backup configuration dialog
 * - Manual sync to S3
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
  LinearProgress,
  Tooltip,
  Divider,
  Stack,
} from '@mui/material';
import {
  Backup as BackupIcon,
  Restore as RestoreIcon,
  Delete as DeleteIcon,
  CloudUpload as CloudUploadIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Storage as StorageIcon,
  CloudDone as CloudDoneIcon,
  CloudOff as CloudOffIcon,
  Refresh as RefreshIcon,
  Verified as VerifiedIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import backupApi, { Backup, BackupStatus as BackupStatusType } from '@services/backupApi';

const BackupsPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [backupStatus, setBackupStatus] = useState<BackupStatusType | null>(null);
  const [backups, setBackups] = useState<Backup[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState<Backup | null>(null);

  // Form states
  const [backupName, setBackupName] = useState('');
  const [backupType, setBackupType] = useState<'database' | 'files' | 'models' | 'full'>('full');
  const [retentionDays, setRetentionDays] = useState(30);
  const [isIncremental, setIsIncremental] = useState(false);
  const [uploadToS3, setUploadToS3] = useState(false);
  const [restoreConfirm, setRestoreConfirm] = useState(false);

  // Config form state
  const [config, setConfig] = useState({
    retention_days: 30,
    backup_schedule: '0 2 * * *',
    s3_enabled: false,
    s3_bucket: '',
    s3_endpoint: '',
    s3_region: 'us-east-1',
    s3_access_key: '',
    s3_secret_key: '',
    notification_email: '',
    enabled: true,
    incremental_enabled: true,
    compression_enabled: true,
  });

  // Refresh interval
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [statusResponse, backupsResponse] = await Promise.all([
        backupApi.getBackupStatus(),
        backupApi.getBackups({ limit: 50 }),
      ]);
      setBackupStatus(statusResponse);
      setBackups(backupsResponse);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch backup data';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchConfig = useCallback(async () => {
    try {
      const configData = await backupApi.getBackupConfig();
      setConfig(configData);
    } catch (err) {
      console.error('Failed to fetch config:', err);
    }
  }, []);

  useEffect(() => {
    fetchData();
    fetchConfig();

    // Set up auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchData();
    }, 30000);
    setRefreshInterval(interval);

    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
      if (interval) clearInterval(interval);
    };
  }, [fetchData, fetchConfig]);

  const handleCreateBackup = async () => {
    try {
      await backupApi.createBackup({
        name: backupName || `Backup ${format(new Date(), 'yyyy-MM-dd HH:mm')}`,
        type: backupType,
        retention_days: retentionDays,
        is_incremental: isIncremental,
        upload_to_s3: uploadToS3,
      });
      setCreateDialogOpen(false);
      setBackupName('');
      setSuccess('Backup creation started. Check the list for progress.');
      fetchData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create backup';
      setError(message);
    }
  };

  const handleRestoreBackup = async () => {
    if (!selectedBackup) return;

    try {
      await backupApi.restoreBackup(selectedBackup.id, {
        restore_type: 'full',
        confirm: restoreConfirm,
        create_backup_before: true,
      });
      setRestoreDialogOpen(false);
      setSelectedBackup(null);
      setRestoreConfirm(false);
      setSuccess('Restore operation started. This may take several minutes.');
      fetchData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to start restore';
      setError(message);
    }
  };

  const handleDeleteBackup = async (backup: Backup) => {
    if (!confirm(`Are you sure you want to delete backup "${backup.name}"?`)) {
      return;
    }

    try {
      await backupApi.deleteBackup(backup.id);
      setSuccess('Backup deleted successfully.');
      fetchData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to delete backup';
      setError(message);
    }
  };

  const handleVerifyBackup = async (backup: Backup) => {
    try {
      const result = await backupApi.verifyBackup(backup.id);
      if (result.valid) {
        setSuccess(`Backup verified: ${result.details || 'Integrity check passed'}`);
      } else {
        setError(`Backup verification failed: ${result.details || 'Unknown error'}`);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to verify backup';
      setError(message);
    }
  };

  const handleSyncS3 = async () => {
    try {
      await backupApi.syncS3();
      setSuccess('S3 sync task started.');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to start S3 sync';
      setError(message);
    }
  };

  const handleCleanup = async () => {
    if (!confirm('Delete all backups older than the retention period?')) {
      return;
    }

    try {
      await backupApi.cleanupBackups();
      setSuccess('Cleanup task started.');
      fetchData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to start cleanup';
      setError(message);
    }
  };

  const handleSaveConfig = async () => {
    try {
      await backupApi.updateBackupConfig(config);
      setConfigDialogOpen(false);
      setSuccess('Configuration saved successfully.');
      fetchData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to save configuration';
      setError(message);
    }
  };

  const getStatusChip = (status: string) => {
    const statusConfig: Record<string, { color: any; icon: React.ReactNode; label: string }> = {
      completed: { color: 'success', icon: <CheckCircleIcon />, label: 'Completed' },
      in_progress: { color: 'info', icon: <ScheduleIcon />, label: 'In Progress' },
      pending: { color: 'default', icon: <ScheduleIcon />, label: 'Pending' },
      failed: { color: 'error', icon: <ErrorIcon />, label: 'Failed' },
      restoring: { color: 'warning', icon: <RestoreIcon />, label: 'Restoring' },
      expired: { color: 'error', icon: <ErrorIcon />, label: 'Expired' },
    };

    const config = statusConfig[status] || statusConfig.pending;
    return (
      <Chip
        icon={config.icon}
        label={config.label}
        color={config.color}
        size="small"
      />
    );
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      database: 'Database',
      files: 'Files',
      models: 'Models',
      full: 'Full',
    };
    return labels[type] || type;
  };

  if (loading && !backupStatus) {
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
        <Typography variant="h4" fontWeight={600}>
          Backup & Restore
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchData}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<CloudUploadIcon />}
            onClick={handleSyncS3}
            disabled={!backupStatus?.enabled || !backupStatus?.recent_backups.some((b) => !b.s3_uploaded)}
          >
            Sync to S3
          </Button>
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => setConfigDialogOpen(true)}
          >
            Configuration
          </Button>
          <Button
            variant="contained"
            startIcon={<BackupIcon />}
            onClick={() => setCreateDialogOpen(true)}
            disabled={!backupStatus?.enabled}
          >
            Create Backup
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

      {/* Status Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <BackupIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Total Backups
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {backupStatus?.total_backups || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <StorageIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Total Size
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {backupStatus?.total_size_human || '0 B'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                {backupStatus?.last_backup_status === 'success' ? (
                  <CheckCircleIcon color="success" sx={{ mr: 1 }} />
                ) : (
                  <ErrorIcon color="error" sx={{ mr: 1 }} />
                )}
                <Typography variant="body2" color="text.secondary">
                  Last Backup
                </Typography>
              </Box>
              <Typography variant="body1" fontWeight={500}>
                {backupStatus?.last_backup_at
                  ? format(new Date(backupStatus.last_backup_at), 'MMM dd, HH:mm')
                  : 'Never'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                {backupStatus?.recent_backups.some((b) => b.s3_uploaded) ? (
                  <CloudDoneIcon color="info" sx={{ mr: 1 }} />
                ) : (
                  <CloudOffIcon color="disabled" sx={{ mr: 1 }} />
                )}
                <Typography variant="body2" color="text.secondary">
                  S3 Status
                </Typography>
              </Box>
              <Typography variant="body1" fontWeight={500}>
                {backupStatus?.recent_backups.some((b) => b.s3_uploaded)
                  ? 'Synced'
                  : 'Not Synced'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Status */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            System Status
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Automated Backups
                </Typography>
                <Chip
                  label={backupStatus?.enabled ? 'Enabled' : 'Disabled'}
                  color={backupStatus?.enabled ? 'success' : 'default'}
                  size="small"
                />
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Retention Period
                </Typography>
                <Typography variant="body2" fontWeight={500}>
                  {config.retention_days} days
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Disk Usage
                </Typography>
                <Typography variant="body2" fontWeight={500}>
                  {backupStatus?.disk_usage_human || 'N/A'}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Next Scheduled Backup
                </Typography>
                <Typography variant="body2" fontWeight={500}>
                  {backupStatus?.next_scheduled_backup
                    ? format(new Date(backupStatus.next_scheduled_backup), 'MMM dd, HH:mm')
                    : 'N/A'}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  S3 Backup
                </Typography>
                <Chip
                  label={config.s3_enabled ? 'Enabled' : 'Disabled'}
                  color={config.s3_enabled ? 'info' : 'default'}
                  size="small"
                />
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Cleanup Old Backups
                </Typography>
                <Button size="small" onClick={handleCleanup}>
                  Run Cleanup
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Backups Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Backup History
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>S3</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {backups.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 3 }}>
                      <Typography color="text.secondary">
                        No backups found. Create your first backup to get started.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  backups.map((backup) => (
                    <TableRow key={backup.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight={500}>
                          {backup.name}
                        </Typography>
                        {backup.is_incremental && (
                          <Chip label="Incremental" size="small" sx={{ mt: 0.5 }} />
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip label={getTypeLabel(backup.type)} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>{getStatusChip(backup.status)}</TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {backup.size_human || '-'}
                        </Typography>
                        {backup.files_count && (
                          <Typography variant="caption" color="text.secondary">
                            {backup.files_count} files
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {format(new Date(backup.created_at), 'MMM dd, HH:mm')}
                        </Typography>
                        {backup.expires_at && (
                          <Typography variant="caption" color="text.secondary">
                            Expires: {format(new Date(backup.expires_at), 'MMM dd')}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {backup.s3_uploaded ? (
                          <CloudDoneIcon color="success" fontSize="small" />
                        ) : (
                          <CloudOffIcon color="disabled" fontSize="small" />
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Verify">
                          <IconButton
                            size="small"
                            onClick={() => handleVerifyBackup(backup)}
                            disabled={backup.status !== 'completed'}
                          >
                            <VerifiedIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Restore">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedBackup(backup);
                              setRestoreDialogOpen(true);
                            }}
                            disabled={backup.status !== 'completed'}
                          >
                            <RestoreIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteBackup(backup)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Create Backup Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Backup</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Backup Name"
            fullWidth
            variant="outlined"
            value={backupName}
            onChange={(e) => setBackupName(e.target.value)}
            placeholder={`Backup ${format(new Date(), 'yyyy-MM-dd HH:mm')}`}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Backup Type</InputLabel>
            <Select
              value={backupType}
              onChange={(e) => setBackupType(e.target.value as typeof backupType)}
              label="Backup Type"
            >
              <MenuItem value="full">Full Backup (Database + Files + Models)</MenuItem>
              <MenuItem value="database">Database Only</MenuItem>
              <MenuItem value="files">Files Only (Resumes)</MenuItem>
              <MenuItem value="models">Models Only (ML Cache)</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>Retention Period</InputLabel>
            <Select
              value={retentionDays}
              onChange={(e) => setRetentionDays(e.target.value as number)}
              label="Retention Period"
            >
              <MenuItem value={7}>7 Days</MenuItem>
              <MenuItem value={14}>14 Days</MenuItem>
              <MenuItem value={30}>30 Days</MenuItem>
              <MenuItem value={60}>60 Days</MenuItem>
              <MenuItem value={90}>90 Days</MenuItem>
            </Select>
          </FormControl>
          <FormControlLabel
            control={
              <Switch
                checked={isIncremental}
                onChange={(e) => setIsIncremental(e.target.checked)}
              />
            }
            label="Incremental Backup (faster, requires previous backup)"
            sx={{ mb: 1 }}
          />
          <FormControlLabel
            control={
              <Switch
                checked={uploadToS3}
                onChange={(e) => setUploadToS3(e.target.checked)}
                disabled={!config.s3_enabled}
              />
            }
            label="Upload to S3 after completion"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateBackup}>
            Create Backup
          </Button>
        </DialogActions>
      </Dialog>

      {/* Restore Dialog */}
      <Dialog open={restoreDialogOpen} onClose={() => setRestoreDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Restore from Backup</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body2">
              Warning: This will replace your current data with the backup data.
            </Typography>
          </Alert>
          {selectedBackup && (
            <>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Backup:</strong> {selectedBackup.name}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Type:</strong> {getTypeLabel(selectedBackup.type)}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Created:</strong> {format(new Date(selectedBackup.created_at), 'PPPp')}
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                <strong>Size:</strong> {selectedBackup.size_human || 'Unknown'}
              </Typography>
            </>
          )}
          <Divider sx={{ my: 2 }} />
          <FormControlLabel
            control={
              <Switch
                checked={restoreConfirm}
                onChange={(e) => setRestoreConfirm(e.target.checked)}
                color="error"
              />
            }
            label="I understand this will replace current data and want to proceed"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setRestoreDialogOpen(false);
            setSelectedBackup(null);
            setRestoreConfirm(false);
          }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleRestoreBackup}
            disabled={!restoreConfirm}
          >
            Restore Backup
          </Button>
        </DialogActions>
      </Dialog>

      {/* Configuration Dialog */}
      <Dialog open={configDialogOpen} onClose={() => setConfigDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Backup Configuration</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.enabled}
                    onChange={(e) => setConfig({ ...config, enabled: e.target.checked })}
                  />
                }
                label="Enable Automated Backups"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.compression_enabled}
                    onChange={(e) => setConfig({ ...config, compression_enabled: e.target.checked })}
                  />
                }
                label="Enable Compression"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.incremental_enabled}
                    onChange={(e) => setConfig({ ...config, incremental_enabled: e.target.checked })}
                  />
                }
                label="Enable Incremental Backups"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Retention Period</InputLabel>
                <Select
                  value={config.retention_days}
                  onChange={(e) => setConfig({ ...config, retention_days: e.target.value as number })}
                  label="Retention Period"
                >
                  <MenuItem value={7}>7 Days</MenuItem>
                  <MenuItem value={14}>14 Days</MenuItem>
                  <MenuItem value={30}>30 Days</MenuItem>
                  <MenuItem value={60}>60 Days</MenuItem>
                  <MenuItem value={90}>90 Days</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Backup Schedule (Cron)"
                value={config.backup_schedule}
                onChange={(e) => setConfig({ ...config, backup_schedule: e.target.value })}
                helperText="Default: 0 2 * * * (daily at 2 AM)"
              />
            </Grid>
            <Grid item xs={12}>
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle2" gutterBottom>
                S3 Configuration (Off-site Backup)
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.s3_enabled}
                    onChange={(e) => setConfig({ ...config, s3_enabled: e.target.checked })}
                  />
                }
                label="Enable S3 Backup"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="S3 Region"
                value={config.s3_region}
                onChange={(e) => setConfig({ ...config, s3_region: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="S3 Bucket Name"
                value={config.s3_bucket}
                onChange={(e) => setConfig({ ...config, s3_bucket: e.target.value })}
                disabled={!config.s3_enabled}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="S3 Endpoint"
                value={config.s3_endpoint}
                onChange={(e) => setConfig({ ...config, s3_endpoint: e.target.value })}
                placeholder="https://s3.amazonaws.com"
                disabled={!config.s3_enabled}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Access Key"
                value={config.s3_access_key}
                onChange={(e) => setConfig({ ...config, s3_access_key: e.target.value })}
                type="password"
                disabled={!config.s3_enabled}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Secret Key"
                value={config.s3_secret_key}
                onChange={(e) => setConfig({ ...config, s3_secret_key: e.target.value })}
                type="password"
                disabled={!config.s3_enabled}
              />
            </Grid>
            <Grid item xs={12}>
              <Divider sx={{ my: 1 }} />
              <TextField
                fullWidth
                label="Notification Email"
                value={config.notification_email}
                onChange={(e) => setConfig({ ...config, notification_email: e.target.value })}
                type="email"
                helperText="Receive email notifications for backup failures"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveConfig}>
            Save Configuration
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default BackupsPage;
