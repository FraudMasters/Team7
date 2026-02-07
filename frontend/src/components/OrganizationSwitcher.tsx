import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Tooltip,
  Divider,
  Typography,
} from '@mui/material';
import {
  Business as BusinessIcon,
  ArrowDropDown as ArrowDropDownIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { useOrganizationContext } from '@/contexts/OrganizationContext';
import { organizationsClient } from '@/api/organizations';
import type { OrganizationResponse } from '@/types/api';

/**
 * OrganizationSwitcher Component
 *
 * Provides a dropdown button for switching between organizations.
 * Displays current organization name with business icon.
 *
 * Features:
 * - Shows current organization with checkmark indicator
 * - Lists all available organizations in dropdown menu
 * - Fetches organizations on mount
 * - Switches organization on selection
 * - Integrates with OrganizationContext for state management
 * - Displays loading state while fetching organizations
 * - Error handling with user-friendly messages
 *
 * @example
 * ```tsx
 * // In Layout component header
 * <OrganizationSwitcher />
 * ```
 */
const OrganizationSwitcher: React.FC = () => {
  const { t } = useTranslation();
  const { currentOrganization, setCurrentOrganization } = useOrganizationContext();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [organizations, setOrganizations] = useState<OrganizationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const open = Boolean(anchorEl);

  /**
   * Fetch organizations on component mount
   */
  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await organizationsClient.listOrganizations(
          true, // isActive only
          undefined, // no search
          0, // skip
          100 // limit - get all organizations
        );

        setOrganizations(response.organizations);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load organizations';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchOrganizations();
  }, []);

  /**
   * Handle button click to open menu
   */
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  /**
   * Handle menu close
   */
  const handleClose = () => {
    setAnchorEl(null);
  };

  /**
   * Handle organization selection
   *
   * @param organization - Organization to switch to
   */
  const handleSelectOrganization = (organization: OrganizationResponse) => {
    setCurrentOrganization(organization);
    handleClose();
  };

  /**
   * Get button label text
   *
   * @returns Button label string
   */
  const getButtonLabel = () => {
    if (loading) {
      return t('organization.loading') || 'Loading...';
    }

    if (error) {
      return t('organization.error') || 'Error';
    }

    if (!currentOrganization) {
      return t('organization.noOrganization') || 'No Organization';
    }

    return currentOrganization.name;
  };

  /**
   * Get tooltip title
   *
   * @returns Tooltip title string
   */
  const getTooltipTitle = () => {
    if (loading) {
      return t('organization.loadingOrganizations') || 'Loading organizations...';
    }

    if (error) {
      return error;
    }

    if (organizations.length === 0) {
      return t('organization.noOrganizations') || 'No organizations available';
    }

    if (!currentOrganization) {
      return t('organization.selectOrganization') || 'Select an organization';
    }

    return `${t('organization.currentOrganization') || 'Current organization'}: ${currentOrganization.name}`;
  };

  /**
   * Get organization menu item label
   *
   * @param organization - Organization to get label for
   * @returns Menu item label string
   */
  const getOrganizationLabel = (organization: OrganizationResponse): string => {
    return organization.name;
  };

  return (
    <Box sx={{ ml: 1 }}>
      <Tooltip title={getTooltipTitle()} arrow>
        <Button
          onClick={handleClick}
          aria-label={getTooltipTitle()}
          aria-expanded={open}
          aria-haspopup="menu"
          startIcon={loading ? <CircularProgress size={16} /> : <BusinessIcon />}
          endIcon={<ArrowDropDownIcon />}
          sx={{
            color: 'inherit',
            bgcolor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: 1,
            padding: '6px 12px',
            textTransform: 'none',
            transition: 'background-color 0.2s ease-in-out',
            '&:hover': {
              bgcolor: 'rgba(255, 255, 255, 0.2)',
            },
            '&:active': {
              bgcolor: 'rgba(255, 255, 255, 0.3)',
            },
            minWidth: 160,
            justifyContent: 'flex-start',
          }}
        >
          <Typography
            variant="body2"
            sx={{
              fontWeight: 500,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: 200,
            }}
          >
            {getButtonLabel()}
          </Typography>
        </Button>
      </Tooltip>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        onClick={handleClose}
        PaperProps={{
          sx: {
            minWidth: 250,
            maxHeight: 400,
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        {/* Header */}
        <Box sx={{ px: 2, py: 1.5 }}>
          <Typography
            variant="subtitle2"
            sx={{
              fontWeight: 600,
              color: 'text.secondary',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              fontSize: '0.75rem',
            }}
          >
            {t('organization.switchOrganization') || 'Switch Organization'}
          </Typography>
        </Box>

        <Divider />

        {/* Error State */}
        {error && (
          <Box sx={{ px: 2, py: 2 }}>
            <Typography variant="body2" color="error">
              {error}
            </Typography>
          </Box>
        )}

        {/* Empty State */}
        {!loading && !error && organizations.length === 0 && (
          <Box sx={{ px: 2, py: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {t('organization.noOrganizationsAvailable') || 'No organizations available'}
            </Typography>
          </Box>
        )}

        {/* Loading State */}
        {loading && (
          <Box sx={{ px: 2, py: 2, display: 'flex', justifyContent: 'center' }}>
            <CircularProgress size={24} />
          </Box>
        )}

        {/* Organizations List */}
        {!loading && !error && organizations.map((organization) => {
          const isSelected = currentOrganization?.id === organization.id;

          return (
            <MenuItem
              key={organization.id}
              onClick={() => handleSelectOrganization(organization)}
              selected={isSelected}
              sx={{
                '&.Mui-selected': {
                  bgcolor: 'action.selected',
                },
                '&.Mui-selected:hover': {
                  bgcolor: 'action.selected',
                  opacity: 0.8,
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <BusinessIcon
                  fontSize="small"
                  sx={{
                    color: isSelected ? 'primary.main' : 'text.primary',
                  }}
                />
              </ListItemIcon>
              <ListItemText
                primary={getOrganizationLabel(organization)}
                sx={{
                  '& .MuiTypography-root': {
                    fontWeight: isSelected ? 600 : 400,
                    fontSize: '0.875rem',
                  },
                }}
              />
              {isSelected && (
                <CheckIcon
                  fontSize="small"
                  color="primary"
                  sx={{ ml: 1 }}
                />
              )}
            </MenuItem>
          );
        })}
      </Menu>
    </Box>
  );
};

export default OrganizationSwitcher;
