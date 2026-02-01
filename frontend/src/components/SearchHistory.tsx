import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Button,
  Alert,
  AlertTitle,
  Stack,
  Card,
  CardContent,
  Chip,
  Divider,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Delete as DeleteIcon,
  History as HistoryIcon,
  Close as CloseIcon,
  Schedule as ScheduleIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { searchHistoryClient } from '@/api/searchHistory';
import type {
  SearchHistoryItem,
  SearchHistoryResponse,
  ApiError,
} from '@/types/api';

/**
 * SearchHistory Component Props
 */
interface SearchHistoryProps {
  /** Callback when a history item is clicked to repeat the search */
  onRepeatSearch?: (query: string | null, filters: Record<string, unknown>) => void;
  /** Maximum number of history items to display (default: 20) */
  limit?: number;
  /** Optional recruiter ID to filter history */
  recruiterId?: string;
}

/**
 * SearchHistory Component
 *
 * Displays recent search history with functionality to:
 * - View recent searches with query and filters
 * - Click to repeat a previous search
 * - Clear all search history
 *
 * Search history is displayed in a vertical list with color-coded
 * search type indicators and detailed information for each search.
 *
 * @example
 * ```tsx
 * <SearchHistory />
 *
 * <SearchHistory
 *   onRepeatSearch={(query, filters) => {
 *     // Handle repeat search
 *   }}
 *   limit={20}
 * />
 * ```
 */
const SearchHistory: React.FC<SearchHistoryProps> = ({
  onRepeatSearch,
  limit = 20,
  recruiterId,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [historyItems, setHistoryItems] = useState<SearchHistoryItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [clearDialogOpen, setClearDialogOpen] = useState(false);
  const [clearing, setClearing] = useState(false);

  /**
   * Fetch search history data from backend
   */
  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response: SearchHistoryResponse = await searchHistoryClient.listSearchHistory(
        0,
        limit,
        recruiterId
      );

      // History items are already sorted by created_at descending from API
      setHistoryItems(response.history);
      setTotalCount(response.total);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load search history. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [limit, recruiterId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  /**
   * Format timestamp for display
   */
  const formatTimestamp = useCallback((timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  }, []);

  /**
   * Get search summary text
   */
  const getSearchSummary = useCallback((item: SearchHistoryItem) => {
    if (item.query) {
      // Truncate query if too long
      const query = item.query.length > 50 ? `${item.query.substring(0, 50)}...` : item.query;
      return `"${query}"`;
    }

    // If no query, show filters summary
    const filters = item.filters || {};
    const filterParts: string[] = [];

    if (filters.skills) {
      const skills = Array.isArray(filters.skills) ? filters.skills : [filters.skills];
      filterParts.push(`Skills: ${skills.slice(0, 3).join(', ')}${skills.length > 3 ? '...' : ''}`);
    }

    if (filters.min_experience_years || filters.max_experience_years) {
      const min = filters.min_experience_years || 0;
      const max = filters.max_experience_years || '+';
      filterParts.push(`Exp: ${min}-${max}y`);
    }

    if (filters.location) {
      filterParts.push(`Location: ${filters.location}`);
    }

    if (filters.min_match_score || filters.max_match_score) {
      const min = filters.min_match_score || 0;
      const max = filters.max_match_score || 100;
      filterParts.push(`Match: ${min}-${max}%`);
    }

    if (filterParts.length === 0) {
      return 'All candidates';
    }

    return filterParts.join(' • ');
  }, []);

  /**
   * Get filter count
   */
  const getFilterCount = useCallback((filters: Record<string, unknown>) => {
    let count = 0;
    if (filters.skills) count++;
    if (filters.min_experience_years || filters.max_experience_years) count++;
    if (filters.location) count++;
    if (filters.education_level) count++;
    if (filters.languages) count++;
    if (filters.min_match_score || filters.max_match_score) count++;
    if (filters.date_from || filters.date_to) count++;
    if (filters.vacancy_id) count++;
    if (filters.stage_id) count++;
    return count;
  }, []);

  /**
   * Handle clicking on a history item to repeat the search
   */
  const handleRepeatSearch = useCallback((item: SearchHistoryItem) => {
    if (onRepeatSearch) {
      onRepeatSearch(item.query, item.filters || {});
    }
  }, [onRepeatSearch]);

  /**
   * Handle clearing all search history
   */
  const handleClearHistory = useCallback(async () => {
    try {
      setClearing(true);
      await searchHistoryClient.clearSearchHistory();
      setHistoryItems([]);
      setTotalCount(0);
      setClearDialogOpen(false);
    } catch (err) {
      const apiError = err as ApiError;
      // If 404, the endpoint doesn't exist yet - just show a message
      if (apiError.status === 404) {
        setError('Clear history feature is not yet implemented in the backend.');
      } else {
        setError(apiError.detail || 'Failed to clear search history. Please try again.');
      }
    } finally {
      setClearing(false);
    }
  }, []);

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
          {t('searchHistory.loading') || 'Loading Search History'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {t('searchHistory.loadingHint') || 'Please wait while we fetch your recent searches'}
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
          <Button color="inherit" onClick={fetchHistory} startIcon={<RefreshIcon />}>
            {t('searchHistory.retry') || 'Retry'}
          </Button>
        }
      >
        <AlertTitle>{t('searchHistory.errorTitle') || 'Error Loading History'}</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (historyItems.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>{t('searchHistory.noHistoryTitle') || 'No Search History'}</AlertTitle>
        {t('searchHistory.noHistory') || 'You haven\'t performed any searches yet. Start searching to see your history here.'}
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HistoryIcon fontSize="large" color="primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                {t('searchHistory.title') || 'Search History'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('searchHistory.subtitle', { count: totalCount }) || `${totalCount} recent ${totalCount === 1 ? 'search' : 'searches'}`}
              </Typography>
            </Box>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchHistory}
              size="small"
            >
              {t('searchHistory.refresh') || 'Refresh'}
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => setClearDialogOpen(true)}
              size="small"
            >
              {t('searchHistory.clear') || 'Clear'}
            </Button>
          </Stack>
        </Box>
      </Paper>

      {/* Search History List */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Stack spacing={2}>
          {historyItems.map((item, index) => {
            const filterCount = getFilterCount(item.filters || {});
            const searchSummary = getSearchSummary(item);

            return (
              <Box key={item.id}>
                <Card
                  variant="outlined"
                  sx={{
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    cursor: onRepeatSearch ? 'pointer' : 'default',
                    '&:hover': onRepeatSearch ? {
                      transform: 'translateX(4px)',
                      boxShadow: 2,
                    } : {},
                  }}
                  onClick={() => onRepeatSearch && handleRepeatSearch(item)}
                >
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    {/* Search Header */}
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        mb: 1,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                        <Box
                          sx={{
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            bgcolor: 'primary.main',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                          }}
                        >
                          <SearchIcon fontSize="small" />
                        </Box>
                        <Typography variant="body1" fontWeight={500} sx={{ flex: 1 }}>
                          {searchSummary}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {item.results_count !== null && (
                          <Chip
                            label={`${item.results_count} results`}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        )}
                        {filterCount > 0 && (
                          <Chip
                            icon={<FilterIcon fontSize="small" />}
                            label={`${filterCount} filter${filterCount > 1 ? 's' : ''}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>

                    {/* Search Details */}
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <ScheduleIcon fontSize="small" color="action" sx={{ fontSize: '1rem' }} />
                        <Typography variant="caption" color="text.secondary">
                          {formatTimestamp(item.created_at)}
                        </Typography>
                        {item.execution_time_seconds !== null && (
                          <>
                            <Divider orientation="vertical" flexItem sx={{ mx: 1, height: 12 }} />
                            <Typography variant="caption" color="text.secondary">
                              {item.execution_time_seconds.toFixed(2)}s
                            </Typography>
                          </>
                        )}
                      </Box>
                      {onRepeatSearch && (
                        <Tooltip title="Repeat this search">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRepeatSearch(item);
                            }}
                          >
                            <RefreshIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </CardContent>
                </Card>
                {index < historyItems.length - 1 && (
                  <Divider sx={{ mt: 2, borderColor: 'divider' }} />
                )}
              </Box>
            );
          })}
        </Stack>
      </Paper>

      {/* Clear History Confirmation Dialog */}
      <Dialog
        open={clearDialogOpen}
        onClose={() => !clearing && setClearDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DeleteIcon color="error" />
            {t('searchHistory.clearDialogTitle') || 'Clear Search History'}
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            {t('searchHistory.clearDialogMessage') ||
              'Are you sure you want to clear all search history? This action cannot be undone.'}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setClearDialogOpen(false)}
            disabled={clearing}
            startIcon={<CloseIcon />}
          >
            {t('searchHistory.cancel') || 'Cancel'}
          </Button>
          <Button
            onClick={handleClearHistory}
            disabled={clearing}
            color="error"
            variant="contained"
            startIcon={<DeleteIcon />}
          >
            {clearing
              ? (t('searchHistory.clearing') || 'Clearing...')
              : (t('searchHistory.confirmClear') || 'Clear History')
            }
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default SearchHistory;
