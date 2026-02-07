import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { organizationsClient } from '@/api/organizations';
import type {
  OrganizationResponse,
  OrganizationCreate,
  OrganizationUpdate,
} from '@/types/api';

/**
 * Organizations Page
 *
 * Displays and manages organizations in the system.
 * Supports listing, creating, updating, and deleting organizations.
 */
const OrganizationsPage: React.FC = () => {
  const { t } = useTranslation();
  const [organizations, setOrganizations] = useState<OrganizationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingOrg, setEditingOrg] = useState<OrganizationResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [orgToDelete, setOrgToDelete] = useState<OrganizationResponse | null>(null);

  // Form state
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');

  /**
   * Load organizations on component mount
   */
  useEffect(() => {
    loadOrganizations();
  }, []);

  /**
   * Load all organizations from the API
   */
  const loadOrganizations = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await organizationsClient.listOrganizations();
      setOrganizations(response.organizations);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load organizations';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Open create dialog
   */
  const handleOpenCreateDialog = () => {
    setEditingOrg(null);
    setName('');
    setSlug('');
    setDialogOpen(true);
    setError(null);
  };

  /**
   * Open edit dialog
   */
  const handleOpenEditDialog = (org: OrganizationResponse) => {
    setEditingOrg(org);
    setName(org.name);
    setSlug(org.slug);
    setDialogOpen(true);
    setError(null);
  };

  /**
   * Close dialog
   */
  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingOrg(null);
    setName('');
    setSlug('');
    setError(null);
  };

  /**
   * Generate slug from name
   */
  const handleNameChange = (value: string) => {
    setName(value);
    if (!editingOrg) {
      // Auto-generate slug for new organizations
      const generatedSlug = value
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '');
      setSlug(generatedSlug);
    }
  };

  /**
   * Submit create or update
   */
  const handleSubmit = async () => {
    if (!name.trim() || !slug.trim()) {
      setError('Name and slug are required');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      if (editingOrg) {
        // Update existing organization
        const updateData: OrganizationUpdate = {
          name: name.trim(),
        };
        const updated = await organizationsClient.updateOrganization(editingOrg.id, updateData);
        setOrganizations(organizations.map((org) => (org.id === updated.id ? updated : org)));
      } else {
        // Create new organization
        const createData: OrganizationCreate = {
          name: name.trim(),
          slug: slug.trim(),
        };
        const created = await organizationsClient.createOrganization(createData);
        setOrganizations([created, ...organizations]);
      }
      handleCloseDialog();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save organization';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Open delete confirmation dialog
   */
  const handleOpenDeleteDialog = (org: OrganizationResponse) => {
    setOrgToDelete(org);
    setDeleteDialogOpen(true);
  };

  /**
   * Close delete dialog
   */
  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setOrgToDelete(null);
  };

  /**
   * Confirm delete organization
   */
  const handleConfirmDelete = async () => {
    if (!orgToDelete) return;

    setSubmitting(true);
    setError(null);

    try {
      await organizationsClient.deleteOrganization(orgToDelete.id);
      setOrganizations(organizations.filter((org) => org.id !== orgToDelete.id));
      handleCloseDeleteDialog();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete organization';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" component="h1" fontWeight={700} gutterBottom>
              Organizations
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Manage organizations and their settings
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenCreateDialog}
            color="primary"
          >
            Create Organization
          </Button>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Loading State */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          /* Organizations Table */
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Organization</TableCell>
                  <TableCell>Slug</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {organizations.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
                      <Box sx={{ textAlign: 'center' }}>
                        <BusinessIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                          No organizations found
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Create your first organization to get started
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ) : (
                  organizations.map((org) => (
                    <TableRow key={org.id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <BusinessIcon color="primary" />
                          <Typography variant="body1" fontWeight={500}>
                            {org.name}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <code style={{ backgroundColor: 'rgba(0,0,0,0.05)', padding: '2px 6px', borderRadius: '4px' }}>
                          {org.slug}
                        </code>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={org.is_active ? 'Active' : 'Inactive'}
                          color={org.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(org.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenEditDialog(org)}
                          color="primary"
                          title="Edit"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDeleteDialog(org)}
                          color="error"
                          title="Delete"
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
        )}
      </Container>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingOrg ? 'Edit Organization' : 'Create Organization'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          <TextField
            autoFocus
            margin="dense"
            label="Organization Name"
            fullWidth
            variant="outlined"
            value={name}
            onChange={(e) => handleNameChange(e.target.value)}
            disabled={submitting}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Slug"
            fullWidth
            variant="outlined"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            disabled={submitting || !!editingOrg}
            helperText={editingOrg ? 'Slug cannot be changed' : 'Unique identifier for the organization'}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} disabled={submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={submitting || !name.trim() || !slug.trim()}
            startIcon={submitting ? <CircularProgress size={16} /> : null}
          >
            {submitting ? 'Saving...' : editingOrg ? 'Save Changes' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={handleCloseDeleteDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Delete Organization</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          <Typography variant="body1">
            Are you sure you want to delete <strong>{orgToDelete?.name}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This will set the organization as inactive. It can be reactivated later if needed.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog} disabled={submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirmDelete}
            variant="contained"
            color="error"
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {submitting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default OrganizationsPage;
