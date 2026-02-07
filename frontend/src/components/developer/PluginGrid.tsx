/**
 * Plugin Grid Component
 *
 * Displays a responsive grid of plugin cards.
 *
 * @module components/developer/PluginGrid
 */

import React from 'react';
import {
  Box,
  Grid,
  Typography,
  Paper,
  CircularProgress,
  Stack,
  Alert,
  AlertTitle,
  Button,
  Chip,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Extension as ExtensionIcon,
} from '@mui/icons-material';
import PluginCard from './PluginCard';
import type { Plugin, PluginDetail } from '@/api/plugins';

interface PluginGridProps {
  plugins: (Plugin | PluginDetail)[];
  loading?: boolean;
  error?: string | null;
  onInstall?: (plugin: Plugin | PluginDetail) => void;
  onUninstall?: (plugin: Plugin | PluginDetail) => void;
  onConfigure?: (plugin: Plugin | PluginDetail) => void;
  onToggleEnable?: (plugin: Plugin | PluginDetail, enabled: boolean) => void;
  onRetry?: () => void;
  emptyMessage?: string;
  showCategoryFilter?: boolean;
}

/**
 * PluginGrid Component
 *
 * Displays a grid of plugin cards with:
 * - Responsive layout (1-4 columns based on screen size)
 * - Loading state with spinner
 * - Error state with retry option
 * - Empty state with message
 * - Plugin cards with all actions
 *
 * @example
 * ```tsx
 * <PluginGrid
 *   plugins={plugins}
 *   loading={isLoading}
 *   error={error}
 *   onInstall={handleInstall}
 *   onConfigure={handleConfigure}
 *   onUninstall={handleUninstall}
 *   onToggleEnable={handleToggle}
 *   onRetry={fetchPlugins}
 * />
 * ```
 */
const PluginGrid: React.FC<PluginGridProps> = ({
  plugins,
  loading = false,
  error = null,
  onInstall,
  onUninstall,
  onConfigure,
  onToggleEnable,
  onRetry,
  emptyMessage = 'No plugins found',
  showCategoryFilter = false,
}) => {
  // Group plugins by category if filter is enabled
  const pluginsByCategory = React.useMemo(() => {
    if (!showCategoryFilter) return { All: plugins };

    const grouped: Record<string, (Plugin | PluginDetail)[]> = {
      All: plugins,
    };

    plugins.forEach((plugin) => {
      const category = plugin.category || 'other';
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(plugin);
    });

    return grouped;
  }, [plugins, showCategoryFilter]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <Stack alignItems="center" spacing={2}>
          <CircularProgress size={48} />
          <Typography variant="body2" color="text.secondary">
            Loading plugins...
          </Typography>
        </Stack>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert
        severity="error"
        action={
          onRetry && (
            <Button color="inherit" onClick={onRetry} startIcon={<RefreshIcon />}>
              Retry
            </Button>
          )
        }
      >
        <AlertTitle>Error Loading Plugins</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (plugins.length === 0) {
    return (
      <Paper
        sx={{
          p: 6,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: 'divider',
        }}
      >
        <Box sx={{ mb: 2 }}>
          <ExtensionIcon sx={{ fontSize: 64, color: 'text.disabled' }} />
        </Box>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          {emptyMessage}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Check back later for new plugins or contact us to request a feature.
        </Typography>
      </Paper>
    );
  }

  return (
    <Stack spacing={4}>
      {Object.entries(pluginsByCategory).map(([category, categoryPlugins]) =>
        categoryPlugins.length > 0 ? (
          <Box key={category}>
            {showCategoryFilter && category !== 'All' && (
              <>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Typography variant="h6" fontWeight={600}>
                    {category}
                  </Typography>
                  <Chip
                    label={`${categoryPlugins.length}`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                </Box>
                <Divider sx={{ mb: 2 }} />
              </>
            )}

            <Grid container spacing={3}>
              {categoryPlugins.map((plugin) => (
                <Grid item xs={12} sm={6} md={4} lg={3} key={plugin.id}>
                  <PluginCard
                    plugin={plugin}
                    onInstall={onInstall}
                    onUninstall={onUninstall}
                    onConfigure={onConfigure}
                    onToggleEnable={onToggleEnable}
                  />
                </Grid>
              ))}
            </Grid>
          </Box>
        ) : null
      )}
    </Stack>
  );
};

export default PluginGrid;
