import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Chip,
  CircularProgress,
  Link,
  Stack,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Person as PersonIcon,
  Work as WorkIcon,
  Description as DescriptionIcon,
  Event as EventIcon,
  Star as StarIcon,
  Schedule as ScheduleIcon,
  Mail as MailIcon,
  Send as SendIcon,
  Settings as SettingsIcon,
  Label as LabelIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import type { NotificationResponse, NotificationType, NotificationPriority } from '@/types/api';

/**
 * NotificationItem Component Props
 */
interface NotificationItemProps {
  /** Notification data to display */
  notification: NotificationResponse;
  /** Callback when notification is clicked */
  onClick?: (notification: NotificationResponse) => void;
  /** Callback when delete button is clicked */
  onDelete?: (notificationId: string) => Promise<void>;
  /** Callback when notification is marked as read/unread */
  onToggleRead?: (notificationId: string, isRead: boolean) => Promise<void>;
  /** Whether to show the delete button */
  showDelete?: boolean;
  /** Whether to show the paper/card wrapper */
  showWrapper?: boolean;
  /** Whether the item is currently being deleted */
  isDeleting?: boolean;
  /** Whether the item is currently being marked as read/unread */
  isTogglingRead?: boolean;
}

/**
 * Get icon for notification type
 */
const getNotificationIcon = (type: NotificationType) => {
  switch (type) {
    case 'candidate_applied':
      return <PersonIcon fontSize="small" />;
    case 'candidate_responded':
      return <SendIcon fontSize="small" />;
    case 'resume_uploaded':
      return <DescriptionIcon fontSize="small" />;
    case 'candidate_moved':
      return <WorkIcon fontSize="small" />;
    case 'new_match':
      return <StarIcon fontSize="small" />;
    case 'interview_scheduled':
      return <EventIcon fontSize="small" />;
    case 'offer_sent':
      return <SendIcon fontSize="small" />;
    case 'offer_accepted':
      return <CheckCircleIcon fontSize="small" />;
    case 'offer_rejected':
      return <ErrorIcon fontSize="small" />;
    case 'reminder':
      return <ScheduleIcon fontSize="small" />;
    case 'system':
      return <SettingsIcon fontSize="small" />;
    case 'digest':
      return <MailIcon fontSize="small" />;
    default:
      return <LabelIcon fontSize="small" />;
  }
};

/**
 * Get color for notification priority
 */
const getPriorityColor = (priority: NotificationPriority) => {
  switch (priority) {
    case 'urgent':
      return 'error' as const;
    case 'high':
      return 'warning' as const;
    case 'normal':
      return 'info' as const;
    case 'low':
      return 'default' as const;
    default:
      return 'default' as const;
  }
};

/**
 * Get label for notification priority
 */
const getPriorityLabel = (priority: NotificationPriority): string => {
  switch (priority) {
    case 'urgent':
      return 'Urgent';
    case 'high':
      return 'High';
    case 'normal':
      return 'Normal';
    case 'low':
      return 'Low';
    default:
      return 'Normal';
  }
};

/**
 * Format timestamp for display
 */
const formatTimestamp = (timestamp: string): string => {
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
};

/**
 * NotificationItem Component
 *
 * Displays a single notification with:
 * - Read/unread visual distinction (background color, font weight)
 * - Priority indicator with colored icon
 * - Notification type icon
 * - Title and message
 * - Link to action_url (context link)
 * - Timestamp with relative formatting
 * - Delete action with loading state
 * - Aggregated count indicator (if applicable)
 * - Expiry indicator (if applicable)
 *
 * @example
 * ```tsx
 * <NotificationItem
 *   notification={notification}
 *   onClick={handleClick}
 *   onDelete={handleDelete}
 *   onToggleRead={handleToggleRead}
 * />
 *
 * // Minimal version without actions
 * <NotificationItem
 *   notification={notification}
 *   showDelete={false}
 *   showWrapper={false}
 * />
 * ```
 */
const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  onClick,
  onDelete,
  onToggleRead,
  showDelete = true,
  showWrapper = true,
  isDeleting = false,
  isTogglingRead = false,
}) => {
  const { t } = useTranslation();

  /**
   * Handle notification click
   */
  const handleClick = useCallback(() => {
    // Mark as read if unread and callback provided
    if (!notification.is_read && onToggleRead) {
      onToggleRead(notification.id, true).catch(() => {
        // Silently fail on mark as read
      });
    }

    // Call click handler
    onClick?.(notification);
  }, [notification, onToggleRead, onClick]);

  /**
   * Handle delete button click
   */
  const handleDelete = useCallback(
    async (event: React.MouseEvent<HTMLElement>) => {
      event.stopPropagation(); // Prevent triggering notification click

      if (onDelete) {
        await onDelete(notification.id);
      }
    },
    [notification.id, onDelete]
  );

  /**
   * Handle link click (stop propagation to prevent double mark as read)
   */
  const handleLinkClick = useCallback((event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();

    // Let the link navigate normally, but don't trigger onClick
    // The onClick will mark it as read, which we want to avoid duplicate calls
  }, []);

  const priorityColor = getPriorityColor(notification.priority);
  const priorityLabel = getPriorityLabel(notification.priority);
  const typeIcon = getNotificationIcon(notification.type);
  const isExpired = notification.expires_at ? new Date(notification.expires_at) < new Date() : false;

  /**
   * Render notification content
   */
  const content = (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 2,
        p: 2,
        bgcolor: notification.is_read ? 'inherit' : 'action.hover',
        borderRadius: showWrapper ? 0 : 1,
        borderLeft: notification.is_read ? 3 : 4,
        borderColor: priorityColor + '.main',
        opacity: isDeleting || isTogglingRead ? 0.5 : 1,
        transition: 'opacity 0.2s ease-in-out',
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': onClick ? {
          bgcolor: notification.is_read ? 'action.hover' : 'action.selected',
        } : {},
      }}
      onClick={handleClick}
    >
      {/* Priority Icon Box */}
      <Box
        sx={{
          flexShrink: 0,
          width: 40,
          height: 40,
          borderRadius: 1,
          bgcolor: priorityColor + '.main',
          color: priorityColor + '.contrastText',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {typeIcon}
      </Box>

      {/* Notification Content */}
      <Box sx={{ flex: 1, minWidth: 0 }}>
        {/* Header: Title, Priority Badge, Timestamp */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 1,
            mb: 0.5,
            flexWrap: 'wrap',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography
              variant="subtitle2"
              fontWeight={notification.is_read ? 'normal' : 600}
              color="text.primary"
            >
              {notification.title}
            </Typography>

            {/* Priority Badge */}
            <Chip
              label={priorityLabel}
              size="small"
              color={priorityColor}
              variant="outlined"
              sx={{ height: 20, fontSize: '0.7rem', fontWeight: 500 }}
            />

            {/* Aggregated Count Badge */}
            {notification.aggregated_count && notification.aggregated_count > 1 && (
              <Chip
                label={`×${notification.aggregated_count}`}
                size="small"
                color="primary"
                variant="filled"
                sx={{ height: 20, fontSize: '0.7rem', fontWeight: 600 }}
              />
            )}

            {/* Expired Badge */}
            {isExpired && (
              <Chip
                label="Expired"
                size="small"
                color="error"
                variant="outlined"
                sx={{ height: 20, fontSize: '0.7rem' }}
              />
            )}

            {/* Unread Indicator */}
            {!notification.is_read && (
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                }}
              />
            )}
          </Box>

          {/* Timestamp */}
          <Typography variant="caption" color="text.secondary" whiteSpace="nowrap">
            {formatTimestamp(notification.created_at)}
          </Typography>
        </Box>

        {/* Message */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            mb: notification.action_url ? 0.5 : 0,
          }}
        >
          {notification.message}
        </Typography>

        {/* Action Link */}
        {notification.action_url && (
          <Link
            href={notification.action_url}
            onClick={handleLinkClick}
            underline="hover"
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              fontSize: '0.875rem',
              fontWeight: 500,
              color: 'primary.main',
            }}
          >
            {notification.action_label || t('notifications.viewDetails') || 'View details'}
          </Link>
        )}

        {/* Read At Timestamp */}
        {notification.is_read && notification.read_at && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
            {t('notifications.readAt', { time: formatTimestamp(notification.read_at) }) ||
              `Read ${formatTimestamp(notification.read_at)}`}
          </Typography>
        )}
      </Box>

      {/* Delete Button */}
      {showDelete && onDelete && (
        <Box sx={{ flexShrink: 0 }}>
          <IconButton
            size="small"
            onClick={handleDelete}
            disabled={isDeleting}
            color="default"
            sx={{ ml: 0.5 }}
          >
            {isDeleting ? (
              <CircularProgress size={16} />
            ) : (
              <DeleteIcon fontSize="small" />
            )}
          </IconButton>
        </Box>
      )}
    </Box>
  );

  /**
   * Render with wrapper if needed
   */
  if (showWrapper) {
    return (
      <Paper
        elevation={notification.is_read ? 1 : 2}
        sx={{
          mb: 1,
          overflow: 'hidden',
          transition: 'box-shadow 0.2s ease-in-out',
        }}
      >
        {content}
      </Paper>
    );
  }

  return content;
};

export default NotificationItem;
