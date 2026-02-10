import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Chip,
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
  TextField,
  CircularProgress,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  Security as SecurityIcon,
  Public as NetworkIcon,
} from '@mui/icons-material';
import { securityConfigClient } from '@/api/securityConfig';
import type {
  IPWhitelistItem,
  IPWhitelistCreate,
  IPWhitelistUpdate,
} from '@/types/api';

/**
 * Form data for creating/editing IP whitelist entries
 */
interface IPWhitelistFormData {
  name: string;
  description: string;
  cidr_notation: string;
  start_ip: string;
  end_ip: string;
  is_active: boolean;
}

/**
 * IPWhitelistManager Component Props
 */
interface IPWhitelistManagerProps {
  /** Organization ID to manage IP whitelist for */
  organizationId?: string;
  /** API endpoint URL for IP whitelist (overrides default) */
  apiUrl?: string;
}

/**
 * IPWhitelistManager Component
 *
 * Provides a comprehensive admin interface for managing organization IP whitelist entries.
 * Features include:
 * - List all IP whitelist entries for the organization
 * - Create new IP whitelist entries (CIDR or IP range)
 * - Edit existing whitelist entries
 * - Delete whitelist entries
 * - Toggle active/inactive status
 * - Real-time updates with optimistic UI
 *
 * @example
 * ```tsx
 * <IPWhitelistManager organizationId="org123" />
 * ```
 */
const IPWhitelistManager: React.FC<IPWhitelistManagerProps> = ({
  organizationId,
  apiUrl,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [entries, setEntries] = useState<IPWhitelistItem[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<IPWhitelistItem | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [entryToDelete, setEntryToDelete] = useState<IPWhitelistItem | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [ipType, setIpType] = useState<'cidr' | 'range'>('cidr');

  // Form state
  const [formData, setFormData] = useState<IPWhitelistFormData>({
    name: '',
    description: '',
    cidr_notation: '',
    start_ip: '',
    end_ip: '',
    is_active: true,
  });

  /**
   * Fetch IP whitelist entries from backend
   */
  const fetchEntries = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await securityConfigClient.listIPWhitelist(organizationId);
      setEntries(result.entries || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load IP whitelist entries';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
  }, [organizationId]);

  /**
   * Open create dialog
   */
  const handleCreate = () => {
    setEditingEntry(null);
    setIpType('cidr');
    setFormData({
      name: '',
      description: '',
      cidr_notation: '',
      start_ip: '',
      end_ip: '',
      is_active: true,
    });
    setDialogOpen(true);
  };

  /**
   * Open edit dialog
   */
  const handleEdit = (entry: IPWhitelistItem) => {
    setEditingEntry(entry);
    setIpType(entry.cidr_notation ? 'cidr' : 'range');
    setFormData({
      name: entry.name,
      description: entry.description || '',
      cidr_notation: entry.cidr_notation || '',
      start_ip: entry.start_ip || '',
      end_ip: entry.end_ip || '',
      is_active: entry.is_active,
    });
    setDialogOpen(true);
  };

  /**
   * Open delete confirmation dialog
   */
  const handleDeleteClick = (entry: IPWhitelistItem) => {
    setEntryToDelete(entry);
    setDeleteDialogOpen(true);
  };

  /**
   * Confirm delete
   */
  const handleDeleteConfirm = async () => {
    if (!entryToDelete) return;

    setSubmitting(true);
    try {
      await securityConfigClient.deleteIPWhitelistEntry(entryToDelete.id);

      // Optimistic update
      setEntries(entries.filter((e) => e.id !== entryToDelete.id));
      setDeleteDialogOpen(false);
      setEntryToDelete(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete IP whitelist entry';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Validate form data
   */
  const validateForm = (): string | null => {
    if (!formData.name.trim()) {
      return 'Name is required';
    }

    if (ipType === 'cidr') {
      if (!formData.cidr_notation.trim()) {
        return 'CIDR notation is required';
      }
      // Basic CIDR validation
      const cidrPattern = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
      if (!cidrPattern.test(formData.cidr_notation.trim())) {
        return 'Invalid CIDR notation. Example: 192.168.1.0/24';
      }
    } else {
      if (!formData.start_ip.trim() || !formData.end_ip.trim()) {
        return 'Both start and end IP addresses are required';
      }
      // Basic IP validation
      const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
      if (!ipPattern.test(formData.start_ip.trim()) || !ipPattern.test(formData.end_ip.trim())) {
        return 'Invalid IP address format. Example: 192.168.1.1';
      }
    }

    return null;
  };

  /**
   * Submit form (create or update)
   */
  const handleSubmit = async () => {
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      if (editingEntry) {
        // Update existing entry
        const updateData: IPWhitelistUpdate = {
          name: formData.name,
          description: formData.description || undefined,
          is_active: formData.is_active,
        };

        if (ipType === 'cidr') {
          updateData.cidr_notation = formData.cidr_notation;
          updateData.start_ip = null;
          updateData.end_ip = null;
        } else {
          updateData.cidr_notation = null;
          updateData.start_ip = formData.start_ip;
          updateData.end_ip = formData.end_ip;
        }

        const updated = await securityConfigClient.updateIPWhitelistEntry(editingEntry.id, updateData);
        setEntries(entries.map((e) => (e.id === updated.id ? updated : e)));
      } else {
        // Create new entry
        const createData: IPWhitelistCreate = {
          organization_id: organizationId,
          name: formData.name,
          description: formData.description || undefined,
          is_active: formData.is_active,
        };

        if (ipType === 'cidr') {
          createData.cidr_notation = formData.cidr_notation;
        } else {
          createData.start_ip = formData.start_ip;
          createData.end_ip = formData.end_ip;
        }

        const created = await securityConfigClient.createIPWhitelistEntry(createData);
        setEntries([created, ...entries]);
      }

      setDialogOpen(false);
      setFormData({
        name: '',
        description: '',
        cidr_notation: '',
        start_ip: '',
        end_ip: '',
        is_active: true,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save IP whitelist entry';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Get IP display text
   */
  const getIPDisplay = (entry: IPWhitelistItem): string => {
    if (entry.cidr_notation) {
      return entry.cidr_notation;
    }
    if (entry.start_ip && entry.end_ip) {
      return `${entry.start_ip} - ${entry.end_ip}`;
    }
    return 'N/A';
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
          Loading IP whitelist entries...
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
          <Button color="inherit" onClick={fetchEntries} startIcon={<RefreshIcon />}>
            Try Again
          </Button>
        }
      >
        <AlertTitle>Error</AlertTitle>
        {error}
      </Alert>
    );
  }

  const activeCount = entries.filter((e) => e.is_active).length;
  const inactiveCount = entries.length - activeCount;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            IP Whitelist Management
          </Typography>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchEntries} size="small">
            Refresh
          </Button>
        </Box>

        {/* Summary Statistics */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'primary.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {entries.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Total Rules
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'success.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {activeCount}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Active
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ borderColor: inactiveCount > 0 ? 'warning.main' : 'text.disabled' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color={inactiveCount > 0 ? 'warning.main' : 'text.disabled'} fontWeight={700}>
                  {inactiveCount}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Inactive
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Create Button */}
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
            size="large"
          >
            Add IP Rule
          </Button>
        </Box>
      </Paper>

      {/* Entries List */}
      {entries.length === 0 ? (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <SecurityIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No IP Whitelist Rules
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Add IP ranges to restrict access to your organization
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {entries.map((entry) => (
            <Grid item xs={12} md={6} key={entry.id}>
              <Card
                variant="outlined"
                sx={{
                  opacity: entry.is_active ? 1 : 0.6,
                  transition: 'opacity 0.2s',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <NetworkIcon color="primary" />
                      <Typography variant="h6" fontWeight={600}>
                        {entry.name}
                      </Typography>
                    </Box>
                    <Stack direction="row" spacing={1}>
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(entry)}
                        color="primary"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteClick(entry)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Stack>
                  </Box>

                  {entry.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {entry.description}
                    </Typography>
                  )}

                  <Box sx={{ mb: 2 }}>
                    <Chip
                      label={getIPDisplay(entry)}
                      size="medium"
                      color={entry.is_active ? 'success' : 'default'}
                      variant="filled"
                    />
                    <Chip
                      label={entry.is_active ? 'Active' : 'Inactive'}
                      size="small"
                      color={entry.is_active ? 'success' : 'default'}
                      variant="outlined"
                      sx={{ ml: 1 }}
                    />
                  </Box>

                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
                    Created: {new Date(entry.created_at).toLocaleDateString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => !submitting && setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              {editingEntry ? 'Edit IP Whitelist Rule' : 'Add IP Whitelist Rule'}
            </Typography>
            <IconButton
              onClick={() => setDialogOpen(false)}
              disabled={submitting}
              size="small"
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Name"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Office Network"
              helperText="A descriptive name for this IP whitelist rule"
              disabled={submitting}
            />

            <TextField
              label="Description"
              fullWidth
              multiline
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Optional description"
              helperText="Optional additional details about this rule"
              disabled={submitting}
            />

            <FormControl fullWidth>
              <InputLabel>IP Type</InputLabel>
              <Select
                value={ipType}
                label="IP Type"
                onChange={(e) => setIpType(e.target.value as 'cidr' | 'range')}
                disabled={submitting}
              >
                <MenuItem value="cidr">CIDR Notation (e.g., 192.168.1.0/24)</MenuItem>
                <MenuItem value="range">IP Range (e.g., 192.168.1.1 - 192.168.1.100)</MenuItem>
              </Select>
            </FormControl>

            {ipType === 'cidr' ? (
              <TextField
                label="CIDR Notation"
                fullWidth
                required
                value={formData.cidr_notation}
                onChange={(e) => setFormData({ ...formData, cidr_notation: e.target.value })}
                placeholder="192.168.1.0/24"
                disabled={submitting}
                helperText="Enter an IP range using CIDR notation (e.g., 192.168.1.0/24 for a range of 256 addresses)"
              />
            ) : (
              <>
                <TextField
                  label="Start IP Address"
                  fullWidth
                  required
                  value={formData.start_ip}
                  onChange={(e) => setFormData({ ...formData, start_ip: e.target.value })}
                  placeholder="192.168.1.1"
                  disabled={submitting}
                  helperText="The starting IP address of the range (e.g., 192.168.1.1)"
                />
                <TextField
                  label="End IP Address"
                  fullWidth
                  required
                  value={formData.end_ip}
                  onChange={(e) => setFormData({ ...formData, end_ip: e.target.value })}
                  placeholder="192.168.1.100"
                  disabled={submitting}
                  helperText="The ending IP address of the range (e.g., 192.168.1.100)"
                />
              </>
            )}

            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  disabled={submitting}
                />
              }
              label="Active"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={submitting || !formData.name}
            startIcon={submitting ? <CircularProgress size={16} /> : null}
          >
            {submitting ? 'Saving...' : editingEntry ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete IP Whitelist Rule</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Are you sure you want to delete the IP whitelist rule &quot;{entryToDelete?.name}&quot;?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {submitting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default IPWhitelistManager;
