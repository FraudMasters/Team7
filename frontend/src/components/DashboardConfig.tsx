import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Chip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Close as CloseIcon,
  Save as SaveIcon,
  DragIndicator as DragIndicatorIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
} from '@mui/icons-material';
import { getDashboardConfig, updateDashboardConfig } from '@/api/preferences';
import type { DashboardConfigResponse } from '@/types/api';

/**
 * Widget configuration interface
 */
interface WidgetConfig {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  icon?: React.ReactNode;
}

/**
 * Available widget definitions
 */
const AVAILABLE_WIDGETS: WidgetConfig[] = [
  {
    id: 'metrics',
    name: 'Key Metrics',
    description: 'Display key hiring metrics and pipeline statistics',
    enabled: true,
  },
  {
    id: 'recent-candidates',
    name: 'Recent Candidates',
    description: 'Show recently added or updated candidates',
    enabled: true,
  },
  {
    id: 'upcoming-interviews',
    name: 'Upcoming Interviews',
    description: 'Display scheduled interviews for the next 7 days',
    enabled: true,
  },
  {
    id: 'activity-feed',
    name: 'Activity Feed',
    description: 'Recent activities and updates across the system',
    enabled: false,
  },
  {
    id: 'top-matches',
    name: 'Top Matches',
    description: 'Best matching candidates for recent job postings',
    enabled: true,
  },
  {
    id: 'tasks',
    name: 'Tasks & Reminders',
    description: 'Personal task list and upcoming deadlines',
    enabled: false,
  },
];

/**
 * Dashboard layout options
 */
interface LayoutOption {
  id: string;
  name: string;
  description: string;
}

/**
 * Available layout options
 */
const LAYOUT_OPTIONS: LayoutOption[] = [
  {
    id: 'grid',
    name: 'Grid Layout',
    description: 'Widgets arranged in a responsive grid',
  },
  {
    id: 'list',
    name: 'List Layout',
    description: 'Widgets stacked vertically in a single column',
  },
  {
    id: 'compact',
    name: 'Compact Layout',
    description: 'Dense widget arrangement for maximum information density',
  },
];

/**
 * DashboardConfig Component Props
 */
interface DashboardConfigProps {
  /** Callback when configuration is saved */
  onConfigSave?: (config: DashboardConfigResponse) => void;
  /** API endpoint URL for dashboard preferences */
  apiUrl?: string;
}

/**
 * DashboardConfig Component
 *
 * Provides a comprehensive interface for configuring dashboard layout and widgets.
 * Features include:
 * - Choose dashboard layout style (grid/list/compact)
 * - Enable/disable dashboard widgets
 * - Reorder widgets to control display priority
 * - Preview widget configuration
 * - Persist configuration to backend
 *
 * @example
 * ```tsx
 * <DashboardConfig onConfigSave={(config) => console.log('Saved', config)} />
 * ```
 */
const DashboardConfig: React.FC<DashboardConfigProps> = ({
  onConfigSave,
  apiUrl = 'http://localhost:8000/api/preferences',
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Dashboard configuration state
  const [layout, setLayout] = useState<string>('grid');
  const [widgetOrder, setWidgetOrder] = useState<string[]>([]);
  const [enabledWidgets, setEnabledWidgets] = useState<Record<string, boolean>>({});

  /**
   * Fetch dashboard configuration from backend
   */
  const fetchConfig = async () => {
    setLoading(true);
    setError(null);

    try {
      const config: DashboardConfigResponse = await getDashboardConfig();

      // Set layout (default to 'grid' if not configured)
      setLayout(config.layout || 'grid');

      // Parse widgets configuration
      if (config.widgets) {
        const widgets = config.widgets as Record<string, unknown>;
        const order = (widgets.widget_order as string[]) || AVAILABLE_WIDGETS.map((w) => w.id);
        const enabled = (widgets.enabled_widgets as Record<string, boolean>) || {};

        setWidgetOrder(order);
        setEnabledWidgets(enabled);
      } else {
        // Default configuration
        const defaultOrder = AVAILABLE_WIDGETS.filter((w) => w.enabled).map((w) => w.id);
        const defaultEnabled = AVAILABLE_WIDGETS.reduce((acc, w) => ({
          ...acc,
          [w.id]: w.enabled,
        }), {} as Record<string, boolean>);

        setWidgetOrder(defaultOrder);
        setEnabledWidgets(defaultEnabled);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load dashboard configuration';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  /**
   * Save dashboard configuration
   */
  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const config: DashboardConfigResponse = await updateDashboardConfig({
        layout,
        widgets: {
          widget_order: widgetOrder,
          enabled_widgets: enabledWidgets,
        },
      });

      setSuccessMessage('Dashboard configuration saved successfully');

      if (onConfigSave) {
        onConfigSave(config);
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to save dashboard configuration';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  /**
   * Move widget up in order
   */
  const handleMoveUp = (widgetId: string) => {
    const currentIndex = widgetOrder.indexOf(widgetId);
    if (currentIndex > 0) {
      const newOrder = [...widgetOrder];
      [newOrder[currentIndex - 1], newOrder[currentIndex]] = [newOrder[currentIndex], newOrder[currentIndex - 1]];
      setWidgetOrder(newOrder);
    }
  };

  /**
   * Move widget down in order
   */
  const handleMoveDown = (widgetId: string) => {
    const currentIndex = widgetOrder.indexOf(widgetId);
    if (currentIndex < widgetOrder.length - 1) {
      const newOrder = [...widgetOrder];
      [newOrder[currentIndex], newOrder[currentIndex + 1]] = [newOrder[currentIndex + 1], newOrder[currentIndex]];
      setWidgetOrder(newOrder);
    }
  };

  /**
   * Toggle widget enabled state
   */
  const handleToggleWidget = (widgetId: string) => {
    setEnabledWidgets({
      ...enabledWidgets,
      [widgetId]: !enabledWidgets[widgetId],
    });
  };

  /**
   * Get widget info by ID
   */
  const getWidgetInfo = (widgetId: string): WidgetConfig | undefined => {
    return AVAILABLE_WIDGETS.find((w) => w.id === widgetId);
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          Loading dashboard configuration...
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" onClick={fetchConfig} startIcon={<RefreshIcon />}>
            Try Again
          </Button>
        }
      >
        <AlertTitle>Error</AlertTitle>
        {error}
      </Alert>
    );
  }

  const enabledCount = Object.values(enabledWidgets).filter(Boolean).length;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Dashboard Configuration
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchConfig}
            size="small"
          >
            Refresh
          </Button>
        </Box>

        {/* Summary Statistics */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'primary.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {AVAILABLE_WIDGETS.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Available Widgets
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'success.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {enabledCount}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Enabled
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'info.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {layout.charAt(0).toUpperCase() + layout.slice(1)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Current Layout
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Save Button */}
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
          {successMessage && (
            <Alert severity="success" sx={{ flex: 1 }}>
              {successMessage}
            </Alert>
          )}
          <Button
            variant="contained"
            startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
            onClick={handleSave}
            disabled={saving}
            size="large"
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </Button>
        </Box>
      </Paper>

      {/* Layout Selection */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Dashboard Layout
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Choose how widgets are arranged on your dashboard
        </Typography>

        <Grid container spacing={2}>
          {LAYOUT_OPTIONS.map((option) => (
            <Grid item xs={12} md={4} key={option.id}>
              <Card
                variant="outlined"
                sx={{
                  cursor: 'pointer',
                  border: layout === option.id ? 2 : 1,
                  borderColor: layout === option.id ? 'primary.main' : 'divider',
                  transition: 'all 0.2s',
                  '&:hover': {
                    boxShadow: 3,
                  },
                }}
                onClick={() => setLayout(option.id)}
              >
                <CardContent>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    {option.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {option.description}
                  </Typography>
                  {layout === option.id && (
                    <Chip
                      label="Active"
                      size="small"
                      color="primary"
                      variant="filled"
                      sx={{ mt: 2 }}
                    />
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Widget Configuration */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Widget Configuration
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Enable/disable widgets and reorder them to control display priority
        </Typography>

        <Stack spacing={2}>
          {widgetOrder.map((widgetId, index) => {
            const widget = getWidgetInfo(widgetId);
            if (!widget) return null;

            const isEnabled = enabledWidgets[widgetId] !== false;

            return (
              <Card
                key={widget.id}
                variant="outlined"
                sx={{
                  opacity: isEnabled ? 1 : 0.6,
                  transition: 'all 0.2s',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
                      <DragIndicatorIcon color="action" />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {widget.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {widget.description}
                        </Typography>
                      </Box>
                    </Box>

                    <Stack direction="row" spacing={1} alignItems="center">
                      <FormControlLabel
                        control={
                          <Switch
                            checked={isEnabled}
                            onChange={() => handleToggleWidget(widget.id)}
                            color="primary"
                          />
                        }
                        label={isEnabled ? 'Enabled' : 'Disabled'}
                      />

                      <Divider orientation="vertical" flexItem />

                      <IconButton
                        size="small"
                        onClick={() => handleMoveUp(widget.id)}
                        disabled={index === 0}
                        color="primary"
                      >
                        <ArrowUpwardIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleMoveDown(widget.id)}
                        disabled={index === widgetOrder.length - 1}
                        color="primary"
                      >
                        <ArrowDownwardIcon fontSize="small" />
                      </IconButton>
                    </Stack>
                  </Box>
                </CardContent>
              </Card>
            );
          })}
        </Stack>

        {/* Legend */}
        <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">
            <strong>Tip:</strong> Drag widgets or use arrow buttons to reorder them.
            Widgets at the top appear first on your dashboard. Disabled widgets are hidden.
          </Typography>
        </Box>
      </Paper>
    </Stack>
  );
};

export default DashboardConfig;
