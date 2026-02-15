import React, { useState, useEffect, useCallback } from 'react';
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
  Switch,
  FormControlLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { savedSearchesClient } from '@/api/savedSearches';
import { filterSuggestionsClient } from '@/api/filterSuggestions';
import type {
  SavedSearchResponse,
  SavedSearchCreate,
  SavedSearchUpdate,
} from '@/types/api';
import type {
  AlertSettingsUpdate,
  AlertSettingsResponse,
} from '@/api/filterSuggestions';

/**
 * Extended saved search response with alert settings
 */
interface SavedSearchWithAlerts extends SavedSearchResponse {
  alert_enabled?: boolean;
  alert_frequency?: string | null;
  last_alert_at?: string | null;
}

/**
 * Form data for creating/editing saved searches
 */
interface SavedSearchFormData {
  name: string;
  query: string;
  filters: Record<string, unknown>;
}

/**
 * Alert frequency options
 */
type AlertFrequency = 'realtime' | 'daily' | 'weekly';

/**
 * Saved search manager component props
 */
interface SavedSearchManagerProps {
  /** Optional callback when a saved search is selected for execution */
  onSearchSelect?: (search: SavedSearchResponse) => void;
  /** Optional callback when saved searches are modified */
  onSavedSearchChange?: () => void;
}

/**
 * SavedSearchManager Component
 *
 * Provides a comprehensive interface for managing saved searches. Features include:
 * - List all saved searches with alert status
 * - Create new saved search entries
 * - Edit existing saved search entries
 * - Delete saved searches
 * - One-click apply to execute saved searches instantly
 * - Toggle alert settings with configurable frequency (real-time, daily, weekly)
 * - Visual indicators for alert-enabled searches
 * - Real-time updates with optimistic UI
 *
 * @example
 * ```tsx
 * <SavedSearchManager
 *   onSearchSelect={(search) => console.log('Selected:', search)}
 *   onSavedSearchChange={() => console.log('Saved searches changed')}
 * />
 * ```
 */
const SavedSearchManager: React.FC<SavedSearchManagerProps> = ({
  onSearchSelect,
  onSavedSearchChange,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savedSearches, setSavedSearches] = useState<SavedSearchWithAlerts[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSearch, setEditingSearch] = useState<SavedSearchWithAlerts | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [searchToDelete, setSearchToDelete] = useState<SavedSearchWithAlerts | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Alert settings state - map of search ID to alert settings
  const [alertSettings, setAlertSettings] = useState<Record<string, AlertSettingsResponse>>({});

  // One-click apply state
  const [applyingSearchId, setApplyingSearchId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<SavedSearchFormData>({
    name: '',
    query: '',
    filters: {},
  });

  /**
   * Fetch saved searches from backend
   */
  const fetchSavedSearches = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await savedSearchesClient.listSavedSearches(0, 100, searchQuery || undefined);
      setSavedSearches(result.saved_searches || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load saved searches';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [searchQuery]);

  useEffect(() => {
    fetchSavedSearches();
  }, [fetchSavedSearches]);

  /**
   * Open create dialog
   */
  const handleCreate = () => {
    setEditingSearch(null);
    setFormData({
      name: '',
      query: '',
      filters: {},
    });
    setDialogOpen(true);
  };

  /**
   * Open edit dialog
   */
  const handleEdit = (search: SavedSearchWithAlerts) => {
    setEditingSearch(search);
    setFormData({
      name: search.name,
      query: search.query,
      filters: search.filters || {},
    });
    setDialogOpen(true);
  };

  /**
   * Handle executing a saved search
   */
  const handleExecuteSearch = (search: SavedSearchWithAlerts) => {
    if (onSearchSelect) {
      onSearchSelect(search);
    }
  };

  /**
   * One-click apply saved search
   * Executes the saved search directly and returns results via callback
   */
  const handleOneClickApply = async (search: SavedSearchWithAlerts) => {
    setApplyingSearchId(search.id);
    try {
      await filterSuggestionsClient.applySavedSearch(search.id);

      // Notify parent of the search results
      if (onSearchSelect) {
        onSearchSelect(search);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to apply saved search';
      setError(errorMessage);
    } finally {
      setApplyingSearchId(null);
    }
  };

  /**
   * Toggle alert settings for a saved search
   */
  const handleAlertToggle = async (search: SavedSearchWithAlerts, enabled: boolean) => {
    const currentSettings = alertSettings[search.id];
    const newFrequency = currentSettings?.alert_frequency || 'daily';

    try {
      const settings: AlertSettingsUpdate = {
        alert_enabled: enabled,
        alert_frequency: enabled ? (newFrequency as AlertFrequency) : undefined,
      };

      const updated = await filterSuggestionsClient.updateAlertSettings(search.id, settings);

      // Update local state
      setAlertSettings((prev) => ({
        ...prev,
        [search.id]: updated,
      }));

      // Update the search in the list
      setSavedSearches((searches) =>
        searches.map((s) =>
          s.id === search.id
            ? {
                ...s,
                alert_enabled: updated.alert_enabled,
                alert_frequency: updated.alert_frequency,
                last_alert_at: updated.last_alert_at,
              }
            : s
        )
      );
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to update alert settings';
      setError(errorMessage);
    }
  };

  /**
   * Change alert frequency for a saved search
   */
  const handleAlertFrequencyChange = async (
    search: SavedSearchWithAlerts,
    frequency: AlertFrequency
  ) => {
    try {
      const settings: AlertSettingsUpdate = {
        alert_frequency: frequency,
      };

      const updated = await filterSuggestionsClient.updateAlertSettings(search.id, settings);

      // Update local state
      setAlertSettings((prev) => ({
        ...prev,
        [search.id]: updated,
      }));

      // Update the search in the list
      setSavedSearches((searches) =>
        searches.map((s) =>
          s.id === search.id
            ? {
                ...s,
                alert_frequency: updated.alert_frequency,
              }
            : s
        )
      );
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to update alert frequency';
      setError(errorMessage);
    }
  };

  /**
   * Open delete confirmation dialog
   */
  const handleDeleteClick = (search: SavedSearchWithAlerts) => {
    setSearchToDelete(search);
    setDeleteDialogOpen(true);
  };

  /**
   * Confirm delete
   */
  const handleDeleteConfirm = async () => {
    if (!searchToDelete) return;

    setSubmitting(true);
    try {
      await savedSearchesClient.deleteSavedSearch(searchToDelete.id);

      // Optimistic update
      setSavedSearches(savedSearches.filter((s) => s.id !== searchToDelete.id));
      setDeleteDialogOpen(false);
      setSearchToDelete(null);

      if (onSavedSearchChange) {
        onSavedSearchChange();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to delete saved search';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Submit form (create or update)
   */
  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    try {
      if (editingSearch) {
        // Update existing saved search
        const updateData: SavedSearchUpdate = {
          name: formData.name,
          query: formData.query,
          filters: Object.keys(formData.filters).length > 0 ? formData.filters : undefined,
        };

        const updated = await savedSearchesClient.updateSavedSearch(editingSearch.id, updateData);
        setSavedSearches(savedSearches.map((s) => (s.id === updated.id ? updated : s)));
      } else {
        // Create new saved search
        const createData: SavedSearchCreate = {
          name: formData.name,
          query: formData.query,
          filters: Object.keys(formData.filters).length > 0 ? formData.filters : undefined,
        };

        const created = await savedSearchesClient.createSavedSearch(createData);
        setSavedSearches([created, ...savedSearches]);
      }

      setDialogOpen(false);
      setFormData({
        name: '',
        query: '',
        filters: {},
      });

      if (onSavedSearchChange) {
        onSavedSearchChange();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to save saved search';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Format filters for display
   */
  const formatFilters = (filters: Record<string, unknown>): string[] => {
    const parts: string[] = [];

    if (filters.min_experience_years) {
      parts.push(`Min Experience: ${filters.min_experience_years}+ years`);
    }
    if (filters.max_experience_years) {
      parts.push(`Max Experience: ${filters.max_experience_years} years`);
    }
    if (filters.location) {
      parts.push(`Location: ${filters.location}`);
    }
    if (filters.skills && Array.isArray(filters.skills)) {
      parts.push(`Skills: ${filters.skills.join(', ')}`);
    }
    if (filters.min_match_score) {
      parts.push(`Min Match: ${filters.min_match_score}%`);
    }
    if (filters.max_match_score) {
      parts.push(`Max Match: ${filters.max_match_score}%`);
    }

    return parts;
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
        <Typography variant="h6" color="secondary">
          Loading saved searches...
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
          <Button color="inherit" onClick={fetchSavedSearches} startIcon={<Icon name="refresh-cw" />}>
            Try Again
          </Button>
        }
      >
        <AlertTitle>Error</AlertTitle>
        {error}
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Saved Searches
          </Typography>
          <Button
            variant="outlined"
            startIcon={<Icon name="refresh-cw" />}
            onClick={fetchSavedSearches}
            size="small"
          >
            Refresh
          </Button>
        </Box>

        <Typography variant="body2" color="secondary" paragraph>
          Save your frequently used search queries and filters for quick access. Get alerted when new candidates match your saved searches.
        </Typography>

        {/* Search Box */}
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            placeholder="Search saved searches..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            startIcon={<Icon name="search" sx={{ mr: 1, color: 'secondary' }} />}
            size="small"
          />
        </Box>

        {/* Summary Statistics */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'primary' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary" fontWeight={700}>
                  {savedSearches.length}
                </Typography>
                <Typography variant="caption" color="secondary">
                  Total Saved Searches
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'success' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success" fontWeight={700}>
                  {savedSearches.filter((s) => s.query).length}
                </Typography>
                <Typography variant="caption" color="secondary">
                  With Queries
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'warning' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="warning" fontWeight={700}>
                  {savedSearches.filter((s) => s.alert_enabled).length}
                </Typography>
                <Typography variant="caption" color="secondary">
                  Alerts Enabled
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Create Button */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            startIcon={<Icon name="plus" />}
            onClick={handleCreate}
            size="large"
          >
            Save Current Search
          </Button>
        </Box>
      </Paper>

      {/* Saved Searches List */}
      {savedSearches.length === 0 ? (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <Icon name="search" sx={{ fontSize: 60, color: 'secondary', mb: 2 }} />
          <Typography variant="h6" color="secondary" gutterBottom>
            No saved searches found
          </Typography>
          <Typography variant="body2" color="secondary">
            Save your search queries to quickly access them later. Click "Save Current Search" to create your first saved search.
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {savedSearches.map((search) => (
            <Grid item xs={12} key={search.id}>
              <Card
                variant="outlined"
                sx={{
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  borderLeft: search.alert_enabled ? '4px solid' : undefined,
                  borderLeftColor: search.alert_enabled ? 'warning.main' : undefined,
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 4,
                  },
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <Typography variant="h6" fontWeight={600}>
                          {search.name}
                        </Typography>
                        {search.alert_enabled && (
                          <Tooltip title="Alerts enabled">
                            <Chip
                              icon={<Icon name="bell" />}
                              label={search.alert_frequency || 'daily'}
                              size="small"
                              color="warning"
                              variant="outlined"
                            />
                          </Tooltip>
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 1 }}>
                        <Chip
                          icon={<Icon name="search" />}
                          label={search.query || 'No query'}
                          size="small"
                          variant="outlined"
                          color="primary"
                        />
                        <Chip
                          label={`Created: ${new Date(search.created_at).toLocaleDateString()}`}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    </Box>
                    <Stack direction="row" spacing={1}>
                      {/* One-click Apply Button */}
                      <Button
                        size="small"
                        onClick={() => handleOneClickApply(search)}
                        variant="contained"
                        color="primary"
                        startIcon={
                          applyingSearchId === search.id ? (
                            <CircularProgress size={16} color="inherit" />
                          ) : (
                            <Icon name="play" />
                          )
                        }
                        disabled={applyingSearchId === search.id}
                      >
                        {applyingSearchId === search.id ? 'Applying...' : 'Apply'}
                      </Button>
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(search)}
                        color="primary"
                      >
                        <Icon name="edit" fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteClick(search)}
                        color="error"
                      >
                        <Icon name="trash-2" fontSize="small" />
                      </IconButton>
                    </Stack>
                  </Box>

                  {search.filters && Object.keys(search.filters).length > 0 && (
                    <>
                      <Divider sx={{ my: 1 }} />
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="subtitle2" color="secondary" gutterBottom>
                          Filters:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {formatFilters(search.filters).map((filter, idx) => (
                            <Chip
                              key={idx}
                              label={filter}
                              size="small"
                              variant="filled"
                              color="info"
                            />
                          ))}
                        </Box>
                      </Box>
                    </>
                  )}

                  {/* Alert Settings Section */}
                  <Divider sx={{ my: 2 }} />
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={search.alert_enabled || false}
                            onChange={(e) => handleAlertToggle(search, e.target.checked)}
                            color="warning"
                          />
                        }
                        label={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Icon name="bell" fontSize="small" />
                            <Typography variant="body2">Get notified when new candidates match</Typography>
                          </Box>
                        }
                      />
                      {search.alert_enabled && (
                        <FormControl size="small" sx={{ minWidth: 120 }}>
                          <InputLabel id={`alert-frequency-${search.id}`}>Frequency</InputLabel>
                          <Select
                            labelId={`alert-frequency-${search.id}`}
                            value={search.alert_frequency || 'daily'}
                            label="Frequency"
                            onChange={(e) => handleAlertFrequencyChange(search, e.target.value as AlertFrequency)}
                          >
                            <MenuItem value="realtime">Real-time</MenuItem>
                            <MenuItem value="daily">Daily</MenuItem>
                            <MenuItem value="weekly">Weekly</MenuItem>
                          </Select>
                        </FormControl>
                      )}
                    </Box>
                    {search.last_alert_at && (
                      <Typography variant="caption" color="secondary">
                        Last alert: {new Date(search.last_alert_at).toLocaleString()}
                      </Typography>
                    )}
                  </Box>

                  <Typography variant="caption" color="secondary" sx={{ display: 'block', mt: 2 }}>
                    Last updated: {new Date(search.updated_at).toLocaleString()}
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
              {editingSearch ? 'Edit Saved Search' : 'Save Search'}
            </Typography>
            <IconButton
              onClick={() => setDialogOpen(false)}
              disabled={submitting}
              size="small"
            >
              <Icon name="x" />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Search Name"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Senior Python Developers"
              disabled={submitting}
              helperText="A descriptive name for this saved search"
            />

            <TextField
              label="Search Query"
              fullWidth
              required
              multiline
              rows={3}
              value={formData.query}
              onChange={(e) => setFormData({ ...formData, query: e.target.value })}
              placeholder="e.g., Python AND (Django OR Flask)"
              disabled={submitting}
              helperText="Use boolean operators (AND, OR, NOT) for complex queries"
            />

            <TextField
              label="Filters (JSON)"
              fullWidth
              multiline
              rows={4}
              value={JSON.stringify(formData.filters, null, 2)}
              onChange={(e) => {
                try {
                  const filters = JSON.parse(e.target.value);
                  setFormData({ ...formData, filters });
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              placeholder='{"min_experience_years": 5, "location": "Remote"}'
              disabled={submitting}
              error={false}
              helperText="Optional filters in JSON format"
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
            disabled={submitting || !formData.name || !formData.query}
            startIcon={submitting ? <CircularProgress size={16} /> : <Icon name="save" />}
          >
            {submitting ? 'Saving...' : editingSearch ? 'Update' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Saved Search</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Are you sure you want to delete "{searchToDelete?.name}"?
          </Typography>
          <Typography variant="body2" color="secondary" sx={{ mt: 1 }}>
            This will permanently remove the saved search. You can still use the search query manually, but it won't be saved for quick access.
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
            startIcon={submitting ? <CircularProgress size={16} /> : <Icon name="trash-2" />}
          >
            {submitting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default SavedSearchManager;
