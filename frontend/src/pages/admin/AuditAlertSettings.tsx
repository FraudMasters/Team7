/**
 * Audit Alert Settings Page
 *
 * Provides comprehensive audit alert configuration management including:
 * - View and manage alert rules
 * - Create new alert configurations
 * - Enable/disable alert rules
 * - Configure thresholds and recipients
 *
 * Accessible at /admin/audit-alerts
 *
 * @example
 * ```tsx
 * <AuditAlertSettings />
 * ```
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Alert,
  Snackbar,
  CircularProgress,
  Paper,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Switch,
  Stack,
  Tooltip,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives/Icon';
import { format } from 'date-fns';
import auditAlertsApi, {
  type AuditAlertConfig,
  type AuditAlertConfigsResponse,
  type AlertTypesResponse,
  type AlertSeveritiesResponse,
} from '../../services/auditAlertsApi';

/**
 * Alert severity color mapping
 */
const SEVERITY_COLORS: Record<string, 'info' | 'warning' | 'error' | 'default'> = {
  info: 'info',
  warning: 'warning',
  error: 'error',
  critical: 'error',
};

/**
 * Alert type display names
 */
const ALERT_TYPE_NAMES: Record<string, string> = {
  failed_logins: 'Failed Logins',
  multiple_login_locations: 'Multiple Login Locations',
  suspicious_login: 'Suspicious Login',
  bulk_data_export: 'Bulk Data Export',
  sensitive_data_access: 'Sensitive Data Access',
  excessive_data_queries: 'Excessive Data Queries',
  permission_changes: 'Permission Changes',
  role_changes: 'Role Changes',
  user_deleted: 'User Deleted',
  user_created: 'User Created',
  configuration_changes: 'Configuration Changes',
  backup_operations: 'Backup Operations',
  system_settings_changed: 'System Settings Changed',
  ip_blocked: 'IP Blocked',
  session_hijacking: 'Session Hijacking',
  unusual_activity_pattern: 'Unusual Activity Pattern',
};

/**
 * AuditAlertSettings Page Component
 */
export function AuditAlertSettings() {
  const [alertConfigs, setAlertConfigs] = useState<AuditAlertConfig[]>([]);
  const [alertTypes, setAlertTypes] = useState<string[]>([]);
  const [severities, setSeverities] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  /**
   * Load alert configurations from API
   */
  const fetchAlertConfigs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [configsData, typesData, severitiesData] = await Promise.all([
        auditAlertsApi.getAlertConfigs({ limit: 100 }),
        auditAlertsApi.getAlertTypes(),
        auditAlertsApi.getAlertSeverities(),
      ]);

      setAlertConfigs(configsData.alert_configs);
      setAlertTypes(typesData.alert_types);
      setSeverities(severitiesData.severities);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load alert configurations';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Handle toggle alert enabled/disabled
   */
  const handleToggleEnabled = async (alertId: string, currentEnabled: boolean) => {
    try {
      // TODO: Implement PUT endpoint to update alert configuration
      // For now, just show a success message
      setSuccess(
        `Alert ${currentEnabled ? 'disabled' : 'enabled'} successfully (API endpoint pending)`
      );

      // Optimistically update the UI
      setAlertConfigs((prev) =>
        prev.map((config) =>
          config.id === alertId ? { ...config, enabled: !currentEnabled } : config
        )
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update alert configuration';
      setError(message);
    }
  };

  /**
   * Handle add new alert rule
   */
  const handleAddRule = () => {
    // TODO: Open dialog/modal to create new alert rule
    setSuccess('Add rule functionality coming soon (UI pending)');
  };

  /**
   * Format alert type for display
   */
  const formatAlertType = (alertType: string): string => {
    return ALERT_TYPE_NAMES[alertType] || alertType.replace(/_/g, ' ');
  };

  /**
   * Get severity chip color
   */
  const getSeverityColor = (severity: string): 'info' | 'warning' | 'error' | 'default' => {
    return SEVERITY_COLORS[severity] || 'default';
  };

  useEffect(() => {
    fetchAlertConfigs();
  }, [fetchAlertConfigs]);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
          <Box display="flex" alignItems="center" gap={1}>
            <Icon name="bell" size={32} />
            <Typography variant="h4">Audit Alert Settings</Typography>
          </Box>
          <Button
            variant="contained"
            color="primary"
            startIcon={<Icon name="plus" />}
            onClick={handleAddRule}
          >
            Add Alert Rule
          </Button>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Configure alert rules to monitor suspicious activity and security events
        </Typography>
      </Box>

      {/* Overview Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <Icon name="shield-check" color="primary" />
                <Typography variant="h6">Total Rules</Typography>
              </Box>
              <Typography variant="h3" color="primary">
                {alertConfigs.length}
              </Typography>
              <Typography variant="body2" color="text.secondary" mt={1}>
                Alert rules configured
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <Icon name="check-circle" color="success" />
                <Typography variant="h6">Active Rules</Typography>
              </Box>
              <Typography variant="h3" color="success">
                {alertConfigs.filter((config) => config.enabled).length}
              </Typography>
              <Typography variant="body2" color="text.secondary" mt={1}>
                Currently monitoring
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <Icon name="alert-triangle" color="warning" />
                <Typography variant="h6">Triggered</Typography>
              </Box>
              <Typography variant="h3" color="warning">
                {alertConfigs.reduce((sum, config) => sum + config.trigger_count, 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary" mt={1}>
                Total alerts triggered
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alert Rules Table */}
      <Paper sx={{ mb: 3 }}>
        <Box p={3}>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Typography variant="h6">Alert Rules</Typography>
            <Button
              variant="outlined"
              startIcon={<Icon name="refresh-cw" />}
              onClick={fetchAlertConfigs}
              disabled={loading}
            >
              Refresh
            </Button>
          </Box>
          <Divider sx={{ mb: 2 }} />

          {alertConfigs.length === 0 ? (
            <Box py={8} textAlign="center">
              <Icon name="bell-off" size={48} color="text.secondary" />
              <Typography variant="h6" color="text.secondary" mt={2}>
                No alert rules configured
              </Typography>
              <Typography variant="body2" color="text.secondary" mt={1}>
                Create your first alert rule to start monitoring suspicious activity
              </Typography>
              <Button
                variant="contained"
                color="primary"
                startIcon={<Icon name="plus" />}
                onClick={handleAddRule}
                sx={{ mt: 3 }}
              >
                Add Alert Rule
              </Button>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell align="center">Threshold</TableCell>
                    <TableCell align="center">Window</TableCell>
                    <TableCell align="center">Triggered</TableCell>
                    <TableCell align="center">Enabled</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {alertConfigs.map((config) => (
                    <TableRow key={config.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {config.name}
                        </Typography>
                        {config.description && (
                          <Typography variant="caption" color="text.secondary">
                            {config.description}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={formatAlertType(config.alert_type)}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={config.severity.toUpperCase()}
                          size="small"
                          color={getSeverityColor(config.severity)}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2">{config.threshold}</Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2">{config.time_window_minutes} min</Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip
                          title={
                            config.last_triggered_at
                              ? `Last: ${format(new Date(config.last_triggered_at), 'MMM d, yyyy HH:mm')}`
                              : 'Never triggered'
                          }
                        >
                          <Chip
                            label={config.trigger_count}
                            size="small"
                            color={config.trigger_count > 0 ? 'warning' : 'default'}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell align="center">
                        <Switch
                          checked={config.enabled}
                          onChange={() => handleToggleEnabled(config.id, config.enabled)}
                          color="primary"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                          <Tooltip title="Edit rule">
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<Icon name="edit" />}
                              onClick={() =>
                                setSuccess('Edit functionality coming soon (UI pending)')
                              }
                            >
                              Edit
                            </Button>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      </Paper>

      {/* Information Cards */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          About Alert Rules
        </Typography>
        <Divider sx={{ my: 2 }} />
        <Stack spacing={2}>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Alert Types
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Configure alerts for various security events including failed logins, bulk data exports,
              permission changes, and unusual activity patterns. Each alert type can have custom
              thresholds and time windows.
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Thresholds and Time Windows
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Thresholds define how many events must occur within the specified time window to trigger
              an alert. For example, "5 failed logins in 10 minutes" would alert on potential brute
              force attacks.
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Severity Levels
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Alerts can be categorized by severity: INFO (informational), WARNING (potential issue),
              ERROR (confirmed issue), and CRITICAL (urgent security threat). Higher severity alerts
              may trigger different notification channels.
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Alert Cooldowns
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Cooldown periods prevent alert fatigue by limiting how frequently the same alert can be
              triggered. During the cooldown period, matching events are still logged but won't generate
              new notifications.
            </Typography>
          </Box>
        </Stack>
      </Paper>

      {/* Success Snackbar */}
      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="success" onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      </Snackbar>

      {/* Error Snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default AuditAlertSettings;
