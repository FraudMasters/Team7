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
  Fab,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

/**
 * Individual custom synonym entry interface
 */
interface CustomSynonymEntry {
  canonical_skill: string;
  custom_synonyms: string[];
  context?: string;
  is_active: boolean;
}

/**
 * Custom synonym response from backend
 */
interface CustomSynonym {
  id: string;
  organization_id: string;
  canonical_skill: string;
  custom_synonyms: string[];
  context?: string;
  created_by?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * List response from backend
 */
interface CustomSynonymListResponse {
  organization_id: string;
  synonyms: CustomSynonym[];
  total_count: number;
}

/**
 * Form data for creating/editing synonyms
 */
interface SynonymFormData {
  canonical_skill: string;
  custom_synonyms: string;
  context: string;
  is_active: boolean;
}

/**
 * CustomSynonymsManager Component Props
 */
interface CustomSynonymsManagerProps {
  /** Organization ID to manage synonyms for */
  organizationId: string;
  /** API endpoint URL for custom synonyms */
  apiUrl?: string;
}

/**
 * CustomSynonymsManager Component
 *
 * Provides a comprehensive admin interface for managing organization-specific
 * custom skill synonyms. Features include:
 * - List all custom synonyms for the organization
 * - Create new custom synonym entries
 * - Edit existing synonym mappings
 * - Delete individual or all synonyms
 * - Toggle active/inactive status
 * - Real-time updates with optimistic UI
 *
 * @example
 * ```tsx
 * <CustomSynonymsManager organizationId="org123" />
 * ```
 */
const CustomSynonymsManager: React.FC<CustomSynonymsManagerProps> = ({
  organizationId,
  apiUrl = 'http://localhost:8000/api/custom-synonyms',
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [synonyms, setSynonyms] = useState<CustomSynonym[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSynonym, setEditingSynonym] = useState<CustomSynonym | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [synonymToDelete, setSynonymToDelete] = useState<CustomSynonym | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [formData, setFormData] = useState<SynonymFormData>({
    canonical_skill: '',
    custom_synonyms: '',
    context: '',
    is_active: true,
  });

  /**
   * Fetch custom synonyms from backend
   */
  const fetchSynonyms = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/?organization_id=${organizationId}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch synonyms: ${response.statusText}`);
      }

      const result: CustomSynonymListResponse = await response.json();
      setSynonyms(result.synonyms || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('adminSynonyms.errors.failedToLoad');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (organizationId) {
      fetchSynonyms();
    }
  }, [organizationId]);

  /**
   * Open create dialog
   */
  const handleCreate = () => {
    setEditingSynonym(null);
    setFormData({
      canonical_skill: '',
      custom_synonyms: '',
      context: '',
      is_active: true,
    });
    setDialogOpen(true);
  };

  /**
   * Open edit dialog
   */
  const handleEdit = (synonym: CustomSynonym) => {
    setEditingSynonym(synonym);
    setFormData({
      canonical_skill: synonym.canonical_skill,
      custom_synonyms: synonym.custom_synonyms.join(', '),
      context: synonym.context || '',
      is_active: synonym.is_active,
    });
    setDialogOpen(true);
  };

  /**
   * Open delete confirmation dialog
   */
  const handleDeleteClick = (synonym: CustomSynonym) => {
    setSynonymToDelete(synonym);
    setDeleteDialogOpen(true);
  };

  /**
   * Confirm delete
   */
  const handleDeleteConfirm = async () => {
    if (!synonymToDelete) return;

    setSubmitting(true);
    try {
      const response = await fetch(`${apiUrl}/${synonymToDelete.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`${t('adminSynonyms.errors.failedToDelete')}: ${response.statusText}`);
      }

      // Optimistic update
      setSynonyms(synonyms.filter((s) => s.id !== synonymToDelete.id));
      setDeleteDialogOpen(false);
      setSynonymToDelete(null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('adminSynonyms.errors.failedToDelete');
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
      // Parse custom synonyms
      const customSynonymsArray = formData.custom_synonyms
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      if (customSynonymsArray.length === 0) {
        throw new Error(t('adminSynonyms.dialog.atLeastOneError'));
      }

      if (editingSynonym) {
        // Update existing synonym
        const response = await fetch(`${apiUrl}/${editingSynonym.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            canonical_skill: formData.canonical_skill,
            custom_synonyms: customSynonymsArray,
            context: formData.context || null,
            is_active: formData.is_active,
          }),
        });

        if (!response.ok) {
          throw new Error(`${t('adminSynonyms.errors.failedToUpdate')}: ${response.statusText}`);
        }

        const updated: CustomSynonym = await response.json();
        setSynonyms(synonyms.map((s) => (s.id === updated.id ? updated : s)));
      } else {
        // Create new synonym
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            organization_id: organizationId,
            synonyms: [
              {
                canonical_skill: formData.canonical_skill,
                custom_synonyms: customSynonymsArray,
                context: formData.context || null,
                is_active: formData.is_active,
              },
            ],
          }),
        });

        if (!response.ok) {
          throw new Error(`${t('adminSynonyms.errors.failedToCreate')}: ${response.statusText}`);
        }

        const result: CustomSynonymListResponse = await response.json();
        if (result.synonyms && result.synonyms.length > 0) {
          setSynonyms([...synonyms, ...result.synonyms]);
        }
      }

      setDialogOpen(false);
      setFormData({
        canonical_skill: '',
        custom_synonyms: '',
        context: '',
        is_active: true,
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('adminSynonyms.errors.failedToCreate');
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Get context color for display
   */
  const getContextColor = (context?: string) => {
    switch (context) {
      case 'web_framework':
        return 'primary' as const;
      case 'language':
        return 'success' as const;
      case 'database':
        return 'warning' as const;
      case 'tool':
        return 'info' as const;
      default:
        return 'default' as const;
    }
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
          {t('adminSynonyms.loading')}
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
          <Button color="inherit" onClick={fetchSynonyms} startIcon={<RefreshIcon />}>
            {t('common.tryAgain')}
          </Button>
        }
      >
        <AlertTitle>{t('adminSynonyms.errorTitle')}</AlertTitle>
        {error}
      </Alert>
    );
  }

  const activeCount = synonyms.filter((s) => s.is_active).length;
  const inactiveCount = synonyms.length - activeCount;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            {t('adminSynonyms.title')}
          </Typography>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchSynonyms} size="small">
            {t('adminSynonyms.refreshButton')}
          </Button>
        </Box>

        {/* Summary Statistics */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'primary.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {synonyms.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('adminSynonyms.totalSynonyms')}
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
                  {t('adminSynonyms.active')}
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
                  {t('adminSynonyms.inactive')}
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
            {t('adminSynonyms.addButton')}
          </Button>
        </Box>
      </Paper>

      {/* Synonyms List */}
      {synonyms.length === 0 ? (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {t('adminSynonyms.noSynonyms')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('adminSynonyms.noSynonymsMessage')}
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {synonyms.map((synonym) => (
            <Grid item xs={12} md={6} key={synonym.id}>
              <Card
                variant="outlined"
                sx={{
                  opacity: synonym.is_active ? 1 : 0.6,
                  transition: 'opacity 0.2s',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" fontWeight={600}>
                      {synonym.canonical_skill}
                    </Typography>
                    <Stack direction="row" spacing={1}>
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(synonym)}
                        color="primary"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteClick(synonym)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Stack>
                  </Box>

                  {synonym.context && (
                    <Box sx={{ mb: 2 }}>
                      <Chip
                        label={synonym.context}
                        size="small"
                        color={getContextColor(synonym.context)}
                        variant="outlined"
                      />
                      <Chip
                        label={synonym.is_active ? t('adminSynonyms.active') : t('adminSynonyms.inactive')}
                        size="small"
                        color={synonym.is_active ? 'success' : 'default'}
                        variant="filled"
                        sx={{ ml: 1 }}
                      />
                    </Box>
                  )}

                  <Divider sx={{ my: 1 }} />

                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                      {t('adminSynonyms.synonym.synonyms')}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {synonym.custom_synonyms.map((custom, index) => (
                        <Chip
                          key={index}
                          label={custom}
                          size="small"
                          variant="filled"
                          color="primary"
                        />
                      ))}
                    </Box>
                  </Box>

                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
                    {t('adminSynonyms.synonym.createdAt')}: {new Date(synonym.created_at).toLocaleDateString()}
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
              {editingSynonym ? t('adminSynonyms.dialog.editTitle') : t('adminSynonyms.dialog.addTitle')}
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
              label={t('adminSynonyms.dialog.canonicalSkill')}
              fullWidth
              required
              value={formData.canonical_skill}
              onChange={(e) => setFormData({ ...formData, canonical_skill: e.target.value })}
              placeholder={t('adminSynonyms.dialog.canonicalSkillPlaceholder')}
              disabled={submitting}
            />

            <TextField
              label={t('adminSynonyms.dialog.customSynonyms')}
              fullWidth
              required
              multiline
              rows={3}
              value={formData.custom_synonyms}
              onChange={(e) => setFormData({ ...formData, custom_synonyms: e.target.value })}
              placeholder={t('adminSynonyms.dialog.customSynonymsPlaceholder')}
              disabled={submitting}
              helperText={t('adminSynonyms.dialog.customSynonymsHelper')}
            />

            <TextField
              label={t('adminSynonyms.dialog.context')}
              fullWidth
              select
              value={formData.context}
              onChange={(e) => setFormData({ ...formData, context: e.target.value })}
              disabled={submitting}
            >
              <MenuItem value="">{t('adminSynonyms.dialog.contextNone')}</MenuItem>
              <MenuItem value="web_framework">{t('adminSynonyms.dialog.contextWebFramework')}</MenuItem>
              <MenuItem value="language">{t('adminSynonyms.dialog.contextLanguage')}</MenuItem>
              <MenuItem value="database">{t('adminSynonyms.dialog.contextDatabase')}</MenuItem>
              <MenuItem value="tool">{t('adminSynonyms.dialog.contextTool')}</MenuItem>
              <MenuItem value="library">{t('adminSynonyms.dialog.contextLibrary')}</MenuItem>
            </TextField>

            <FormControl fullWidth>
              <InputLabel>{t('adminSynonyms.dialog.status')}</InputLabel>
              <Select
                value={formData.is_active.toString()}
                label={t('adminSynonyms.dialog.status')}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.value === 'true' })}
                disabled={submitting}
              >
                <MenuItem value="true">{t('adminSynonyms.dialog.statusActive')}</MenuItem>
                <MenuItem value="false">{t('adminSynonyms.dialog.statusInactive')}</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={submitting}>
            {t('adminSynonyms.dialog.cancel')}
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={submitting || !formData.canonical_skill || !formData.custom_synonyms}
            startIcon={submitting ? <CircularProgress size={16} /> : null}
          >
            {submitting ? t('adminSynonyms.dialog.saving') : editingSynonym ? t('adminSynonyms.dialog.update') : t('adminSynonyms.dialog.create')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>{t('adminSynonyms.deleteDialog.title')}</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            {t('adminSynonyms.deleteDialog.message', {
              skill: synonymToDelete?.canonical_skill
            })}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {t('adminSynonyms.deleteDialog.warning')}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={submitting}>
            {t('adminSynonyms.deleteDialog.cancel')}
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {submitting ? t('adminSynonyms.deleteDialog.deleting') : t('adminSynonyms.deleteDialog.confirm')}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default CustomSynonymsManager;
