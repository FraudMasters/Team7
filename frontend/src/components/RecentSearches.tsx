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
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import { searchAnalyticsClient } from '@/api/searchAnalytics';
import type { SearchQueryResponse } from '@/types/api';

/**
 * Recent searches component props
 */
interface RecentSearchesProps {
  /** Optional callback when a recent search is selected for execution */
  onSearchSelect?: (search: SearchQueryResponse) => void;
  /** Maximum number of recent searches to display */
  maxItems?: number;
}

/**
 * RecentSearches Component
 *
 * Displays a list of recent search queries to help users quickly access
 * and re-run previous searches. Features include:
 * - List of recent searches ordered by creation time (most recent first)
 * - Click to re-run a search
 * - Display of search query, filters, and timestamp
 * - Number of results returned by each search
 * - Loading and error states
 *
 * @example
 * ```tsx
 * <RecentSearches
 *   onSearchSelect={(search) => console.log('Selected:', search)}
 *   maxItems={10}
 * />
 * ```
 */
const RecentSearches: React.FC<RecentSearchesProps> = ({
  onSearchSelect,
  maxItems = 20,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recentSearches, setRecentSearches] = useState<SearchQueryResponse[]>([]);

  /**
   * Fetch recent searches from backend
   */
  const fetchRecentSearches = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await searchAnalyticsClient.getRecentSearches(maxItems, 0);
      setRecentSearches(result.searches || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load recent searches';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [maxItems]);

  useEffect(() => {
    fetchRecentSearches();
  }, [fetchRecentSearches]);

  /**
   * Handle clicking a recent search to re-run it
   */
  const handleSearchClick = (search: SearchQueryResponse) => {
    if (onSearchSelect) {
      onSearchSelect(search);
    }
  };

  /**
   * Format timestamp for display
   */
  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) {
        return t('recentSearches.justNow', 'Just now');
      }
      if (diffMins < 60) {
        return t('recentSearches.minutesAgo', '{{count}} minutes ago', { count: diffMins });
      }
      if (diffHours < 24) {
        return t('recentSearches.hoursAgo', '{{count}} hours ago', { count: diffHours });
      }
      if (diffDays < 7) {
        return t('recentSearches.daysAgo', '{{count}} days ago', { count: diffDays });
      }

      // Format as locale date for older searches
      return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return timestamp;
    }
  };

  /**
   * Format filter count for display
   */
  const getFilterCount = (filters: Record<string, unknown>): number => {
    if (!filters || typeof filters !== 'object') {
      return 0;
    }
    return Object.keys(filters).filter((key) => {
      const value = filters[key];
      // Count non-empty values
      return (
        value !== null &&
        value !== undefined &&
        value !== '' &&
        !(Array.isArray(value) && value.length === 0)
      );
    }).length;
  };

  /**
   * Truncate long query strings for display
   */
  const truncateQuery = (query: string, maxLength: number = 60): string => {
    if (query.length <= maxLength) {
      return query;
    }
    return `${query.substring(0, maxLength)}...`;
  };

  return (
    <Paper elevation={2} sx={{ p: 3 }}>
      <Stack spacing={2}>
        {/* Header */}
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={1}>
            <Icon name="History" />
            <Typography variant="h6">
              {t('recentSearches.title', 'Recent Searches')}
            </Typography>
          </Stack>
          <Tooltip title={t('recentSearches.refreshTooltip', 'Refresh')}>
            <IconButton onClick={fetchRecentSearches} disabled={loading}>
              <Icon name="Refresh" />
            </IconButton>
          </Tooltip>
        </Stack>

        <Divider />

        {/* Loading State */}
        {loading && (
          <Box display="flex" justifyContent="center" alignItems="center" py={4}>
            <CircularProgress />
          </Box>
        )}

        {/* Error State */}
        {error && !loading && (
          <Alert severity="error">
            <AlertTitle>{t('recentSearches.errorTitle', 'Error')}</AlertTitle>
            {error}
          </Alert>
        )}

        {/* Empty State */}
        {!loading && !error && recentSearches.length === 0 && (
          <Alert severity="info">
            <AlertTitle>{t('recentSearches.emptyTitle', 'No Recent Searches')}</AlertTitle>
            {t(
              'recentSearches.emptyMessage',
              'Your recent search history will appear here. Start searching to see your search history.'
            )}
          </Alert>
        )}

        {/* Recent Searches List */}
        {!loading && !error && recentSearches.length > 0 && (
          <List sx={{ maxHeight: 600, overflow: 'auto' }}>
            {recentSearches.map((search, index) => {
              const filterCount = getFilterCount(search.filters);

              return (
                <React.Fragment key={search.id}>
                  {index > 0 && <Divider />}
                  <ListItem disablePadding>
                    <ListItemButton
                      onClick={() => handleSearchClick(search)}
                      sx={{
                        py: 2,
                        '&:hover': {
                          backgroundColor: 'action.hover',
                        },
                      }}
                    >
                      <ListItemText
                        primary={
                          <Stack direction="row" alignItems="center" spacing={1}>
                            <Icon name="Search" fontSize="small" />
                            <Typography variant="body1" fontWeight="medium">
                              {truncateQuery(search.query || t('recentSearches.emptyQuery', '(empty query)'))}
                            </Typography>
                            {filterCount > 0 && (
                              <Chip
                                label={t('recentSearches.filterCount', '{{count}} filters', {
                                  count: filterCount,
                                })}
                                size="small"
                                color="primary"
                                variant="outlined"
                              />
                            )}
                          </Stack>
                        }
                        secondary={
                          <Stack direction="row" alignItems="center" spacing={2} mt={0.5}>
                            <Typography variant="caption" color="text.secondary">
                              <Icon name="AccessTime" fontSize="inherit" sx={{ mr: 0.5, verticalAlign: 'middle' }} />
                              {formatTimestamp(search.created_at)}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              <Icon name="List" fontSize="inherit" sx={{ mr: 0.5, verticalAlign: 'middle' }} />
                              {t('recentSearches.resultsCount', '{{count}} results', {
                                count: search.results_count,
                              })}
                            </Typography>
                            {search.execution_time_ms && (
                              <Typography variant="caption" color="text.secondary">
                                <Icon name="Speed" fontSize="inherit" sx={{ mr: 0.5, verticalAlign: 'middle' }} />
                                {t('recentSearches.executionTime', '{{time}}ms', {
                                  time: Math.round(search.execution_time_ms),
                                })}
                              </Typography>
                            )}
                          </Stack>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                </React.Fragment>
              );
            })}
          </List>
        )}

        {/* Summary */}
        {!loading && !error && recentSearches.length > 0 && (
          <Typography variant="caption" color="text.secondary" textAlign="center">
            {t('recentSearches.summary', 'Showing {{shown}} of {{total}} recent searches', {
              shown: recentSearches.length,
              total: recentSearches.length,
            })}
          </Typography>
        )}
      </Stack>
    </Paper>
  );
};

export default RecentSearches;
