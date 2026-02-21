import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Stack,
  Card,
  CardContent,
  Grid,
  Chip,
  Skeleton,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  Speed as SpeedIcon,
  HourglassEmpty as HourglassEmptyIcon,
  People as PeopleIcon,
  TrendingUp as TrendingUpIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Visibility as VisibilityIcon,
  SkipNext as SkipNextIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import type { QueueMetricsResponse, QueueCountsResponse } from '@/hooks/useCandidateQueue';

/**
 * QueueMetrics Component Props
 */
export interface QueueMetricsProps {
  /** Queue metrics data including wait times, throughput, and counts */
  metrics: QueueMetricsResponse | undefined;
  /** Whether data is currently loading */
  isLoading?: boolean;
  /** Optional title for the metrics panel */
  title?: string;
  /** Optional description subtitle */
  description?: string;
  /** Whether to show detailed metrics */
  showDetails?: boolean;
}

/**
 * Format hours into a human-readable string
 */
function formatWaitTime(hours: number | null): string {
  if (hours === null) return '--';

  if (hours < 1) {
    const minutes = Math.round(hours * 60);
    return `${minutes}m`;
  }

  if (hours < 24) {
    const wholeHours = Math.floor(hours);
    const minutes = Math.round((hours - wholeHours) * 60);
    return minutes > 0 ? `${wholeHours}h ${minutes}m` : `${wholeHours}h`;
  }

  const days = Math.floor(hours / 24);
  const remainingHours = Math.round(hours % 24);
  return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days}d`;
}

/**
 * Format a timestamp into relative time
 */
function formatRelativeTime(timestamp: string | null): string {
  if (!timestamp) return '--';

  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);

  return formatWaitTime(diffHours);
}

/**
 * Get color based on wait time severity
 */
function getWaitTimeColor(hours: number | null): 'success' | 'info' | 'warning' | 'error' {
  if (hours === null) return 'info';
  if (hours <= 4) return 'success';
  if (hours <= 24) return 'info';
  if (hours <= 72) return 'warning';
  return 'error';
}

/**
 * Get tooltip text for wait time
 */
function getWaitTimeTooltip(hours: number | null): string {
  if (hours === null) return 'No pending items to calculate wait time';
  if (hours <= 4) return 'Excellent - candidates are being processed quickly';
  if (hours <= 24) return 'Good - within typical processing time';
  if (hours <= 72) return 'Warning - some candidates waiting longer than expected';
  return 'Critical - candidates waiting too long';
}

/**
 * Status card configuration
 */
interface StatusCardConfig {
  key: keyof QueueCountsResponse;
  label: string;
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'default';
  description: string;
}

const STATUS_CARDS: StatusCardConfig[] = [
  {
    key: 'pending',
    label: 'Pending',
    icon: <HourglassEmptyIcon fontSize="small" />,
    color: 'warning',
    description: 'Awaiting review',
  },
  {
    key: 'in_review',
    label: 'In Review',
    icon: <VisibilityIcon fontSize="small" />,
    color: 'info',
    description: 'Currently being reviewed',
  },
  {
    key: 'completed',
    label: 'Completed',
    icon: <CheckCircleIcon fontSize="small" />,
    color: 'success',
    description: 'Review finished',
  },
  {
    key: 'skipped',
    label: 'Skipped',
    icon: <SkipNextIcon fontSize="small" />,
    color: 'default',
    description: 'Skipped review',
  },
];

/**
 * QueueMetrics Component
 *
 * Displays queue performance metrics including:
 * - Status counts (pending, in review, completed, skipped)
 * - Average and median wait times
 * - Throughput metrics (24h and 7d)
 * - Oldest pending item indicator
 *
 * @example
 * ```tsx
 * const { data: metrics, isLoading } = useQueueMetrics();
 *
 * <QueueMetrics
 *   metrics={metrics}
 *   isLoading={isLoading}
 *   title="Queue Performance"
 * />
 * ```
 */
const QueueMetrics: React.FC<QueueMetricsProps> = ({
  metrics,
  isLoading = false,
  title = 'Queue Metrics',
  description = 'Performance metrics for the candidate review queue',
  showDetails = true,
}) => {
  /**
   * Render loading skeleton
   */
  if (isLoading) {
    return (
      <Paper elevation={1} sx={{ p: 3 }}>
        <Stack spacing={3}>
          <Box>
            <Skeleton variant="text" width={200} height={32} />
            <Skeleton variant="text" width={300} height={20} />
          </Box>
          <Grid container spacing={2}>
            {[1, 2, 3, 4].map((i) => (
              <Grid item xs={6} sm={3} key={i}>
                <Skeleton variant="rectangular" height={80} sx={{ borderRadius: 1 }} />
              </Grid>
            ))}
          </Grid>
          <Skeleton variant="rectangular" height={120} sx={{ borderRadius: 1 }} />
        </Stack>
      </Paper>
    );
  }

  /**
   * Render empty state
   */
  if (!metrics) {
    return (
      <Paper elevation={1} sx={{ p: 3, textAlign: 'center' }}>
        <AssessmentIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="body2" color="text.secondary">
          No queue metrics available
        </Typography>
      </Paper>
    );
  }

  const { counts, average_wait_time_hours, median_wait_time_hours, oldest_pending_at, throughput_last_24h, throughput_last_7d } = metrics;

  return (
    <Stack spacing={3}>
      {/* Header */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <AssessmentIcon color="primary" />
          <Typography variant="h5" fontWeight={700}>
            {title}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      </Box>

      {/* Status Counts Grid */}
      <Paper elevation={2} sx={{ p: 2 }}>
        <Typography variant="subtitle2" fontWeight={600} color="text.secondary" sx={{ mb: 2 }}>
          <PeopleIcon sx={{ fontSize: 18, mr: 0.5, verticalAlign: 'middle' }} />
          Candidates by Status
        </Typography>
        <Grid container spacing={2}>
          {STATUS_CARDS.map((status) => (
            <Grid item xs={6} sm={3} key={status.key}>
              <Card
                variant="outlined"
                sx={{
                  height: '100%',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 2,
                  },
                  borderLeft: 3,
                  borderLeftColor: `${status.color}.main`,
                }}
              >
                <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                  <Box sx={{ color: `${status.color}.main`, mb: 0.5 }}>
                    {status.icon}
                  </Box>
                  <Typography variant="h4" fontWeight={700}>
                    {counts[status.key] ?? 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {status.label}
                  </Typography>
                  {showDetails && (
                    <Typography variant="caption" display="block" color="text.disabled" sx={{ fontSize: '0.65rem' }}>
                      {status.description}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Total */}
        <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Total in Queue
            </Typography>
            <Chip
              label={counts.total}
              size="small"
              color="primary"
              variant="outlined"
              sx={{ fontWeight: 600 }}
            />
          </Box>
        </Box>
      </Paper>

      {/* Wait Time and Throughput */}
      <Grid container spacing={3}>
        {/* Wait Times */}
        <Grid item xs={12} md={6}>
          <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <ScheduleIcon color="primary" fontSize="small" />
              <Typography variant="subtitle1" fontWeight={600}>
                Wait Times
              </Typography>
            </Box>

            <Stack spacing={2}>
              {/* Average Wait Time */}
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                  <Typography variant="body2" color="text.secondary">
                    Average Wait
                  </Typography>
                  <Tooltip title={getWaitTimeTooltip(average_wait_time_hours)} arrow>
                    <Chip
                      icon={<HourglassEmptyIcon />}
                      label={formatWaitTime(average_wait_time_hours)}
                      size="small"
                      color={getWaitTimeColor(average_wait_time_hours)}
                      variant="outlined"
                    />
                  </Tooltip>
                </Box>
                <Box
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    bgcolor: 'action.hover',
                    overflow: 'hidden',
                  }}
                >
                  <Box
                    sx={{
                      height: '100%',
                      width: `${Math.min((average_wait_time_hours ?? 0) / 72 * 100, 100)}%`,
                      bgcolor: `${getWaitTimeColor(average_wait_time_hours)}.main`,
                      borderRadius: 3,
                      transition: 'width 0.5s ease-in-out',
                    }}
                  />
                </Box>
              </Box>

              {/* Median Wait Time */}
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                  <Typography variant="body2" color="text.secondary">
                    Median Wait
                  </Typography>
                  <Chip
                    label={formatWaitTime(median_wait_time_hours)}
                    size="small"
                    color={getWaitTimeColor(median_wait_time_hours)}
                    variant="outlined"
                  />
                </Box>
              </Box>

              {/* Oldest Pending */}
              <Box sx={{ pt: 1, borderTop: 1, borderColor: 'divider' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    Oldest Pending
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {formatRelativeTime(oldest_pending_at)}
                  </Typography>
                </Box>
                {oldest_pending_at && (
                  <Typography variant="caption" color="text.disabled">
                    Since {new Date(oldest_pending_at).toLocaleString()}
                  </Typography>
                )}
              </Box>
            </Stack>
          </Paper>
        </Grid>

        {/* Throughput */}
        <Grid item xs={12} md={6}>
          <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <TrendingUpIcon color="primary" fontSize="small" />
              <Typography variant="subtitle1" fontWeight={600}>
                Throughput
              </Typography>
            </Box>

            <Stack spacing={3}>
              {/* Last 24 Hours */}
              <Card
                variant="outlined"
                sx={{
                  bgcolor: 'background.default',
                  borderLeft: 3,
                  borderLeftColor: 'primary.main',
                }}
              >
                <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Last 24 Hours
                      </Typography>
                      <Typography variant="caption" color="text.disabled">
                        Completed reviews
                      </Typography>
                    </Box>
                    <Typography variant="h4" fontWeight={700} color="primary">
                      {throughput_last_24h}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>

              {/* Last 7 Days */}
              <Card
                variant="outlined"
                sx={{
                  bgcolor: 'background.default',
                  borderLeft: 3,
                  borderLeftColor: 'secondary.main',
                }}
              >
                <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Last 7 Days
                      </Typography>
                      <Typography variant="caption" color="text.disabled">
                        Completed reviews
                      </Typography>
                    </Box>
                    <Typography variant="h4" fontWeight={700} color="secondary">
                      {throughput_last_7d}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>

              {/* Daily Average */}
              {throughput_last_7d > 0 && (
                <Box sx={{ pt: 1, borderTop: 1, borderColor: 'divider' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Daily Average (7d)
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {(throughput_last_7d / 7).toFixed(1)} reviews/day
                    </Typography>
                  </Box>
                </Box>
              )}
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      {/* Performance Indicator */}
      {showDetails && (
        <Paper elevation={0} sx={{ p: 2, bgcolor: 'action.hover' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <SpeedIcon
              color={getWaitTimeColor(average_wait_time_hours)}
              sx={{ fontSize: 32 }}
            />
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle2" fontWeight={600}>
                Queue Health
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {average_wait_time_hours === null
                  ? 'No pending items in queue'
                  : average_wait_time_hours <= 4
                    ? 'Excellent - candidates are being processed quickly'
                    : average_wait_time_hours <= 24
                      ? 'Good - processing within expected timeframes'
                      : average_wait_time_hours <= 72
                        ? 'Attention needed - some candidates waiting longer than expected'
                        : 'Action required - significant backlog detected'}
              </Typography>
            </Box>
            <Chip
              label={
                average_wait_time_hours === null
                  ? 'Empty'
                  : average_wait_time_hours <= 4
                    ? 'Excellent'
                    : average_wait_time_hours <= 24
                      ? 'Good'
                      : average_wait_time_hours <= 72
                        ? 'Warning'
                        : 'Critical'
              }
              color={getWaitTimeColor(average_wait_time_hours)}
              size="small"
            />
          </Box>
        </Paper>
      )}
    </Stack>
  );
};

export default QueueMetrics;
