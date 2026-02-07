import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Avatar,
  Chip,
  IconButton,
  Stack,
  alpha,
  CardProps,
  Theme,
  SxProps,
} from '@mui/material';
import {
  Person as PersonIcon,
  ChevronRight as ChevronRightIcon,
  Delete as DeleteIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
} from '@mui/icons-material';
import { useSwipeGesture } from '../hooks/useSwipeGesture';
import { useTheme } from '@mui/material/styles';
import type { CandidateListItem } from '../types/api';

/**
 * Swipe action configuration
 */
export interface SwipeAction {
  /**
   * Icon to display for the action
   */
  icon: React.ReactElement;

  /**
   * Background color for the action
   */
  color: string;

  /**
   * Label for accessibility
   */
  label: string;

  /**
   * Callback when action is triggered
   */
  onAction: () => void;
}

/**
 * Mobile candidate card props
 */
export interface MobileCandidateCardProps extends Omit<CardProps, 'onSwipe'> {
  /**
   * Candidate data to display
   */
  candidate: CandidateListItem;

  /**
   * Swipe action for left swipe
   * @example
   * ```tsx
   * leftAction={{
   *   icon: <DeleteIcon />,
   *   color: '#f44336',
   *   label: 'Delete',
   *   onAction: () => handleDelete(candidate.id)
   * }}
   * ```
   */
  leftAction?: SwipeAction;

  /**
   * Swipe action for right swipe
   * @example
   * ```tsx
   * rightAction={{
   *   icon: <StarIcon />,
   *   color: '#ff9800',
   *   label: 'Save',
   *   onAction: () => handleSave(candidate.id)
   * }}
   * ```
   */
  rightAction?: SwipeAction;

  /**
   * Callback when card is clicked
   */
  onClick?: () => void;

  /**
   * Whether to show the candidate avatar
   * @default true
   */
  showAvatar?: boolean;

  /**
   * Whether to show tags
   * @default true
   */
  showTags?: boolean;

  /**
   * Whether to show activity indicator
   * @default true
   */
  showActivity?: boolean;

  /**
   * Custom sx props for the card
   */
  sx?: SxProps<Theme>;

  /**
   * Swipe threshold in pixels
   * @default 80
   */
  swipeThreshold?: number;

  /**
   * Whether swipe actions are enabled
   * @default true
   */
  swipeEnabled?: boolean;
}

/**
 * MobileCandidateCard Component
 *
 * A mobile-optimized candidate card with swipe actions and touch-friendly layout.
 * Designed for screens with width < 600px (mobile breakpoint).
 *
 * Features:
 * - Swipe left/right for quick actions (e.g., save, delete, archive)
 * - 44x44px minimum touch targets (iOS/Android accessibility guidelines)
 * - Visual feedback during swipe gesture
 * - Animated action reveal
 * - Touch-optimized spacing and sizing
 *
 * @example
 * ```tsx
 * function CandidateList() {
 *   const [candidates, setCandidates] = useState<CandidateListItem[]>([]);
 *
 *   const handleSave = (id: string) => {
 *     // Save candidate logic
 *   };
 *
 *   const handleDelete = (id: string) => {
 *     // Delete candidate logic
 *   };
 *
 *   return (
 *     <Stack spacing={2}>
 *       {candidates.map((candidate) => (
 *         <MobileCandidateCard
 *           key={candidate.id}
 *           candidate={candidate}
 *           leftAction={{
 *             icon: <DeleteIcon />,
 *             color: '#f44336',
 *             label: 'Delete',
 *             onAction: () => handleDelete(candidate.id)
 *           }}
 *           rightAction={{
 *             icon: <StarIcon />,
 *             color: '#ff9800',
 *             label: 'Save',
 *             onAction: () => handleSave(candidate.id)
 *           }}
 *           onClick={() => navigate(`/candidates/${candidate.id}`)}
 *         />
 *       ))}
 *     </Stack>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Without swipe actions
 * <MobileCandidateCard
 *   candidate={candidate}
 *   onClick={() => viewDetails(candidate.id)}
 *   showTags={false}
 * />
 * ```
 */
const MobileCandidateCard: React.FC<MobileCandidateCardProps> = ({
  candidate,
  leftAction,
  rightAction,
  onClick,
  showAvatar = true,
  showTags = true,
  showActivity = true,
  swipeThreshold = 80,
  swipeEnabled = true,
  sx = {},
  ...cardProps
}) => {
  const theme = useTheme();
  const [swipeOffset, setSwipeOffset] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [actionTriggered, setActionTriggered] = useState<string | null>(null);

  /**
   * Reset swipe offset
   */
  const resetSwipe = React.useCallback(() => {
    setSwipeOffset(0);
    setIsDragging(false);
  }, []);

  /**
   * Handle swipe start
   */
  const handleSwipeStart = React.useCallback(() => {
    setIsDragging(true);
    setActionTriggered(null);
  }, []);

  /**
   * Handle swiping (during gesture)
   */
  const handleSwiping = React.useCallback(
    (data: import('../hooks/useSwipeGesture').SwipeEventData) => {
      // Constrain swipe to horizontal axis only
      const constrainedOffset = Math.max(-150, Math.min(150, data.deltaX));
      setSwipeOffset(constrainedOffset);
    },
    []
  );

  /**
   * Handle swipe end (trigger action or reset)
   */
  const handleSwiped = React.useCallback(
    (data: import('../hooks/useSwipeGesture').SwipeEventData) => {
      setIsDragging(false);

      // Check if threshold met and action available
      if (Math.abs(swipeOffset) >= swipeThreshold) {
        if (swipeOffset > 0 && rightAction) {
          setActionTriggered('right');
          rightAction.onAction();
          setTimeout(resetSwipe, 300);
        } else if (swipeOffset < 0 && leftAction) {
          setActionTriggered('left');
          leftAction.onAction();
          setTimeout(resetSwipe, 300);
        } else {
          resetSwipe();
        }
      } else {
        resetSwipe();
      }
    },
    [swipeOffset, swipeThreshold, leftAction, rightAction, resetSwipe]
  );

  /**
   * Setup swipe gesture handlers
   */
  const swipeProps = useSwipeGesture(
    {
      onSwipeStart: handleSwipeStart,
      onSwiping: handleSwiping,
      onSwiped: handleSwiped,
    },
    {
      delta: 10,
      track: leftAction && rightAction ? ['left', 'right'] : leftAction ? ['left'] : ['right'],
      preventScrollOnSwipe: false,
      enabled: swipeEnabled && !onClick, // Disable swipe if onClick is present
    }
  );

  /**
   * Generate avatar color from candidate name
   */
  const getAvatarColor = React.useCallback((name: string) => {
    const colors = [
      '#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5',
      '#2196f3', '#00bcd4', '#009688', '#4caf50', '#8bc34a',
      '#cddc39', '#ffeb3b', '#ffc107', '#ff9800', '#ff5722'
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  }, []);

  /**
   * Get candidate initials for avatar
   */
  const getInitials = React.useCallback((name: string) => {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }, []);

  // Calculate action visibility based on swipe offset
  const leftActionVisible = swipeOffset < -swipeThreshold / 2;
  const rightActionVisible = swipeOffset > swipeThreshold / 2;

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        mb: 1.5,
      }}
    >
      {/* Left action background (revealed when swiping left) */}
      {leftAction && (
        <Box
          sx={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            width: '100%',
            backgroundColor: leftAction.color,
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-start',
            pl: 3,
            opacity: leftActionVisible ? 1 : 0,
            transition: isDragging ? 'none' : 'opacity 0.2s ease',
            zIndex: 0,
            pointerEvents: 'none',
          }}
        >
          <Box sx={{ color: 'white', display: 'flex', alignItems: 'center', gap: 1 }}>
            {leftAction.icon}
            <Typography variant="body2" fontWeight={600}>
              {leftAction.label}
            </Typography>
          </Box>
        </Box>
      )}

      {/* Right action background (revealed when swiping right) */}
      {rightAction && (
        <Box
          sx={{
            position: 'absolute',
            right: 0,
            top: 0,
            bottom: 0,
            width: '100%',
            backgroundColor: rightAction.color,
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            pr: 3,
            opacity: rightActionVisible ? 1 : 0,
            transition: isDragging ? 'none' : 'opacity 0.2s ease',
            zIndex: 0,
            pointerEvents: 'none',
          }}
        >
          <Box sx={{ color: 'white', display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" fontWeight={600}>
              {rightAction.label}
            </Typography>
            {rightAction.icon}
          </Box>
        </Box>
      )}

      {/* Main card */}
      <Card
        {...(swipeEnabled && !onClick ? swipeProps : {})}
        onClick={onClick}
        sx={{
          position: 'relative',
          zIndex: 1,
          transform: `translateX(${swipeOffset}px)`,
          transition: isDragging ? 'none' : 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          cursor: onClick ? 'pointer' : 'grab',
          '&:active': !onClick ? {
            cursor: 'grabbing',
          } : {},
          ...sx,
        }}
        {...cardProps}
      >
        <CardContent
          sx={{
            p: 2,
            '&:last-child': {
              pb: 2,
            },
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 2,
            }}
          >
            {/* Avatar - 44x44px minimum touch target */}
            {showAvatar && (
              <Avatar
                sx={{
                  width: 44,
                  height: 44,
                  bgcolor: getAvatarColor(candidate.filename || 'Candidate'),
                  fontSize: '1rem',
                  fontWeight: 600,
                  flexShrink: 0,
                }}
              >
                <PersonIcon />
              </Avatar>
            )}

            {/* Content */}
            <Box
              sx={{
                flex: 1,
                minWidth: 0, // Allow text truncation
              }}
            >
              {/* Name and stage */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  mb: 0.5,
                }}
              >
                <Typography
                  variant="subtitle1"
                  fontWeight={600}
                  sx={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    mr: 1,
                  }}
                >
                  {candidate.filename || 'Unknown Candidate'}
                </Typography>
                {onClick && (
                  <ChevronRightIcon
                    sx={{
                      fontSize: 20,
                      color: 'text.secondary',
                      flexShrink: 0,
                    }}
                  />
                )}
              </Box>

              {/* Stage chip */}
              <Chip
                label={candidate.stage_name || candidate.current_stage}
                size="small"
                sx={{
                  height: 24,
                  fontSize: '0.75rem',
                  mb: 1,
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                  color: 'primary.main',
                  fontWeight: 500,
                }}
              />

              {/* Tags - if enabled */}
              {showTags && candidate.tags && candidate.tags.length > 0 && (
                <Box
                  sx={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 0.5,
                    mb: 1,
                  }}
                >
                  {candidate.tags.slice(0, 2).map((tag) => (
                    <Chip
                      key={tag.id}
                      label={tag.tag_name}
                      size="small"
                      sx={{
                        height: 20,
                        fontSize: '0.7rem',
                        bgcolor: tag.color || alpha(theme.palette.grey[500], 0.1),
                        color: tag.color ? 'white' : 'text.secondary',
                      }}
                    />
                  ))}
                  {candidate.tags.length > 2 && (
                    <Chip
                      label={`+${candidate.tags.length - 2}`}
                      size="small"
                      sx={{
                        height: 20,
                        fontSize: '0.7rem',
                        bgcolor: alpha(theme.palette.grey[300], 0.5),
                        color: 'text.secondary',
                      }}
                    />
                  )}
                </Box>
              )}

              {/* Activity indicator and notes count */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  mt: 0.5,
                }}
              >
                {/* Latest activity */}
                {showActivity && candidate.latest_activity && (
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.5,
                    }}
                  >
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: 'success.main',
                      }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {new Date(candidate.latest_activity.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                )}

                {/* Notes count */}
                {candidate.notes_count > 0 && (
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.5,
                    }}
                  >
                    <Typography variant="caption" color="text.secondary">
                      {candidate.notes_count} {candidate.notes_count === 1 ? 'note' : 'notes'}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default MobileCandidateCard;
