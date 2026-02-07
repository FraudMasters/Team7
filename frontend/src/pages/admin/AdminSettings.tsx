import { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Snackbar,
  CircularProgress,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Security as SecurityIcon,
  AdminPanelSettings as AdminPanelSettingsIcon,
  Email as EmailIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  Cloud as CloudIcon,
  Lock as LockIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { apiClient } from '../../api/client';

/**
 * System settings interface
 */
interface SystemSettings {
  // Authentication settings
  authEnabled: boolean;
  oidcAuthority: string;
  oidcClientId: string;
  sessionTimeout: number;
  passwordMinLength: number;
  passwordRequireSpecial: boolean;
  passwordRequireNumber: boolean;

  // Email settings
  smtpEnabled: boolean;
  smtpHost: string;
  smtpPort: number;
  smtpUsername: string;
  smtpFromAddress: string;
  emailNotificationsEnabled: boolean;

  // System limits
  maxUsersPerOrganization: number;
  maxVacanciesPerOrganization: number;
  maxFileSizeMB: number;
  maxApiRequestsPerMinute: number;

  // Data retention
  auditLogRetentionDays: number;
  deletedDataRetentionDays: number;
  autoPurgeEnabled: boolean;

  // Feature flags
  maintenanceMode: boolean;
  registrationOpen: boolean;
  analyticsEnabled: boolean;
}

/**
 * Default system settings
 */
const DEFAULT_SETTINGS: SystemSettings = {
  authEnabled: false,
  oidcAuthority: 'http://localhost:8080/realms/agenthr',
  oidcClientId: 'agenthr-frontend',
  sessionTimeout: 3600,
  passwordMinLength: 8,
  passwordRequireSpecial: true,
  passwordRequireNumber: true,

  smtpEnabled: false,
  smtpHost: 'smtp.example.com',
  smtpPort: 587,
  smtpUsername: '',
  smtpFromAddress: 'noreply@agenthr.com',
  emailNotificationsEnabled: true,

  maxUsersPerOrganization: 100,
  maxVacanciesPerOrganization: 500,
  maxFileSizeMB: 10,
  maxApiRequestsPerMinute: 60,

  auditLogRetentionDays: 90,
  deletedDataRetentionDays: 30,
  autoPurgeEnabled: false,

  maintenanceMode: false,
  registrationOpen: true,
  analyticsEnabled: true,
};

/**
 * AdminSettings Page Component
 *
 * Provides system configuration interface for administrators:
 * - Authentication and security settings
 * - Email/SMTP configuration
 * - System limits and quotas
 * - Data retention policies
 * - Feature flags and maintenance mode
 *
 * Accessible at /admin/settings
 *
 * @example
 * ```tsx
 * <AdminSettings />
 * ```
 */
export function AdminSettings() {
  const [settings, setSettings] = useState<SystemSettings>(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  /**
   * Load settings from API
   */
  const handleLoadSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      // TODO: Replace with actual API call when endpoint is available
      // const response = await apiClient.get<SystemSettings>('/admin/settings');
      // setSettings(response.data);

      // Mock delay for now
      await new Promise((resolve) => setTimeout(resolve, 500));
      setSettings(DEFAULT_SETTINGS);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load settings';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Save settings to API
   */
  const handleSaveSettings = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      // TODO: Replace with actual API call when endpoint is available
      // await apiClient.put('/admin/settings', settings);

      // Mock delay for now
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setSuccess('System settings saved successfully');
      setHasChanges(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save settings';
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  /**
   * Update setting value
   */
  const updateSetting = <K extends keyof SystemSettings>(
    key: K,
    value: SystemSettings[K]
  ) => {
    setSettings((prev) => ({
      ...prev,
      [key]: value,
    }));
    setHasChanges(true);
  };

  /**
   * Reset to defaults
   */
  const handleResetToDefaults = () => {
    setSettings(DEFAULT_SETTINGS);
    setHasChanges(true);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <AdminPanelSettingsIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" fontWeight={700}>
                System Settings
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Configure system-wide settings and preferences
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={loading ? <CircularProgress size={16} /> : <RefreshIcon />}
              onClick={handleLoadSettings}
              disabled={loading}
            >
              Reload
            </Button>
            <Button
              variant="contained"
              startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
              onClick={handleSaveSettings}
              disabled={saving || !hasChanges}
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Error/Success Messages */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Snackbar
          open={Boolean(success)}
          autoHideDuration={6000}
          onClose={() => setSuccess(null)}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert severity="success" onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        </Snackbar>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress size={60} />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {/* Authentication & Security */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <SecurityIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Authentication & Security
                </Typography>
              </Box>

              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Authentication Enabled"
                    secondary="Enable KeyCloak OIDC authentication"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.authEnabled}
                      onChange={(e) => updateSetting('authEnabled', e.target.checked)}
                      color="primary"
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Registration Open"
                    secondary="Allow new user self-registration"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.registrationOpen}
                      onChange={(e) => updateSetting('registrationOpen', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              <TextField
                fullWidth
                label="OIDC Authority"
                value={settings.oidcAuthority}
                onChange={(e) => updateSetting('oidcAuthority', e.target.value)}
                sx={{ mb: 2 }}
                helperText="KeyCloak realm URL"
              />

              <TextField
                fullWidth
                label="OIDC Client ID"
                value={settings.oidcClientId}
                onChange={(e) => updateSetting('oidcClientId', e.target.value)}
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                type="number"
                label="Session Timeout (seconds)"
                value={settings.sessionTimeout}
                onChange={(e) => updateSetting('sessionTimeout', parseInt(e.target.value) || 3600)}
                sx={{ mb: 2 }}
              />

              <TextField
                fullWidth
                type="number"
                label="Minimum Password Length"
                value={settings.passwordMinLength}
                onChange={(e) => updateSetting('passwordMinLength', parseInt(e.target.value) || 8)}
                sx={{ mb: 2 }}
              />

              <List dense>
                <ListItem>
                  <ListItemText primary="Require Special Characters" />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.passwordRequireSpecial}
                      onChange={(e) => updateSetting('passwordRequireSpecial', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText primary="Require Numbers" />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.passwordRequireNumber}
                      onChange={(e) => updateSetting('passwordRequireNumber', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </Paper>
          </Grid>

          {/* Email Configuration */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <EmailIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Email Configuration
                </Typography>
              </Box>

              <List dense>
                <ListItem>
                  <ListItemText
                    primary="SMTP Enabled"
                    secondary="Enable email sending via SMTP"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.smtpEnabled}
                      onChange={(e) => updateSetting('smtpEnabled', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Email Notifications"
                    secondary="Send system notifications via email"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.emailNotificationsEnabled}
                      onChange={(e) => updateSetting('emailNotificationsEnabled', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              <TextField
                fullWidth
                label="SMTP Host"
                value={settings.smtpHost}
                onChange={(e) => updateSetting('smtpHost', e.target.value)}
                sx={{ mb: 2 }}
                disabled={!settings.smtpEnabled}
              />

              <TextField
                fullWidth
                type="number"
                label="SMTP Port"
                value={settings.smtpPort}
                onChange={(e) => updateSetting('smtpPort', parseInt(e.target.value) || 587)}
                sx={{ mb: 2 }}
                disabled={!settings.smtpEnabled}
              />

              <TextField
                fullWidth
                label="SMTP Username"
                value={settings.smtpUsername}
                onChange={(e) => updateSetting('smtpUsername', e.target.value)}
                sx={{ mb: 2 }}
                disabled={!settings.smtpEnabled}
              />

              <TextField
                fullWidth
                label="From Address"
                value={settings.smtpFromAddress}
                onChange={(e) => updateSetting('smtpFromAddress', e.target.value)}
                sx={{ mb: 2 }}
                disabled={!settings.smtpEnabled}
                helperText="Default sender email address"
              />
            </Paper>
          </Grid>

          {/* System Limits */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <SpeedIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  System Limits
                </Typography>
              </Box>

              <TextField
                fullWidth
                type="number"
                label="Max Users Per Organization"
                value={settings.maxUsersPerOrganization}
                onChange={(e) =>
                  updateSetting('maxUsersPerOrganization', parseInt(e.target.value) || 100)
                }
                sx={{ mb: 2 }}
                helperText="Maximum number of users allowed per organization"
              />

              <TextField
                fullWidth
                type="number"
                label="Max Vacancies Per Organization"
                value={settings.maxVacanciesPerOrganization}
                onChange={(e) =>
                  updateSetting('maxVacanciesPerOrganization', parseInt(e.target.value) || 500)
                }
                sx={{ mb: 2 }}
                helperText="Maximum number of active job postings per organization"
              />

              <TextField
                fullWidth
                type="number"
                label="Max File Size (MB)"
                value={settings.maxFileSizeMB}
                onChange={(e) => updateSetting('maxFileSizeMB', parseInt(e.target.value) || 10)}
                sx={{ mb: 2 }}
                helperText="Maximum file upload size in megabytes"
              />

              <TextField
                fullWidth
                type="number"
                label="API Rate Limit (per minute)"
                value={settings.maxApiRequestsPerMinute}
                onChange={(e) =>
                  updateSetting('maxApiRequestsPerMinute', parseInt(e.target.value) || 60)
                }
                helperText="Maximum API requests per minute per user"
              />
            </Paper>
          </Grid>

          {/* Data Retention */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <StorageIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Data Retention
                </Typography>
              </Box>

              <TextField
                fullWidth
                type="number"
                label="Audit Log Retention (days)"
                value={settings.auditLogRetentionDays}
                onChange={(e) =>
                  updateSetting('auditLogRetentionDays', parseInt(e.target.value) || 90)
                }
                sx={{ mb: 2 }}
                helperText="How long to keep audit log entries"
              />

              <TextField
                fullWidth
                type="number"
                label="Deleted Data Retention (days)"
                value={settings.deletedDataRetentionDays}
                onChange={(e) =>
                  updateSetting('deletedDataRetentionDays', parseInt(e.target.value) || 30)
                }
                sx={{ mb: 2 }}
                helperText="How long to keep soft-deleted data before permanent removal"
              />

              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Auto-Purge Enabled"
                    secondary="Automatically purge expired data"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.autoPurgeEnabled}
                      onChange={(e) => updateSetting('autoPurgeEnabled', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </Paper>
          </Grid>

          {/* Feature Flags */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <CloudIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Feature Flags
                </Typography>
              </Box>

              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Maintenance Mode"
                    secondary="Disable system for maintenance (read-only)"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.maintenanceMode}
                      onChange={(e) => updateSetting('maintenanceMode', e.target.checked)}
                      color="warning"
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Analytics Enabled"
                    secondary="Enable usage analytics and reporting"
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      checked={settings.analyticsEnabled}
                      onChange={(e) => updateSetting('analyticsEnabled', e.target.checked)}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </List>

              {settings.maintenanceMode && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  <Typography variant="body2" fontWeight={600}>
                    Maintenance Mode Active
                  </Typography>
                  <Typography variant="body2">
                    The system is in read-only mode. Users cannot make changes.
                  </Typography>
                </Alert>
              )}
            </Paper>
          </Grid>

          {/* Actions */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    Settings Actions
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {hasChanges
                      ? 'You have unsaved changes'
                      : 'All settings are up to date'}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant="outlined"
                    onClick={handleResetToDefaults}
                    disabled={!hasChanges}
                  >
                    Reset to Defaults
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
                    onClick={handleSaveSettings}
                    disabled={saving || !hasChanges}
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </Button>
                </Box>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Container>
  );
}
