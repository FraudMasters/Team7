import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Paper,
  Stack,
  Button,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Warning as DegradedIcon,
  Error as UnhealthyIcon,
  Refresh as RefreshIcon,
  Storage as DatabaseIcon,
  Memory as RedisIcon,
  Speed as CeleryIcon,
  Psychology as MLModelIcon,
  Cloud as ExternalApiIcon,
  Hub as DependencyIcon,
  Timeline as ResponseTimeIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import {
  getDetailedHealth,
  getDependencyGraph,
  getHealthCheckResult,
} from '@/api/health';
import type {
  DetailedHealthResponse,
  DependencyGraphResponse,
  ComponentHealthStatus,
} from '@/types/api';
import LoadingSpinner from '../components/LoadingSpinner';
import DependencyGraph from '../components/DependencyGraph';

/**
 * Health Dashboard Page
 *
 * Central health monitoring dashboard showing:
 * - Overall system health status
 * - Individual component health cards
 * - Service dependency information
 * - Auto-refresh functionality
 */
const HealthDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [healthData, setHealthData] = useState<DetailedHealthResponse | null>(null);
  const [dependencyData, setDependencyData] = useState<DependencyGraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  /**
   * Fetch health data from API
   */
  const fetchHealthData = useCallback(async () => {
    try {
      setError(null);
      const [health, deps] = await Promise.all([
        getDetailedHealth(),
        getDependencyGraph(),
      ]);
      setHealthData(health);
      setDependencyData(deps);
      setLastRefresh(new Date());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch health data';
      setError(errorMessage);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  /**
   * Manual refresh handler
   */
  const handleRefresh = () => {
    setRefreshing(true);
    fetchHealthData();
  };

  /**
   * Initial data fetch
   */
  useEffect(() => {
    fetchHealthData();
  }, [fetchHealthData]);

  /**
   * Auto-refresh every 30 seconds
   */
  useEffect(() => {
    const interval = setInterval(() => {
      fetchHealthData();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchHealthData]);

  /**
   * Get status color for chip
   */
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

  /**
   * Get status icon
   */
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <HealthyIcon />;
      case 'degraded':
        return <DegradedIcon />;
      case 'unhealthy':
        return <UnhealthyIcon />;
      default:
        return <UnhealthyIcon />;
    }
  };

  /**
   * Get icon for component type
   */
  const getComponentIcon = (name: string) => {
    switch (name) {
      case 'database':
        return <DatabaseIcon sx={{ fontSize: 32 }} />;
      case 'redis':
        return <RedisIcon sx={{ fontSize: 32 }} />;
      case 'celery':
        return <CeleryIcon sx={{ fontSize: 32 }} />;
      case 'ml_ner_model':
      case 'ml_zero_shot_model':
      case 'ml_language_tools':
        return <MLModelIcon sx={{ fontSize: 32 }} />;
      case 'external_api':
        return <ExternalApiIcon sx={{ fontSize: 32 }} />;
      default:
        return <DependencyIcon sx={{ fontSize: 32 }} />;
    }
  };

  /**
   * Get display name for component
   */
  const getDisplayName = (name: string): string => {
    const names: Record<string, string> = {
      database: 'Database',
      redis: 'Redis Cache',
      celery: 'Celery Workers',
      ml_ner_model: 'NER Model',
      ml_zero_shot_model: 'Zero-Shot Model',
      ml_language_tools: 'Language Tools',
      external_api: 'External APIs',
    };
    return names[name] || name;
  };

  /**
   * Get category display name
   */
  const getCategoryName = (category: string): string => {
    const categories: Record<string, string> = {
      infrastructure: 'Infrastructure',
      messaging: 'Messaging',
      ml: 'Machine Learning',
      external: 'External Services',
    };
    return categories[category] || category;
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <LoadingSpinner variant="dashboard" message="Loading health status..." />
      </Container>
    );
  }

  /**
   * Render error state
   */
  if (error && !healthData) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }} className="health-dashboard">
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" component="h1" fontWeight={700} gutterBottom>
            System Health Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time monitoring of all system components and services
          </Typography>
        </Box>
        <Stack direction="row" spacing={2} alignItems="center">
          {lastRefresh && (
            <Typography variant="caption" color="text.secondary">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </Typography>
          )}
          <Button
            variant="outlined"
            startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={handleRefresh}
            disabled={refreshing}
            size="small"
          >
            Refresh
          </Button>
        </Stack>
      </Box>

      {/* Overall Status Alert */}
      {healthData && (
        <Box sx={{ mb: 4 }}>
          <Alert
            severity={getStatusColor(healthData.status)}
            sx={{
              display: 'flex',
              alignItems: 'center',
              '& .MuiAlert-icon': {
                fontSize: 28,
              },
            }}
          >
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" fontWeight={600}>
                Overall System Status: {healthData.status.toUpperCase()}
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                Health Score: {healthData.overall_health_percentage}%
                {healthData.critical_issues.length > 0 && (
                  <Box component="span" sx={{ ml: 2 }}>
                    • {healthData.critical_issues.length} critical issue(s)
                  </Box>
                )}
                {healthData.warnings.length > 0 && (
                  <Box component="span" sx={{ ml: 2 }}>
                    • {healthData.warnings.length} warning(s)
                  </Box>
                )}
              </Typography>
            </Box>
          </Alert>

          {/* Critical Issues */}
          {healthData.critical_issues.length > 0 && (
            <Alert severity="error" sx={{ mt: 2 }}>
              <Typography variant="subtitle2" fontWeight={600}>
                Critical Issues:
              </Typography>
              <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
                {healthData.critical_issues.map((issue, idx) => (
                  <Typography component="li" variant="body2" key={idx}>
                    {issue}
                  </Typography>
                ))}
              </Box>
            </Alert>
          )}

          {/* Warnings */}
          {healthData.warnings.length > 0 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              <Typography variant="subtitle2" fontWeight={600}>
                Warnings:
              </Typography>
              <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
                {healthData.warnings.map((warning, idx) => (
                  <Typography component="li" variant="body2" key={idx}>
                    {warning}
                  </Typography>
                ))}
              </Box>
            </Alert>
          )}
        </Box>
      )}

      {/* Service Status Cards */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" fontWeight={600} gutterBottom>
          Service Status
        </Typography>
        <Grid container spacing={3} columns={{ xs: 12, sm: 12, md: 12 }}>
          {healthData &&
            Object.entries(healthData.checks).map(([name, check]) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={name}>
                <Card
                  sx={{
                    height: '100%',
                    borderLeft: 4,
                    borderColor: `${getStatusColor(check.status)}.main`,
                    transition: 'all 0.2s',
                    '&:hover': {
                      boxShadow: 4,
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Box
                        sx={{
                          width: 48,
                          height: 48,
                          borderRadius: 2,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: `${getStatusColor(check.status)}.main`,
                          color: 'white',
                          mr: 2,
                        }}
                      >
                        {getComponentIcon(name)}
                      </Box>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle1" fontWeight={600} noWrap>
                          {getDisplayName(name)}
                        </Typography>
                        <Chip
                          icon={getStatusIcon(check.status)}
                          label={check.status.toUpperCase()}
                          size="small"
                          color={getStatusColor(check.status)}
                          sx={{ mt: 0.5 }}
                        />
                      </Box>
                    </Box>

                    <Stack spacing={1} sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Category
                        </Typography>
                        <Typography variant="caption" fontWeight={500}>
                          {getCategoryName(check.category)}
                        </Typography>
                      </Box>
                      {check.response_time_ms !== undefined && (
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" color="text.secondary">
                            Response Time
                          </Typography>
                          <Typography variant="caption" fontWeight={500}>
                            {check.response_time_ms}ms
                          </Typography>
                        </Box>
                      )}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="caption" color="text.secondary">
                          Essential
                        </Typography>
                        <Chip
                          label={check.essential ? 'Yes' : 'No'}
                          size="small"
                          variant={check.essential ? 'filled' : 'outlined'}
                          color={check.essential ? 'primary' : 'default'}
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      </Box>
                    </Stack>

                    {check.error && (
                      <Alert severity="error" sx={{ mt: 1 }}>
                        <Typography variant="caption" sx={{ wordBreak: 'break-word' }}>
                          {check.error}
                        </Typography>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
        </Grid>
      </Box>

      {/* Dependency Summary */}
      {dependencyData && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" fontWeight={600} gutterBottom>
            Service Dependencies
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" fontWeight={700} color="primary.main">
                  {dependencyData.summary.total_services}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Services
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" fontWeight={700} color="success.main">
                  {dependencyData.summary.essential_services}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Essential Services
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" fontWeight={700} color="info.main">
                  {dependencyData.summary.max_dependency_depth}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Max Dependency Depth
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body1" fontWeight={600} color="text.secondary">
                  {dependencyData.summary.critical_path.join(' → ')}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Critical Path
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Dependency Graph Visualization */}
      {dependencyData && healthData && (
        <Box sx={{ mb: 4 }}>
          <DependencyGraph
            dependencyData={dependencyData}
            healthData={healthData}
          />
        </Box>
      )}

      {/* Footer info */}
      <Box sx={{ mt: 4, pt: 2, borderTop: 1, borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary">
          Health data auto-refreshes every 30 seconds. Click the Refresh button to update immediately.
        </Typography>
      </Box>
    </Container>
  );
};

export default HealthDashboard;
