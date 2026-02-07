import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  IconButton,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  Chip,
  FormControlLabel,
  Switch,
  TextField,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Close as CloseIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  ArrowUpward as UpIcon,
  ArrowDownward as DownIcon,
  Remove as RemoveIcon,
  Add as AddIcon,
  Dashboard as DashboardIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';

/**
 * Available widget definition
 */
interface AvailableWidget {
  id: string;
  name: string;
  description: string;
  category: 'overview' | 'pipeline' | 'performance' | 'analytics';
  icon: React.ReactNode;
  required: boolean;
}

/**
 * Selected widget in dashboard
 */
interface SelectedWidget {
  id: string;
  name: string;
  description: string;
  category: string;
  required: boolean;
}

/**
 * Dashboard configuration from backend
 */
interface DashboardConfiguration {
  id: string;
  organization_id: string;
  user_id?: string;
  name: string;
  widgets: string[];
  filters: Record<string, string | boolean | number>;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Form data for dashboard configuration
 */
interface DashboardFormData {
  name: string;
  is_default: boolean;
}

/**
 * DashboardCustomizer Component Props
 */
interface DashboardCustomizerProps {
  /** Organization ID for dashboard configuration */
  organizationId?: string;
  /** User ID for personalized dashboards */
  userId?: string;
  /** API endpoint URL for dashboard configurations */
  apiUrl?: string;
  /** Callback when dashboard configuration is saved */
  onDashboardChange?: (config: DashboardConfiguration) => void;
  /** Current active widgets */
  currentWidgets?: string[];
}

/**
 * DashboardCustomizer Component
 *
 * Provides a modal interface for customizing the analytics dashboard.
 * Features include:
 * - Browse and select available widgets
 * - Reorder widgets to customize layout
 * - Save and load dashboard configurations
 * - Set default dashboard configuration
 * - Real-time preview of dashboard configuration
 *
 * @example
 * ```tsx
 * <DashboardCustomizer organizationId="org123" />
 * ```
 */
const DashboardCustomizer: React.FC<DashboardCustomizerProps> = ({
  organizationId = 'default-org',
  userId,
  apiUrl = 'http://localhost:8000/api/analytics/dashboards',
  onDashboardChange,
  currentWidgets = [],
}) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [dashboardConfigs, setDashboardConfigs] = useState<DashboardConfiguration[]>([]);
  const [selectedWidgets, setSelectedWidgets] = useState<SelectedWidget[]>([]);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [editingConfig, setEditingConfig] = useState<DashboardConfiguration | null>(null);

  // Form state
  const [formData, setFormData] = useState<DashboardFormData>({
    name: '',
    is_default: false,
  });

  // Available widgets for the dashboard
  const [availableWidgets] = useState<AvailableWidget[]>([
    {
      id: 'key-metrics',
      name: 'Key Metrics',
      description: 'Time-to-hire, resume processing, and match rate statistics',
      category: 'overview',
      icon: <DashboardIcon />,
      required: true,
    },
    {
      id: 'funnel',
      name: 'Funnel Visualization',
      description: 'Candidate progression through pipeline stages',
      category: 'pipeline',
      icon: <DashboardIcon />,
      required: true,
    },
    {
      id: 'source-tracking',
      name: 'Source Tracking',
      description: 'Vacancy and hire distribution by source',
      category: 'pipeline',
      icon: <DashboardIcon />,
      required: false,
    },
    {
      id: 'recruiter-performance',
      name: 'Recruiter Performance',
      description: 'Individual recruiter metrics and comparisons',
      category: 'performance',
      icon: <DashboardIcon />,
      required: false,
    },
    {
      id: 'skill-demand',
      name: 'Skill Demand',
      description: 'Most requested skills and trending technologies',
      category: 'analytics',
      icon: <DashboardIcon />,
      required: false,
    },
    {
      id: 'fairness-dashboard',
      name: 'Fairness Dashboard',
      description: 'Diversity and inclusion metrics',
      category: 'analytics',
      icon: <DashboardIcon />,
      required: false,
    },
    {
      id: 'predictive-analytics',
      name: 'Predictive Analytics',
      description: 'Pipeline forecasting and hiring predictions',
      category: 'analytics',
      icon: <DashboardIcon />,
      required: false,
    },
  ]);

  /**
   * Fetch dashboard configurations from backend
   */
  const fetchDashboardConfigs = async () => {
    setLoading(true);
    setError(null);

    try {
      const url = userId
        ? `${apiUrl}/?organization_id=${organizationId}&user_id=${userId}`
        : `${apiUrl}/?organization_id=${organizationId}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch dashboard configurations: ${response.statusText}`);
      }

      const result = await response.json();
      setDashboardConfigs(result.dashboards || result || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load dashboard configurations';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Open the customizer modal
   */
  const handleOpen = () => {
    setOpen(true);
    fetchDashboardConfigs();

    // Initialize selected widgets from current widgets or default
    if (currentWidgets.length > 0) {
      const initializedWidgets = currentWidgets
        .map((widgetId) => availableWidgets.find((w) => w.id === widgetId))
        .filter((w): w is AvailableWidget => w !== undefined)
        .map((w) => ({
          id: w.id,
          name: w.name,
          description: w.description,
          category: w.category,
          required: w.required,
        }));
      setSelectedWidgets(initializedWidgets);
    } else {
      // Load default required widgets
      const defaultWidgets = availableWidgets
        .filter((w) => w.required)
        .map((w) => ({
          id: w.id,
          name: w.name,
          description: w.description,
          category: w.category,
          required: w.required,
        }));
      setSelectedWidgets(defaultWidgets);
    }

    setFormData({
      name: '',
      is_default: false,
    });
    setEditingConfig(null);
    setError(null);
    setSuccess(false);
  };

  /**
   * Close the customizer modal
   */
  const handleClose = () => {
    if (!submitting) {
      setOpen(false);
      setError(null);
      setSuccess(false);
    }
  };

  /**
   * Add widget to selected list
   */
  const handleAddWidget = (widget: AvailableWidget) => {
    if (selectedWidgets.find((w) => w.id === widget.id)) {
      return; // Already selected
    }
    setSelectedWidgets([
      ...selectedWidgets,
      {
        id: widget.id,
        name: widget.name,
        description: widget.description,
        category: widget.category,
        required: widget.required,
      },
    ]);
  };

  /**
   * Remove widget from selected list
   */
  const handleRemoveWidget = (widgetId: string) => {
    const widget = availableWidgets.find((w) => w.id === widgetId);
    if (widget?.required) {
      setError('Required widgets cannot be removed');
      return;
    }
    setSelectedWidgets(selectedWidgets.filter((w) => w.id !== widgetId));
    setError(null);
  };

  /**
   * Move widget up in selected list
   */
  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    const newWidgets = [...selectedWidgets];
    [newWidgets[index - 1], newWidgets[index]] = [newWidgets[index], newWidgets[index - 1]];
    setSelectedWidgets(newWidgets);
  };

  /**
   * Move widget down in selected list
   */
  const handleMoveDown = (index: number) => {
    if (index === selectedWidgets.length - 1) return;
    const newWidgets = [...selectedWidgets];
    [newWidgets[index], newWidgets[index + 1]] = [newWidgets[index + 1], newWidgets[index]];
    setSelectedWidgets(newWidgets);
  };

  /**
   * Drag start handler
   */
  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  /**
   * Drag over handler
   */
  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;

    const newWidgets = [...selectedWidgets];
    const draggedItem = newWidgets[draggedIndex];
    newWidgets.splice(draggedIndex, 1);
    newWidgets.splice(index, 0, draggedItem);
    setSelectedWidgets(newWidgets);
    setDraggedIndex(index);
  };

  /**
   * Drag end handler
   */
  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  /**
   * Reset to default widgets
   */
  const handleReset = () => {
    const defaultWidgets = availableWidgets
      .filter((w) => w.required)
      .map((w) => ({
        id: w.id,
        name: w.name,
        description: w.description,
        category: w.category,
        required: w.required,
      }));
    setSelectedWidgets(defaultWidgets);
    setError(null);
  };

  /**
   * Load a saved dashboard configuration
   */
  const handleLoadConfig = (config: DashboardConfiguration) => {
    const loadedWidgets = config.widgets
      .map((widgetId) => availableWidgets.find((w) => w.id === widgetId))
      .filter((w): w is AvailableWidget => w !== undefined)
      .map((w) => ({
        id: w.id,
        name: w.name,
        description: w.description,
        category: w.category,
        required: w.required,
      }));

    setSelectedWidgets(loadedWidgets);
    setEditingConfig(config);
    setFormData({
      name: config.name,
      is_default: config.is_default,
    });
    setError(null);
  };

  /**
   * Save dashboard configuration
   */
  const handleSave = async () => {
    if (selectedWidgets.length === 0) {
      setError('Please select at least one widget');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const configData = {
        name: formData.name || 'My Dashboard',
        organization_id: organizationId,
        user_id: userId,
        widgets: selectedWidgets.map((w) => w.id),
        filters: {},
        is_default: formData.is_default,
      };

      let response;

      if (editingConfig) {
        // Update existing configuration
        response = await fetch(`${apiUrl}/${editingConfig.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(configData),
        });
      } else {
        // Create new configuration
        response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(configData),
        });
      }

      if (!response.ok) {
        throw new Error(`Failed to save dashboard configuration: ${response.statusText}`);
      }

      const saved: DashboardConfiguration = await response.json();

      // Update dashboard configs list
      if (editingConfig) {
        setDashboardConfigs(dashboardConfigs.map((c) => (c.id === saved.id ? saved : c)));
      } else {
        setDashboardConfigs([...dashboardConfigs, saved]);
      }

      setEditingConfig(saved);
      setSuccess(true);

      if (onDashboardChange) {
        onDashboardChange(saved);
      }

      // Close modal after a short delay to show success message
      setTimeout(() => {
        handleClose();
      }, 1000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save dashboard configuration';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Apply changes without saving
   */
  const handleApply = () => {
    if (selectedWidgets.length === 0) {
      setError('Please select at least one widget');
      return;
    }

    // Create a temporary config object to pass back
    const tempConfig: DashboardConfiguration = {
      id: editingConfig?.id || 'temp',
      organization_id: organizationId,
      user_id: userId,
      name: formData.name || 'My Dashboard',
      widgets: selectedWidgets.map((w) => w.id),
      filters: {},
      is_default: formData.is_default,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    if (onDashboardChange) {
      onDashboardChange(tempConfig);
    }

    handleClose();
  };

  /**
   * Get category color
   */
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'overview':
        return 'primary' as const;
      case 'pipeline':
        return 'info' as const;
      case 'performance':
        return 'success' as const;
      case 'analytics':
        return 'warning' as const;
      default:
        return 'default' as const;
    }
  };

  return (
    <>
      {/* Trigger Button */}
      <Button
        variant="outlined"
        startIcon={<SettingsIcon />}
        onClick={handleOpen}
        size="small"
      >
        Customize Dashboard
      </Button>

      {/* Customizer Dialog */}
      <Dialog
        open={open}
        onClose={handleClose}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '80vh' },
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <DashboardIcon color="primary" sx={{ fontSize: 32 }} />
              <Box>
                <Typography variant="h6" fontWeight={600}>
                  Customize Dashboard
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Add, remove, and reorder dashboard widgets
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<RefreshIcon />}
                onClick={fetchDashboardConfigs}
                disabled={loading}
              >
                Refresh
              </Button>
              <IconButton onClick={handleClose} disabled={submitting} size="small">
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>

        <DialogContent sx={{ pb: 2 }}>
          <Stack spacing={3} sx={{ height: '100%' }}>
            {/* Success Message */}
            {success && (
              <Alert severity="success" onClose={() => setSuccess(false)}>
                <AlertTitle>Success</AlertTitle>
                Dashboard configuration saved successfully!
              </Alert>
            )}

            {/* Error Message */}
            {error && (
              <Alert severity="error" onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            {/* Dashboard Name and Settings */}
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Dashboard Name"
                    fullWidth
                    size="small"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., My Analytics Dashboard"
                    disabled={submitting}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={formData.is_default}
                          onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                          disabled={submitting}
                        />
                      }
                      label="Set as default"
                    />
                  </Box>
                </Grid>
              </Grid>

              {/* Saved Configurations */}
              {dashboardConfigs.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="text.secondary" gutterBottom>
                    Load saved configuration:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
                    {dashboardConfigs.map((config) => (
                      <Chip
                        key={config.id}
                        label={config.name}
                        onClick={() => handleLoadConfig(config)}
                        onDelete={
                          editingConfig?.id === config.id
                            ? undefined
                            : () => handleLoadConfig(config)
                        }
                        deleteIcon={<CheckIcon />}
                        color={editingConfig?.id === config.id ? 'primary' : 'default'}
                        variant={editingConfig?.id === config.id ? 'filled' : 'outlined'}
                        sx={{ cursor: 'pointer' }}
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </Paper>

            {/* Widgets Selection */}
            <Grid container spacing={2} sx={{ flex: 1, overflow: 'hidden' }}>
              {/* Available Widgets */}
              <Grid item xs={12} md={6} sx={{ display: 'flex', flexDirection: 'column' }}>
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                  }}
                >
                  <Typography variant="subtitle1" gutterBottom fontWeight={600}>
                    Available Widgets
                  </Typography>
                  <Typography variant="caption" color="text.secondary" paragraph>
                    Click to add widgets to your dashboard
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <Box sx={{ flex: 1, overflow: 'auto' }}>
                    <Stack spacing={1}>
                      {availableWidgets.map((widget) => {
                        const isSelected = selectedWidgets.find((w) => w.id === widget.id);
                        return (
                          <Card
                            key={widget.id}
                            variant="outlined"
                            sx={{
                              cursor: widget.required ? 'default' : isSelected ? 'default' : 'pointer',
                              opacity: isSelected ? 0.5 : 1,
                              '&:hover': !widget.required && !isSelected ? { boxShadow: 3 } : {},
                              transition: 'all 0.2s',
                            }}
                            onClick={() => !widget.required && !isSelected && handleAddWidget(widget)}
                          >
                            <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                              <Box
                                sx={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                }}
                              >
                                <Box sx={{ flex: 1 }}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                    {widget.icon}
                                    <Typography variant="subtitle2" fontWeight={600}>
                                      {widget.name}
                                    </Typography>
                                    <Chip
                                      label={widget.category}
                                      size="tiny"
                                      color={getCategoryColor(widget.category)}
                                      variant="filled"
                                      sx={{
                                        height: 20,
                                        fontSize: '0.7rem',
                                        '& .MuiChip-label': { px: 0.5 },
                                      }}
                                    />
                                    {widget.required && (
                                      <Chip label="Required" size="tiny" color="error" variant="filled" />
                                    )}
                                  </Box>
                                  <Typography variant="caption" color="text.secondary">
                                    {widget.description}
                                  </Typography>
                                </Box>
                                {!isSelected && !widget.required && <AddIcon color="action" fontSize="small" />}
                                {isSelected && <CheckIcon color="success" fontSize="small" />}
                              </Box>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </Stack>
                  </Box>
                </Paper>
              </Grid>

              {/* Selected Widgets */}
              <Grid item xs={12} md={6} sx={{ display: 'flex', flexDirection: 'column' }}>
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                  }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 1,
                    }}
                  >
                    <Typography variant="subtitle1" fontWeight={600}>
                      Selected Widgets ({selectedWidgets.length})
                    </Typography>
                    <Button size="small" onClick={handleReset} disabled={submitting}>
                      Reset to Default
                    </Button>
                  </Box>
                  <Typography variant="caption" color="text.secondary" paragraph>
                    Drag to reorder or use arrows to move up/down
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <Box sx={{ flex: 1, overflow: 'auto' }}>
                    <Stack spacing={1}>
                      {selectedWidgets.length === 0 ? (
                        <Box sx={{ py: 4, textAlign: 'center' }}>
                          <Typography variant="body2" color="text.secondary">
                            No widgets selected. Click on available widgets to add them to your
                            dashboard.
                          </Typography>
                        </Box>
                      ) : (
                        selectedWidgets.map((widget, index) => (
                          <Card
                            key={widget.id}
                            variant="outlined"
                            draggable
                            onDragStart={() => handleDragStart(index)}
                            onDragOver={(e) => handleDragOver(e, index)}
                            onDragEnd={handleDragEnd}
                            sx={{
                              cursor: 'grab',
                              border: draggedIndex === index ? '2px solid primary.main' : undefined,
                              '&:active': { cursor: 'grabbing' },
                              '&:hover': { boxShadow: 2 },
                              transition: 'all 0.2s',
                            }}
                          >
                            <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                              <Box
                                sx={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                }}
                              >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                                  <Typography
                                    variant="body2"
                                    fontWeight={600}
                                    sx={{
                                      minWidth: 24,
                                      textAlign: 'center',
                                      color: 'text.secondary',
                                    }}
                                  >
                                    {index + 1}.
                                  </Typography>
                                  <Box sx={{ flex: 1 }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                      <Typography variant="subtitle2" fontWeight={600}>
                                        {widget.name}
                                      </Typography>
                                      <Chip
                                        label={widget.category}
                                        size="tiny"
                                        color={getCategoryColor(widget.category)}
                                        variant="filled"
                                        sx={{
                                          height: 20,
                                          fontSize: '0.7rem',
                                          '& .MuiChip-label': { px: 0.5 },
                                        }}
                                      />
                                      {widget.required && (
                                        <Chip
                                          label="Required"
                                          size="tiny"
                                          color="error"
                                          variant="filled"
                                        />
                                      )}
                                    </Box>
                                    <Typography variant="caption" color="text.secondary">
                                      {widget.description}
                                    </Typography>
                                  </Box>
                                </Box>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <IconButton
                                    size="small"
                                    onClick={() => handleMoveUp(index)}
                                    disabled={index === 0}
                                    title="Move up"
                                  >
                                    <UpIcon fontSize="small" />
                                  </IconButton>
                                  <IconButton
                                    size="small"
                                    onClick={() => handleMoveDown(index)}
                                    disabled={index === selectedWidgets.length - 1}
                                    title="Move down"
                                  >
                                    <DownIcon fontSize="small" />
                                  </IconButton>
                                  {!widget.required && (
                                    <IconButton
                                      size="small"
                                      onClick={() => handleRemoveWidget(widget.id)}
                                      color="error"
                                      title="Remove"
                                    >
                                      <RemoveIcon fontSize="small" />
                                    </IconButton>
                                  )}
                                </Box>
                              </Box>
                            </CardContent>
                          </Card>
                        ))
                      )}
                    </Stack>
                  </Box>
                </Paper>
              </Grid>
            </Grid>
          </Stack>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
            <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'center' }}>
              {selectedWidgets.length} widget{selectedWidgets.length !== 1 ? 's' : ''} selected
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button onClick={handleClose} disabled={submitting}>
                Cancel
              </Button>
              <Button
                onClick={handleApply}
                variant="outlined"
                disabled={submitting || selectedWidgets.length === 0}
              >
                Apply Changes
              </Button>
              <Button
                onClick={handleSave}
                variant="contained"
                disabled={submitting || selectedWidgets.length === 0}
                startIcon={submitting ? <CircularProgress size={16} /> : <SaveIcon />}
              >
                {submitting ? 'Saving...' : 'Save Configuration'}
              </Button>
            </Box>
          </Box>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default DashboardCustomizer;
