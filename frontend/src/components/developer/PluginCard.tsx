/**
 * Plugin Card Component
 *
 * Displays a single plugin card in the marketplace grid.
 *
 * @module components/developer/PluginCard
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Box,
  Typography,
  Chip,
  Button,
  Stack,
  Avatar,
  IconButton,
  Menu,
  MenuItem,
  Rating,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  Extension as ExtensionIcon,
  Download as DownloadIcon,
  CheckCircle as CheckCircleIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Settings as SettingsIcon,
  Star as StarIcon,
  Person as PersonIcon,
  Verified as VerifiedIcon,
} from '@mui/icons-material';
import type { Plugin, PluginDetail } from '@/api/plugins';

interface PluginCardProps {
  plugin: Plugin | PluginDetail;
  onInstall?: (plugin: Plugin | PluginDetail) => void;
  onUninstall?: (plugin: Plugin | PluginDetail) => void;
  onConfigure?: (plugin: Plugin | PluginDetail) => void;
  onToggleEnable?: (plugin: Plugin | PluginDetail, enabled: boolean) => void;
}

/**
 * Format date to readable string
 */
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

/**
 * Format install count to readable string
 */
const formatInstallCount = (count: number): string => {
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}K`;
  }
  return count.toString();
};

/**
 * PluginCard Component
 *
 * Displays a plugin card with:
 * - Plugin logo/icon
 * - Name and description
 * - Author and verification status
 * - Rating and install count
 * - Category and tags
 * - Install/Configure/Uninstall actions
 *
 * @example
 * ```tsx
 * <PluginCard
 *   plugin={pluginData}
 *   onInstall={(p) => handleInstall(p.id)}
 *   onConfigure={(p) => handleConfigure(p.id)}
 *   onUninstall={(p) => handleUninstall(p.id)}
 * />
 * ```
 */
const PluginCard: React.FC<PluginCardProps> = ({
  plugin,
  onInstall,
  onUninstall,
  onConfigure,
  onToggleEnable,
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleInstallClick = () => {
    onInstall?.(plugin);
  };

  const handleConfigureClick = () => {
    handleMenuClose();
    onConfigure?.(plugin);
  };

  const handleUninstallClick = () => {
    handleMenuClose();
    onUninstall?.(plugin);
  };

  const handleToggleEnable = () => {
    handleMenuClose();
    onToggleEnable?.(plugin, !plugin.is_enabled);
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 4,
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        {/* Header with logo and name */}
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Avatar
            src={plugin.logo_url || undefined}
            sx={{
              width: 56,
              height: 56,
              bgcolor: 'primary.main',
              fontSize: '1.5rem',
            }}
          >
            <ExtensionIcon fontSize="large" />
          </Avatar>

          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
              <Typography variant="h6" fontWeight={600} noWrap>
                {plugin.name}
              </Typography>
              {plugin.is_official && (
                <Tooltip title="Official Plugin">
                  <VerifiedIcon color="primary" fontSize="small" />
                </Tooltip>
              )}
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                label={plugin.category}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
              <Typography variant="caption" color="text.secondary" noWrap>
                v{plugin.version}
              </Typography>
            </Box>
          </Box>

          <IconButton size="small" onClick={handleMenuOpen}>
            <MoreVertIcon />
          </IconButton>
        </Box>

        {/* Description */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 2,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {plugin.description}
        </Typography>

        {/* Author */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 2 }}>
          <PersonIcon fontSize="small" color="disabled" />
          <Typography variant="caption" color="text.secondary">
            {plugin.author}
          </Typography>
        </Box>

        {/* Rating and stats */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          {plugin.rating_count > 0 ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Rating
                value={plugin.average_rating || 0}
                precision={0.1}
                size="small"
                readOnly
                sx={{ fontSize: '0.875rem' }}
              />
              <Typography variant="caption" color="text.secondary">
                ({plugin.rating_count})
              </Typography>
            </Box>
          ) : (
            <Typography variant="caption" color="text.secondary" italic>
              No ratings yet
            </Typography>
          )}

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <DownloadIcon fontSize="small" color="disabled" sx={{ fontSize: '0.875rem' }} />
            <Typography variant="caption" color="text.secondary">
              {formatInstallCount(plugin.install_count)} installs
            </Typography>
          </Box>
        </Box>

        {/* Tags */}
        {plugin.tags && plugin.tags.length > 0 && (
          <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
            {plugin.tags.slice(0, 3).map((tag) => (
              <Chip
                key={tag}
                label={tag}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            ))}
            {plugin.tags.length > 3 && (
              <Chip
                label={`+${plugin.tags.length - 3}`}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            )}
          </Stack>
        )}
      </CardContent>

      <Divider />

      <CardActions sx={{ justifyContent: 'space-between', px: 2, py: 1 }}>
        {plugin.is_installed ? (
          <>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <CheckCircleIcon color="success" fontSize="small" />
              <Typography variant="caption" color="text.secondary">
                {plugin.is_enabled ? 'Enabled' : 'Installed'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <Button
                size="small"
                variant="outlined"
                onClick={() => onToggleEnable?.(plugin, !plugin.is_enabled)}
              >
                {plugin.is_enabled ? 'Disable' : 'Enable'}
              </Button>
              {'config_schema' in plugin && plugin.config_schema && (
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<SettingsIcon />}
                  onClick={() => onConfigure?.(plugin)}
                >
                  Configure
                </Button>
              )}
            </Box>
          </>
        ) : (
          <Button
            size="small"
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={handleInstallClick}
            fullWidth
          >
            Install Plugin
          </Button>
        )}
      </CardActions>

      {/* Options Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        {plugin.is_installed ? (
          <>
            <MenuItem onClick={handleToggleEnable}>
              {plugin.is_enabled ? 'Disable' : 'Enable'} Plugin
            </MenuItem>
            {'config_schema' in plugin && plugin.config_schema && (
              <MenuItem onClick={handleConfigureClick}>
                <SettingsIcon fontSize="small" sx={{ mr: 1 }} />
                Configure
              </MenuItem>
            )}
            <MenuItem onClick={handleUninstallClick} sx={{ color: 'error.main' }}>
              <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
              Uninstall
            </MenuItem>
          </>
        ) : (
          <MenuItem onClick={handleInstallClick}>
            <DownloadIcon fontSize="small" sx={{ mr: 1 }} />
            Install Plugin
          </MenuItem>
        )}
      </Menu>
    </Card>
  );
};

export default PluginCard;
