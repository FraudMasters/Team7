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
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  Avatar,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Edit as EditIcon,
  Label as LabelIcon,
  SwapHoriz as SwapHorizIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  EventAvailable as EventAvailableIcon,
  Star as StarIcon,
  Comment as CommentIcon,
  Tag as TagIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { candidateActivitiesClient } from '@/api/candidateActivities';
import type {
  ActivityItem,
  ActivityTimelineResponse,
  ApiError,
} from '@/types/api';

/**
 * CandidateActivityTimeline Component Props
 */
interface CandidateActivityTimelineProps {
  /** Resume ID for the candidate */
  resumeId: string;
  /** Optional vacancy ID to filter activities */
  vacancyId?: string;
  /** Optional activity type filter */
  activityType?: string;
  /** API endpoint URL for activities */
  apiUrl?: string;
  /** Maximum number of activities to display (0 = unlimited) */
  limit?: number;
}

/**
 * Get activity type icon and color
 */
const getActivityTypeDisplay = (activityType: string) => {
  const displays: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
    stage_changed: {
      icon: <SwapHorizIcon />,
      color: 'primary',
      label: 'Stage Changed',
    },
    note_added: {
      icon: <CommentIcon />,
      color: 'success',
      label: 'Note Added',
    },
    note_updated: {
      icon: <EditIcon />,
      color: 'info',
      label: 'Note Updated',
    },
    note_deleted: {
      icon: <ErrorIcon />,
      color: 'error',
      label: 'Note Deleted',
    },
    tag_added: {
      icon: <TagIcon />,
      color: 'secondary',
      label: 'Tag Added',
    },
    tag_removed: {
      icon: <LabelIcon />,
      color: 'warning',
      label: 'Tag Removed',
    },
    ranking_changed: {
      icon: <StarIcon />,
      color: 'primary',
      label: 'Ranking Changed',
    },
    rating_changed: {
      icon: <StarIcon />,
      color: 'secondary',
      label: 'Rating Changed',
    },
    contact_attempt: {
      icon: <PersonIcon />,
      color: 'info',
      label: 'Contact Attempt',
    },
    interview_scheduled: {
      icon: <EventAvailableIcon />,
      color: 'success',
      label: 'Interview Scheduled',
    },
    feedback_provided: {
      icon: <CommentIcon />,
      color: 'warning',
      label: 'Feedback Provided',
    },
    status_updated: {
      icon: <InfoIcon />,
      color: 'info',
      label: 'Status Updated',
    },
  };

  return (
    displays[activityType] || {
      icon: <ScheduleIcon />,
      color: 'default',
      label: activityType,
    }
  );
};

/**
 * CandidateActivityTimeline Component
 *
 * Displays chronological activity history for a candidate including:
 * - Stage changes through the hiring pipeline
 * - Notes additions, updates, and deletions
 * - Tag additions and removals
 * - Ranking and rating changes
 * - Contact attempts and interviews
 * - Feedback and status updates
 *
 * Activities are displayed in a vertical timeline with color-coded
 * activity type indicators and detailed information for each event.
 *
 * @example
 * ```tsx
 * <CandidateActivityTimeline resumeId="resume-uuid" />
 *
 * <CandidateActivityTimeline
 *   resumeId="resume-uuid"
 *   vacancyId="vacancy-uuid"
 *   activityType="stage_changed"
 *   limit={20}
 * />
 * ```
 */
const CandidateActivityTimeline: React.FC<CandidateActivityTimelineProps> = ({
  resumeId,
  vacancyId,
  activityType,
  limit = 50,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activities, setActivities] = useState<ActivityItem[]>([]);

  /**
   * Fetch activity timeline data from backend
   */
  const fetchActivities = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response: ActivityTimelineResponse = await candidateActivitiesClient.listActivities(
        resumeId,
        activityType,
        vacancyId,
        limit
      );

      // Activities are already sorted by created_at descending from API
      setActivities(response.activities);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load activity timeline. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [resumeId, activityType, vacancyId, limit]);

  useEffect(() => {
    fetchActivities();
  }, [fetchActivities]);

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
   * Get author display name from recruiter_id
   */
  const getAuthorName = useCallback((recruiterId: string | null) => {
    if (!recruiterId) return 'System';
    // Extract username from email or use ID
    if (recruiterId.includes('@')) {
      return recruiterId.split('@')[0];
    }
    return recruiterId;
  }, []);

  /**
   * Get author initials for avatar
   */
  const getAuthorInitials = useCallback((name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  }, []);

  /**
   * Generate activity description
   */
  const getActivityDescription = useCallback((activity: ActivityItem) => {
    const author = getAuthorName(activity.recruiter_id);

    switch (activity.activity_type) {
      case 'stage_changed':
        return `${author} moved candidate from "${activity.from_stage || 'Unknown'}" to "${activity.to_stage || 'Unknown'}"${
          activity.reason ? `: ${activity.reason}` : ''
        }`;

      case 'note_added':
        return `${author} added a note${activity.reason ? `: ${activity.reason}` : ''}`;

      case 'note_updated':
        return `${author} updated a note`;

      case 'note_deleted':
        return `${author} deleted a note`;

      case 'tag_added':
        return `${author} added tag${activity.reason ? `: ${activity.reason}` : ''}`;

      case 'tag_removed':
        return `${author} removed tag${activity.reason ? `: ${activity.reason}` : ''}`;

      case 'ranking_changed':
        return `${author} changed ranking${activity.reason ? `: ${activity.reason}` : ''}`;

      case 'rating_changed':
        return `${author} changed rating${activity.reason ? `: ${activity.reason}` : ''}`;

      case 'contact_attempt':
        return `${author} attempted to contact candidate${activity.reason ? `: ${activity.reason}` : ''}`;

      case 'interview_scheduled':
        return `${author} scheduled an interview${activity.reason ? `: ${activity.reason}` : ''}`;

      case 'feedback_provided':
        return `${author} provided feedback${activity.reason ? `: ${activity.reason}` : ''}`;

      case 'status_updated':
        return `${author} updated status${activity.reason ? `: ${activity.reason}` : ''}`;

      default:
        return `${author} performed ${activity.activity_type}${activity.reason ? `: ${activity.reason}` : ''}`;
    }
  }, [getAuthorName]);

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
          {t('activityTimeline.loading')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {t('activityTimeline.loadingHint')}
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
          <Button color="inherit" onClick={fetchActivities} startIcon={<RefreshIcon />}>
            {t('activityTimeline.retry')}
          </Button>
        }
      >
        <AlertTitle>{t('activityTimeline.errorTitle')}</AlertTitle>
        {error}
      </Alert>
    );
  }

  if (activities.length === 0) {
    return (
      <Alert severity="info">
        <AlertTitle>{t('activityTimeline.noActivitiesTitle')}</AlertTitle>
        {t('activityTimeline.noActivities')}
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ScheduleIcon fontSize="large" color="primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                {t('activityTimeline.title')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('activityTimeline.subtitle', { count: activities.length })}
                {vacancyId && ` ${t('activityTimeline.forVacancy')}`}
                {activityType && ` ${t('activityTimeline.filteredBy', { type: activityType })}`}
              </Typography>
            </Box>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchActivities}
            size="small"
          >
            {t('activityTimeline.refresh')}
          </Button>
        </Box>
      </Paper>

      {/* Activity Timeline */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Timeline>
          {activities.map((activity, index) => {
            const display = getActivityTypeDisplay(activity.activity_type);
            const author = getAuthorName(activity.recruiter_id);

            return (
              <TimelineItem key={activity.id}>
                <TimelineSeparator>
                  <TimelineDot color={display.color as any}>{display.icon}</TimelineDot>
                  {index < activities.length - 1 && <TimelineConnector />}
                </TimelineSeparator>
                <TimelineContent sx={{ py: 2 }}>
                  <Card
                    variant="outlined"
                    sx={{
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      '&:hover': {
                        transform: 'translateX(4px)',
                        boxShadow: 2,
                      },
                    }}
                  >
                    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                      {/* Activity Header */}
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          mb: 1,
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip
                            icon={display.icon}
                            label={display.label}
                            size="small"
                            color={display.color as any}
                            variant="outlined"
                          />
                          <Typography variant="caption" color="text.secondary">
                            {formatTimestamp(activity.created_at)}
                          </Typography>
                        </Box>
                        {activity.vacancy_id && (
                          <Chip
                            label={activity.vacancy_id.slice(0, 8)}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem' }}
                          />
                        )}
                      </Box>

                      {/* Activity Description */}
                      <Typography variant="body2" color="text.primary" sx={{ mb: 1 }}>
                        {getActivityDescription(activity)}
                      </Typography>

                      {/* Activity Details */}
                      {(activity.from_stage || activity.to_stage || activity.reason) && (
                        <Box sx={{ mt: 1 }}>
                          {activity.from_stage && activity.to_stage && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                              <Chip
                                label={activity.from_stage}
                                size="small"
                                sx={{ fontSize: '0.7rem', opacity: 0.8 }}
                              />
                              <SwapHorizIcon fontSize="small" color="action" />
                              <Chip
                                label={activity.to_stage}
                                size="small"
                                color="primary"
                                sx={{ fontSize: '0.7rem' }}
                              />
                            </Box>
                          )}
                          {activity.reason && (
                            <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                              "{activity.reason}"
                            </Typography>
                          )}
                        </Box>
                      )}

                      {/* Author Info */}
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1.5 }}>
                        <Avatar
                          sx={{
                            width: 24,
                            height: 24,
                            bgcolor: 'action.selected',
                            fontSize: '0.7rem',
                          }}
                        >
                          {getAuthorInitials(author)}
                        </Avatar>
                        <Typography variant="caption" color="text.secondary">
                          {author}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </TimelineContent>
              </TimelineItem>
            );
          })}
        </Timeline>
      </Paper>
    </Stack>
  );
};

export default CandidateActivityTimeline;
