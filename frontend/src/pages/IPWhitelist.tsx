/**
 * IP Whitelist Configuration Page
 *
 * Provides comprehensive IP whitelist management functionality including:
 * - List all IP whitelist entries for the organization
 * - Add new IP ranges (CIDR notation or IP range)
 * - Edit existing whitelist entries
 * - Delete whitelist entries
 * - Toggle active/inactive status
 * - Filter and search entries
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Snackbar,
  LinearProgress,
  Tooltip,
  Grid,
  IconButton,
  Stack,
  Pagination,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Security as SecurityIcon,
  Public as NetworkIcon,
  Info as InfoIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { securityConfigClient } from '@/api/securityConfig';
import type {
  IPWhitelistItem,
  IPWhitelistCreate,
  IPWhitelistUpdate,
} from '@/types/api';

interface FilterState {
  is_active: string;
  ip_type: string;
}

interface FormData {
  name: string;
  description: string;
  cidr_notation: string;
  start_ip: string;
  end_ip: string;
  is_active: boolean;
}

const IPWhitelistPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [entries, setEntries] = useState<IPWhitelistItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Pagination
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Filters
  const [filters, setFilters] = useState<FilterState>({
    is_active: '',
    ip_type: '',
  });

  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<IPWhitelistItem | null>(null);
  const [entryToDelete, setEntryToDelete] = useState<IPWhitelistItem | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [ipType, setIpType] = useState<'cidr' | 'range'>('cidr');

  // Form state
  const [formData, setFormData] = useState<FormData>({
    name: '',
    description: '',
    cidr_notation: '',
    start_ip: '',
    end_ip: '',
    is_active: true,
  });

  const fetchEntries = useCallback(async () => {
    try {
      setLoading(true);
      const isActiveFilter = filters.is_active === '' ? undefined : filters.is_active === 'active';

      // TODO: Get organization ID from auth context
      const response = await securityConfigClient.listIPWhitelist(
        undefined, // organizationId - will use system default or user's org
        isActiveFilter,
        rowsPerPage,
        (page - 1) * rowsPerPage
      );

      setEntries(response.entries || []);
      setTotalCount(response.total_count);
      setError(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch IP whitelist entries';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [filters, page, rowsPerPage]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

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

  const handleDeleteClick = (entry: IPWhitelistItem) => {
    setEntryToDelete(entry);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!entryToDelete) return;

    setSubmitting(true);
    try {
      await securityConfigClient.deleteIPWhitelistEntry(entryToDelete.id);
      setEntries(entries.filter((e) => e.id !== entryToDelete.id));
      setTotalCount(totalCount - 1);
      setDeleteDialogOpen(false);
      setEntryToDelete(null);
      setSuccess('IP whitelist entry deleted successfully.');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to delete IP whitelist entry';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

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
          updateData.start_ip = undefined;
          updateData.end_ip = undefined;
        } else {
          updateData.cidr_notation = undefined;
          updateData.start_ip = formData.start_ip;
          updateData.end_ip = formData.end_ip;
        }

        const updated = await securityConfigClient.updateIPWhitelistEntry(editingEntry.id, updateData);
        setEntries(entries.map((e) => (e.id === updated.id ? updated : e)));
        setSuccess('IP whitelist entry updated successfully.');
      } else {
        // Create new entry
        const createData: IPWhitelistCreate = {
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
        setTotalCount(totalCount + 1);
        setSuccess('IP whitelist entry created successfully.');
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
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to save IP whitelist entry';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleClearFilters = () => {
    setFilters({
      is_active: '',
      ip_type: '',
    });
    setPage(1);
  };

  const getIPDisplay = (entry: IPWhitelistItem): string => {
    if (entry.cidr_notation) {
      return entry.cidr_notation;
    }
    if (entry.start_ip && entry.end_ip) {
      return `${entry.start_ip} - ${entry.end_ip}`;
    }
    return 'N/A';
  };

  const getIPType = (entry: IPWhitelistItem): string => {
    return entry.cidr_notation ? 'CIDR' : 'Range';
  };

  const getFilteredEntries = () => {
    return entries.filter((entry) => {
      if (filters.ip_type === 'cidr' && !entry.cidr_notation) return false;
      if (filters.ip_type === 'range' && entry.cidr_notation) return false;
      return true;
    });
  };

  const filteredEntries = getFilteredEntries();
  const activeCount = entries.filter((e) => e.is_active).length;
  const inactiveCount = entries.length - activeCount;

  if (loading && entries.length === 0) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ width: '100%', mt: 4 }}>
          <LinearProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <SecurityIcon fontSize="large" color="primary" />
          <Typography variant="h4" fontWeight={600}>
            IP Whitelist Configuration
          </Typography>
        </Box>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchEntries}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Add IP Rule
          </Button>
        </Stack>
      </Box>

      {/* Info Alert */}
      <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 3 }}>
        <Typography variant="body2">
          Configure IP whitelist rules to restrict access to your organization. Only users from
          whitelisted IP addresses will be able to access the system when IP whitelist enforcement is enabled.
        </Typography>
      </Alert>

      {/* Error/Success Messages */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Filters Card */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Filters</Typography>
            {(filters.is_active || filters.ip_type) && (
              <Button
                size="small"
                startIcon={<ClearIcon />}
                onClick={handleClearFilters}
                sx={{ ml: 'auto' }}
              >
                Clear All
              </Button>
            )}
          </Box>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={filters.is_active}
                  onChange={(e) => {
                    setFilters({ ...filters, is_active: e.target.value });
                    setPage(1);
                  }}
                  label="Status"
                >
                  <MenuItem value="">
                    <em>All</em>
                  </MenuItem>
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>IP Type</InputLabel>
                <Select
                  value={filters.ip_type}
                  onChange={(e) => {
                    setFilters({ ...filters, ip_type: e.target.value });
                    setPage(1);
                  }}
                  label="IP Type"
                >
                  <MenuItem value="">
                    <em>All Types</em>
                  </MenuItem>
                  <MenuItem value="cidr">CIDR Notation</MenuItem>
                  <MenuItem value="range">IP Range</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <NetworkIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Total Rules
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600}>
                {totalCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <NetworkIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Active
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600} color="success.main">
                {activeCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <NetworkIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Inactive
                </Typography>
              </Box>
              <Typography variant="h4" fontWeight={600} color={inactiveCount > 0 ? 'warning.main' : 'text.secondary'}>
                {inactiveCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <NetworkIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Showing
                </Typography>
              </Box>
              <Typography variant="body1" fontWeight={500}>
                {filteredEntries.length} of {totalCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* IP Whitelist Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>IP Range</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredEntries.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                      <Typography color="text.secondary">
                        No IP whitelist entries found. Add an IP rule to get started.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredEntries.map((entry) => (
                    <TableRow
                      key={entry.id}
                      hover
                      sx={{ opacity: entry.is_active ? 1 : 0.6 }}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight={500}>
                          {entry.name}
                        </Typography>
                        {entry.description && (
                          <Typography variant="caption" color="text.secondary">
                            {entry.description}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {getIPDisplay(entry)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getIPType(entry)}
                          size="small"
                          color="info"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={entry.is_active ? 'Active' : 'Inactive'}
                          size="small"
                          color={entry.is_active ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {format(new Date(entry.created_at), 'MMM dd, yyyy')}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Edit">
                          <IconButton
                            size="small"
                            onClick={() => handleEdit(entry)}
                            color="primary"
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteClick(entry)}
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          {totalCount > rowsPerPage && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={Math.ceil(totalCount / rowsPerPage)}
                page={page}
                onChange={(e, newPage) => setPage(newPage)}
                color="primary"
                showFirstButton
                showLastButton
              />
            </Box>
          )}
        </CardContent>
      </Card>

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
              <ClearIcon />
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
                helperText="Enter IP range in CIDR notation"
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
                />
                <TextField
                  label="End IP Address"
                  fullWidth
                  required
                  value={formData.end_ip}
                  onChange={(e) => setFormData({ ...formData, end_ip: e.target.value })}
                  placeholder="192.168.1.100"
                  disabled={submitting}
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
          >
            {editingEntry ? 'Update' : 'Create'}
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
            startIcon={<DeleteIcon />}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default IPWhitelistPage;
