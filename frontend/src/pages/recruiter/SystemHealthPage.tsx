/**
 * System Health Page
 *
 * Displays real-time health status of all system components including:
 * - Database connectivity
 * - Redis cache
 * - Celery workers
 * - ML models
 * - External services (LanguageTool, S3)
 * - Storage system
 *
 * Auto-refreshes every 30 seconds to provide up-to-date status information.
 * Includes historical health trend visualization showing uptime and degradation events.
 */
import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
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
  LinearProgress,
  Chip,
  Stack,
  Paper,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  Storage as StorageIcon,
  Memory as MemoryIcon,
  Work as WorkIcon,
  Psychology as PsychologyIcon,
  Cloud as CloudIcon,
  Folder as FolderIcon,
  Api as ApiIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useQuery } from '@tanstack/react-query';
import healthApi from '@/services/healthApi';
import type { SystemHealthResponse, ComponentHealth } from '@/types/api';

/**
 * Health history entry interface
 */
interface HealthHistoryEntry {
  timestamp: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: Record<string, string>;
}

const SystemHealthPage: React.FC = () => {
  const { t } = useTranslation();
  const healthHistoryRef = useRef<HealthHistoryEntry[]>([]);
  const MAX_HISTORY_ENTRIES = 60; // Store last 60 data points (30 minutes with 30s interval)

  const {
    data: healthData,
    isLoading,
    error,
    refetch,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ['system-health'],
    queryFn: async () => {
      return await healthApi.getSystemHealth();
    },
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  /**
   * Store health check history when data is updated
   */
  useEffect(() => {
    if (healthData) {
      const entry: HealthHistoryEntry = {
        timestamp: healthData.timestamp,
        status: healthData.status,
        components: Object.fromEntries(
          Object.entries(healthData.components).map(([key, comp]) => [key, comp.status])
        ),
      };

      healthHistoryRef.current = [...healthHistoryRef.current, entry].slice(-MAX_HISTORY_ENTRIES);
    }
  }, [healthData]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon sx={{ fontSize: 32 }} />;
      case 'degraded':
        return <WarningIcon sx={{ fontSize: 32 }} />;
      case 'unhealthy':
        return <ErrorIcon sx={{ fontSize: 32 }} />;
      default:
        return <ErrorIcon sx={{ fontSize: 32 }} />;
    }
  };

  const getStatusColor = (status: string): 'success' | 'warning' | 'error' => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'unhealthy':
        return 'error';
      default:
        return 'error';
    }
  };

  const getStatusChip = (status: string) => {
    const color = getStatusColor(status);
    const label = status.charAt(0).toUpperCase() + status.slice(1);
    return (
      <Chip
        label={label}
        color={color}
        size="small"
      />
    );
  };

  const getComponentIcon = (componentName: string) => {
    switch (componentName) {
      case 'api':
        return <ApiIcon sx={{ fontSize: 40 }} />;
      case 'database':
        return <StorageIcon sx={{ fontSize: 40 }} />;
      case 'redis':
        return <MemoryIcon sx={{ fontSize: 40 }} />;
      case 'celery_workers':
        return <WorkIcon sx={{ fontSize: 40 }} />;
      case 'ml_models':
        return <PsychologyIcon sx={{ fontSize: 40 }} />;
      case 'storage':
        return <FolderIcon sx={{ fontSize: 40 }} />;
      case 'external_services':
        return <CloudIcon sx={{ fontSize: 40 }} />;
      default:
        return <CheckCircleIcon sx={{ fontSize: 40 }} />;
    }
  };

  const getComponentDisplayName = (componentName: string): string => {
    switch (componentName) {
      case 'api':
        return 'API Service';
      case 'database':
        return 'Database';
      case 'redis':
        return 'Redis Cache';
      case 'celery_workers':
        return 'Celery Workers';
      case 'ml_models':
        return 'ML Models';
      case 'storage':
        return 'File Storage';
      case 'external_services':
        return 'External Services';
      default:
        return componentName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
    }
  };

  if (isLoading && !healthData) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ width: '100%', mt: 4 }}>
          <LinearProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" fontWeight={600} gutterBottom>
            System Health Monitor
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time status of all system components
            {dataUpdatedAt && ` • Last updated: ${format(new Date(dataUpdatedAt), 'HH:mm:ss')}`}
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
          disabled={isLoading}
        >
          Refresh
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {(error as Error).message || 'Failed to fetch health data'}
        </Alert>
      )}

      {/* Overall System Status */}
      {healthData && (
        <Card sx={{ mb: 4, bgcolor: getStatusColor(healthData.status) === 'success' ? 'success.light' : getStatusColor(healthData.status) === 'warning' ? 'warning.light' : 'error.light' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ color: getStatusColor(healthData.status) === 'success' ? 'success.dark' : getStatusColor(healthData.status) === 'warning' ? 'warning.dark' : 'error.dark' }}>
                {getStatusIcon(healthData.status)}
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6" fontWeight={600} color="text.primary">
                  Overall System Status: {healthData.status.toUpperCase()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {healthData.service} v{healthData.version}
                </Typography>
              </Box>
              {getStatusChip(healthData.status)}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Component Status Cards */}
      <Grid container spacing={3}>
        {healthData &&
          Object.entries(healthData.components).map(([key, component]) => (
            <Grid item xs={12} sm={6} md={4} key={key}>
              <Card
                sx={{
                  height: '100%',
                  borderLeft: 4,
                  borderColor: getStatusColor(component.status) === 'success' ? 'success.main' : getStatusColor(component.status) === 'warning' ? 'warning.main' : 'error.main',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                    <Box
                      sx={{
                        mr: 2,
                        color: getStatusColor(component.status) === 'success' ? 'success.main' : getStatusColor(component.status) === 'warning' ? 'warning.main' : 'error.main',
                      }}
                    >
                      {getComponentIcon(component.name)}
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                        {getComponentDisplayName(component.name)}
                      </Typography>
                      {getStatusChip(component.status)}
                    </Box>
                  </Box>

                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {component.message}
                    </Typography>

                    {component.response_time_ms !== undefined && (
                      <Typography variant="caption" color="text.secondary">
                        Response time: {component.response_time_ms.toFixed(2)}ms
                      </Typography>
                    )}

                    {component.degraded_mode !== undefined && component.degraded_mode && (
                      <Chip
                        label="Degraded Mode"
                        size="small"
                        color="warning"
                        variant="outlined"
                        sx={{ mt: 1 }}
                      />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
      </Grid>

      {/* Health History Trend */}
      <Paper sx={{ mt: 4, p: 3 }} elevation={2}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TimelineIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Health History (Last 30 Minutes)
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Chip
              label={`${healthHistoryRef.current.filter((e) => e.status === 'healthy').length} Healthy`}
              color="success"
              size="small"
            />
            <Chip
              label={`${healthHistoryRef.current.filter((e) => e.status === 'degraded').length} Degraded`}
              color="warning"
              size="small"
            />
            <Chip
              label={`${healthHistoryRef.current.filter((e) => e.status === 'unhealthy').length} Unhealthy`}
              color="error"
              size="small"
            />
          </Box>
        </Box>

        {healthHistoryRef.current.length === 0 ? (
          <Alert severity="info">
            Health history is being collected. Check back in a few moments.
          </Alert>
        ) : (
          <Box>
            {/* Uptime Summary */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Card variant="outlined">
                  <CardContent sx={{ textAlign: 'center', py: 1 }}>
                    <Typography variant="h4" color="success.main" fontWeight={700}>
                      {healthHistoryRef.current.length > 0
                        ? Math.round(
                            (healthHistoryRef.current.filter((e) => e.status === 'healthy').length /
                              healthHistoryRef.current.length) *
                              100
                          )
                        : 0}
                      %
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Uptime (Healthy)
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card variant="outlined">
                  <CardContent sx={{ textAlign: 'center', py: 1 }}>
                    <Typography variant="h4" color="warning.main" fontWeight={700}>
                      {healthHistoryRef.current.length > 0
                        ? Math.round(
                            (healthHistoryRef.current.filter((e) => e.status === 'degraded').length /
                              healthHistoryRef.current.length) *
                              100
                          )
                        : 0}
                      %
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Degraded Time
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card variant="outlined">
                  <CardContent sx={{ textAlign: 'center', py: 1 }}>
                    <Typography variant="h4" color="error.main" fontWeight={700}>
                      {healthHistoryRef.current.length > 0
                        ? Math.round(
                            (healthHistoryRef.current.filter((e) => e.status === 'unhealthy').length /
                              healthHistoryRef.current.length) *
                              100
                          )
                        : 0}
                      %
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Downtime (Unhealthy)
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card variant="outlined">
                  <CardContent sx={{ textAlign: 'center', py: 1 }}>
                    <Typography variant="h4" fontWeight={700}>
                      {healthHistoryRef.current.length}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Data Points
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Timeline Visualization */}
            <Typography variant="subtitle2" gutterBottom fontWeight={600}>
              System Status Timeline
            </Typography>
            <Box
              sx={{
                display: 'flex',
                gap: 0.5,
                height: 60,
                alignItems: 'center',
                overflow: 'hidden',
              }}
            >
              {healthHistoryRef.current.map((entry, index) => {
                const color =
                  entry.status === 'healthy'
                    ? 'success.main'
                    : entry.status === 'degraded'
                    ? 'warning.main'
                    : 'error.main';
                return (
                  <Box
                    key={`${entry.timestamp}-${index}`}
                    sx={{
                      flex: 1,
                      height: '100%',
                      bgcolor: color,
                      minWidth: 2,
                      borderRadius: 0.5,
                      transition: 'transform 0.2s',
                      '&:hover': {
                        transform: 'scaleY(1.1)',
                      },
                    }}
                    title={`${format(new Date(entry.timestamp), 'HH:mm:ss')} - ${entry.status.toUpperCase()}`}
                  />
                );
              })}
            </Box>

            {/* Degradation Events */}
            {healthHistoryRef.current.some((e) => e.status !== 'healthy') && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                  Degradation Events
                </Typography>
                <Stack spacing={1}>
                  {healthHistoryRef.current
                    .filter((e) => e.status !== 'healthy')
                    .slice(-10)
                    .reverse()
                    .map((entry, index) => (
                      <Card
                        key={`event-${index}`}
                        variant="outlined"
                        sx={{
                          borderLeft: 4,
                          borderColor:
                            entry.status === 'degraded' ? 'warning.main' : 'error.main',
                        }}
                      >
                        <CardContent sx={{ py: 1.5, px: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {entry.status === 'degraded' ? (
                                <WarningIcon color="warning" fontSize="small" />
                              ) : (
                                <ErrorIcon color="error" fontSize="small" />
                              )}
                              <Typography variant="body2" fontWeight={600}>
                                {entry.status === 'degraded' ? 'Degraded' : 'Unhealthy'}
                              </Typography>
                            </Box>
                            <Typography variant="caption" color="text.secondary">
                              {format(new Date(entry.timestamp), 'HH:mm:ss')}
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    ))}
                </Stack>
              </Box>
            )}
          </Box>
        )}
      </Paper>

      {/* System Information */}
      {healthData && (
        <Card sx={{ mt: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              System Information
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Service Name
                </Typography>
                <Typography variant="body1" fontWeight={500}>
                  {healthData.service}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Version
                </Typography>
                <Typography variant="body1" fontWeight={500}>
                  {healthData.version}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Timestamp
                </Typography>
                <Typography variant="body1" fontWeight={500}>
                  {format(new Date(healthData.timestamp), 'PPpp')}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Components Monitored
                </Typography>
                <Typography variant="body1" fontWeight={500}>
                  {Object.keys(healthData.components).length}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Status Legend */}
      <Paper sx={{ mt: 4, p: 3 }}>
        <Typography variant="subtitle2" gutterBottom fontWeight={600}>
          Status Legend
        </Typography>
        <Stack direction="row" spacing={3}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CheckCircleIcon color="success" />
            <Typography variant="body2">
              <strong>Healthy:</strong> Component is functioning normally
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WarningIcon color="warning" />
            <Typography variant="body2">
              <strong>Degraded:</strong> Component has issues but system can function
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ErrorIcon color="error" />
            <Typography variant="body2">
              <strong>Unhealthy:</strong> Component is not functioning properly
            </Typography>
          </Box>
        </Stack>
      </Paper>
    </Container>
  );
};

export { SystemHealthPage };
export default SystemHealthPage;
