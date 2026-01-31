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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  DragIndicator as DragIndicatorIcon,
} from '@mui/icons-material';
import { workflowStagesClient } from '@/api/workflowStages';
import type {
  WorkflowStageResponse,
  WorkflowStageCreate,
  WorkflowStageUpdate,
} from '@/types/api';

/**
 * Form data for creating/editing workflow stages
 */
interface StageFormData {
  stage_name: string;
  stage_order: number;
  is_active: boolean;
  color: string;
  description: string;
}

/**
 * Stage config component props
 */
interface StageConfigProps {
  /** Organization ID to manage stages for */
  organizationId?: string;
}

/**
 * StageConfig Component
 *
 * Provides a comprehensive admin interface for managing organization-specific
 * workflow stages. Features include:
 * - List all workflow stages for the organization
 * - Create new workflow stage entries
 * - Edit existing stage entries
 * - Delete workflow stages
 * - Toggle active/inactive status
 * - Customize stage colors and descriptions
 * - Real-time updates with optimistic UI
 *
 * @example
 * ```tsx
 * <StageConfig organizationId="org123" />
 * ```
 */
const StageConfig: React.FC<StageConfigProps> = ({
  organizationId = 'default',
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stages, setStages] = useState<WorkflowStageResponse[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingStage, setEditingStage] = useState<WorkflowStageResponse | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [stageToDelete, setStageToDelete] = useState<WorkflowStageResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [formData, setFormData] = useState<StageFormData>({
    stage_name: '',
    stage_order: 0,
    is_active: true,
    color: '#3B82F6',
    description: '',
  });

  /**
   * Fetch workflow stages from backend
   */
  const fetchStages = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await workflowStagesClient.listStages(organizationId);
      setStages(result.stages || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load workflow stages';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    fetchStages();
  }, [fetchStages]);

  /**
   * Open create dialog
   */
  const handleCreate = () => {
    setEditingStage(null);
    const nextOrder = Math.max(...stages.map((s) => s.stage_order), -1) + 1;
    setFormData({
      stage_name: '',
      stage_order: nextOrder,
      is_active: true,
      color: '#3B82F6',
      description: '',
    });
    setDialogOpen(true);
  };

  /**
   * Open edit dialog
   */
  const handleEdit = (stage: WorkflowStageResponse) => {
    setEditingStage(stage);
    setFormData({
      stage_name: stage.stage_name,
      stage_order: stage.stage_order,
      is_active: stage.is_active,
      color: stage.color || '#3B82F6',
      description: stage.description || '',
    });
    setDialogOpen(true);
  };

  /**
   * Open delete confirmation dialog
   */
  const handleDeleteClick = (stage: WorkflowStageResponse) => {
    setStageToDelete(stage);
    setDeleteDialogOpen(true);
  };

  /**
   * Confirm delete
   */
  const handleDeleteConfirm = async () => {
    if (!stageToDelete) return;

    setSubmitting(true);
    try {
      await workflowStagesClient.deleteStage(stageToDelete.id);

      // Optimistic update
      setStages(stages.filter((s) => s.id !== stageToDelete.id));
      setDeleteDialogOpen(false);
      setStageToDelete(null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to delete workflow stage';
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
      if (editingStage) {
        // Update existing stage
        const updateData: WorkflowStageUpdate = {
          stage_name: formData.stage_name,
          stage_order: formData.stage_order,
          is_active: formData.is_active,
          color: formData.color,
          description: formData.description || undefined,
        };

        const updated = await workflowStagesClient.updateStage(editingStage.id, updateData);
        setStages(stages.map((s) => (s.id === updated.id ? updated : s)));
      } else {
        // Create new stage
        const createData: WorkflowStageCreate = {
          organization_id: organizationId,
          stage_name: formData.stage_name,
          stage_order: formData.stage_order,
          is_active: formData.is_active,
          color: formData.color,
          description: formData.description || undefined,
        };

        const created = await workflowStagesClient.createStage(createData);
        setStages([...stages, created]);
      }

      setDialogOpen(false);
      setFormData({
        stage_name: '',
        stage_order: 0,
        is_active: true,
        color: '#3B82F6',
        description: '',
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to save workflow stage';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Validate hex color
   */
  const isValidColor = (color: string) => {
    return /^#[0-9A-F]{6}$/i.test(color);
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
          Loading workflow stages...
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
          <Button color="inherit" onClick={fetchStages} startIcon={<RefreshIcon />}>
            Try Again
          </Button>
        }
      >
        <AlertTitle>Error</AlertTitle>
        {error}
      </Alert>
    );
  }

  const activeCount = stages.filter((s) => s.is_active).length;
  const inactiveCount = stages.length - activeCount;

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Workflow Stage Configuration
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchStages}
            size="small"
          >
            Refresh
          </Button>
        </Box>

        <Typography variant="body2" color="text.secondary" paragraph>
          Customize your organization's hiring workflow stages. Add, edit, or remove stages to match your recruitment process.
        </Typography>

        {/* Summary Statistics */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'primary.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {stages.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Total Stages
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
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
            size="large"
          >
            Add Stage
          </Button>
        </Box>
      </Paper>

      {/* Stages List */}
      {stages.length === 0 ? (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No workflow stages configured
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create your first workflow stage to get started with your hiring pipeline.
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {stages
            .sort((a, b) => a.stage_order - b.stage_order)
            .map((stage) => (
              <Grid item xs={12} md={6} key={stage.id}>
                <Card
                  variant="outlined"
                  sx={{
                    opacity: stage.is_active ? 1 : 0.6,
                    transition: 'opacity 0.2s',
                    borderLeft: `6px solid ${stage.color || '#3B82F6'}`,
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <DragIndicatorIcon color="action" fontSize="small" />
                        <Typography variant="h6" fontWeight={600}>
                          {stage.stage_name}
                        </Typography>
                      </Box>
                      <Stack direction="row" spacing={1}>
                        <IconButton
                          size="small"
                          onClick={() => handleEdit(stage)}
                          color="primary"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteClick(stage)}
                          color="error"
                          disabled={stage.is_default}
                          title={stage.is_default ? 'Cannot delete default stage' : 'Delete stage'}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Stack>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <Chip
                        label={stage.is_active ? 'Active' : 'Inactive'}
                        size="small"
                        color={stage.is_active ? 'success' : 'default'}
                        variant="filled"
                      />
                      {stage.is_default && (
                        <Chip
                          label="Default"
                          size="small"
                          color="info"
                          variant="filled"
                          sx={{ ml: 1 }}
                        />
                      )}
                      <Chip
                        label={`Order: ${stage.stage_order}`}
                        size="small"
                        variant="outlined"
                        sx={{ ml: 1 }}
                      />
                    </Box>

                    {stage.description && (
                      <>
                        <Divider sx={{ my: 1 }} />
                        <Typography variant="body2" color="text.secondary">
                          {stage.description}
                        </Typography>
                      </>
                    )}

                    <Box sx={{ mt: 2 }}>
                      <Box
                        sx={{
                          width: '100%',
                          height: 8,
                          backgroundColor: stage.color || '#3B82F6',
                          borderRadius: 1,
                        }}
                      />
                    </Box>

                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
                      Created: {new Date(stage.created_at).toLocaleDateString()}
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
              {editingStage ? 'Edit Workflow Stage' : 'Add Workflow Stage'}
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
              label="Stage Name"
              fullWidth
              required
              value={formData.stage_name}
              onChange={(e) => setFormData({ ...formData, stage_name: e.target.value })}
              placeholder="e.g., Technical Interview"
              disabled={submitting}
            />

            <TextField
              label="Stage Order"
              fullWidth
              required
              type="number"
              value={formData.stage_order}
              onChange={(e) => setFormData({ ...formData, stage_order: parseInt(e.target.value) || 0 })}
              placeholder="0"
              disabled={submitting}
              helperText="Lower numbers appear first in the workflow"
            />

            <TextField
              label="Color"
              fullWidth
              required
              value={formData.color}
              onChange={(e) => setFormData({ ...formData, color: e.target.value })}
              placeholder="#3B82F6"
              disabled={submitting}
              error={!isValidColor(formData.color)}
              helperText={
                !isValidColor(formData.color)
                  ? 'Invalid hex color format (use #RRGGBB)'
                  : 'Hex color code for stage visualization'
              }
              InputProps={{
                startAdornment: (
                  <Box
                    sx={{
                      width: 24,
                      height: 24,
                      backgroundColor: formData.color,
                      borderRadius: 1,
                      mr: 1,
                      border: '1px solid',
                      borderColor: 'divider',
                    }}
                  />
                ),
              }}
            />

            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe what happens in this stage..."
              disabled={submitting}
            />

            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.is_active.toString()}
                label="Status"
                onChange={(e) => setFormData({ ...formData, is_active: e.target.value === 'true' })}
                disabled={submitting}
              >
                <MenuItem value="true">Active</MenuItem>
                <MenuItem value="false">Inactive</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={submitting || !formData.stage_name || !isValidColor(formData.color)}
            startIcon={submitting ? <CircularProgress size={16} /> : null}
          >
            {submitting ? 'Saving...' : editingStage ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Workflow Stage</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Are you sure you want to delete "{stageToDelete?.stage_name}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This will remove the stage from your workflow. Candidates in this stage will need to be moved to another stage first.
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

export default StageConfig;
