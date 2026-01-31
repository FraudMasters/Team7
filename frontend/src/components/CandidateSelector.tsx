import React, { useState, useCallback, useEffect } from 'react';
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
  FormControlLabel,
  Grid,
  Card,
  CardContent,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as RadioButtonUncheckedIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

/**
 * Individual candidate interface
 */
interface Candidate {
  /** Unique identifier for the candidate (resume_id) */
  resume_id: string;
  /** Candidate's name or identifier */
  name?: string;
  /** Match percentage for the vacancy */
  match_percentage?: number;
  /** Number of matched skills */
  matched_skills_count?: number;
  /** Number of required skills */
  total_skills_count?: number;
  /** Overall match status */
  overall_match?: boolean;
}

/**
 * CandidateSelector Component Props
 */
interface CandidateSelectorProps {
  /** Array of available candidates for selection */
  candidates: Candidate[];
  /** Callback when selected candidates change */
  onSelectionChange?: (selectedCandidates: string[]) => void;
  /** Initially selected candidate IDs */
  initialSelectedIds?: string[];
  /** Maximum number of candidates allowed */
  maxCandidates?: number;
  /** Minimum number of candidates required */
  minCandidates?: number;
  /** Disabled state */
  disabled?: boolean;
  /** Show match percentage in candidate cards */
  showMatchPercentage?: boolean;
  /** Show skills count in candidate cards */
  showSkillsCount?: boolean;
  /** Custom height for the candidate list container */
  containerHeight?: number | string;
}

/**
 * CandidateSelector Component
 *
 * Provides a multi-select interface for choosing candidates to compare:
 * - Select 2-5 candidates from a list
 * - Visual feedback for selected candidates
 * - Match percentage and skills count display
 * - Validation for min/max selection limits
 * - Checkbox or card-based selection
 *
 * @example
 * ```tsx
 * <CandidateSelector
 *   candidates={candidates}
 *   onSelectionChange={(ids) => console.log('Selected:', ids)}
 *   maxCandidates={5}
 *   minCandidates={2}
 * />
 * ```
 */
const CandidateSelector: React.FC<CandidateSelectorProps> = ({
  candidates,
  onSelectionChange,
  initialSelectedIds = [],
  maxCandidates = 5,
  minCandidates = 2,
  disabled = false,
  showMatchPercentage = true,
  showSkillsCount = true,
  containerHeight = 500,
}) => {
  const [selectedIds, setSelectedIds] = useState<string[]>(initialSelectedIds);

  /**
   * Handle selection change
   */
  const handleSelectionChange = useCallback(
    (newSelectedIds: string[]) => {
      setSelectedIds(newSelectedIds);
      onSelectionChange?.(newSelectedIds);
    },
    [onSelectionChange]
  );

  /**
   * Toggle candidate selection
   */
  const handleToggleCandidate = useCallback(
    (resumeId: string) => {
      if (disabled) {
        return;
      }

      const isSelected = selectedIds.includes(resumeId);

      if (isSelected) {
        // Remove from selection
        const newSelectedIds = selectedIds.filter((id) => id !== resumeId);
        handleSelectionChange(newSelectedIds);
      } else {
        // Add to selection if not at max limit
        if (selectedIds.length < maxCandidates) {
          const newSelectedIds = [...selectedIds, resumeId];
          handleSelectionChange(newSelectedIds);
        }
      }
    },
    [selectedIds, maxCandidates, disabled, handleSelectionChange]
  );

  /**
   * Select all candidates (up to max limit)
   */
  const handleSelectAll = useCallback(() => {
    if (disabled) {
      return;
    }

    const countToSelect = Math.min(candidates.length, maxCandidates);
    const newSelectedIds = candidates.slice(0, countToSelect).map((c) => c.resume_id);
    handleSelectionChange(newSelectedIds);
  }, [candidates, maxCandidates, disabled, handleSelectionChange]);

  /**
   * Clear all selections
   */
  const handleClearAll = useCallback(() => {
    if (disabled) {
      return;
    }

    handleSelectionChange([]);
  }, [disabled, handleSelectionChange]);

  // Update state when initial selected IDs change
  useEffect(() => {
    setSelectedIds(initialSelectedIds);
  }, [initialSelectedIds]);

  const isValidRange = selectedIds.length >= minCandidates && selectedIds.length <= maxCandidates;
  const isMinMet = selectedIds.length >= minCandidates;
  const isMaxReached = selectedIds.length >= maxCandidates;
  const canSelectMore = selectedIds.length < maxCandidates;

  // Sort candidates by match percentage if available
  const sortedCandidates = React.useMemo(() => {
    return [...candidates].sort((a, b) => {
      if (a.match_percentage !== undefined && b.match_percentage !== undefined) {
        return b.match_percentage - a.match_percentage;
      }
      return 0;
    });
  }, [candidates]);

  return (
    <Stack spacing={2}>
      {/* Header Section */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CheckCircleIcon sx={{ mr: 1, fontSize: 24, color: 'primary.main' }} />
            <Typography variant="h6" fontWeight={600}>
              Select Candidates to Compare
            </Typography>
          </Box>
          <Chip
            label={`${selectedIds.length} / ${maxCandidates} selected`}
            size="medium"
            color={isMinMet ? 'primary' : 'default'}
            variant={isMinMet ? 'filled' : 'outlined'}
          />
        </Box>
        <Divider sx={{ mb: 2 }} />

        {/* Selection Count Info */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Select <strong>{minCandidates}-{maxCandidates} candidates</strong> for side-by-side comparison
          </Typography>
          {!isValidRange && (
            <Alert severity={selectedIds.length < minCandidates ? 'warning' : 'info'} sx={{ mt: 1 }}>
              {selectedIds.length < minCandidates
                ? `At least ${minCandidates} candidate${minCandidates > 1 ? 's are' : ' is'} required for comparison`
                : `Maximum ${maxCandidates} candidates can be compared at once`}
            </Alert>
          )}
        </Box>

        {/* Action Buttons */}
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            onClick={handleSelectAll}
            disabled={disabled || candidates.length === 0 || selectedIds.length === maxCandidates}
            size="small"
          >
            Select {maxCandidates} Best
          </Button>
          <Button
            variant="outlined"
            onClick={handleClearAll}
            disabled={disabled || selectedIds.length === 0}
            size="small"
            color="secondary"
          >
            Clear All
          </Button>
        </Stack>
      </Paper>

      {/* Candidates List */}
      <Paper elevation={1} sx={{ p: 3 }}>
        {candidates.length === 0 ? (
          <Alert severity="info">
            <Typography variant="body2">
              No candidates available for this vacancy. Upload resumes to see candidates here.
            </Typography>
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
                const cannotSelect = !isSelected && !canSelectMore;

                return (
                  <Grid item xs={12} sm={6} md={4} key={candidate.resume_id}>
                    <Card
                      onClick={() => handleToggleCandidate(candidate.resume_id)}
                      sx={{
                        cursor: disabled ? 'not-allowed' : 'pointer',
                        border: isSelected ? 2 : 1,
                        borderColor: isSelected ? 'primary.main' : 'divider',
                        bgcolor: isSelected ? 'primary.50' : 'background.paper',
                        opacity: cannotSelect ? 0.6 : 1,
                        transition: 'all 0.2s ease-in-out',
                        '&:hover': !disabled
                          ? {
                              boxShadow: cannotSelect ? undefined : 4,
                              transform: cannotSelect ? undefined : 'translateY(-2px)',
                            }
                          : undefined,
                      }}
                    >
                      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                        <Stack spacing={1} direction="row" alignItems="flex-start">
                          {/* Checkbox */}
                          <Checkbox
                            checked={isSelected}
                            disabled={disabled || cannotSelect}
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

                            {/* Match Percentage */}
                            {showMatchPercentage && candidate.match_percentage !== undefined && (
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
                                {candidate.overall_match !== undefined && (
                                  <Tooltip title={candidate.overall_match ? 'Meets requirements' : 'Partially meets requirements'}>
                                    <Box sx={{ ml: 0.5, display: 'flex' }}>
                                      {candidate.overall_match ? (
                                        <CheckCircleIcon sx={{ fontSize: 16, color: 'success.main' }} />
                                      ) : (
                                        <InfoIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                                      )}
                                    </Box>
                                  </Tooltip>
                                )}
                              </Box>
                            )}

                            {/* Skills Count */}
                            {showSkillsCount &&
                              candidate.matched_skills_count !== undefined &&
                              candidate.total_skills_count !== undefined && (
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                                  {candidate.matched_skills_count} / {candidate.total_skills_count} skills matched
                                </Typography>
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
      {!isValidRange && (
        <Alert severity="info" variant="outlined">
          <Typography variant="body2">
            <strong>Tip:</strong> Select {minCandidates}-{maxCandidates} candidates to enable comparison. Candidates are
            sorted by match percentage.
          </Typography>
        </Alert>
      )}

      {/* Selection Limit Warning */}
      {isMaxReached && (
        <Alert severity="info" variant="outlined">
          <Typography variant="body2">
            Maximum selection limit reached. Deselect a candidate to choose another one.
          </Typography>
        </Alert>
      )}
    </Stack>
  );
};

export default CandidateSelector;
