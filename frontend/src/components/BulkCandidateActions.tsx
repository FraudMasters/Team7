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
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as RadioButtonUncheckedIcon,
  ArrowForward as ArrowForwardIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { apiClient } from '@/api/client';
import type { WorkflowStageResponse } from '@/types/api';

/**
 * Individual candidate interface for bulk actions
 */
interface BulkCandidate {
  /** Unique identifier for the candidate (resume_id) */
  resume_id: string;
  /** Candidate's name or identifier */
  name?: string;
  /** Current stage name */
  current_stage?: string;
  /** Match percentage for the vacancy */
  match_percentage?: number;
}

/**
 * Bulk move result interface
 */
interface BulkMoveResult {
  resume_id: string;
  success: boolean;
  error?: string;
  new_stage?: string;
}

/**
 * BulkCandidateActions Component Props
 */
interface BulkCandidateActionsProps {
  /** Array of available candidates for bulk operations */
  candidates: BulkCandidate[];
  /** Available workflow stages to move candidates to */
  stages: WorkflowStageResponse[];
  /** Callback when bulk move operation completes */
  onBulkMoveComplete?: (results: BulkMoveResult[]) => void;
  /** Callback when selection changes */
  onSelectionChange?: (selectedCandidates: string[]) => void;
  /** Vacancy ID for the move operation */
  vacancyId?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Custom height for the candidate list container */
  containerHeight?: number | string;
}

/**
 * BulkCandidateActions Component
 *
 * Provides a multi-select interface for bulk candidate operations:
 * - Select multiple candidates from a list
 * - Choose target stage from dropdown
 * - Execute bulk stage move operation
 * - Visual feedback for selection and operation status
 * - Detailed error handling and success notifications
 *
 * @example
 * ```tsx
 * <BulkCandidateActions
 *   candidates={candidates}
 *   stages={stages}
 *   onBulkMoveComplete={(results) => console.log('Results:', results)}
 *   vacancyId="vacancy-123"
 * />
 * ```
 */
const BulkCandidateActions: React.FC<BulkCandidateActionsProps> = ({
  candidates,
  stages,
  onBulkMoveComplete,
  onSelectionChange,
  vacancyId,
  disabled = false,
  containerHeight = 400,
}) => {
  const { t } = useTranslation();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectedStageId, setSelectedStageId] = useState<string>('');
  const [isMoving, setIsMoving] = useState(false);
  const [moveResults, setMoveResults] = useState<BulkMoveResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  /**
   * Handle selection change
   */
  const handleSelectionChange = useCallback(
    (newSelectedIds: string[]) => {
      setSelectedIds(newSelectedIds);
      onSelectionChange?.(newSelectedIds);
      // Clear previous results when selection changes
      setMoveResults(null);
      setError(null);
    },
    [onSelectionChange]
  );

  /**
   * Toggle candidate selection
   */
  const handleToggleCandidate = useCallback(
    (resumeId: string) => {
      if (disabled || isMoving) {
        return;
      }

      const isSelected = selectedIds.includes(resumeId);
      const newSelectedIds = isSelected
        ? selectedIds.filter((id) => id !== resumeId)
        : [...selectedIds, resumeId];

      handleSelectionChange(newSelectedIds);
    },
    [selectedIds, disabled, isMoving, handleSelectionChange]
  );

  /**
   * Select all candidates
   */
  const handleSelectAll = useCallback(() => {
    if (disabled || isMoving) {
      return;
    }

    const newSelectedIds = candidates.map((c) => c.resume_id);
    handleSelectionChange(newSelectedIds);
  }, [candidates, disabled, isMoving, handleSelectionChange]);

  /**
   * Clear all selections
   */
  const handleClearAll = useCallback(() => {
    if (disabled || isMoving) {
      return;
    }

    handleSelectionChange([]);
  }, [disabled, isMoving, handleSelectionChange]);

  /**
   * Handle stage selection change
   */
  const handleStageChange = useCallback((event: React.ChangeEvent<{ value: unknown }>) => {
    setSelectedStageId(event.target.value as string);
    setError(null);
  }, []);

  /**
   * Execute bulk move operation
   */
  const handleBulkMove = useCallback(async () => {
    if (selectedIds.length === 0 || !selectedStageId || isMoving) {
      return;
    }

    setIsMoving(true);
    setError(null);
    setMoveResults(null);

    try {
      const response = await apiClient.post('/api/candidates/bulk-move', {
        resume_ids: selectedIds,
        stage_id: selectedStageId,
        vacancy_id: vacancyId,
      });

      const results = response.data.results || [];
      setMoveResults(results);

      // Count successes and failures
      const successCount = results.filter((r: BulkMoveResult) => r.success).length;
      const failCount = results.filter((r: BulkMoveResult) => !r.success).length;

      if (failCount > 0) {
        setError(
          t('bulkActions.movePartialSuccess', { success: successCount, failed: failCount })
        );
      }

      // Notify parent component
      onBulkMoveComplete?.(results);

      // Clear selection on full success
      if (failCount === 0) {
        handleSelectionChange([]);
        setSelectedStageId('');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('bulkActions.moveError');
      setError(errorMessage);
    } finally {
      setIsMoving(false);
    }
  }, [selectedIds, selectedStageId, vacancyId, isMoving, onBulkMoveComplete, handleSelectionChange, t]);

  const hasSelection = selectedIds.length > 0;
  const canMove = hasSelection && selectedStageId && !isMoving;
  const activeStages = stages.filter((s) => s.is_active);

  // Sort stages by order
  const sortedStages = React.useMemo(() => {
    return [...activeStages].sort((a, b) => a.stage_order - b.stage_order);
  }, [activeStages]);

  // Sort candidates by match percentage if available
  const sortedCandidates = React.useMemo(() => {
    return [...candidates].sort((a, b) => {
      if (a.match_percentage !== undefined && b.match_percentage !== undefined) {
        return b.match_percentage - a.match_percentage;
      }
      return 0;
    });
  }, [candidates]);

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
              {t('bulkActions.title')}
            </Typography>
          </Box>
          <Chip
            label={t('bulkActions.selected', { count: selectedIds.length })}
            size="medium"
            color={hasSelection ? 'primary' : 'default'}
            variant={hasSelection ? 'filled' : 'outlined'}
          />
        </Box>
        <Divider sx={{ mb: 2 }} />

        {/* Selection Info */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {t('bulkActions.selectCount')}
          </Typography>
        </Box>

        {/* Selection Actions */}
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <Button
            variant="outlined"
            onClick={handleSelectAll}
            disabled={disabled || isMoving || candidates.length === 0}
            size="small"
          >
            {t('bulkActions.selectAll')} ({candidates.length})
          </Button>
          <Button
            variant="outlined"
            onClick={handleClearAll}
            disabled={disabled || isMoving || !hasSelection}
            size="small"
            color="secondary"
          >
            {t('bulkActions.clearSelection')}
          </Button>
        </Stack>
      </Paper>

      {/* Stage Selection */}
      {hasSelection && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            {t('bulkActions.moveCandidates', {
              count: selectedIds.length,
              plural: pluralize(selectedIds.length),
            })}
          </Typography>

          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small" disabled={isMoving}>
                <InputLabel id="bulk-stage-select-label">{t('bulkActions.targetStage')}</InputLabel>
                <Select
                  labelId="bulk-stage-select-label"
                  value={selectedStageId}
                  onChange={handleStageChange}
                  label={t('bulkActions.targetStage')}
                >
                  {sortedStages.map((stage) => (
                    <MenuItem key={stage.id} value={stage.id}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box
                          sx={{
                            width: 12,
                            height: 12,
                            borderRadius: '50%',
                            bgcolor: stage.color || '#primary.main',
                          }}
                        />
                        {stage.stage_name}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Button
                variant="contained"
                onClick={handleBulkMove}
                disabled={!canMove}
                fullWidth
                startIcon={isMoving ? <CircularProgress size={16} /> : <ArrowForwardIcon />}
                sx={{ height: 40 }}
              >
                {isMoving ? t('bulkActions.moving') : t('bulkActions.moveToStage')}
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Error Alert */}
      <Collapse in={!!error}>
        <Alert severity={error?.includes(t('bulkActions.movePartialSuccess', { success: 0, failed: 0 }).split(' ')[0]) ? 'warning' : 'error'} sx={{ mt: 2 }}>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Collapse>

      {/* Success Alert */}
      <Collapse in={!!moveResults && moveResults.every((r) => r.success)}>
        <Alert severity="success" sx={{ mt: 2 }}>
          <Typography variant="body2">
            {t('bulkActions.moveSuccess', {
              count: selectedIds.length,
              plural: pluralize(selectedIds.length),
            })}
          </Typography>
        </Alert>
      </Collapse>

      {/* Candidates List */}
      <Paper elevation={1} sx={{ p: 3 }}>
        {candidates.length === 0 ? (
          <Alert severity="info">
            <Typography variant="body2">{t('bulkActions.noCandidates')}</Typography>
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
              {sortedCandidates.map((candidate) => {
                const isSelected = selectedIds.includes(candidate.resume_id);
                const result = moveResults?.find((r) => r.resume_id === candidate.resume_id);

                return (
                  <Grid item xs={12} sm={6} md={4} key={candidate.resume_id}>
                    <Card
                      onClick={() => handleToggleCandidate(candidate.resume_id)}
                      sx={{
                        cursor: disabled || isMoving ? 'not-allowed' : 'pointer',
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
                        '&:hover': !disabled && !isMoving
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
                            disabled={disabled || isMoving}
                            size="small"
                            sx={{ p: 0.5, mt: 0.5 }}
                            icon={<RadioButtonUncheckedIcon />}
                            checkedIcon={<CheckCircleIcon />}
                          />

                          {/* Candidate Info */}
                          <Box sx={{ flex: 1, minWidth: 0 }}>
                            {/* Candidate Name/ID */}
                            <Typography
                              variant="subtitle2"
                              fontWeight={isSelected ? 600 : 400}
                              sx={{
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {candidate.name || candidate.resume_id}
                            </Typography>

                            {/* Current Stage */}
                            {candidate.current_stage && (
                              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                                {t('bulkActions.current', { stage: candidate.current_stage })}
                              </Typography>
                            )}

                            {/* Match Percentage */}
                            {candidate.match_percentage !== undefined && (
                              <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                                <Chip
                                  label={`${candidate.match_percentage.toFixed(0)}%`}
                                  size="small"
                                  color={
                                    candidate.match_percentage >= 80
                                      ? 'success'
                                      : candidate.match_percentage >= 60
                                        ? 'primary'
                                        : 'default'
                                  }
                                  variant="outlined"
                                  sx={{ height: 20, fontSize: '0.7rem', '& .MuiChip-label': { px: 1 } }}
                                />
                              </Box>
                            )}

                            {/* Error/Success Indicator */}
                            {result && (
                              <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                                {result.error ? (
                                  <Tooltip title={result.error}>
                                    <WarningIcon sx={{ fontSize: 16, color: 'error.main' }} />
                                  </Tooltip>
                                ) : result.new_stage ? (
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
      {hasSelection && !selectedStageId && (
        <Alert severity="info" variant="outlined">
          <Typography variant="body2">
            <strong>{t('bulkActions.tip')}</strong> {t('bulkActions.selectStageTip')}
          </Typography>
        </Alert>
      )}
    </Stack>
  );
};

export default BulkCandidateActions;
