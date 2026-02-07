import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Checkbox,
  Chip,
  Stack,
  Divider,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Collapse,
  Grid,
  Card,
  CardContent,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  RadioGroup,
  FormControlLabel,
  Radio,
  TextField,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as RadioButtonUncheckedIcon,
  Warning as WarningIcon,
  Delete as DeleteIcon,
  PowerSettingsNew as PowerSettingsNewIcon,
  ContentCopy as ContentCopyIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { apiClient } from '@/api/client';

/**
 * Individual vacancy interface for bulk actions
 */
interface BulkVacancy {
  /** Unique identifier for the vacancy */
  id: string;
  /** Vacancy title */
  title: string;
  /** Vacancy description */
  description?: string;
  /** Required skills */
  required_skills?: string[];
  /** Minimum experience in months */
  min_experience_months?: number;
  /** Industry */
  industry?: string;
  /** Work format */
  work_format?: string;
  /** Location */
  location?: string;
  /** Is vacancy active */
  is_active?: boolean;
  /** Organization ID */
  organization_id?: string;
}

/**
 * Bulk operation result interface
 */
interface BulkOperationResult {
  id: string;
  success: boolean;
  error?: string;
  message?: string;
}

/**
 * Organization interface for assignment
 */
interface Organization {
  /** Unique identifier for the organization */
  id: string;
  /** Organization name */
  name: string;
  /** Organization industry */
  industry?: string;
  /** Organization location */
  location?: string;
}

/**
 * BulkVacancyActions Component Props
 */
interface BulkVacancyActionsProps {
  /** Array of available vacancies for bulk operations */
  vacancies: BulkVacancy[];
  /** Array of available organizations for assignment */
  organizations: Organization[];
  /** Callback when bulk delete operation completes */
  onBulkDeleteComplete?: (results: BulkOperationResult[]) => void;
  /** Callback when bulk status update completes */
  onBulkStatusUpdateComplete?: (results: BulkOperationResult[]) => void;
  /** Callback when bulk duplicate completes */
  onBulkDuplicateComplete?: (results: BulkOperationResult[]) => void;
  /** Callback when bulk assign completes */
  onBulkAssignComplete?: (results: BulkOperationResult[]) => void;
  /** Callback when selection changes */
  onSelectionChange?: (selectedVacancies: string[]) => void;
  /** Disabled state */
  disabled?: boolean;
  /** Custom height for the vacancy list container */
  containerHeight?: number | string;
}

/**
 * BulkVacancyActions Component
 *
 * Provides a multi-select interface for bulk vacancy operations:
 * - Select multiple vacancies from a list
 * - Execute bulk operations (delete, update status, duplicate, assign)
 * - Visual feedback for selection and operation status
 * - Detailed error handling and success notifications
 *
 * @example
 * ```tsx
 * <BulkVacancyActions
 *   vacancies={vacancies}
 *   onBulkDeleteComplete={(results) => console.log('Results:', results)}
 * />
 * ```
 */
const BulkVacancyActions: React.FC<BulkVacancyActionsProps> = ({
  vacancies,
  organizations,
  onBulkDeleteComplete,
  onBulkStatusUpdateComplete,
  onBulkDuplicateComplete,
  onBulkAssignComplete,
  onSelectionChange,
  disabled = false,
  containerHeight = 400,
}) => {
  const { t } = useTranslation();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [operationResults, setOperationResults] = useState<BulkOperationResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Delete state
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Status update state
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);
  const [targetStatus, setTargetStatus] = useState<'active' | 'inactive'>('active');

  // Duplicate state
  const [isDuplicating, setIsDuplicating] = useState(false);
  const [duplicateDialogOpen, setDuplicateDialogOpen] = useState(false);

  // Assign state
  const [isAssigning, setIsAssigning] = useState(false);
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [selectedOrganizationId, setSelectedOrganizationId] = useState<string>('');

  /**
   * Handle selection change
   */
  const handleSelectionChange = useCallback(
    (newSelectedIds: string[]) => {
      setSelectedIds(newSelectedIds);
      onSelectionChange?.(newSelectedIds);
      // Clear previous results when selection changes
      setOperationResults(null);
      setError(null);
    },
    [onSelectionChange]
  );

  /**
   * Toggle vacancy selection
   */
  const handleToggleVacancy = useCallback(
    (id: string) => {
      if (disabled || isProcessing) {
        return;
      }

      const isSelected = selectedIds.includes(id);
      const newSelectedIds = isSelected
        ? selectedIds.filter((vacancyId) => vacancyId !== id)
        : [...selectedIds, id];

      handleSelectionChange(newSelectedIds);
    },
    [selectedIds, disabled, isProcessing, handleSelectionChange]
  );

  /**
   * Select all vacancies
   */
  const handleSelectAll = useCallback(() => {
    if (disabled || isProcessing) {
      return;
    }

    const newSelectedIds = vacancies.map((v) => v.id);
    handleSelectionChange(newSelectedIds);
  }, [vacancies, disabled, isProcessing, handleSelectionChange]);

  /**
   * Clear all selections
   */
  const handleClearAll = useCallback(() => {
    if (disabled || isProcessing) {
      return;
    }

    handleSelectionChange([]);
  }, [disabled, isProcessing, handleSelectionChange]);

  /**
   * Execute bulk delete operation
   */
  const handleBulkDelete = useCallback(async () => {
    if (selectedIds.length === 0 || isDeleting) {
      return;
    }

    setIsDeleting(true);
    setError(null);
    setOperationResults(null);

    try {
      const response = await apiClient.post<{ results: BulkOperationResult[] }>('/api/vacancies/bulk-delete', {
        vacancy_ids: selectedIds,
      });

      const results = response.data.results || [];
      setOperationResults(results);

      // Count successes and failures
      const successCount = results.filter((r) => r.success).length;
      const failCount = results.filter((r) => !r.success).length;

      if (failCount > 0) {
        setError(
          t('bulkVacancyActions.deletePartialSuccess', { success: successCount, failed: failCount })
        );
      }

      // Notify parent component
      onBulkDeleteComplete?.(results);

      // Clear selection on full success
      if (failCount === 0) {
        handleSelectionChange([]);
      }

      // Close dialog
      setDeleteDialogOpen(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('bulkVacancyActions.deleteError');
      setError(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  }, [selectedIds, isDeleting, onBulkDeleteComplete, handleSelectionChange, t]);

  /**
   * Execute bulk status update operation
   */
  const handleBulkStatusUpdate = useCallback(async () => {
    if (selectedIds.length === 0 || isUpdatingStatus) {
      return;
    }

    setIsUpdatingStatus(true);
    setError(null);
    setOperationResults(null);

    try {
      const response = await apiClient.post<{ results: BulkOperationResult[] }>('/api/vacancies/bulk-update-status', {
        vacancy_ids: selectedIds,
        is_active: targetStatus === 'active',
      });

      const results = response.data.results || [];
      setOperationResults(results);

      // Count successes and failures
      const successCount = results.filter((r) => r.success).length;
      const failCount = results.filter((r) => !r.success).length;

      if (failCount > 0) {
        setError(
          t('bulkVacancyActions.statusPartialSuccess', { success: successCount, failed: failCount })
        );
      }

      // Notify parent component
      onBulkStatusUpdateComplete?.(results);

      // Clear selection on full success
      if (failCount === 0) {
        handleSelectionChange([]);
      }

      // Close dialog
      setStatusDialogOpen(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('bulkVacancyActions.statusError');
      setError(errorMessage);
    } finally {
      setIsUpdatingStatus(false);
    }
  }, [selectedIds, isUpdatingStatus, targetStatus, onBulkStatusUpdateComplete, handleSelectionChange, t]);

  /**
   * Execute bulk duplicate operation
   */
  const handleBulkDuplicate = useCallback(async () => {
    if (selectedIds.length === 0 || isDuplicating) {
      return;
    }

    setIsDuplicating(true);
    setError(null);
    setOperationResults(null);

    try {
      const response = await apiClient.post<{ results: BulkOperationResult[] }>('/api/vacancies/bulk-duplicate', {
        vacancy_ids: selectedIds,
      });

      const results = response.data.results || [];
      setOperationResults(results);

      // Count successes and failures
      const successCount = results.filter((r) => r.success).length;
      const failCount = results.filter((r) => !r.success).length;

      if (failCount > 0) {
        setError(
          t('bulkVacancyActions.duplicatePartialSuccess', { success: successCount, failed: failCount })
        );
      }

      // Notify parent component
      onBulkDuplicateComplete?.(results);

      // Clear selection on full success
      if (failCount === 0) {
        handleSelectionChange([]);
      }

      // Close dialog
      setDuplicateDialogOpen(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('bulkVacancyActions.duplicateError');
      setError(errorMessage);
    } finally {
      setIsDuplicating(false);
    }
  }, [selectedIds, isDuplicating, onBulkDuplicateComplete, handleSelectionChange, t]);

  /**
   * Execute bulk assign operation
   */
  const handleBulkAssign = useCallback(async () => {
    if (selectedIds.length === 0 || !selectedOrganizationId || isAssigning) {
      return;
    }

    setIsAssigning(true);
    setError(null);
    setOperationResults(null);

    try {
      const response = await apiClient.post<{ results: BulkOperationResult[] }>('/api/vacancies/bulk-assign', {
        vacancy_ids: selectedIds,
        organization_id: selectedOrganizationId,
      });

      const results = response.data.results || [];
      setOperationResults(results);

      // Count successes and failures
      const successCount = results.filter((r) => r.success).length;
      const failCount = results.filter((r) => !r.success).length;

      if (failCount > 0) {
        setError(
          t('bulkVacancyActions.assignPartialSuccess', { success: successCount, failed: failCount })
        );
      }

      // Notify parent component
      onBulkAssignComplete?.(results);

      // Clear selection on full success
      if (failCount === 0) {
        handleSelectionChange([]);
      }

      // Close dialog
      setAssignDialogOpen(false);
      setSelectedOrganizationId('');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('bulkVacancyActions.assignError');
      setError(errorMessage);
    } finally {
      setIsAssigning(false);
    }
  }, [selectedIds, selectedOrganizationId, isAssigning, onBulkAssignComplete, handleSelectionChange, t]);

  /**
   * Handle organization selection change
   */
  const handleOrganizationChange = useCallback((event: SelectChangeEvent<string>) => {
    setSelectedOrganizationId(event.target.value as string);
    setError(null);
  }, []);

  const hasSelection = selectedIds.length > 0;

  // Helper function for pluralization
  const pluralize = (count: number) => (count === 1 ? '' : 's');

  return (
    <Stack spacing={2}>
      {/* Header Section */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CheckCircleIcon sx={{ mr: 1, fontSize: 24, color: 'primary.main' }} />
            <Typography variant="h6" fontWeight={600}>
              {t('bulkVacancyActions.title')}
            </Typography>
          </Box>
          <Chip
            label={t('bulkVacancyActions.selected', { count: selectedIds.length })}
            size="medium"
            color={hasSelection ? 'primary' : 'default'}
            variant={hasSelection ? 'filled' : 'outlined'}
          />
        </Box>
        <Divider sx={{ mb: 2 }} />

        {/* Selection Info */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {t('bulkVacancyActions.selectCount')}
          </Typography>
        </Box>

        {/* Selection Actions */}
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <Button
            variant="outlined"
            onClick={handleSelectAll}
            disabled={disabled || isProcessing || vacancies.length === 0}
            size="small"
          >
            {t('bulkVacancyActions.selectAll')} ({vacancies.length})
          </Button>
          <Button
            variant="outlined"
            onClick={handleClearAll}
            disabled={disabled || isProcessing || !hasSelection}
            size="small"
            color="secondary"
          >
            {t('bulkVacancyActions.clearSelection')}
          </Button>

          {/* Bulk Action Buttons */}
          <Button
            variant="outlined"
            onClick={() => setDeleteDialogOpen(true)}
            disabled={disabled || isProcessing || isDeleting || !hasSelection}
            size="small"
            startIcon={<DeleteIcon />}
            color="error"
          >
            {t('bulkVacancyActions.delete')}
          </Button>
          <Button
            variant="outlined"
            onClick={() => setStatusDialogOpen(true)}
            disabled={disabled || isProcessing || isUpdatingStatus || !hasSelection}
            size="small"
            startIcon={<PowerSettingsNewIcon />}
            color="warning"
          >
            {t('bulkVacancyActions.updateStatus')}
          </Button>
          <Button
            variant="outlined"
            onClick={() => setDuplicateDialogOpen(true)}
            disabled={disabled || isProcessing || isDuplicating || !hasSelection}
            size="small"
            startIcon={<ContentCopyIcon />}
            color="info"
          >
            {t('bulkVacancyActions.duplicate')}
          </Button>
          <Button
            variant="outlined"
            onClick={() => setAssignDialogOpen(true)}
            disabled={disabled || isProcessing || isAssigning || !hasSelection}
            size="small"
            startIcon={<BusinessIcon />}
            color="success"
          >
            {t('bulkVacancyActions.assign')}
          </Button>
        </Stack>
      </Paper>

      {/* Error Alert */}
      <Collapse in={!!error}>
        <Alert severity="error" sx={{ mt: 2 }}>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Collapse>

      {/* Success Alert */}
      <Collapse in={!!operationResults && operationResults.every((r) => r.success)}>
        <Alert severity="success" sx={{ mt: 2 }}>
          <Typography variant="body2">
            {t('bulkVacancyActions.operationSuccess', {
              count: selectedIds.length,
              plural: pluralize(selectedIds.length),
            })}
          </Typography>
        </Alert>
      </Collapse>

      {/* Vacancies List */}
      <Paper elevation={1} sx={{ p: 3 }}>
        {vacancies.length === 0 ? (
          <Alert severity="info">
            <Typography variant="body2">{t('bulkVacancyActions.noVacancies')}</Typography>
          </Alert>
        ) : (
          <Box
            sx={{
              maxHeight: typeof containerHeight === 'number' ? `${containerHeight}px` : containerHeight,
              overflowY: 'auto',
              pr: 1,
            }}
          >
            <Grid container spacing={2}>
              {vacancies.map((vacancy) => {
                const isSelected = selectedIds.includes(vacancy.id);
                const result = operationResults?.find((r) => r.id === vacancy.id);

                return (
                  <Grid item xs={12} sm={6} md={4} key={vacancy.id}>
                    <Card
                      onClick={() => handleToggleVacancy(vacancy.id)}
                      sx={{
                        cursor: disabled || isProcessing ? 'not-allowed' : 'pointer',
                        border: isSelected ? 2 : 1,
                        borderColor: result?.error
                          ? 'error.main'
                          : isSelected
                            ? 'primary.main'
                            : 'divider',
                        bgcolor: result?.error
                          ? 'error.50'
                          : isSelected
                            ? 'primary.50'
                            : 'background.paper',
                        transition: 'all 0.2s ease-in-out',
                        '&:hover': !disabled && !isProcessing
                          ? {
                              boxShadow: 3,
                              transform: 'translateY(-2px)',
                            }
                          : undefined,
                      }}
                    >
                      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                        <Stack spacing={1} direction="row" alignItems="flex-start">
                          {/* Checkbox */}
                          <Checkbox
                            checked={isSelected}
                            disabled={disabled || isProcessing}
                            size="small"
                            sx={{ p: 0.5, mt: 0.5 }}
                            icon={<RadioButtonUncheckedIcon />}
                            checkedIcon={<CheckCircleIcon />}
                          />

                          {/* Vacancy Info */}
                          <Box sx={{ flex: 1, minWidth: 0 }}>
                            {/* Vacancy Title */}
                            <Typography
                              variant="subtitle2"
                              fontWeight={isSelected ? 600 : 400}
                              sx={{
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {vacancy.title}
                            </Typography>

                            {/* Industry */}
                            {vacancy.industry && (
                              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                                {vacancy.industry}
                              </Typography>
                            )}

                            {/* Location */}
                            {vacancy.location && (
                              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                                {vacancy.location}
                              </Typography>
                            )}

                            {/* Status Badge */}
                            <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                              <Chip
                                label={vacancy.is_active !== false ? t('bulkVacancyActions.active') : t('bulkVacancyActions.inactive')}
                                size="small"
                                color={vacancy.is_active !== false ? 'success' : 'default'}
                                variant="outlined"
                                sx={{ height: 20, fontSize: '0.7rem', '& .MuiChip-label': { px: 1 } }}
                              />
                            </Box>

                            {/* Error/Success Indicator */}
                            {result && (
                              <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                                {result.error ? (
                                  <Tooltip title={result.error}>
                                    <WarningIcon sx={{ fontSize: 16, color: 'error.main' }} />
                                  </Tooltip>
                                ) : result.success ? (
                                  <CheckCircleIcon sx={{ fontSize: 16, color: 'success.main' }} />
                                ) : null}
                              </Box>
                            )}
                          </Box>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          </Box>
        )}
      </Paper>

      {/* Info Alert */}
      {hasSelection && (
        <Alert severity="info" variant="outlined">
          <Typography variant="body2">
            <strong>{t('bulkVacancyActions.tip')}</strong> {t('bulkVacancyActions.selectActionTip')}
          </Typography>
        </Alert>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('bulkVacancyActions.deleteDialog.title')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('bulkVacancyActions.deleteDialog.description', { count: selectedIds.length })}
          </Typography>
          <Alert severity="warning">
            <Typography variant="body2">
              {t('bulkVacancyActions.deleteDialog.warning')}
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={isDeleting}>
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleBulkDelete}
            variant="contained"
            color="error"
            disabled={isDeleting}
            startIcon={isDeleting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {isDeleting ? t('bulkVacancyActions.deleteDialog.deleting') : t('bulkVacancyActions.deleteDialog.confirm')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Status Update Confirmation Dialog */}
      <Dialog open={statusDialogOpen} onClose={() => setStatusDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('bulkVacancyActions.statusDialog.title')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('bulkVacancyActions.statusDialog.description', { count: selectedIds.length })}
          </Typography>

          <FormControl component="fieldset">
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              {t('bulkVacancyActions.statusDialog.selectStatus')}
            </Typography>
            <RadioGroup
              value={targetStatus}
              onChange={(e) => setTargetStatus(e.target.value as 'active' | 'inactive')}
            >
              <FormControlLabel
                value="active"
                control={<Radio />}
                label={t('bulkVacancyActions.statusDialog.active')}
                disabled={isUpdatingStatus}
              />
              <FormControlLabel
                value="inactive"
                control={<Radio />}
                label={t('bulkVacancyActions.statusDialog.inactive')}
                disabled={isUpdatingStatus}
              />
            </RadioGroup>
          </FormControl>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              {t('bulkVacancyActions.statusDialog.info')}
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStatusDialogOpen(false)} disabled={isUpdatingStatus}>
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleBulkStatusUpdate}
            variant="contained"
            color="warning"
            disabled={isUpdatingStatus}
            startIcon={isUpdatingStatus ? <CircularProgress size={16} /> : <PowerSettingsNewIcon />}
          >
            {isUpdatingStatus ? t('bulkVacancyActions.statusDialog.updating') : t('bulkVacancyActions.statusDialog.confirm')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Duplicate Confirmation Dialog */}
      <Dialog open={duplicateDialogOpen} onClose={() => setDuplicateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('bulkVacancyActions.duplicateDialog.title')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('bulkVacancyActions.duplicateDialog.description', { count: selectedIds.length })}
          </Typography>
          <Alert severity="info">
            <Typography variant="body2">
              {t('bulkVacancyActions.duplicateDialog.info')}
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDuplicateDialogOpen(false)} disabled={isDuplicating}>
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleBulkDuplicate}
            variant="contained"
            color="info"
            disabled={isDuplicating}
            startIcon={isDuplicating ? <CircularProgress size={16} /> : <ContentCopyIcon />}
          >
            {isDuplicating ? t('bulkVacancyActions.duplicateDialog.duplicating') : t('bulkVacancyActions.duplicateDialog.confirm')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Assign to Organization Dialog */}
      <Dialog open={assignDialogOpen} onClose={() => setAssignDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('bulkVacancyActions.assignDialog.title')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('bulkVacancyActions.assignDialog.description', { count: selectedIds.length })}
          </Typography>

          <FormControl fullWidth size="small" disabled={isAssigning}>
            <InputLabel id="bulk-organization-select-label">{t('bulkVacancyActions.assignDialog.selectOrganization')}</InputLabel>
            <Select
              labelId="bulk-organization-select-label"
              value={selectedOrganizationId}
              onChange={handleOrganizationChange}
              label={t('bulkVacancyActions.assignDialog.selectOrganization')}
            >
              {organizations.map((org) => (
                <MenuItem key={org.id} value={org.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BusinessIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                    <Box>
                      <Typography variant="body2">{org.name}</Typography>
                      {org.industry && (
                        <Typography variant="caption" color="text.secondary">
                          {org.industry}
                        </Typography>
                      )}
                    </Box>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              {t('bulkVacancyActions.assignDialog.info')}
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAssignDialogOpen(false)} disabled={isAssigning}>
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleBulkAssign}
            variant="contained"
            color="success"
            disabled={!selectedOrganizationId || isAssigning}
            startIcon={isAssigning ? <CircularProgress size={16} /> : <BusinessIcon />}
          >
            {isAssigning ? t('bulkVacancyActions.assignDialog.assigning') : t('bulkVacancyActions.assignDialog.confirm')}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default BulkVacancyActions;
