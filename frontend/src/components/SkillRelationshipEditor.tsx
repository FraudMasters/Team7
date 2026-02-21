import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { config } from '@/config';
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
  Slider,
  Tooltip,
  Autocomplete,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  Link as LinkIcon,
  FilterList as FilterListIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';

/**
 * Skill taxonomy summary for autocomplete
 */
interface SkillTaxonomySummary {
  id: string;
  skill_name: string;
  industry: string;
  context?: string;
}

/**
 * Skill relationship response from backend
 */
interface SkillRelationship {
  id: string;
  source_skill_id: string;
  target_skill_id: string;
  source_skill_name?: string;
  target_skill_name?: string;
  relationship_type: string;
  weight?: number;
  extra_metadata?: Record<string, unknown>;
  is_active: boolean;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

/**
 * List response from backend
 */
interface SkillRelationshipListResponse {
  relationships: SkillRelationship[];
  total_count: number;
}

/**
 * Relationship type definition
 */
interface RelationshipTypeOption {
  value: string;
  label: string;
  description: string;
}

/**
 * Form data for creating/editing relationships
 */
interface RelationshipFormData {
  source_skill_id: string;
  target_skill_id: string;
  relationship_type: string;
  weight: number;
  is_active: boolean;
}

/**
 * SkillRelationshipEditor component props
 */
interface SkillRelationshipEditorProps {
  /** Organization ID to manage relationships for */
  organizationId?: string;
  /** API endpoint URL for skill relationships */
  apiUrl?: string;
  /** Taxonomy API URL for fetching skills */
  taxonomyApiUrl?: string;
  /** Pre-selected source skill ID */
  sourceSkillId?: string;
  /** Callback when a relationship is created/updated/deleted */
  onRelationshipChange?: () => void;
}

/**
 * Get relationship type color
 */
const getRelationshipTypeColor = (
  type: string
): 'primary' | 'success' | 'warning' | 'info' | 'error' | 'default' => {
  switch (type) {
    case 'parent_child':
      return 'primary';
    case 'similar':
      return 'success';
    case 'prerequisite':
      return 'warning';
    case 'related':
      return 'info';
    default:
      return 'default';
  }
};

/**
 * Get relationship type label
 */
const getRelationshipTypeLabel = (type: string): string => {
  switch (type) {
    case 'parent_child':
      return 'Parent → Child';
    case 'similar':
      return 'Similar';
    case 'prerequisite':
      return 'Prerequisite';
    case 'related':
      return 'Related';
    default:
      return type;
  }
};

/**
 * SkillRelationshipEditor Component
 *
 * Provides an interface for managing relationships between skills.
 * Features include:
 * - List all skill relationships
 * - Create new relationships between skills
 * - Edit existing relationships (type, weight, status)
 * - Delete relationships
 * - Filter by relationship type
 * - Visual relationship display with skill names
 *
 * @example
 * ```tsx
 * <SkillRelationshipEditor
 *   sourceSkillId="skill-123"
 *   onRelationshipChange={() => refreshData()}
 * />
 * ```
 */
const SkillRelationshipEditor: React.FC<SkillRelationshipEditorProps> = ({
  organizationId = 'default',
  apiUrl = `${config.api.url}/api/skill-relationships`,
  taxonomyApiUrl = `${config.api.url}/api/skill-taxonomies`,
  sourceSkillId,
  onRelationshipChange,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [relationships, setRelationships] = useState<SkillRelationship[]>([]);
  const [skills, setSkills] = useState<SkillTaxonomySummary[]>([]);
  const [relationshipTypes, setRelationshipTypes] = useState<RelationshipTypeOption[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRelationship, setEditingRelationship] = useState<SkillRelationship | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [relationshipToDelete, setRelationshipToDelete] = useState<SkillRelationship | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [typeFilter, setTypeFilter] = useState<string>('');

  // Form state
  const [formData, setFormData] = useState<RelationshipFormData>({
    source_skill_id: sourceSkillId || '',
    target_skill_id: '',
    relationship_type: 'related',
    weight: 0.5,
    is_active: true,
  });

  /**
   * Fetch skill relationships from backend
   */
  const fetchRelationships = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (sourceSkillId) {
        params.append('source_skill_id', sourceSkillId);
      }
      if (typeFilter) {
        params.append('relationship_type', typeFilter);
      }

      const response = await fetch(`${apiUrl}/?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch relationships: ${response.statusText}`);
      }

      const result: SkillRelationshipListResponse = await response.json();
      setRelationships(result.relationships || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('skillRelationship.errors.failedToLoad', 'Failed to load relationships');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, sourceSkillId, typeFilter, t]);

  /**
   * Fetch available skills for autocomplete
   */
  const fetchSkills = useCallback(async () => {
    try {
      const response = await fetch(`${taxonomyApiUrl}/?include_inactive=false`);

      if (!response.ok) {
        throw new Error(`Failed to fetch skills: ${response.statusText}`);
      }

      const result = await response.json();
      const skillList: SkillTaxonomySummary[] = (result.skills || []).map((s: any) => ({
        id: s.id,
        skill_name: s.skill_name,
        industry: s.industry,
        context: s.context,
      }));
      setSkills(skillList);
    } catch (err) {
      // Non-blocking error - skills are optional for display
    }
  }, [taxonomyApiUrl]);

  /**
   * Fetch relationship types from backend
   */
  const fetchRelationshipTypes = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/types/`);

      if (!response.ok) {
        throw new Error(`Failed to fetch relationship types: ${response.statusText}`);
      }

      const result = await response.json();
      setRelationshipTypes(result.relationship_types || []);
    } catch (err) {
      // Use default types if API fails
      setRelationshipTypes([
        { value: 'parent_child', label: 'Parent → Child', description: 'Hierarchical relationship' },
        { value: 'similar', label: 'Similar', description: 'Skills that can be substituted' },
        { value: 'prerequisite', label: 'Prerequisite', description: 'One skill is required before another' },
        { value: 'related', label: 'Related', description: 'Skills often used together' },
      ]);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchRelationships();
    fetchSkills();
    fetchRelationshipTypes();
  }, [fetchRelationships, fetchSkills, fetchRelationshipTypes]);

  /**
   * Open create dialog
   */
  const handleCreate = () => {
    setEditingRelationship(null);
    setFormData({
      source_skill_id: sourceSkillId || '',
      target_skill_id: '',
      relationship_type: 'related',
      weight: 0.5,
      is_active: true,
    });
    setDialogOpen(true);
  };

  /**
   * Open edit dialog
   */
  const handleEdit = (relationship: SkillRelationship) => {
    setEditingRelationship(relationship);
    setFormData({
      source_skill_id: relationship.source_skill_id,
      target_skill_id: relationship.target_skill_id,
      relationship_type: relationship.relationship_type,
      weight: relationship.weight ?? 0.5,
      is_active: relationship.is_active,
    });
    setDialogOpen(true);
  };

  /**
   * Open delete confirmation dialog
   */
  const handleDeleteClick = (relationship: SkillRelationship) => {
    setRelationshipToDelete(relationship);
    setDeleteDialogOpen(true);
  };

  /**
   * Confirm delete
   */
  const handleDeleteConfirm = async () => {
    if (!relationshipToDelete) return;

    setSubmitting(true);
    try {
      const response = await fetch(`${apiUrl}/${relationshipToDelete.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`${t('skillRelationship.errors.failedToDelete', 'Failed to delete relationship')}: ${response.statusText}`);
      }

      // Optimistic update
      setRelationships(relationships.filter((r) => r.id !== relationshipToDelete.id));
      setDeleteDialogOpen(false);
      setRelationshipToDelete(null);

      if (onRelationshipChange) {
        onRelationshipChange();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('skillRelationship.errors.failedToDelete', 'Failed to delete relationship');
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
      if (!formData.source_skill_id || !formData.target_skill_id) {
        throw new Error(t('skillRelationship.errors.skillsRequired', 'Both source and target skills are required'));
      }

      if (formData.source_skill_id === formData.target_skill_id) {
        throw new Error(t('skillRelationship.errors.sameSkill', 'Source and target skills cannot be the same'));
      }

      if (editingRelationship) {
        // Update existing relationship
        const response = await fetch(`${apiUrl}/${editingRelationship.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            relationship_type: formData.relationship_type,
            weight: formData.weight,
            is_active: formData.is_active,
          }),
        });

        if (!response.ok) {
          throw new Error(`${t('skillRelationship.errors.failedToUpdate', 'Failed to update relationship')}: ${response.statusText}`);
        }

        const updated: SkillRelationship = await response.json();
        setRelationships(relationships.map((r) => (r.id === updated.id ? updated : r)));
      } else {
        // Create new relationship
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            relationships: [
              {
                source_skill_id: formData.source_skill_id,
                target_skill_id: formData.target_skill_id,
                relationship_type: formData.relationship_type,
                weight: formData.weight,
                is_active: formData.is_active,
              },
            ],
          }),
        });

        if (!response.ok) {
          throw new Error(`${t('skillRelationship.errors.failedToCreate', 'Failed to create relationship')}: ${response.statusText}`);
        }

        const result: SkillRelationshipListResponse = await response.json();
        if (result.relationships && result.relationships.length > 0) {
          setRelationships([...relationships, ...result.relationships]);
        }
      }

      setDialogOpen(false);
      setFormData({
        source_skill_id: sourceSkillId || '',
        target_skill_id: '',
        relationship_type: 'related',
        weight: 0.5,
        is_active: true,
      });

      if (onRelationshipChange) {
        onRelationshipChange();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('skillRelationship.errors.failedToCreate', 'Failed to create relationship');
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Get skill name by ID
   */
  const getSkillName = (skillId: string): string => {
    const skill = skills.find((s) => s.id === skillId);
    return skill?.skill_name || skillId.substring(0, 8);
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
          {t('skillRelationship.loading', 'Loading relationships...')}
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
          <Button color="inherit" onClick={fetchRelationships} startIcon={<RefreshIcon />}>
            {t('common.tryAgain', 'Try Again')}
          </Button>
        }
      >
        <AlertTitle>{t('skillRelationship.errorTitle', 'Error')}</AlertTitle>
        {error}
      </Alert>
    );
  }

  const activeCount = relationships.filter((r) => r.is_active).length;
  const inactiveCount = relationships.length - activeCount;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            {t('skillRelationship.title', 'Skill Relationships')}
          </Typography>
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchRelationships} size="small">
              {t('skillRelationship.refreshButton', 'Refresh')}
            </Button>
          </Stack>
        </Box>

        {/* Filter and Create */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Stack direction="row" spacing={2} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <FilterListIcon fontSize="small" />
                  <Typography variant="body2">{t('skillRelationship.filterByType', 'Filter by Type')}</Typography>
                </Stack>
              </InputLabel>
              <Select
                value={typeFilter}
                label="Filter by Type"
                onChange={(e) => setTypeFilter(e.target.value)}
                startAdornment={
                  <FilterListIcon fontSize="small" sx={{ ml: 1, mr: 1, color: 'action.active' }} />
                }
              >
                <MenuItem value="">{t('skillRelationship.allTypes', 'All Types')}</MenuItem>
                {relationshipTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
            size="large"
          >
            {t('skillRelationship.addButton', 'Add Relationship')}
          </Button>
        </Box>

        {/* Summary Statistics */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'primary.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {relationships.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('skillRelationship.totalRelationships', 'Total Relationships')}
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
                  {t('skillRelationship.active', 'Active')}
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
                  {t('skillRelationship.inactive', 'Inactive')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Relationships List */}
      {relationships.length === 0 ? (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <LinkIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {t('skillRelationship.noRelationships', 'No Relationships Found')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('skillRelationship.noRelationshipsMessage', 'Create relationships between skills to improve matching accuracy.')}
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
            sx={{ mt: 2 }}
          >
            {t('skillRelationship.addFirstRelationship', 'Add First Relationship')}
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {relationships.map((relationship) => (
            <Grid item xs={12} md={6} key={relationship.id}>
              <Card
                variant="outlined"
                sx={{
                  opacity: relationship.is_active ? 1 : 0.6,
                  transition: 'opacity 0.2s',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1" fontWeight={600}>
                        {relationship.source_skill_name || getSkillName(relationship.source_skill_id)}
                      </Typography>
                      <ArrowForwardIcon fontSize="small" color="action" />
                      <Typography variant="subtitle1" fontWeight={600}>
                        {relationship.target_skill_name || getSkillName(relationship.target_skill_id)}
                      </Typography>
                    </Box>
                    <Stack direction="row" spacing={1}>
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(relationship)}
                        color="primary"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteClick(relationship)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Stack>
                  </Box>

                  <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                    <Chip
                      label={getRelationshipTypeLabel(relationship.relationship_type)}
                      size="small"
                      color={getRelationshipTypeColor(relationship.relationship_type)}
                      variant="filled"
                    />
                    <Chip
                      label={relationship.is_active ? t('skillRelationship.active', 'Active') : t('skillRelationship.inactive', 'Inactive')}
                      size="small"
                      color={relationship.is_active ? 'success' : 'default'}
                      variant="outlined"
                    />
                    {relationship.weight !== undefined && relationship.weight !== null && (
                      <Tooltip title={`Relationship strength: ${Math.round(relationship.weight * 100)}%`}>
                        <Chip
                          label={`${Math.round(relationship.weight * 100)}%`}
                          size="small"
                          variant="outlined"
                          color="primary"
                        />
                      </Tooltip>
                    )}
                  </Stack>

                  <Divider sx={{ my: 1 }} />

                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                    {t('skillRelationship.createdAt', 'Created')}: {new Date(relationship.created_at).toLocaleDateString()}
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
              {editingRelationship
                ? t('skillRelationship.dialog.editTitle', 'Edit Relationship')
                : t('skillRelationship.dialog.addTitle', 'Add Relationship')}
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
            {/* Source Skill */}
            <Autocomplete
              value={skills.find((s) => s.id === formData.source_skill_id) || null}
              onChange={(_event, newValue) => {
                setFormData({ ...formData, source_skill_id: newValue?.id || '' });
              }}
              options={skills}
              getOptionLabel={(option) => option.skill_name}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              renderOption={(props, option) => (
                <li {...props} key={option.id}>
                  <Box>
                    <Typography variant="body2">{option.skill_name}</Typography>
                    {option.context && (
                      <Typography variant="caption" color="text.secondary">
                        {option.context} • {option.industry}
                      </Typography>
                    )}
                  </Box>
                </li>
              )}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label={t('skillRelationship.dialog.sourceSkill', 'Source Skill')}
                  placeholder={t('skillRelationship.dialog.skillPlaceholder', 'Search skills...')}
                  required
                  disabled={submitting || !!editingRelationship}
                />
              )}
              disabled={submitting || !!editingRelationship}
            />

            {/* Target Skill */}
            <Autocomplete
              value={skills.find((s) => s.id === formData.target_skill_id) || null}
              onChange={(_event, newValue) => {
                setFormData({ ...formData, target_skill_id: newValue?.id || '' });
              }}
              options={skills.filter((s) => s.id !== formData.source_skill_id)}
              getOptionLabel={(option) => option.skill_name}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              renderOption={(props, option) => (
                <li {...props} key={option.id}>
                  <Box>
                    <Typography variant="body2">{option.skill_name}</Typography>
                    {option.context && (
                      <Typography variant="caption" color="text.secondary">
                        {option.context} • {option.industry}
                      </Typography>
                    )}
                  </Box>
                </li>
              )}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label={t('skillRelationship.dialog.targetSkill', 'Target Skill')}
                  placeholder={t('skillRelationship.dialog.skillPlaceholder', 'Search skills...')}
                  required
                  disabled={submitting || !!editingRelationship}
                />
              )}
              disabled={submitting || !!editingRelationship}
            />

            {/* Relationship Type */}
            <FormControl fullWidth required>
              <InputLabel>{t('skillRelationship.dialog.relationshipType', 'Relationship Type')}</InputLabel>
              <Select
                value={formData.relationship_type}
                label={t('skillRelationship.dialog.relationshipType', 'Relationship Type')}
                onChange={(e) => setFormData({ ...formData, relationship_type: e.target.value })}
                disabled={submitting}
              >
                {relationshipTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    <Box>
                      <Typography variant="body2">{type.label}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {type.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Weight Slider */}
            <Box>
              <Typography variant="body2" gutterBottom>
                {t('skillRelationship.dialog.weight', 'Relationship Strength')}: {Math.round(formData.weight * 100)}%
              </Typography>
              <Slider
                value={formData.weight}
                onChange={(_event, value) => setFormData({ ...formData, weight: value as number })}
                min={0}
                max={1}
                step={0.1}
                marks={[
                  { value: 0, label: 'Weak' },
                  { value: 0.5, label: 'Medium' },
                  { value: 1, label: 'Strong' },
                ]}
                disabled={submitting}
              />
            </Box>

            {/* Status */}
            <FormControl fullWidth>
              <InputLabel>{t('skillRelationship.dialog.status', 'Status')}</InputLabel>
              <Select
                value={formData.is_active.toString()}
                label={t('skillRelationship.dialog.status', 'Status')}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.value === 'true' })}
                disabled={submitting}
              >
                <MenuItem value="true">{t('skillRelationship.dialog.statusActive', 'Active')}</MenuItem>
                <MenuItem value="false">{t('skillRelationship.dialog.statusInactive', 'Inactive')}</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={submitting}>
            {t('skillRelationship.dialog.cancel', 'Cancel')}
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={submitting || !formData.source_skill_id || !formData.target_skill_id || !formData.relationship_type}
            startIcon={submitting ? <CircularProgress size={16} /> : null}
          >
            {submitting
              ? t('skillRelationship.dialog.saving', 'Saving...')
              : editingRelationship
                ? t('skillRelationship.dialog.update', 'Update')
                : t('skillRelationship.dialog.create', 'Create')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>{t('skillRelationship.deleteDialog.title', 'Delete Relationship')}</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            {t('skillRelationship.deleteDialog.message', 'Are you sure you want to delete this relationship?')}
          </Typography>
          {relationshipToDelete && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
              <Stack direction="row" alignItems="center" spacing={1}>
                <Typography variant="body2" fontWeight={600}>
                  {relationshipToDelete.source_skill_name || getSkillName(relationshipToDelete.source_skill_id)}
                </Typography>
                <ArrowForwardIcon fontSize="small" color="action" />
                <Typography variant="body2" fontWeight={600}>
                  {relationshipToDelete.target_skill_name || getSkillName(relationshipToDelete.target_skill_id)}
                </Typography>
              </Stack>
              <Chip
                label={getRelationshipTypeLabel(relationshipToDelete.relationship_type)}
                size="small"
                color={getRelationshipTypeColor(relationshipToDelete.relationship_type)}
                sx={{ mt: 1 }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={submitting}>
            {t('skillRelationship.deleteDialog.cancel', 'Cancel')}
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {submitting ? t('skillRelationship.deleteDialog.deleting', 'Deleting...') : t('skillRelationship.deleteDialog.confirm', 'Delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default SkillRelationshipEditor;
