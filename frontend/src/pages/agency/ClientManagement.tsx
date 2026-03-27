import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  Alert,
  Stack,
  Divider,
  CircularProgress,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Chip,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Business as BusinessIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { clientTenantsClient, ClientTenantStatus } from '@/api/clientTenants';
import { organizationsClient } from '@/api/organizations';
import type { ClientTenantResponse, ClientTenantCreate, ClientTenantUpdate } from '@/api/clientTenants';
import type { OrganizationResponse } from '@/types';

/**
 * Form state interface for add/edit client dialog
 */
interface ClientFormState {
  organization_id: string;
  organization_name: string;
  status: string;
  is_primary: boolean;
}

/**
 * Form validation errors interface
 */
interface FormErrors {
  organization_id?: string;
  organization_name?: string;
  status?: string;
}

/**
 * Client Management Page
 *
 * Provides an interface for agency admins to manage their client organizations:
 * - View all client tenants
 * - Add new clients (organizations)
 * - Edit client status (active, inactive, suspended)
 * - Set primary client
 * - Delete client relationships
 *
 * Accessible at /agency/clients
 *
 * @example
 * ```tsx
 * // Route configuration in App.tsx
 * <Route path="/agency/clients" element={<ClientManagement />} />
 * ```
 */
const ClientManagement: React.FC = () => {
  const { t } = useTranslation();

  // Current agency ID (in production, this would come from auth context)
  const [agencyId] = useState<string>('agency123');

  // Client tenants state
  const [clients, setClients] = useState<ClientTenantResponse[]>([]);
  const [organizations, setOrganizations] = useState<OrganizationResponse[]>([]);

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<ClientTenantResponse | null>(null);
  const [formData, setFormData] = useState<ClientFormState>({
    organization_id: '',
    organization_name: '',
    status: ClientTenantStatus.Active,
    is_primary: false,
  });

  // UI state
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errors, setErrors] = useState<FormErrors>({});

  /**
   * Load client tenants and organizations
   */
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Load client tenants for this agency
      const clientsResponse = await clientTenantsClient.listClientTenants(agencyId);
      setClients(clientsResponse.client_tenants);

      // Load all organizations to populate dropdown when adding new clients
      const orgsResponse = await organizationsClient.listOrganizations();
      setOrganizations(orgsResponse.organizations);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load client data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [agencyId]);

  /**
   * Load data on component mount
   */
  useEffect(() => {
    loadData();
  }, [loadData]);

  /**
   * Validate form fields
   */
  const validateForm = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    if (!editingClient) {
      // When adding new client, need to select organization or enter name
      if (!formData.organization_id && !formData.organization_name.trim()) {
        newErrors.organization_id = 'Please select an existing organization or enter a new organization name';
      }

      if (formData.organization_name.trim() && formData.organization_name.trim().length < 2) {
        newErrors.organization_name = 'Organization name must be at least 2 characters';
      }
    }

    if (!formData.status) {
      newErrors.status = 'Status is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData, editingClient]);

  /**
   * Handle form field change
   */
  const handleFormChange = useCallback((field: keyof ClientFormState, value: string | boolean) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear error for this field when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  }, [errors]);

  /**
   * Open add client dialog
   */
  const handleAddClick = useCallback(() => {
    setEditingClient(null);
    setFormData({
      organization_id: '',
      organization_name: '',
      status: ClientTenantStatus.Active,
      is_primary: false,
    });
    setErrors({});
    setDialogOpen(true);
  }, []);

  /**
   * Open edit client dialog
   */
  const handleEditClick = useCallback((client: ClientTenantResponse) => {
    setEditingClient(client);
    setFormData({
      organization_id: client.organization_id,
      organization_name: '',
      status: client.status,
      is_primary: client.is_primary,
    });
    setErrors({});
    setDialogOpen(true);
  }, []);

  /**
   * Close dialog
   */
  const handleDialogClose = useCallback(() => {
    setDialogOpen(false);
    setEditingClient(null);
    setFormData({
      organization_id: '',
      organization_name: '',
      status: ClientTenantStatus.Active,
      is_primary: false,
    });
    setErrors({});
  }, []);

  /**
   * Handle form submission
   */
  const handleSubmit = useCallback(async () => {
    if (!validateForm()) {
      return;
    }

    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      if (editingClient) {
        // Update existing client tenant
        const updateData: ClientTenantUpdate = {
          status: formData.status,
          is_primary: formData.is_primary,
        };

        await clientTenantsClient.updateClientTenant(editingClient.id, updateData);
        setSuccessMessage('Client updated successfully');
      } else {
        // Create new client tenant
        let orgId = formData.organization_id;

        // If user entered a new organization name, create the organization first
        if (!orgId && formData.organization_name.trim()) {
          const newOrg = await organizationsClient.createOrganization({
            name: formData.organization_name.trim(),
            slug: formData.organization_name.trim().toLowerCase().replace(/\s+/g, '-'),
            is_active: true,
          });
          orgId = newOrg.id;
        }

        const createData: ClientTenantCreate = {
          agency_id: agencyId,
          organization_id: orgId,
          status: formData.status,
          is_primary: formData.is_primary,
        };

        await clientTenantsClient.createClientTenant(createData);
        setSuccessMessage('Client added successfully');
      }

      // Reload data and close dialog
      await loadData();
      handleDialogClose();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save client';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  }, [formData, editingClient, agencyId, validateForm, loadData, handleDialogClose]);

  /**
   * Handle delete client
   */
  const handleDelete = useCallback(async (clientId: string) => {
    if (!window.confirm('Are you sure you want to remove this client? This action cannot be undone.')) {
      return;
    }

    setError(null);
    setSuccessMessage(null);

    try {
      await clientTenantsClient.deleteClientTenant(clientId);
      setSuccessMessage('Client removed successfully');
      await loadData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete client';
      setError(errorMessage);
    }
  }, [loadData]);

  /**
   * Get organization name by ID
   */
  const getOrganizationName = useCallback((orgId: string): string => {
    const org = organizations.find(o => o.id === orgId);
    return org?.name || 'Unknown Organization';
  }, [organizations]);

  /**
   * Get status chip color
   */
  const getStatusColor = (status: string): 'success' | 'default' | 'error' => {
    switch (status) {
      case ClientTenantStatus.Active:
        return 'success';
      case ClientTenantStatus.Inactive:
        return 'default';
      case ClientTenantStatus.Suspended:
        return 'error';
      default:
        return 'default';
    }
  };

  // Show loading spinner while data is loading
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
      {/* Page header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            <BusinessIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Client Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your agency's client organizations
          </Typography>
        </Box>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleAddClick}
        >
          Add Client
        </Button>
      </Box>

      {/* Error and success messages */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {/* Clients table */}
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Organization</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Primary</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {clients.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      No clients yet. Click "Add Client" to get started.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                clients.map((client) => (
                  <TableRow key={client.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={500}>
                        {getOrganizationName(client.organization_id)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ID: {client.organization_id.substring(0, 8)}...
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={client.status}
                        color={getStatusColor(client.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {client.is_primary && (
                        <Chip label="Primary" color="primary" size="small" variant="outlined" />
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(client.created_at).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => handleEditClick(client)}
                        color="primary"
                        aria-label="edit"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(client.id)}
                        color="error"
                        aria-label="delete"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Add/Edit client dialog */}
      <Dialog open={dialogOpen} onClose={handleDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingClient ? 'Edit Client' : 'Add Client'}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 2 }}>
            {!editingClient && (
              <>
                {/* Select existing organization */}
                <TextField
                  select
                  label="Select Existing Organization"
                  value={formData.organization_id}
                  onChange={(e) => handleFormChange('organization_id', e.target.value)}
                  error={!!errors.organization_id}
                  helperText={errors.organization_id || 'Select an existing organization or create a new one below'}
                  fullWidth
                  disabled={!!formData.organization_name.trim()}
                >
                  <MenuItem value="">
                    <em>None</em>
                  </MenuItem>
                  {organizations.map((org) => (
                    <MenuItem key={org.id} value={org.id}>
                      {org.name}
                    </MenuItem>
                  ))}
                </TextField>

                <Divider>OR</Divider>

                {/* Create new organization */}
                <TextField
                  label="New Organization Name"
                  value={formData.organization_name}
                  onChange={(e) => handleFormChange('organization_name', e.target.value)}
                  error={!!errors.organization_name}
                  helperText={errors.organization_name || 'Enter a name to create a new organization'}
                  fullWidth
                  disabled={!!formData.organization_id}
                />
              </>
            )}

            {/* Status */}
            <TextField
              select
              label="Status"
              value={formData.status}
              onChange={(e) => handleFormChange('status', e.target.value)}
              error={!!errors.status}
              helperText={errors.status}
              fullWidth
              required
            >
              <MenuItem value={ClientTenantStatus.Active}>Active</MenuItem>
              <MenuItem value={ClientTenantStatus.Inactive}>Inactive</MenuItem>
              <MenuItem value={ClientTenantStatus.Suspended}>Suspended</MenuItem>
            </TextField>

            {/* Primary client checkbox */}
            <TextField
              select
              label="Primary Client"
              value={formData.is_primary ? 'yes' : 'no'}
              onChange={(e) => handleFormChange('is_primary', e.target.value === 'yes')}
              helperText="Set as primary client for this agency"
              fullWidth
            >
              <MenuItem value="no">No</MenuItem>
              <MenuItem value="yes">Yes</MenuItem>
            </TextField>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose} disabled={saving}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            color="primary"
            disabled={saving}
            startIcon={saving ? <CircularProgress size={16} /> : null}
          >
            {saving ? 'Saving...' : editingClient ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ClientManagement;
