import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Chip,
  Stack,
  CircularProgress,
  Alert,
  Divider,
  Tooltip,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { useClientTenants } from '@/hooks/useAgencyData';
import { useTenantContext } from '@/hooks/useTenantContext';
import type { ClientTenantResponse } from '@/api/clientTenants';

/**
 * Extended client tenant with organization details
 */
interface ClientTenantWithOrg extends ClientTenantResponse {
  organization_name?: string;
}

/**
 * ClientSelector Component Props
 */
interface ClientSelectorProps {
  /** Agency ID to fetch clients for */
  agencyId: string;
  /** Callback when client is selected */
  onClientSelect?: (tenant: ClientTenantResponse | null) => void;
  /** Disabled state */
  disabled?: boolean;
  /** Compact mode for inline display */
  compact?: boolean;
  /** Show all clients regardless of status */
  showAllStatuses?: boolean;
  /** Custom label */
  label?: string;
  /** Full width */
  fullWidth?: boolean;
}

/**
 * ClientSelector Component
 *
 * Provides a dropdown interface for selecting client organizations in agency mode.
 * Features include:
 * - Dropdown selector for switching between client tenants
 * - Integration with tenant context for API request scoping
 * - Visual status indicators (active, inactive, suspended)
 * - Primary client badge
 * - Loading and error states
 * - Automatic context updates on selection
 *
 * @example
 * ```tsx
 * <ClientSelector
 *   agencyId="agency-uuid"
 *   onClientSelect={(tenant) => console.log('Selected:', tenant)}
 *   fullWidth
 * />
 * ```
 */
const ClientSelector: React.FC<ClientSelectorProps> = ({
  agencyId,
  onClientSelect,
  disabled = false,
  compact = false,
  showAllStatuses = false,
  label = 'Select Client',
  fullWidth = true,
}) => {
  const { tenantId, setTenantId, setOrganizationId } = useTenantContext();

  // Fetch client tenants for the agency
  const { data, isLoading, error, refetch } = useClientTenants(
    agencyId,
    undefined,
    showAllStatuses ? undefined : 'active'
  );

  /**
   * Handle client selection
   */
  const handleClientChange = useCallback(
    (event: any) => {
      const selectedId = event.target.value;

      if (!selectedId) {
        // Clear selection
        setTenantId(null);
        setOrganizationId(null);
        onClientSelect?.(null);
        return;
      }

      const tenant = data?.client_tenants.find((t) => t.id === selectedId);
      if (tenant) {
        setTenantId(tenant.id);
        setOrganizationId(tenant.organization_id);
        onClientSelect?.(tenant);
      }
    },
    [data, setTenantId, setOrganizationId, onClientSelect]
  );

  /**
   * Get status color for chip
   */
  const getStatusColor = (status: string): 'success' | 'default' | 'warning' | 'error' => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'default';
      case 'suspended':
        return 'error';
      default:
        return 'warning';
    }
  };

  /**
   * Filter and sort tenants
   */
  const sortedTenants = useMemo(() => {
    if (!data?.client_tenants) return [];

    // Sort by: primary first, then active, then alphabetically by organization_id
    return [...data.client_tenants].sort((a, b) => {
      // Primary clients first
      if (a.is_primary && !b.is_primary) return -1;
      if (!a.is_primary && b.is_primary) return 1;

      // Then active clients
      if (a.status === 'active' && b.status !== 'active') return -1;
      if (a.status !== 'active' && b.status === 'active') return 1;

      // Then alphabetically by organization_id
      return a.organization_id.localeCompare(b.organization_id);
    });
  }, [data]);

  /**
   * Loading state
   */
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: compact ? 'flex-start' : 'center',
          py: compact ? 1 : 2,
        }}
      >
        <CircularProgress size={compact ? 20 : 24} sx={{ mr: 1 }} />
        <Typography variant={compact ? 'body2' : 'body1'} color="text.secondary">
          Loading clients...
        </Typography>
      </Box>
    );
  }

  /**
   * Error state
   */
  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Tooltip title="Retry loading clients">
            <Box
              onClick={() => refetch()}
              sx={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}
            >
              <Icon name="refresh" />
            </Box>
          </Tooltip>
        }
      >
        <Typography variant="body2">
          {(error as any)?.detail || 'Failed to load clients'}
        </Typography>
      </Alert>
    );
  }

  /**
   * No clients available
   */
  if (!sortedTenants || sortedTenants.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="body2">
          No clients available for this agency. Add clients to get started.
        </Typography>
      </Alert>
    );
  }

  /**
   * Render dropdown selector
   */
  return (
    <FormControl fullWidth={fullWidth} disabled={disabled} size={compact ? 'small' : 'medium'}>
      <InputLabel id="client-selector-label">{label}</InputLabel>
      <Select
        labelId="client-selector-label"
        id="client-selector"
        value={tenantId || ''}
        label={label}
        onChange={handleClientChange}
        renderValue={(selected) => {
          if (!selected) {
            return <em>None</em>;
          }

          const tenant = sortedTenants.find((t) => t.id === selected);
          if (!tenant) return selected;

          return (
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography variant="body2">{tenant.organization_id}</Typography>
              {tenant.is_primary && (
                <Chip
                  label="Primary"
                  size="small"
                  color="primary"
                  variant="outlined"
                  sx={{ height: 20, fontSize: '0.7rem' }}
                />
              )}
              {tenant.status !== 'active' && (
                <Chip
                  label={tenant.status}
                  size="small"
                  color={getStatusColor(tenant.status)}
                  variant="outlined"
                  sx={{ height: 20, fontSize: '0.7rem', textTransform: 'capitalize' }}
                />
              )}
            </Stack>
          );
        }}
      >
        {/* Clear selection option */}
        <MenuItem value="">
          <em>None</em>
        </MenuItem>

        <Divider />

        {/* Client tenants list */}
        {sortedTenants.map((tenant) => (
          <MenuItem key={tenant.id} value={tenant.id}>
            <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
              {/* Organization ID/Name */}
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  variant="body2"
                  sx={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {tenant.organization_id}
                </Typography>
              </Box>

              {/* Badges */}
              <Stack direction="row" spacing={0.5} sx={{ ml: 1 }}>
                {tenant.is_primary && (
                  <Chip
                    label="Primary"
                    size="small"
                    color="primary"
                    variant="filled"
                    sx={{ height: 20, fontSize: '0.65rem' }}
                  />
                )}
                <Chip
                  label={tenant.status}
                  size="small"
                  color={getStatusColor(tenant.status)}
                  variant={tenant.status === 'active' ? 'outlined' : 'filled'}
                  sx={{
                    height: 20,
                    fontSize: '0.65rem',
                    textTransform: 'capitalize',
                  }}
                />
              </Stack>
            </Box>
          </MenuItem>
        ))}
      </Select>

      {/* Helper text */}
      {!compact && tenantId && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, ml: 1.5 }}>
          <Icon name="info" sx={{ fontSize: 12, mr: 0.5, verticalAlign: 'middle' }} />
          All data will be scoped to the selected client organization
        </Typography>
      )}
    </FormControl>
  );
};

export default ClientSelector;
