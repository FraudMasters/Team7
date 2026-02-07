import React, { useCallback, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Avatar,
  IconButton,
  Button,
  Stack,
  TextField,
  Chip,
  CircularProgress,
  Collapse,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Reply as ReplyIcon,
  CheckCircle as CheckCircleIcon,
  MarkEmailRead as MarkEmailReadIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { teamCommentsClient } from '@/api/teamComments';
import type {
  TeamCommentResponse,
  TeamCommentUpdate,
  ApiError,
} from '@/types/api';

/**
 * CommentThread Component Props
 */
interface CommentThreadProps {
  /** The comment to display */
  comment: TeamCommentResponse;
  /** Nested replies to this comment */
  replies?: TeamCommentResponse[];
  /** Current user ID */
  currentUserId: string;
  /** Depth level for nested comments (0 = top-level) */
  depth?: number;
  /** Whether the component is read-only */
  readOnly?: boolean;
  /** Whether replies are enabled */
  enableReplies?: boolean;
  /** Callback when a comment is updated */
  onCommentUpdate?: () => void;
  /** Callback when a comment is deleted */
  onCommentDelete?: () => void;
  /** Callback when a reply is added */
  onReplyAdd?: () => void;
}

/**
 * CommentThread Component
 *
 * Displays a single comment with nested replies:
 * - Shows comment with author, avatar, and timestamp
 * - Supports threaded/nested replies
 * - Allows editing comments (within 5 minutes by author)
 * - Supports deleting comments (by author)
 * - Comments can be marked as resolved
 * - Handles loading and error states gracefully
 * - Recursively renders nested replies
 *
 * @example
 * ```tsx
 * <CommentThread
 *   comment={commentData}
 *   replies={repliesData}
 *   currentUserId="user-123"
 *   onCommentUpdate={handleUpdate}
 *   onCommentDelete={handleDelete}
 * />
 *
 * <CommentThread
 *   comment={commentData}
 *   replies={repliesData}
 *   currentUserId="user-123"
 *   readOnly
 *   depth={1}
 * />
 * ```
 */
const CommentThread: React.FC<CommentThreadProps> = ({
  comment,
  replies = [],
  currentUserId,
  depth = 0,
  readOnly = false,
  enableReplies = true,
  onCommentUpdate,
  onCommentDelete,
  onReplyAdd,
}) => {
  const { t } = useTranslation();
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const [replying, setReplying] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [showReplies, setShowReplies] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
   * Check if comment can be edited (within 5 minutes by author)
   */
  const canEdit = useCallback((): boolean => {
    const now = new Date();
    const createdAt = new Date(comment.created_at);
    const diffMs = now.getTime() - createdAt.getTime();
    const diffMins = diffMs / 60000;
    return diffMins <= 5 && comment.author_id === currentUserId;
  }, [comment.created_at, comment.author_id, currentUserId]);

  /**
   * Check if user can delete this comment (by author)
   */
  const canDelete = useCallback((): boolean => {
    return comment.author_id === currentUserId;
  }, [comment.author_id, currentUserId]);

  /**
   * Get author display name from author_id
   */
  const getAuthorName = useCallback((authorId: string): string => {
    if (!authorId) return 'Unknown';
    // Extract username from email or use ID
    if (authorId.includes('@')) {
      return authorId.split('@')[0];
    }
    return authorId;
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
   * Handle saving edited comment
   */
  const handleSaveEdit = useCallback(async () => {
    if (!editContent.trim()) {
      setError('Comment content cannot be empty.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const updateData: TeamCommentUpdate = {
        content: editContent.trim(),
      };

      await teamCommentsClient.updateComment(comment.id, updateData);

      setEditing(false);
      onCommentUpdate?.();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to update comment. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [comment.id, editContent, onCommentUpdate]);

  /**
   * Handle canceling edit
   */
  const handleCancelEdit = useCallback(() => {
    setEditContent(comment.content);
    setEditing(false);
    setError(null);
  }, [comment.content]);

  /**
   * Handle deleting comment
   */
  const handleDelete = useCallback(async () => {
    try {
      setDeleting(true);
      setError(null);

      await teamCommentsClient.deleteComment(comment.id);

      onCommentDelete?.();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to delete comment. Please try again.');
    } finally {
      setDeleting(false);
    }
  }, [comment.id, onCommentDelete]);

  /**
   * Handle toggling resolved status
   */
  const handleToggleResolved = useCallback(async () => {
    try {
      setSubmitting(true);
      setError(null);

      const updateData: TeamCommentUpdate = {
        is_resolved: !comment.is_resolved,
      };

      await teamCommentsClient.updateComment(comment.id, updateData);

      onCommentUpdate?.();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to update comment. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [comment.id, comment.is_resolved, onCommentUpdate]);

  /**
   * Handle submitting a reply
   */
  const handleSubmitReply = useCallback(async () => {
    if (!replyContent.trim()) {
      setError('Reply content cannot be empty.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      await teamCommentsClient.createComment({
        resume_id: comment.resume_id,
        author_id: currentUserId,
        parent_comment_id: comment.id,
        content: replyContent.trim(),
        is_resolved: false,
      });

      setReplyContent('');
      setReplying(false);
      setShowReplies(true);
      onReplyAdd?.();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to add reply. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [comment, currentUserId, replyContent, onReplyAdd]);

  /**
   * Handle canceling reply
   */
  const handleCancelReply = useCallback(() => {
    setReplyContent('');
    setReplying(false);
    setError(null);
  }, []);

  const authorName = getAuthorName(comment.author_id);
  const hasReplies = replies.length > 0;

  return (
    <Card
      variant="outlined"
      sx={{
        ml: depth > 0 ? `${depth * 2}%` : 0,
        backgroundColor: comment.is_resolved ? 'action.disabledBackground' : 'background.paper',
        borderLeft: depth > 0 ? '2px solid' : '1px solid',
        borderLeftColor: depth > 0 ? 'divider' : 'divider',
      }}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Stack spacing={1.5}>
          {/* Error Message */}
          {error && (
            <Typography variant="caption" color="error" sx={{ mt: 1 }}>
              {error}
            </Typography>
          )}

          <Box sx={{ display: 'flex', gap: 1.5 }}>
            {/* Author Avatar */}
            <Avatar
              sx={{
                width: 36,
                height: 36,
                bgcolor: 'primary.main',
                fontSize: '0.875rem',
              }}
            >
              {getAuthorInitials(authorName)}
            </Avatar>

            {/* Comment Content */}
            <Box sx={{ flex: 1, minWidth: 0 }}>
              {/* Comment Header */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: 1,
                  mb: 0.5,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  <Typography variant="subtitle2" fontWeight={600}>
                    {authorName}
                  </Typography>
                  {comment.is_resolved && (
                    <Chip
                      icon={<CheckCircleIcon fontSize="small" />}
                      label="Resolved"
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  )}
                  {comment.edits_count > 0 && (
                    <Typography variant="caption" color="text.secondary">
                      (edited {comment.edits_count > 1 ? `${comment.edits_count}x` : 'once'})
                    </Typography>
                  )}
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Typography variant="caption" color="text.secondary">
                    {formatTimestamp(comment.created_at)}
                  </Typography>
                  {!readOnly && (
                    <>
                      {canEdit() && !editing && (
                        <IconButton
                          size="small"
                          onClick={() => setEditing(true)}
                          sx={{ ml: 0.5 }}
                          title="Edit comment"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      )}
                      {canDelete() && (
                        <IconButton
                          size="small"
                          onClick={handleDelete}
                          disabled={deleting}
                          sx={{ ml: 0.5 }}
                          title="Delete comment"
                        >
                          {deleting ? <CircularProgress size={16} /> : <DeleteIcon fontSize="small" />}
                        </IconButton>
                      )}
                    </>
                  )}
                </Box>
              </Box>

              {/* Comment Text or Edit Form */}
              {editing ? (
                <Stack spacing={1}>
                  <TextField
                    multiline
                    rows={2}
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    disabled={submitting}
                    fullWidth
                    size="small"
                    placeholder="Edit your comment..."
                  />
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={handleSaveEdit}
                      disabled={!editContent.trim() || submitting}
                    >
                      {submitting ? 'Saving...' : 'Save'}
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={handleCancelEdit}
                      disabled={submitting}
                    >
                      Cancel
                    </Button>
                  </Box>
                </Stack>
              ) : (
                <Typography variant="body2" color="text.primary" sx={{ wordBreak: 'break-word' }}>
                  {comment.content}
                </Typography>
              )}

              {/* Comment Actions */}
              {!editing && !readOnly && (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mt: 1,
                    flexWrap: 'wrap',
                  }}
                >
                  {enableReplies && depth < 5 && (
                    <Button
                      size="small"
                      startIcon={<ReplyIcon />}
                      onClick={() => setReplying(!replying)}
                    >
                      {replying ? 'Cancel' : 'Reply'}
                    </Button>
                  )}
                  {hasReplies && (
                    <Button
                      size="small"
                      startIcon={showReplies ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      onClick={() => setShowReplies(!showReplies)}
                    >
                      {showReplies ? 'Hide' : 'Show'} {replies.length} {replies.length === 1 ? 'reply' : 'replies'}
                    </Button>
                  )}
                  {comment.author_id === currentUserId && (
                    <Button
                      size="small"
                      startIcon={<MarkEmailReadIcon />}
                      onClick={handleToggleResolved}
                      disabled={submitting}
                    >
                      {comment.is_resolved ? 'Reopen' : 'Resolve'}
                    </Button>
                  )}
                </Box>
              )}

              {/* Reply Form */}
              {enableReplies && replying && (
                <Box sx={{ mt: 1.5 }}>
                  <TextField
                    multiline
                    rows={2}
                    placeholder="Write a reply..."
                    value={replyContent}
                    onChange={(e) => setReplyContent(e.target.value)}
                    disabled={submitting}
                    fullWidth
                    size="small"
                    sx={{ mb: 1 }}
                  />
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={handleSubmitReply}
                      disabled={!replyContent.trim() || submitting}
                    >
                      {submitting ? 'Posting...' : 'Post Reply'}
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={handleCancelReply}
                      disabled={submitting}
                    >
                      Cancel
                    </Button>
                  </Box>
                </Box>
              )}
            </Box>
          </Box>
        </Stack>
      </CardContent>

      {/* Nested Replies */}
      <Collapse in={showReplies && hasReplies}>
        <Box sx={{ px: 2, pb: 2 }}>
          <Stack spacing={1.5}>
            {replies.map((reply) => (
              <CommentThread
                key={reply.id}
                comment={reply}
                replies={[]} // Nested replies would need to be passed separately
                currentUserId={currentUserId}
                depth={depth + 1}
                readOnly={readOnly}
                enableReplies={enableReplies}
                onCommentUpdate={onCommentUpdate}
                onCommentDelete={onCommentDelete}
                onReplyAdd={onReplyAdd}
              />
            ))}
          </Stack>
        </Box>
      </Collapse>
    </Card>
  );
};

export default CommentThread;
