import React, { useState, useCallback } from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Avatar,
  Chip,
  Stack,
  alpha,
  CardProps,
  Theme,
  SxProps,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import {
  Person as PersonIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Schedule as ScheduleIcon,
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useSwipeGesture } from '../hooks/useSwipeGesture';
import { useTheme } from '@mui/material/styles';
import type { ReviewQueueCandidate } from '../api/hiringManager';

/**
 * Swipe action configuration for review cards
 */
export interface ReviewSwipeAction {
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
 * Mobile review card props
 */
export interface MobileReviewCardProps extends Omit<CardProps, 'onSwipe'> {
  /**
   * Candidate data to display
   */
  candidate: ReviewQueueCandidate;

  /**
   * Swipe action for left swipe (typically reject)
   * @example
   * ```tsx
   * leftAction={{
   *   icon: <CancelIcon />,
   *   color: '#f44336',
   *   label: 'Reject',
   *   onAction: () => handleReject(candidate.id)
   * }}
   * ```
   */
  leftAction?: ReviewSwipeAction;

  /**
   * Swipe action for right swipe (typically approve)
   * @example
   * ```tsx
   * rightAction={{
   *   icon: <CheckCircleIcon />,
   *   color: '#4caf50',
   *   label: 'Approve',
   *   onAction: () => handleApprove(candidate.id)
   * }}
   * ```
   */
  rightAction?: ReviewSwipeAction;

  /**
   * Callback when card is clicked (view details)
   */
  onClick?: () => void;

  /**
   * Whether to show the candidate avatar
   * @default true
   */
  showAvatar?: boolean;

  /**
   * Whether to show recruiter feedback preview
   * @default true
   */
  showFeedback?: boolean;

  /**
   * Whether to show team consensus
   * @default true
   */
  showConsensus?: boolean;

  /**
   * Whether to show match score
   * @default true
   */
  showMatchScore?: boolean;

  /**
   * Custom sx props for the card
   */
  sx?: SxProps<Theme>;

  /**
   * Swipe threshold in pixels
   * @default 100
   */
  swipeThreshold?: number;

  /**
   * Whether swipe actions are enabled
   * @default true
   */
  swipeEnabled?: boolean;

  /**
   * Whether to show in compact mode for smaller tablets
   * @default false
   */
  compact?: boolean;
}

/**
 * Get color for priority chip
 */
function getPriorityColor(priority: string | null): 'error' | 'warning' | 'info' | 'default' {
  switch (priority) {
    case 'urgent':
      return 'error';
    case 'high':
      return 'warning';
    case 'normal':
      return 'info';
    default:
      return 'default';
  }
}

/**
 * Get color for consensus chip
 */
function getConsensusColor(consensus: string | null): 'success' | 'error' | 'warning' | 'default' {
  switch (consensus) {
    case 'approve':
      return 'success';
    case 'reject':
      return 'error';
    case 'mixed':
      return 'warning';
    default:
      return 'default';
  }
}

/**
 * MobileReviewCard Component
 *
 * A mobile-optimized candidate review card for the hiring manager portal.
 * Designed for tablets with touch-friendly swipe actions for approve/reject.
 *
 * Features:
 * - Swipe left for reject, right for approve
 * - 44x44px minimum touch targets (iOS/Android accessibility guidelines)
 * - Visual feedback during swipe gesture
 * - Animated action reveal
 * - Match score visualization
 * - Team consensus indicator
 * - Recruiter feedback preview
 * - Days in stage indicator
 *
 * @example
 * ```tsx
 * function ReviewQueue() {
 *   const handleApprove = (id: string) => {
 *     // Approve candidate logic
 *   };
 *
 *   const handleReject = (id: string) => {
 *     // Reject candidate logic
 *   };
 *
 *   return (
 *     <Stack spacing={2}>
 *       {candidates.map((candidate) => (
 *         <MobileReviewCard
 *           key={candidate.id}
 *           candidate={candidate}
 *           leftAction={{
 *             icon: <CancelIcon />,
 *             color: '#f44336',
 *             label: 'Reject',
 *             onAction: () => handleReject(candidate.id)
 *           }}
 *           rightAction={{
 *             icon: <CheckCircleIcon />,
 *             color: '#4caf50',
 *             label: 'Approve',
 *             onAction: () => handleApprove(candidate.id)
 *           }}
 *           onClick={() => navigate(`/hiring-manager/candidates/${candidate.id}`)}
 *         />
 *       ))}
 *     </Stack>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Compact mode for smaller tablets
 * <MobileReviewCard
 *   candidate={candidate}
 *   compact
 *   showFeedback={false}
 *   onClick={() => viewDetails(candidate.id)}
 * />
 * ```
 */
const MobileReviewCard: React.FC<MobileReviewCardProps> = ({
  candidate,
  leftAction,
  rightAction,
  onClick,
  showAvatar = true,
  showFeedback = true,
  showConsensus = true,
  showMatchScore = true,
  swipeThreshold = 100,
  swipeEnabled = true,
  compact = false,
  sx = {},
  ...cardProps
}) => {
  const theme = useTheme();
  const [swipeOffset, setSwipeOffset] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [actionTriggered, setActionTriggered] = useState<string | null>(null);

  const candidateName = candidate.candidate_name || candidate.filename || 'Unknown Candidate';

  /**
   * Generate avatar color from candidate name
   */
  const getAvatarColor = useCallback((name: string) => {
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
  const getInitials = useCallback((name: string) => {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  }, []);

  /**
   * Reset swipe offset
   */
  const resetSwipe = useCallback(() => {
    setSwipeOffset(0);
    setIsDragging(false);
  }, []);

  /**
   * Handle swipe start
   */
  const handleSwipeStart = useCallback(() => {
    setIsDragging(true);
    setActionTriggered(null);
  }, []);

  /**
   * Handle swiping (during gesture)
   */
  const handleSwiping = useCallback(
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
  const handleSwiped = useCallback(
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

  // Calculate action visibility based on swipe offset
  const leftActionVisible = swipeOffset < -swipeThreshold / 2;
  const rightActionVisible = swipeOffset > swipeThreshold / 2;

  // Calculate match score percentage
  const matchScorePercent = candidate.match_score !== null
    ? Math.round(candidate.match_score * 100)
    : null;

  // Get match score color
  const getMatchScoreColor = (score: number) => {
    if (score >= 80) return 'success.main';
    if (score >= 60) return 'warning.main';
    return 'error.main';
  };

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        mb: 2,
      }}
    >
      {/* Left action background (revealed when swiping left - Reject) */}
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

      {/* Right action background (revealed when swiping right - Approve) */}
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
          border: candidate.priority === 'urgent'
            ? `2px solid ${theme.palette.error.main}`
            : actionTriggered === 'right'
              ? `2px solid ${theme.palette.success.main}`
              : actionTriggered === 'left'
                ? `2px solid ${theme.palette.error.main}`
                : undefined,
          '&:active': !onClick ? {
            cursor: 'grabbing',
          } : {},
          ...sx,
        }}
        {...cardProps}
      >
        <CardContent
          sx={{
            p: compact ? 1.5 : 2,
            '&:last-child': {
              pb: compact ? 1.5 : 2,
            },
          }}
        >
          {/* Header Row */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: compact ? 1.5 : 2,
            }}
          >
            {/* Avatar - 48x48px for tablet touch targets */}
            {showAvatar && (
              <Avatar
                sx={{
                  width: compact ? 40 : 48,
                  height: compact ? 40 : 48,
                  bgcolor: getAvatarColor(candidateName),
                  fontSize: compact ? '0.875rem' : '1rem',
                  fontWeight: 600,
                  flexShrink: 0,
                }}
              >
                {getInitials(candidateName)}
              </Avatar>
            )}

            {/* Content */}
            <Box
              sx={{
                flex: 1,
                minWidth: 0, // Allow text truncation
              }}
            >
              {/* Name and Priority */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  mb: 0.5,
                }}
              >
                <Typography
                  variant={compact ? 'body1' : 'subtitle1'}
                  fontWeight={600}
                  sx={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    mr: 1,
                  }}
                >
                  {candidateName}
                </Typography>

                {/* Priority Badge */}
                {candidate.priority && (
                  <Tooltip title="Priority">
                    <Chip
                      icon={candidate.priority === 'urgent' ? <WarningIcon /> : undefined}
                      label={candidate.priority.toUpperCase()}
                      size="small"
                      color={getPriorityColor(candidate.priority)}
                      sx={{
                        height: compact ? 20 : 24,
                        fontSize: '0.65rem',
                        fontWeight: 600,
                        flexShrink: 0,
                      }}
                    />
                  </Tooltip>
                )}
              </Box>

              {/* Vacancy Title */}
              {candidate.vacancy_title && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    mb: 0.5,
                  }}
                >
                  {candidate.vacancy_title}
                </Typography>
              )}

              {/* Stage and Days in Stage */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                  mb: 1,
                  flexWrap: 'wrap',
                }}
              >
                <Chip
                  label={candidate.stage_name || candidate.current_stage}
                  size="small"
                  variant="outlined"
                  sx={{
                    height: compact ? 22 : 24,
                    fontSize: compact ? '0.7rem' : '0.75rem',
                  }}
                />

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <ScheduleIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                  <Typography variant="caption" color="text.secondary">
                    {candidate.days_in_stage}d
                  </Typography>
                </Box>
              </Box>

              {/* Match Score */}
              {showMatchScore && matchScorePercent !== null && (
                <Box sx={{ mb: compact ? 0.5 : 1 }}>
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      mb: 0.5,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <TrendingUpIcon sx={{ fontSize: 16, color: getMatchScoreColor(matchScorePercent) }} />
                      <Typography variant="caption" color="text.secondary">
                        Match Score
                      </Typography>
                    </Box>
                    <Typography
                      variant="caption"
                      fontWeight={600}
                      color={getMatchScoreColor(matchScorePercent)}
                    >
                      {matchScorePercent}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={matchScorePercent}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      bgcolor: alpha(theme.palette.primary.main, 0.1),
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 3,
                        bgcolor: getMatchScoreColor(matchScorePercent),
                      },
                    }}
                  />
                </Box>
              )}

              {/* Team Consensus */}
              {showConsensus && candidate.team_consensus && (
                <Box sx={{ mb: compact ? 0.5 : 1 }}>
                  <Chip
                    icon={
                      candidate.team_consensus === 'approve' ? <CheckCircleIcon /> :
                      candidate.team_consensus === 'reject' ? <CancelIcon /> :
                      undefined
                    }
                    label={`Team: ${candidate.team_consensus.charAt(0).toUpperCase() + candidate.team_consensus.slice(1)}`}
                    size="small"
                    color={getConsensusColor(candidate.team_consensus)}
                    variant="outlined"
                    sx={{ height: compact ? 22 : 24 }}
                  />
                </Box>
              )}

              {/* Recruiter Feedback Preview */}
              {showFeedback && candidate.recruiter_feedback && candidate.recruiter_feedback.length > 0 && (
                <Box sx={{ mb: compact ? 0.5 : 1 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                    Recruiter Feedback ({candidate.recruiter_feedback.length})
                  </Typography>
                  <Box
                    sx={{
                      p: compact ? 0.75 : 1,
                      bgcolor: alpha(theme.palette.primary.main, 0.05),
                      borderRadius: 1,
                    }}
                  >
                    {candidate.recruiter_feedback.slice(0, compact ? 1 : 2).map((feedback, index) => (
                      <Box key={index} sx={{ mb: index < Math.min(1, candidate.recruiter_feedback.length - 1) ? 0.5 : 0 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="caption" fontWeight={600}>
                            {feedback.recruiter_name}
                          </Typography>
                          {feedback.rating && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
                              <StarIcon sx={{ fontSize: 12, color: 'warning.main' }} />
                              <Typography variant="caption">{feedback.rating}</Typography>
                            </Box>
                          )}
                        </Box>
                        {feedback.notes && !compact && (
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              display: 'block',
                            }}
                          >
                            {feedback.notes}
                          </Typography>
                        )}
                      </Box>
                    ))}
                    {!compact && candidate.recruiter_feedback.length > 2 && (
                      <Typography variant="caption" color="text.secondary">
                        +{candidate.recruiter_feedback.length - 2} more
                      </Typography>
                    )}
                  </Box>
                </Box>
              )}

              {/* Tags */}
              {candidate.tags && candidate.tags.length > 0 && !compact && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                  {candidate.tags.slice(0, 3).map((tag) => (
                    <Chip
                      key={tag}
                      label={tag}
                      size="small"
                      sx={{
                        height: 20,
                        fontSize: '0.65rem',
                        bgcolor: alpha(theme.palette.grey[500], 0.1),
                      }}
                    />
                  ))}
                  {candidate.tags.length > 3 && (
                    <Chip
                      label={`+${candidate.tags.length - 3}`}
                      size="small"
                      sx={{ height: 20, fontSize: '0.65rem' }}
                    />
                  )}
                </Box>
              )}

              {/* Swipe Hint (when swipe is enabled) */}
              {swipeEnabled && !onClick && (leftAction || rightAction) && (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 2,
                    mt: 1.5,
                    pt: 1,
                    borderTop: `1px solid ${theme.palette.divider}`,
                  }}
                >
                  {leftAction && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <CancelIcon sx={{ fontSize: 14 }} />
                      Swipe left to reject
                    </Typography>
                  )}
                  {rightAction && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <CheckCircleIcon sx={{ fontSize: 14 }} />
                      Swipe right to approve
                    </Typography>
                  )}
                </Box>
              )}

              {/* Tap to View Hint (when onClick is enabled) */}
              {onClick && (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mt: 1.5,
                    pt: 1,
                    borderTop: `1px solid ${theme.palette.divider}`,
                  }}
                >
                  <Typography variant="caption" color="primary">
                    Tap to view details
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default MobileReviewCard;

// Re-export types for convenience
export type { ReviewQueueCandidate } from '../api/hiringManager';
