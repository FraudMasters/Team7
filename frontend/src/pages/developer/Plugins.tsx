/**
 * Plugins Marketplace Page
 *
 * Main page for browsing and managing plugins in the AgentHR marketplace.
 *
 * @module pages/developer/Plugins
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Stack,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  AlertTitle,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  InputAdornment,
  CircularProgress,
  Divider,
  IconButton,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterListIcon,
  Refresh as RefreshIcon,
  Extension as ExtensionIcon,
  Download as DownloadIcon,
  CheckCircle as CheckCircleIcon,
  Star as StarIcon,
  Verified as VerifiedIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import PluginGrid from '@/components/developer/PluginGrid';
import {
  pluginsClient,
  PluginCategory,
  type Plugin,
  type PluginDetail,
  type MarketplaceStatistics,
} from '@/api/plugins';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`plugins-tabpanel-${index}`}
      aria-labelledby={`plugins-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

/**
 * Plugins Page Component
 *
 * Provides a comprehensive interface for:
 * - Browsing available plugins in the marketplace
 * - Searching and filtering plugins
 * - Installing/uninstalling plugins
 * - Managing installed plugins
 * - Viewing marketplace statistics
 *
 * @example
 * ```tsx
 * // Routed at /developer/plugins
 * import { Plugins } from '@/pages/developer/Plugins';
 * ```
 */
const Plugins: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string | undefined>();
  const [officialOnly, setOfficialOnly] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Marketplace plugins state
  const [marketplacePlugins, setMarketplacePlugins] = useState<Plugin[]>([]);
  const [marketplaceLoading, setMarketplaceLoading] = useState(true);
  const [marketplaceError, setMarketplaceError] = useState<string | null>(null);

  // Installed plugins state
  const [installedPlugins, setInstalledPlugins] = useState<Plugin[]>([]);
  const [installedLoading, setInstalledLoading] = useState(true);
  const [installedError, setInstalledError] = useState<string | null>(null);

  // Statistics state
  const [statistics, setStatistics] = useState<MarketplaceStatistics | null>(null);

  // Installation state
  const [installingPluginId, setInstallingPluginId] = useState<string | null>(null);
  const [installDialogOpen, setInstallDialogOpen] = useState(false);
  const [selectedPlugin, setSelectedPlugin] = useState<Plugin | PluginDetail | null>(null);

  const fetchMarketplacePlugins = useCallback(async () => {
    setMarketplaceLoading(true);
    setMarketplaceError(null);

    try {
      const filters: {
        category?: string;
        is_official?: boolean;
        search?: string;
      } = {};

      if (categoryFilter) {
        filters.category = categoryFilter;
      }
      if (officialOnly) {
        filters.is_official = true;
      }
      if (searchQuery) {
        filters.search = searchQuery;
      }

      const plugins = await pluginsClient.listPlugins(filters);
      setMarketplacePlugins(plugins);
    } catch (err) {
      setMarketplaceError(err instanceof Error ? err.message : 'Failed to load plugins');
    } finally {
      setMarketplaceLoading(false);
    }
  }, [categoryFilter, officialOnly, searchQuery]);

  const fetchInstalledPlugins = useCallback(async () => {
    setInstalledLoading(true);
    setInstalledError(null);

    try {
      const plugins = await pluginsClient.listInstalled();
      setInstalledPlugins(plugins);
    } catch (err) {
      setInstalledError(err instanceof Error ? err.message : 'Failed to load installed plugins');
    } finally {
      setInstalledLoading(false);
    }
  }, []);

  const fetchStatistics = useCallback(async () => {
    try {
      const stats = await pluginsClient.getMarketplaceStats();
      setStatistics(stats);
    } catch (err) {
      // Silently fail for statistics
    }
  }, []);

  useEffect(() => {
    fetchMarketplacePlugins();
    fetchInstalledPlugins();
    fetchStatistics();
  }, [fetchMarketplacePlugins, fetchInstalledPlugins, fetchStatistics, refreshTrigger]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
  };

  const handleCategoryClick = (category: string | undefined) => {
    setCategoryFilter(category);
  };

  const handleOfficialOnlyToggle = () => {
    setOfficialOnly((prev) => !prev);
  };

  const handleInstall = (plugin: Plugin | PluginDetail) => {
    setSelectedPlugin(plugin);
    setInstallDialogOpen(true);
  };

  const handleInstallConfirm = async () => {
    if (!selectedPlugin) return;

    setInstallingPluginId(selectedPlugin.id);
    setInstallDialogOpen(false);

    try {
      await pluginsClient.installPlugin(selectedPlugin.id);
      setRefreshTrigger((prev) => prev + 1);
    } catch (err) {
      setMarketplaceError(err instanceof Error ? err.message : 'Failed to install plugin');
    } finally {
      setInstallingPluginId(null);
      setSelectedPlugin(null);
    }
  };

  const handleUninstall = async (plugin: Plugin | PluginDetail) => {
    try {
      await pluginsClient.uninstallPlugin(plugin.id);
      setRefreshTrigger((prev) => prev + 1);
    } catch (err) {
      setMarketplaceError(err instanceof Error ? err.message : 'Failed to uninstall plugin');
    }
  };

  const handleToggleEnable = async (plugin: Plugin | PluginDetail, enabled: boolean) => {
    try {
      // Find the installation ID
      const installation = installedPlugins.find((p) => p.plugin_id === plugin.id);
      if (installation) {
        await pluginsClient.updateInstallation(installation.id, { is_enabled: enabled });
        setRefreshTrigger((prev) => prev + 1);
      }
    } catch (err) {
      setMarketplaceError(err instanceof Error ? err.message : 'Failed to update plugin');
    }
  };

  const handleConfigure = (plugin: Plugin | PluginDetail) => {
    // TODO: Implement configuration dialog
  };

  const filteredMarketplacePlugins = marketplacePlugins;
  const filteredInstalledPlugins = installedPlugins.filter((p) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        p.plugin_name.toLowerCase().includes(query) ||
        p.description.toLowerCase().includes(query)
      );
    }
    return true;
  });

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            Plugin Marketplace
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Extend AgentHR with community and official plugins
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => setRefreshTrigger((prev) => prev + 1)}
        >
          Refresh
        </Button>
      </Stack>

      {/* Statistics Cards */}
      {statistics && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
                border: '1px solid',
                borderColor: 'primary.main',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <ExtensionIcon />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {statistics.total_plugins}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Plugins
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
                border: '1px solid',
                borderColor: 'success.main',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <VerifiedIcon />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {statistics.official_plugins}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Official Plugins
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%)',
                border: '1px solid',
                borderColor: 'warning.main',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <DownloadIcon />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {statistics.total_installations}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Installations
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%)',
                border: '1px solid',
                borderColor: 'error.main',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 2,
                      background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <CheckCircleIcon />
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {installedPlugins.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Installed
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Getting Started Section */}
      <Paper sx={{ p: 3, mb: 4, border: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Getting Started with Plugins
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Plugins extend AgentHR's functionality with custom integrations, automations, and enhancements.
          Browse the marketplace, install plugins with one click, and manage them from your dashboard.
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip label="Integrations" size="small" variant="outlined" />
          <Chip label="Automations" size="small" variant="outlined" />
          <Chip label="Analytics" size="small" variant="outlined" />
          <Chip label="Notifications" size="small" variant="outlined" />
        </Box>
      </Paper>

      {/* Search and Filter */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center">
          <TextField
            placeholder="Search plugins..."
            value={searchQuery}
            onChange={handleSearchChange}
            fullWidth
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: searchQuery && (
                <InputAdornment position="end">
                  <IconButton
                    size="small"
                    onClick={() => setSearchQuery('')}
                  >
                    <CloseIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip
              label={!categoryFilter ? 'All Categories' : categoryFilter}
              onClick={() => handleCategoryClick(undefined)}
              color={!categoryFilter ? 'primary' : 'default'}
              clickable
            />
            <Chip
              label="Official"
              onClick={handleOfficialOnlyToggle}
              color={officialOnly ? 'primary' : 'default'}
              clickable
              icon={<VerifiedIcon />}
            />
            <Divider orientation="vertical" flexItem />
            {Object.values(PluginCategory).map((category) => (
              <Chip
                key={category}
                label={category}
                onClick={() => handleCategoryClick(category)}
                color={categoryFilter === category ? 'primary' : 'default'}
                clickable
              />
            ))}
          </Box>
        </Stack>
      </Paper>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label={`Marketplace (${marketplacePlugins.length})`} />
          <Tab label={`Installed (${installedPlugins.length})`} />
        </Tabs>
      </Box>

      {/* Marketplace Tab */}
      <TabPanel value={tabValue} index={0}>
        <PluginGrid
          plugins={filteredMarketplacePlugins}
          loading={marketplaceLoading}
          error={marketplaceError}
          onInstall={handleInstall}
          onUninstall={handleUninstall}
          onConfigure={handleConfigure}
          onToggleEnable={handleToggleEnable}
          onRetry={fetchMarketplacePlugins}
          emptyMessage={searchQuery ? `No plugins matching "${searchQuery}"` : 'No plugins available in the marketplace'}
        />
      </TabPanel>

      {/* Installed Tab */}
      <TabPanel value={tabValue} index={1}>
        <PluginGrid
          plugins={filteredInstalledPlugins}
          loading={installedLoading}
          error={installedError}
          onInstall={handleInstall}
          onUninstall={handleUninstall}
          onConfigure={handleConfigure}
          onToggleEnable={handleToggleEnable}
          onRetry={fetchInstalledPlugins}
          emptyMessage="You haven't installed any plugins yet"
        />
      </TabPanel>

      {/* Install Confirmation Dialog */}
      <Dialog open={installDialogOpen} onClose={() => setInstallDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Install Plugin?</DialogTitle>
        <DialogContent>
          <Stack spacing={2}>
            <Alert severity="info">
              <AlertTitle>Plugin Installation</AlertTitle>
              You're about to install <strong>{selectedPlugin?.name}</strong> by {selectedPlugin?.author}.
            </Alert>

            {selectedPlugin && 'permissions' in selectedPlugin && selectedPlugin.permissions && selectedPlugin.permissions.length > 0 && (
              <>
                <Typography variant="subtitle2" fontWeight={600}>
                  Required Permissions:
                </Typography>
                <Stack spacing={0.5}>
                  {selectedPlugin.permissions.map((permission) => (
                    <Chip key={permission} label={permission} size="small" variant="outlined" />
                  ))}
                </Stack>
              </>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInstallDialogOpen(false)} disabled={!!installingPluginId}>
            Cancel
          </Button>
          <Button
            onClick={handleInstallConfirm}
            variant="contained"
            disabled={!!installingPluginId}
            startIcon={installingPluginId ? <CircularProgress size={16} /> : <DownloadIcon />}
          >
            {installingPluginId ? 'Installing...' : 'Install Plugin'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Plugins;
