import React, { useState, useCallback } from 'react';
import {
  Badge,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Typography,
  Paper,
  CircularProgress,
  Divider,
  ListItemText,
  ListItemIcon,
  Button,
  Alert,
  Chip,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  NotificationsNone as NotificationsNoneIcon,
  DoneAll as DoneAllIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Person as PersonIcon,
  Work as WorkIcon,
  Description as DescriptionIcon,
  Event as EventIcon,
  Star as StarIcon,
  Label as LabelIcon,
  Schedule as ScheduleIcon,
  Mail as MailIcon,
  Send as SendIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useNotificationContext } from '@/contexts/NotificationContext';
import type { NotificationResponse, NotificationType } from '@/types/api';

/**
 * NotificationCenter Component Props
 */
interface NotificationCenterProps {
  /** Maximum number of notifications to display in dropdown (0 = unlimited) */
  maxNotifications?: number;
  /** Position of the menu (left or right) */
  anchorOrigin?: {
    vertical: 'top' | 'bottom';
    horizontal: 'left' | 'right';
  };
  /** Callback when notification is clicked */
  onNotificationClick?: (notification: NotificationResponse) => void;
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
const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'urgent':
      return 'error';
    case 'high':
      return 'warning';
    case 'normal':
      return 'info';
    case 'low':
      return 'default';
    default:
      return 'default';
  }
};

/**
 * NotificationCenter Component
 *
 * Displays a notification center with unread badge and dropdown list:
 * - Shows badge with unread count
 * - Dropdown menu with notification list
 * - Mark all as read action
 * - Individual notification actions (mark read, delete)
 * - Click to navigate to notification context
 * - Handles loading and error states gracefully
 * - Real-time updates via NotificationContext
 *
 * @example
 * ```tsx
 * <NotificationCenter />
 *
 * <NotificationCenter
 *   maxNotifications={10}
 *   onNotificationClick={(notification) => navigate(notification.action_url)}
 * />
 * ```
 */
const NotificationCenter: React.FC<NotificationCenterProps> = ({
  maxNotifications = 10,
  anchorOrigin = { vertical: 'bottom', horizontal: 'right' },
  onNotificationClick,
}) => {
  const { t } = useTranslation();
  const {
    notifications,
    unreadCount,
    isLoading,
    error,
    markNotificationRead,
    markAllRead,
    deleteNotification,
    refreshNotifications,
    clearError,
  } = useNotificationContext();

  // Menu state
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [markingReadId, setMarkingReadId] = useState<string | null>(null);
  const [markingAllRead, setMarkingAllRead] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const menuOpen = Boolean(anchorEl);

  /**
   * Handle menu open
   */
  const handleMenuOpen = useCallback(
    (event: React.MouseEvent<HTMLElement>) => {
      setAnchorEl(event.currentTarget);
      // Refresh notifications when opening menu
      refreshNotifications();
    },
    [refreshNotifications]
  );

  /**
   * Handle menu close
   */
  const handleMenuClose = useCallback(() => {
    setAnchorEl(null);
  }, []);

  /**
   * Handle notification click
   */
  const handleNotificationClick = useCallback(
    async (notification: NotificationResponse) => {
      try {
        // Mark as read if unread
        if (!notification.is_read) {
          setMarkingReadId(notification.id);
          await markNotificationRead(notification.id, true);
          setMarkingReadId(null);
        }

        // Close menu
        handleMenuClose();

        // Call custom click handler
        onNotificationClick?.(notification);
      } catch (err) {
        setMarkingReadId(null);
        // Silently fail on mark as read
      }
    },
    [markNotificationRead, onNotificationClick, handleMenuClose]
  );

  /**
   * Handle delete notification
   */
  const handleDelete = useCallback(
    async (event: React.MouseEvent<HTMLElement>, notificationId: string) => {
      event.stopPropagation(); // Prevent menu close

      try {
        setDeletingId(notificationId);
        await deleteNotification(notificationId);
        setSuccessMessage('Notification deleted.');
        setTimeout(() => setSuccessMessage(null), 2000);
      } catch (err) {
        setSuccessMessage(null);
      } finally {
        setDeletingId(null);
      }
    },
    [deleteNotification]
  );

  /**
   * Handle mark all as read
   */
  const handleMarkAllRead = useCallback(
    async (event: React.MouseEvent<HTMLElement>) => {
      event.stopPropagation(); // Prevent menu close

      try {
        setMarkingAllRead(true);
        const result = await markAllRead();
        setSuccessMessage(`Marked ${result.updated_count} notifications as read.`);
        setTimeout(() => setSuccessMessage(null), 2000);
      } catch (err) {
        setSuccessMessage(null);
      } finally {
        setMarkingAllRead(false);
      }
    },
    [markAllRead]
  );

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

  // Display notifications (apply maxNotifications limit if set)
  const displayedNotifications =
    maxNotifications > 0 ? notifications.slice(0, maxNotifications) : notifications;

  return (
    <>
      {/* Notification Icon Button with Badge */}
      <IconButton
        color="inherit"
        onClick={handleMenuOpen}
        aria-label={`Notifications ${unreadCount > 0 ? `(${unreadCount} unread)` : ''}`}
      >
        <Badge badgeContent={unreadCount} color="error" max={99}>
          {unreadCount > 0 ? (
            <NotificationsIcon />
          ) : (
            <NotificationsNoneIcon />
          )}
        </Badge>
      </IconButton>

      {/* Dropdown Menu */}
      <Menu
        anchorEl={anchorEl}
        open={menuOpen}
        onClose={handleMenuClose}
        anchorOrigin={anchorOrigin}
        transformOrigin={{
          vertical: 'top',
          horizontal: anchorOrigin.horizontal === 'right' ? 'right' : 'left',
        }}
        PaperProps={{
          sx: {
            width: 380,
            maxHeight: 500,
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        {/* Header */}
        <Box
          sx={{
            px: 2,
            py: 1.5,
            borderBottom: 1,
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Typography variant="subtitle1" fontWeight={600}>
            Notifications
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label={unreadCount}
              size="small"
              color={unreadCount > 0 ? 'primary' : 'default'}
            />
            {unreadCount > 0 && (
              <Button
                size="small"
                startIcon={
                  markingAllRead ? (
                    <CircularProgress size={14} />
                  ) : (
                    <DoneAllIcon fontSize="small" />
                  )
                }
                onClick={handleMarkAllRead}
                disabled={markingAllRead}
              >
                Mark all read
              </Button>
            )}
          </Box>
        </Box>

        {/* Success Message */}
        {successMessage && (
          <Alert
            severity="success"
            icon={<CheckCircleIcon fontSize="inherit" />}
            onClose={() => setSuccessMessage(null)}
            sx={{ mx: 1, mt: 1 }}
          >
            {successMessage}
          </Alert>
        )}

        {/* Error Message */}
        {error && (
          <Alert severity="error" onClose={clearError} sx={{ mx: 1, mt: 1 }}>
            {error}
          </Alert>
        )}

        {/* Loading State */}
        {isLoading && notifications.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              py: 4,
            }}
          >
            <CircularProgress size={40} sx={{ mb: 2 }} />
            <Typography variant="body2" color="text.secondary">
              {t('notifications.loading') || 'Loading notifications...'}
            </Typography>
          </Box>
        ) : notifications.length === 0 ? (
          /* Empty State */
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              py: 4,
              px: 2,
            }}
          >
            <NotificationsNoneIcon
              sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }}
            />
            <Typography variant="body2" color="text.secondary" align="center">
              {t('notifications.noNotifications') || 'No notifications yet'}
            </Typography>
          </Box>
        ) : (
          /* Notification List */
          <Box sx={{ maxHeight: 400, overflowY: 'auto' }}>
            {displayedNotifications.map((notification) => (
              <MenuItem
                key={notification.id}
                onClick={() => handleNotificationClick(notification)}
                sx={{
                  px: 2,
                  py: 1.5,
                  borderBottom: 1,
                  borderColor: 'divider',
                  bgcolor: notification.is_read ? 'inherit' : 'action.hover',
                  '&:last-child': { borderBottom: 'none' },
                  opacity: markingReadId === notification.id ? 0.5 : 1,
                }}
                disabled={markingReadId === notification.id}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: 1,
                      bgcolor: getPriorityColor(notification.priority) + '.main',
                      color: getPriorityColor(notification.priority) + '.contrastText',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {getNotificationIcon(notification.type)}
                  </Box>
                </ListItemIcon>

                <ListItemText
                  primary={
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        justifyContent: 'space-between',
                        gap: 1,
                      }}
                    >
                      <Typography
                        variant="subtitle2"
                        fontWeight={notification.is_read ? 'normal' : 600}
                        sx={{ flex: 1 }}
                      >
                        {notification.title}
                      </Typography>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        whiteSpace="nowrap"
                      >
                        {formatTimestamp(notification.created_at)}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        mt: 0.5,
                      }}
                    >
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          flex: 1,
                          mr: 1,
                        }}
                      >
                        {notification.message}
                      </Typography>
                    </Box>
                  }
                />

                {/* Delete Button */}
                <IconButton
                  size="small"
                  onClick={(e) => handleDelete(e, notification.id)}
                  disabled={deletingId === notification.id}
                  sx={{ ml: 0.5 }}
                  edge="end"
                >
                  {deletingId === notification.id ? (
                    <CircularProgress size={16} />
                  ) : (
                    <DeleteIcon fontSize="small" />
                  )}
                </IconButton>
              </MenuItem>
            ))}

            {/* Show more indicator */}
            {maxNotifications > 0 && notifications.length > maxNotifications && (
              <Box sx={{ py: 1.5, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">
                  {t('notifications.showingMore', {
                    shown: displayedNotifications.length,
                    total: notifications.length,
                  }) ||
                    `Showing ${displayedNotifications.length} of ${notifications.length} notifications`}
                </Typography>
              </Box>
            )}
          </Box>
        )}

        {/* Footer */}
        {notifications.length > 0 && (
          <>
            <Divider />
            <Box sx={{ px: 2, py: 1, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                {t('notifications.total', {
                  count: notifications.length,
                  unread: unreadCount,
                }) ||
                  `${notifications.length} total notifications, ${unreadCount} unread`}
              </Typography>
            </Box>
          </>
        )}
      </Menu>
    </>
  );
};

export default NotificationCenter;
