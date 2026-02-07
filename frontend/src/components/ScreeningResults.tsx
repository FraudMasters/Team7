import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Stack,
  Button,
  Chip,
  Tabs,
  Tab,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  ArrowForward as MoveIcon,
  Star as StarIcon,
  Schedule as ReviewIcon,
  Block as RejectIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { apiClient } from '@/api/client';
import type {
  ScreeningResultResponse,
  ScreeningResultListResponse,
  ScreeningTier,
  WorkflowStageResponse,
} from '@/types/api';

/**
 * Tab configuration for tier filtering
 */
interface TierTab {
  value: ScreeningTier | 'all';
  label: string;
  icon: React.ReactNode;
  color: 'success' | 'warning' | 'error' | 'default';
  description: string;
}

/**
 * ScreeningResults Component Props
 */
interface ScreeningResultsProps {
  /** Vacancy ID to filter results (optional) */
  vacancyId?: string;
  /** Available workflow stages for moving candidates */
  stages?: WorkflowStageResponse[];
  /** Callback when viewing candidate details */
  onViewCandidate?: (resumeId: string) => void;
  /** Callback when moving candidate to stage */
  onMoveCandidate?: (resumeId: string, stageId: string) => void;
  /** Disabled state */
  disabled?: boolean;
}

/**
 * ScreeningResults Component
 *
 * Displays screening results with tier-based filtering:
 * - Tab-based filtering by tier (HIGH_PRIORITY, REVIEW, REJECT, All)
 * - Sortable table with candidate information
 * - Color-coded tier indicators
 * - Actions: view details, move to stage
 * - Rejection reasons for rejected candidates
 * - Score visualization with progress bars
 *
 * @example
 * ```tsx
 * <ScreeningResults
 *   vacancyId="vacancy-123"
 *   stages={stages}
 *   onViewCandidate={(id) => navigate(`/candidates/${id}`)}
 *   onMoveCandidate={(id, stageId) => moveToStage(id, stageId)}
 * />
 * ```
 */
const ScreeningResults: React.FC<ScreeningResultsProps> = ({
  vacancyId,
  stages = [],
  onViewCandidate,
  onMoveCandidate,
  disabled = false,
}) => {
  const { t } = useTranslation();

  // State
  const [selectedTab, setSelectedTab] = useState<ScreeningTier | 'all'>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ScreeningResultResponse[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVacancyId, setSelectedVacancyId] = useState<string>(vacancyId || '');
  const [moveDialogOpen, setMoveDialogOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<ScreeningResultResponse | null>(null);
  const [selectedStageId, setSelectedStageId] = useState<string>('');
  const [isMoving, setIsMoving] = useState(false);

  /**
   * Tier tab configuration
   */
  const tierTabs: TierTab[] = [
    {
      value: 'all',
      label: t('screeningResults.tabs.all'),
      icon: <FilterIcon />,
      color: 'default',
      description: t('screeningResults.tabs.allDescription'),
    },
    {
      value: 'HIGH_PRIORITY',
      label: t('screeningResults.tabs.highPriority'),
      icon: <StarIcon />,
      color: 'success',
      description: t('screeningResults.tabs.highPriorityDescription'),
    },
    {
      value: 'REVIEW',
      label: t('screeningResults.tabs.review'),
      icon: <ReviewIcon />,
      color: 'warning',
      description: t('screeningResults.tabs.reviewDescription'),
    },
    {
      value: 'REJECT',
      label: t('screeningResults.tabs.reject'),
      icon: <RejectIcon />,
      color: 'error',
      description: t('screeningResults.tabs.rejectDescription'),
    },
  ];

  /**
   * Fetch screening results from API
   */
  const fetchResults = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params: Record<string, string> = {};

      if (selectedVacancyId) {
        params.vacancy_id = selectedVacancyId;
      }

      if (selectedTab !== 'all') {
        params.tier = selectedTab;
      }

      const response = await apiClient.get<ScreeningResultListResponse>(
        '/api/screening/results',
        { params }
      );

      setResults(response.data.results || []);
      setTotalCount(response.data.total_count || 0);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('screeningResults.errors.loadFailed');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [selectedVacancyId, selectedTab, t]);

  /**
   * Initial data fetch
   */
  React.useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  /**
   * Handle tab change
   */
  const handleTabChange = useCallback(
    (_event: React.SyntheticEvent, newValue: ScreeningTier | 'all') => {
      setSelectedTab(newValue);
    },
    []
  );

  /**
   * Handle refresh
   */
  const handleRefresh = useCallback(() => {
    fetchResults();
  }, [fetchResults]);

  /**
   * Handle search input
   */
  const handleSearchChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
  }, []);

  /**
   * Handle vacancy filter change
   */
  const handleVacancyChange = useCallback((event: SelectChangeEvent<string>) => {
    setSelectedVacancyId(event.target.value);
  }, []);

  /**
   * Handle view candidate
   */
  const handleViewCandidate = useCallback(
    (result: ScreeningResultResponse) => {
      if (onViewCandidate) {
        onViewCandidate(result.resume_id);
      }
    },
    [onViewCandidate]
  );

  /**
   * Handle move candidate open dialog
   */
  const handleMoveDialogOpen = useCallback((result: ScreeningResultResponse) => {
    setSelectedCandidate(result);
    setMoveDialogOpen(true);
  }, []);

  /**
   * Handle move dialog close
   */
  const handleMoveDialogClose = useCallback(() => {
    setMoveDialogOpen(false);
    setSelectedCandidate(null);
    setSelectedStageId('');
  }, []);

  /**
   * Handle move candidate to stage
   */
  const handleMoveCandidate = useCallback(async () => {
    if (!selectedCandidate || !selectedStageId || isMoving) {
      return;
    }

    setIsMoving(true);
    setError(null);

    try {
      if (onMoveCandidate) {
        await onMoveCandidate(selectedCandidate.resume_id, selectedStageId);
      }

      handleMoveDialogClose();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('screeningResults.errors.moveFailed');
      setError(errorMessage);
    } finally {
      setIsMoving(false);
    }
  }, [selectedCandidate, selectedStageId, isMoving, onMoveCandidate, t]);

  /**
   * Get tier color
   */
  const getTierColor = (tier: ScreeningTier): 'success' | 'warning' | 'error' => {
    switch (tier) {
      case 'HIGH_PRIORITY':
        return 'success';
      case 'REVIEW':
        return 'warning';
      case 'REJECT':
        return 'error';
      default:
        return 'default';
    }
  };

  /**
   * Get score color
   */
  const getScoreColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  /**
   * Filter results by search query
   */
  const filteredResults = React.useMemo(() => {
    if (!searchQuery) {
      return results;
    }

    const query = searchQuery.toLowerCase();
    return results.filter(
      (result) =>
        result.candidate_name?.toLowerCase().includes(query) ||
        result.candidate_email?.toLowerCase().includes(query) ||
        result.filename?.toLowerCase().includes(query) ||
        result.vacancy_title?.toLowerCase().includes(query)
    );
  }, [results, searchQuery]);

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
          {t('screeningResults.loading')}
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error && !results.length) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" onClick={handleRefresh} startIcon={<RefreshIcon />}>
            {t('common.retry')}
          </Button>
        }
      >
        <Typography variant="subtitle1" fontWeight={600}>
          {t('screeningResults.errors.loadTitle')}
        </Typography>
        <Typography variant="body2">{error}</Typography>
      </Alert>
    );
  }

  const activeStages = stages.filter((s) => s.is_active);
  const currentTab = tierTabs.find((tab) => tab.value === selectedTab);

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {currentTab?.icon}
            <Typography variant="h6" fontWeight={600} sx={{ ml: 1 }}>
              {t('screeningResults.title')}
            </Typography>
          </Box>
          <Chip
            label={t('screeningResults.count', { count: filteredResults.length })}
            size="medium"
            color="primary"
            variant="outlined"
          />
        </Box>
        <Divider sx={{ mb: 2 }} />

        {/* Description */}
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {currentTab?.description}
        </Typography>

        {/* Filters */}
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              size="small"
              placeholder={t('screeningResults.searchPlaceholder')}
              value={searchQuery}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              disabled={disabled}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth size="small" disabled={disabled}>
              <InputLabel id="vacancy-select-label">
                {t('screeningResults.filterByVacancy')}
              </InputLabel>
              <Select
                labelId="vacancy-select-label"
                value={selectedVacancyId}
                onChange={handleVacancyChange}
                label={t('screeningResults.filterByVacancy')}
              >
                <MenuItem value="">{t('screeningResults.allVacancies')}</MenuItem>
                {/* Vacancies would be loaded from API */}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Tier Tabs */}
      <Paper elevation={1} sx={{ p: 2 }}>
        <Tabs
          value={selectedTab}
          onChange={handleTabChange}
          variant="fullWidth"
          textColor="primary"
          indicatorColor="primary"
        >
          {tierTabs.map((tab) => (
            <Tab
              key={tab.value}
              value={tab.value}
              label={
                <Stack direction="row" spacing={1} alignItems="center">
                  {tab.icon}
                  <Typography variant="body2" fontWeight={600}>
                    {tab.label}
                  </Typography>
                </Stack>
              }
              disabled={disabled}
              sx={{
                color: tab.value !== 'all' ? `${tab.color}.main` : 'inherit',
                '&.Mui-selected': {
                  color: tab.value !== 'all' ? `${tab.color}.main` : 'primary.main',
                  fontWeight: 700,
                },
              }}
            />
          ))}
        </Tabs>
      </Paper>

      {/* Error Alert */}
      {error && results.length > 0 && (
        <Alert severity="error" onClose={() => setError(null)}>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      )}

      {/* Results Table */}
      {filteredResults.length === 0 ? (
        <Alert severity="info">
          <Typography variant="subtitle1" fontWeight={600}>
            {t('screeningResults.noResults')}
          </Typography>
          <Typography variant="body2">
            {searchQuery || selectedVacancyId || selectedTab !== 'all'
              ? t('screeningResults.noResultsFilter')
              : t('screeningResults.noResultsAny')}
          </Typography>
        </Alert>
      ) : (
        <TableContainer component={Paper} elevation={1}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>{t('screeningResults.table.candidate')}</TableCell>
                <TableCell>{t('screeningResults.table.vacancy')}</TableCell>
                <TableCell>{t('screeningResults.table.tier')}</TableCell>
                <TableCell>{t('screeningResults.table.score')}</TableCell>
                <TableCell>{t('screeningResults.table.screenedDate')}</TableCell>
                <TableCell align="right">{t('screeningResults.table.actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredResults.map((result) => (
                <TableRow
                  key={result.id}
                  hover
                  sx={{
                    '&:last-child td, &:last-child th': { border: 0 },
                  }}
                >
                  {/* Candidate Info */}
                  <TableCell component="th" scope="row">
                    <Stack spacing={0.5}>
                      <Typography variant="body2" fontWeight={600}>
                        {result.candidate_name || result.filename || result.resume_id}
                      </Typography>
                      {result.candidate_email && (
                        <Typography variant="caption" color="text.secondary">
                          {result.candidate_email}
                        </Typography>
                      )}
                    </Stack>
                  </TableCell>

                  {/* Vacancy */}
                  <TableCell>
                    <Typography variant="body2">
                      {result.vacancy_title || result.vacancy_id}
                    </Typography>
                  </TableCell>

                  {/* Tier */}
                  <TableCell>
                    <Chip
                      label={t(`screeningResults.tiers.${result.tier.toLowerCase()}`)}
                      size="small"
                      color={getTierColor(result.tier)}
                      variant="filled"
                    />
                  </TableCell>

                  {/* Score */}
                  <TableCell>
                    <Stack spacing={0.5} sx={{ minWidth: 120 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" fontWeight={600} color={getScoreColor(result.score_applied)}>
                          {result.score_applied.toFixed(0)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {t('screeningResults.scoreLabel')}
                        </Typography>
                      </Box>
                      {/* Rejection reasons for REJECT tier */}
                      {result.tier === 'REJECT' && result.rejection_reasons.length > 0 && (
                        <Tooltip
                          title={
                            <Stack spacing={0.5}>
                              <Typography variant="caption" fontWeight={600}>
                                {t('screeningResults.rejectionReasons')}:
                              </Typography>
                              {result.rejection_reasons.map((reason, idx) => (
                                <Typography key={idx} variant="caption">
                                  • {reason}
                                </Typography>
                              ))}
                            </Stack>
                          }
                        >
                          <Typography
                            variant="caption"
                            sx={{
                              color: 'error.main',
                              cursor: 'help',
                              display: 'inline-block',
                              maxWidth: 150,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {result.rejection_reasons[0]}
                            {result.rejection_reasons.length > 1 && ' (+more)'}
                          </Typography>
                        </Tooltip>
                      )}
                    </Stack>
                  </TableCell>

                  {/* Screened Date */}
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(result.screening_timestamp).toLocaleDateString()}
                    </Typography>
                  </TableCell>

                  {/* Actions */}
                  <TableCell align="right">
                    <Stack direction="row" spacing={1} justifyContent="flex-end">
                      {/* View Details */}
                      <Tooltip title={t('screeningResults.actions.view')}>
                        <IconButton
                          size="small"
                          onClick={() => handleViewCandidate(result)}
                          disabled={disabled}
                          color="primary"
                        >
                          <ViewIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>

                      {/* Move to Stage */}
                      {activeStages.length > 0 && result.tier !== 'REJECT' && (
                        <Tooltip title={t('screeningResults.actions.move')}>
                          <IconButton
                            size="small"
                            onClick={() => handleMoveDialogOpen(result)}
                            disabled={disabled}
                            color="success"
                          >
                            <MoveIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Summary Stats */}
      {results.length > 0 && (
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent>
                <Stack spacing={1} alignItems="center">
                  <StarIcon sx={{ fontSize: 40, color: 'success.main' }} />
                  <Typography variant="h4" fontWeight={700} color="success.main">
                    {results.filter((r) => r.tier === 'HIGH_PRIORITY').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('screeningResults.stats.highPriority')}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent>
                <Stack spacing={1} alignItems="center">
                  <ReviewIcon sx={{ fontSize: 40, color: 'warning.main' }} />
                  <Typography variant="h4" fontWeight={700} color="warning.main">
                    {results.filter((r) => r.tier === 'REVIEW').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('screeningResults.stats.review')}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent>
                <Stack spacing={1} alignItems="center">
                  <RejectIcon sx={{ fontSize: 40, color: 'error.main' }} />
                  <Typography variant="h4" fontWeight={700} color="error.main">
                    {results.filter((r) => r.tier === 'REJECT').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('screeningResults.stats.reject')}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Move to Stage Dialog */}
      <Dialog open={moveDialogOpen} onClose={handleMoveDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>{t('screeningResults.moveDialog.title')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('screeningResults.moveDialog.description', {
              candidate: selectedCandidate?.candidate_name || selectedCandidate?.filename,
            })}
          </Typography>

          <FormControl fullWidth size="small" disabled={isMoving}>
            <InputLabel id="stage-select-label">{t('screeningResults.moveDialog.stage')}</InputLabel>
            <Select
              labelId="stage-select-label"
              value={selectedStageId}
              onChange={(e) => setSelectedStageId(e.target.value)}
              label={t('screeningResults.moveDialog.stage')}
            >
              {activeStages.map((stage) => (
                <MenuItem key={stage.id} value={stage.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        bgcolor: stage.color || 'primary.main',
                      }}
                    />
                    {stage.stage_name}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleMoveDialogClose} disabled={isMoving}>
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleMoveCandidate}
            variant="contained"
            disabled={!selectedStageId || isMoving}
            startIcon={isMoving ? <CircularProgress size={16} /> : <MoveIcon />}
          >
            {isMoving ? t('screeningResults.moveDialog.moving') : t('screeningResults.moveDialog.move')}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default ScreeningResults;
