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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  DragIndicator as DragIcon,
  Save as SaveIcon,
  Workflow as WorkflowIcon,
} from '@mui/icons-material';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { organizationsClient } from '@/api/organizations';
import type { WorkflowStageConfigResponse, WorkflowStageConfigCreate, WorkflowStageConfigUpdate } from '@/types';
import ColorPicker from '@/components/organizations/ColorPicker';

/**
 * Form state interface for workflow stage
 */
interface WorkflowStageFormState {
  stage_name: string;
  stage_order: number;
  is_active: boolean;
  color: string;
  description: string;
}

/**
 * Form validation errors interface
 */
interface FormErrors {
  stage_name?: string;
  stage_order?: string;
  color?: string;
  description?: string;
}

/**
 * Default form state
 */
const DEFAULT_FORM_STATE: WorkflowStageFormState = {
  stage_name: '',
  stage_order: 0,
  is_active: true,
  color: '#3B82F6',
  description: '',
};

/**
 * Workflow Stages Settings Page
 *
 * Provides an interface for managing organization workflow stages:
 * - View all workflow stages
 * - Add new workflow stages
 * - Edit existing workflow stages
 * - Delete workflow stages
 * - Reorder stages via drag and drop
 * - Customize stage colors
 *
 * Accessible at /workflow-stages
 *
 * @example
 * ```tsx
 * // Route configuration in App.tsx
 * <Route path="/workflow-stages" element={<WorkflowStagesSettings />} />
 * ```
 */
const WorkflowStagesSettings: React.FC = () => {
  const { t } = useTranslation();

  // Organization ID (in production, from auth context)
  const [organizationId] = useState<string>('org123');

  // Data state
  const [stages, setStages] = useState<WorkflowStageConfigResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [editingStageId, setEditingStageId] = useState<string | null>(null);
  const [formData, setFormData] = useState<WorkflowStageFormState>(DEFAULT_FORM_STATE);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [saving, setSaving] = useState(false);
  const [deletingStageId, setDeletingStageId] = useState<string | null>(null);

  /**
   * Load workflow stages
   */
  const loadStages = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await organizationsClient.listWorkflowStageConfigs(organizationId, true);
      // Sort stages by order
      const sortedStages = response.stages.sort((a, b) => a.stage_order - b.stage_order);
      setStages(sortedStages);
    } catch (err) {
      const errorMessage = err instanceof Error
        ? err.message
        : t('workflowStages.errors.loadFailed') || 'Failed to load workflow stages';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [organizationId, t]);

  /**
   * Validate form fields
   */
  const validateForm = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    // Stage name validation
    if (!formData.stage_name.trim()) {
      newErrors.stage_name = t('validation.required', { field: t('workflowStages.stageName') }) || 'Stage name is required';
    } else if (formData.stage_name.trim().length < 2) {
      newErrors.stage_name = t('validation.minLength', { field: t('workflowStages.stageName'), min: 2 }) || 'Stage name must be at least 2 characters';
    } else if (formData.stage_name.trim().length > 100) {
      newErrors.stage_name = t('validation.maxLength', { field: t('workflowStages.stageName'), max: 100 }) || 'Stage name must not exceed 100 characters';
    }

    // Stage order validation
    if (formData.stage_order < 0) {
      newErrors.stage_order = t('workflowStages.errors.invalidOrder') || 'Stage order must be a positive number';
    }

    // Color validation
    const hexColorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
    if (!hexColorRegex.test(formData.color)) {
      newErrors.color = t('workflowStages.errors.invalidColor') || 'Invalid hex color format (e.g., #3B82F6)';
    }

    // Description validation (optional but with max length)
    if (formData.description && formData.description.trim().length > 500) {
      newErrors.description = t('validation.maxLength', { field: t('workflowStages.description'), max: 500 }) || 'Description must not exceed 500 characters';
    }

    setFormErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData, t]);

  /**
   * Handle dialog open for create
   */
  const handleCreateClick = useCallback(() => {
    setDialogMode('create');
    setEditingStageId(null);
    setFormData({
      ...DEFAULT_FORM_STATE,
      stage_order: stages.length > 0 ? Math.max(...stages.map(s => s.stage_order)) + 1 : 0,
    });
    setFormErrors({});
    setDialogOpen(true);
  }, [stages.length]);

  /**
   * Handle dialog open for edit
   */
  const handleEditClick = useCallback((stage: WorkflowStageConfigResponse) => {
    setDialogMode('edit');
    setEditingStageId(stage.id);
    setFormData({
      stage_name: stage.stage_name,
      stage_order: stage.stage_order,
      is_active: stage.is_active,
      color: stage.color || '#3B82F6',
      description: stage.description || '',
    });
    setFormErrors({});
    setDialogOpen(true);
  }, []);

  /**
   * Handle dialog close
   */
  const handleDialogClose = useCallback(() => {
    setDialogOpen(false);
    setFormData(DEFAULT_FORM_STATE);
    setFormErrors({});
    setEditingStageId(null);
  }, []);

  /**
   * Handle form field change
   */
  const handleFieldChange = useCallback((field: keyof WorkflowStageFormState, value: string | boolean) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear error for this field when user starts typing
    if (formErrors[field as keyof FormErrors]) {
      setFormErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }

    // Clear success message when user makes changes
    if (successMessage) {
      setSuccessMessage(null);
    }
  }, [formErrors, successMessage]);

  /**
   * Handle form submit (create or update)
   */
  const handleSubmit = useCallback(async () => {
    if (!validateForm()) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      if (dialogMode === 'create') {
        const createData: WorkflowStageConfigCreate = {
          organization_id: organizationId,
          stage_name: formData.stage_name.trim(),
          stage_order: formData.stage_order,
          is_active: formData.is_active,
          color: formData.color,
          description: formData.description.trim() || undefined,
        };

        await organizationsClient.createWorkflowStageConfig(createData);
        setSuccessMessage(t('workflowStages.createSuccess') || 'Workflow stage created successfully');
      } else if (dialogMode === 'edit' && editingStageId) {
        const updateData: WorkflowStageConfigUpdate = {
          stage_name: formData.stage_name.trim(),
          stage_order: formData.stage_order,
          is_active: formData.is_active,
          color: formData.color,
          description: formData.description.trim() || undefined,
        };

        await organizationsClient.updateWorkflowStageConfig(editingStageId, updateData);
        setSuccessMessage(t('workflowStages.updateSuccess') || 'Workflow stage updated successfully');
      }

      handleDialogClose();
      await loadStages();
    } catch (err) {
      const errorMessage = err instanceof Error
        ? err.message
        : t('workflowStages.errors.saveFailed') || 'Failed to save workflow stage';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  }, [dialogMode, editingStageId, formData, organizationId, validateForm, t, handleDialogClose, loadStages]);

  /**
   * Handle delete stage
   */
  const handleDeleteClick = useCallback(async (stageId: string) => {
    if (!confirm(t('workflowStages.confirmDelete') || 'Are you sure you want to delete this workflow stage?')) {
      return;
    }

    setDeletingStageId(stageId);
    setError(null);

    try {
      await organizationsClient.deleteWorkflowStageConfig(stageId);
      setSuccessMessage(t('workflowStages.deleteSuccess') || 'Workflow stage deleted successfully');
      await loadStages();
    } catch (err) {
      const errorMessage = err instanceof Error
        ? err.message
        : t('workflowStages.errors.deleteFailed') || 'Failed to delete workflow stage';
      setError(errorMessage);
    } finally {
      setDeletingStageId(null);
    }
  }, [t, loadStages]);

  /**
   * Handle drag end (reorder stages)
   */
  const handleDragEnd = useCallback(async (result: DropResult) => {
    const { destination, source } = result;

    // Dropped outside the list or in the same position
    if (!destination || (destination.droppableId === source.droppableId && destination.index === source.index)) {
      return;
    }

    // Reorder stages locally
    const newStages = Array.from(stages);
    const [reorderedStage] = newStages.splice(source.index, 1);
    newStages.splice(destination.index, 0, reorderedStage);

    // Update stage orders
    const updatedStages = newStages.map((stage, index) => ({
      ...stage,
      stage_order: index,
    }));

    setStages(updatedStages);

    // Save new order to backend
    try {
      const stageOrders = updatedStages.map(stage => ({
        id: stage.id,
        stage_order: stage.stage_order,
      }));

      await organizationsClient.reorderWorkflowStages({ stage_orders: stageOrders });
      setSuccessMessage(t('workflowStages.reorderSuccess') || 'Workflow stages reordered successfully');
    } catch (err) {
      const errorMessage = err instanceof Error
        ? err.message
        : t('workflowStages.errors.reorderFailed') || 'Failed to reorder workflow stages';
      setError(errorMessage);
      // Revert changes on error
      await loadStages();
    }
  }, [stages, t, loadStages]);

  // Load stages on mount
  useEffect(() => {
    loadStages();
  }, [loadStages]);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {t('workflowStages.title') || 'Workflow Stages'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('workflowStages.subtitle') || 'Customize your hiring workflow stages and their order'}
        </Typography>
      </Box>

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Error Alert */}
      {error && !loading && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Alert */}
      {successMessage && !loading && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {/* Main Content */}
      {!loading && (
        <Paper sx={{ p: 4 }}>
          <Stack spacing={3}>
            {/* Header with Add Button */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h6" fontWeight={600}>
                  {t('workflowStages.stagesList') || 'Your Workflow Stages'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('workflowStages.stagesCount', { count: stages.length }) ||
                    `${stages.length} stage${stages.length !== 1 ? 's' : ''} configured`}
                </Typography>
              </Box>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleCreateClick}
                size="large"
              >
                {t('workflowStages.addStage') || 'Add Stage'}
              </Button>
            </Box>

            <Divider />

            {/* Stages List with Drag and Drop */}
            {stages.length === 0 ? (
              <Box sx={{ py: 8, textAlign: 'center' }}>
                <WorkflowIcon sx={{ fontSize: 64, color: 'action.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  {t('workflowStages.emptyState.title') || 'No workflow stages configured'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('workflowStages.emptyState.message') || 'Click "Add Stage" to create your first workflow stage'}
                </Typography>
              </Box>
            ) : (
              <DragDropContext onDragEnd={handleDragEnd}>
                <Droppable droppableId="workflow-stages">
                  {(provided) => (
                    <List
                      {...provided.droppableProps}
                      ref={provided.innerRef}
                      sx={{ bgcolor: 'background.default', borderRadius: 2 }}
                    >
                      {stages.map((stage, index) => (
                        <Draggable
                          key={stage.id}
                          draggableId={stage.id}
                          index={index}
                          isDragDisabled={!!deletingStageId}
                        >
                          {(provided, snapshot) => (
                            <ListItem
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              sx={{
                                bgcolor: snapshot.isDragging ? 'action.hover' : 'background.paper',
                                borderRadius: 2,
                                mb: 1,
                                border: '1px solid',
                                borderColor: 'divider',
                                boxShadow: snapshot.isDragging ? 4 : 1,
                                '&:hover': {
                                  borderColor: 'primary.main',
                                },
                              }}
                            >
                              <Box
                                {...provided.dragHandleProps}
                                sx={{ mr: 2, cursor: 'grab' }}
                              >
                                <DragIcon color="action" />
                              </Box>

                              {/* Stage Color Indicator */}
                              <Box
                                sx={{
                                  width: 40,
                                  height: 40,
                                  borderRadius: 2,
                                  bgcolor: stage.color || 'primary.main',
                                  mr: 2,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  color: 'white',
                                  fontWeight: 600,
                                }}
                              >
                                {index + 1}
                              </Box>

                              {/* Stage Details */}
                              <ListItemText
                                primary={
                                  <Typography variant="subtitle1" fontWeight={600}>
                                    {stage.stage_name}
                                  </Typography>
                                }
                                secondary={
                                  <Stack direction="row" spacing={1} alignItems="center">
                                    <Typography variant="body2" color="text.secondary">
                                      {stage.description || t('workflowStages.noDescription') || 'No description'}
                                    </Typography>
                                    {!stage.is_active && (
                                      <Typography variant="caption" color="error">
                                        ({t('common.inactive') || 'Inactive'})
                                      </Typography>
                                    )}
                                  </Stack>
                                }
                              />

                              {/* Actions */}
                              <ListItemSecondaryAction>
                                <Stack direction="row" spacing={1}>
                                  <IconButton
                                    onClick={() => handleEditClick(stage)}
                                    disabled={!!deletingStageId}
                                    color="primary"
                                  >
                                    <EditIcon />
                                  </IconButton>
                                  <IconButton
                                    onClick={() => handleDeleteClick(stage.id)}
                                    disabled={deletingStageId === stage.id}
                                    color="error"
                                  >
                                    {deletingStageId === stage.id ? (
                                      <CircularProgress size={24} />
                                    ) : (
                                      <DeleteIcon />
                                    )}
                                  </IconButton>
                                </Stack>
                              </ListItemSecondaryAction>
                            </ListItem>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </List>
                  )}
                </Droppable>
              </DragDropContext>
            )}
          </Stack>
        </Paper>
      )}

      {/* Create/Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={handleDialogClose}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {dialogMode === 'create'
            ? (t('workflowStages.dialog.createTitle') || 'Create New Workflow Stage')
            : (t('workflowStages.dialog.editTitle') || 'Edit Workflow Stage')
          }
        </DialogTitle>
        <DialogContent dividers>
          <Stack spacing={3}>
            {/* Stage Name */}
            <Box>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                {t('workflowStages.stageName') || 'Stage Name'}
                <span style={{ color: 'red' }}> *</span>
              </Typography>
              <TextField
                fullWidth
                value={formData.stage_name}
                onChange={(e) => handleFieldChange('stage_name', e.target.value)}
                error={!!formErrors.stage_name}
                helperText={formErrors.stage_name || (t('workflowStages.dialog.nameHelper') || 'e.g., Technical Interview')}
                placeholder={t('workflowStages.dialog.namePlaceholder') || 'Technical Interview'}
                disabled={saving}
                inputProps={{ maxLength: 100 }}
              />
            </Box>

            {/* Stage Order */}
            <Box>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                {t('workflowStages.stageOrder') || 'Stage Order'}
                <span style={{ color: 'red' }}> *</span>
              </Typography>
              <TextField
                fullWidth
                type="number"
                value={formData.stage_order}
                onChange={(e) => handleFieldChange('stage_order', parseInt(e.target.value) || 0)}
                error={!!formErrors.stage_order}
                helperText={formErrors.stage_order || (t('workflowStages.dialog.orderHelper') || 'Lower numbers appear first')}
                disabled={saving}
                inputProps={{ min: 0, step: 1 }}
              />
            </Box>

            {/* Color Picker */}
            <ColorPicker
              id="stage-color"
              label={t('workflowStages.color') || 'Stage Color'}
              value={formData.color}
              onChange={(color) => handleFieldChange('color', color)}
              helperText={t('workflowStages.dialog.colorHelper') || 'Color used in UI to identify this stage'}
              defaultColor="#3B82F6"
              disabled={saving}
            />

            {/* Description */}
            <Box>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                {t('workflowStages.description') || 'Description'}
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={3}
                value={formData.description}
                onChange={(e) => handleFieldChange('description', e.target.value)}
                error={!!formErrors.description}
                helperText={formErrors.description || (t('workflowStages.dialog.descriptionHelper') || 'Optional description of this stage')}
                placeholder={t('workflowStages.dialog.descriptionPlaceholder') || 'Describe what happens in this stage'}
                disabled={saving}
                inputProps={{ maxLength: 500 }}
              />
            </Box>

            {/* Active Status */}
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => handleFieldChange('is_active', e.target.checked)}
                  disabled={saving}
                  color="primary"
                />
              }
              label={
                <Box>
                  <Typography variant="subtitle2" fontWeight={600}>
                    {t('workflowStages.active') || 'Active'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {t('workflowStages.dialog.activeHelper') || 'Inactive stages are hidden from the workflow'}
                  </Typography>
                </Box>
              }
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={handleDialogClose}
            disabled={saving}
          >
            {t('common.cancel') || 'Cancel'}
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
            disabled={saving}
          >
            {saving
              ? (t('common.saving') || 'Saving...')
              : (dialogMode === 'create'
                  ? (t('common.create') || 'Create')
                  : (t('common.save') || 'Save')
                )
            }
          </Button>
        </DialogActions>
      </Dialog>

      {/* Info Box */}
      {!loading && (
        <Box sx={{ mt: 3 }}>
          <Paper sx={{ p: 3, bgcolor: 'info.main', bgcolorOpacity: 0.1 }}>
            <Stack direction="row" spacing={2} alignItems="flex-start">
              <WorkflowIcon color="info" sx={{ mt: 0.5 }} />
              <Box>
                <Typography variant="subtitle2" fontWeight={600} color="info.dark">
                  {t('workflowStages.info.title') || 'Workflow Stages'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('workflowStages.info.message') ||
                    'Customize your hiring pipeline by creating workflow stages that match your process. Drag and drop to reorder stages. Each stage can have a custom color for visual identification.'
                  }
                </Typography>
              </Box>
            </Stack>
          </Paper>
        </Box>
      )}
    </Container>
  );
};

export default WorkflowStagesSettings;
