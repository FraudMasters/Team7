import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  CircularProgress,
  Alert,
  AlertTitle,
  Divider,
  Avatar,
  Card,
  CardContent,
  IconButton,
  Chip,
  Popper,
  Paper as PopperPaper,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ClickAwayListener,
} from '@mui/material';
import {
  Send as SendIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
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
  TeamCommentCreate,
  TeamCommentUpdate,
  ApiError,
} from '@/types/api';

/**
 * Team member for mention autocomplete
 */
interface TeamMember {
  id: string;
  name: string;
}

/**
 * TeamComments Component Props
 */
interface TeamCommentsProps {
  /** Resume ID for the candidate */
  resumeId: string;
  /** Author ID (current user) for creating comments */
  authorId: string;
  /** Whether the component is read-only (no add/edit/delete) */
  readOnly?: boolean;
  /** Callback when comments change */
  onCommentsChange?: (comments: TeamCommentResponse[]) => void;
  /** Maximum number of top-level comments to display (0 = unlimited) */
  maxComments?: number;
  /** Show resolved comments */
  showResolved?: boolean;
  /** Enable threaded replies */
  enableReplies?: boolean;
  /** List of team members available for @mentions (optional - will extract from comments if not provided) */
  teamMembers?: TeamMember[];
}

/**
 * TeamComments Component
 *
 * Displays threaded team comments and discussions:
 * - Shows list of top-level comments with author and timestamp
 * - Allows adding new top-level comments
 * - Supports threaded replies to comments
 * - Allows editing comments (within 5 minutes)
 * - Supports deleting comments (by author)
 * - Comments can be marked as resolved
 * - Displays author information with avatars
 * - Handles loading and error states gracefully
 *
 * @example
 * ```tsx
 * <TeamComments
 *   resumeId="resume-uuid"
 *   authorId="recruiter-uuid"
 *   onCommentsChange={(comments) => console.log('Comments updated:', comments)}
 * />
 *
 * <TeamComments
 *   resumeId="resume-uuid"
 *   authorId="recruiter-uuid"
 *   readOnly
 *   maxComments={5}
 * />
 * ```
 */
const TeamComments: React.FC<TeamCommentsProps> = ({
  resumeId,
  authorId,
  readOnly = false,
  onCommentsChange,
  maxComments = 0,
  showResolved = true,
  enableReplies = true,
  teamMembers: propTeamMembers,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [comments, setComments] = useState<TeamCommentResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [expandedReplies, setExpandedReplies] = useState<Set<string>>(new Set());

  // New comment form state
  const [newCommentContent, setNewCommentContent] = useState('');
  const [replyToContent, setReplyToContent] = useState<Record<string, string>>({});
  const [editContent, setEditContent] = useState<Record<string, string>>({});

  // Mention autocomplete state
  const [mentionAnchorEl, setMentionAnchorEl] = useState<HTMLElement | null>(null);
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionIndex, setMentionIndex] = useState(0);
  const [activeTextField, setActiveTextField] = useState<'new' | 'reply' | 'edit' | null>(null);
  const [activeCommentId, setActiveCommentId] = useState<string | null>(null);
  const mentionCursorPos = useRef<number>(0);
  const mainTextFieldRef = useRef<HTMLInputElement>(null);

  /**
   * Fetch comments for this candidate
   */
  const fetchComments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await teamCommentsClient.listComments(resumeId);

      // Filter comments based on showResolved setting
      let filteredComments = response.comments;
      if (!showResolved) {
        filteredComments = filteredComments.filter((c) => !c.is_resolved);
      }

      // Sort comments by created_at descending (newest first)
      const sortedComments = filteredComments.sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );

      setComments(sortedComments);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load comments. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [resumeId, showResolved]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  /**
   * Notify parent when comments change
   */
  useEffect(() => {
    onCommentsChange?.(comments);
  }, [comments, onCommentsChange]);

  /**
   * Check if comment can be edited (within 5 minutes)
   */
  const canEditComment = useCallback((comment: TeamCommentResponse): boolean => {
    const now = new Date();
    const createdAt = new Date(comment.created_at);
    const diffMs = now.getTime() - createdAt.getTime();
    const diffMins = diffMs / 60000;
    return diffMins <= 5 && comment.author_id === authorId;
  }, [authorId]);

  /**
   * Handle adding a new top-level comment
   */
  const handleAddComment = useCallback(async () => {
    if (!newCommentContent.trim()) {
      setError('Comment content cannot be empty.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const commentData: TeamCommentCreate = {
        resume_id: resumeId,
        author_id: authorId,
        content: newCommentContent.trim(),
        is_resolved: false,
      };

      await teamCommentsClient.createComment(commentData);

      // Refresh comments
      await fetchComments();

      // Reset form
      setNewCommentContent('');

      setSuccessMessage('Comment added successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to add comment. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [resumeId, authorId, newCommentContent, fetchComments]);

  /**
   * Handle adding a reply to a comment
   */
  const handleAddReply = useCallback(
    async (parentCommentId: string) => {
      const replyContent = replyToContent[parentCommentId];
      if (!replyContent?.trim()) {
        setError('Reply content cannot be empty.');
        return;
      }

      try {
        setSubmitting(parentCommentId);
        setError(null);

        const commentData: TeamCommentCreate = {
          resume_id: resumeId,
          author_id: authorId,
          parent_comment_id: parentCommentId,
          content: replyContent.trim(),
          is_resolved: false,
        };

        await teamCommentsClient.createComment(commentData);

        // Refresh comments
        await fetchComments();

        // Clear reply content for this parent
        setReplyToContent((prev) => ({ ...prev, [parentCommentId]: '' }));

        setSuccessMessage('Reply added successfully.');
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to add reply. Please try again.');
      } finally {
        setSubmitting(false);
      }
    },
    [resumeId, authorId, replyToContent, fetchComments]
  );

  /**
   * Handle editing a comment
   */
  const handleEditComment = useCallback(
    async (commentId: string) => {
      const content = editContent[commentId];
      if (!content?.trim()) {
        setError('Comment content cannot be empty.');
        return;
      }

      try {
        setEditing(commentId);
        setError(null);

        const updateData: TeamCommentUpdate = {
          content: content.trim(),
        };

        await teamCommentsClient.updateComment(commentId, updateData);

        // Refresh comments
        await fetchComments();

        // Clear edit content
        setEditContent((prev) => {
          const newState = { ...prev };
          delete newState[commentId];
          return newState;
        });

        setSuccessMessage('Comment updated successfully.');
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to update comment. Please try again.');
      } finally {
        setEditing(null);
      }
    },
    [editContent, fetchComments]
  );

  /**
   * Handle deleting a comment
   */
  const handleDeleteComment = useCallback(
    async (commentId: string) => {
      try {
        setDeleting(commentId);
        setError(null);

        await teamCommentsClient.deleteComment(commentId);

        // Refresh comments
        await fetchComments();

        setSuccessMessage('Comment deleted successfully.');
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to delete comment. Please try again.');
      } finally {
        setDeleting(null);
      }
    },
    [fetchComments]
  );

  /**
   * Handle toggling resolved status
   */
  const handleToggleResolved = useCallback(
    async (commentId: string, currentStatus: boolean) => {
      try {
        setEditing(commentId);
        setError(null);

        const updateData: TeamCommentUpdate = {
          is_resolved: !currentStatus,
        };

        await teamCommentsClient.updateComment(commentId, updateData);

        // Refresh comments
        await fetchComments();

        setSuccessMessage(!currentStatus ? 'Comment marked as resolved.' : 'Comment marked as unresolved.');
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to update comment. Please try again.');
      } finally {
        setEditing(null);
      }
    },
    [fetchComments]
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
   * Get replies for a comment
   */
  const getRepliesForComment = useCallback(
    (parentCommentId: string): TeamCommentResponse[] => {
      return comments.filter((c) => c.parent_comment_id === parentCommentId);
    },
    [comments]
  );

  /**
   * Toggle replies visibility
   */
  const toggleReplies = useCallback((commentId: string) => {
    setExpandedReplies((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(commentId)) {
        newSet.delete(commentId);
      } else {
        newSet.add(commentId);
      }
      return newSet;
    });
  }, []);

  /**
   * Get top-level comments (apply maxComments limit if set)
   */
  const topLevelComments = comments.filter((c) => !c.parent_comment_id);
  const displayedComments = maxComments > 0 ? topLevelComments.slice(0, maxComments) : topLevelComments;

  /**
   * Extract unique team members from comments
   */
  const extractTeamMembersFromComments = useCallback((): TeamMember[] => {
    const uniqueMembers = new Map<string, string>();
    comments.forEach((comment) => {
      const authorId = comment.author_id;
      if (authorId && !uniqueMembers.has(authorId)) {
        const name = getAuthorName(authorId);
        uniqueMembers.set(authorId, name);
      }
    });
    return Array.from(uniqueMembers.entries()).map(([id, name]) => ({ id, name }));
  }, [comments, getAuthorName]);

  /**
   * Get team members (use props or extract from comments)
   */
  const availableTeamMembers = propTeamMembers || extractTeamMembersFromComments();

  /**
   * Filter team members based on mention query
   */
  const filteredMembers = availableTeamMembers.filter(
    (member) =>
      member.name.toLowerCase().includes(mentionQuery.toLowerCase()) ||
      member.id.toLowerCase().includes(mentionQuery.toLowerCase())
  );

  /**
   * Handle text input change with mention detection
   */
  const handleTextInputChange = useCallback(
    (
      value: string,
      fieldType: 'new' | 'reply' | 'edit',
      commentId: string | null,
      setter: (value: string) => void,
      event?: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
    ) => {
      setter(value);

      if (!event || !event.target) {
        setMentionAnchorEl(null);
        return;
      }

      const input = event.target as HTMLInputElement;
      const cursorPosition = input.selectionStart || 0;

      // Find the @ symbol before cursor
      const textBeforeCursor = value.substring(0, cursorPosition);
      const atMatch = textBeforeCursor.match(/@(\w*)$/);

      if (atMatch) {
        const query = atMatch[1];
        setMentionQuery(query);
        setMentionIndex(0);
        setActiveTextField(fieldType);
        setActiveCommentId(commentId);
        mentionCursorPos.current = cursorPosition - atMatch[0].length;

        // Set anchor element to the input field
        if (input && input.parentElement) {
          setMentionAnchorEl(input.parentElement);
        }
      } else {
        setMentionAnchorEl(null);
        setMentionQuery('');
      }
    },
    []
  );

  /**
   * Insert selected mention into text
   */
  const insertMention = useCallback(
    (member: TeamMember) => {
      const mention = `@${member.id}`;
      let setter: (value: string) => void;
      let currentValue: string;

      if (activeTextField === 'new') {
        setter = setNewCommentContent;
        currentValue = newCommentContent;
      } else if (activeTextField === 'reply' && activeCommentId) {
        setter = (value) => setReplyToContent((prev) => ({ ...prev, [activeCommentId]: value }));
        currentValue = replyToContent[activeCommentId] || '';
      } else if (activeTextField === 'edit' && activeCommentId) {
        setter = (value) => setEditContent((prev) => ({ ...prev, [activeCommentId]: value }));
        currentValue = editContent[activeCommentId] || '';
      } else {
        return;
      }

      // Insert the mention at the cursor position
      const before = currentValue.substring(0, mentionCursorPos.current);
      const after = currentValue.substring(mentionCursorPos.current + mentionQuery.length + 1);
      const newValue = before + mention + ' ' + after;

      setter(newValue);
      setMentionAnchorEl(null);
      setMentionQuery('');
      setMentionIndex(0);

      // Focus back to the input field
      setTimeout(() => {
        if (activeTextField === 'new' && mainTextFieldRef.current) {
          mainTextFieldRef.current.focus();
        }
      }, 0);
    },
    [
      activeTextField,
      activeCommentId,
      newCommentContent,
      replyToContent,
      editContent,
      mentionQuery,
      mentionCursorPos,
    ]
  );

  /**
   * Handle mention keydown (arrow keys and enter)
   */
  const handleMentionKeyDown = useCallback(
    (event: React.KeyboardEvent, fieldType: 'new' | 'reply' | 'edit', commentId: string | null) => {
      if (!mentionAnchorEl || filteredMembers.length === 0) {
        return;
      }

      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setMentionIndex((prev) => (prev + 1) % filteredMembers.length);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setMentionIndex((prev) => (prev - 1 + filteredMembers.length) % filteredMembers.length);
      } else if (event.key === 'Enter') {
        event.preventDefault();
        insertMention(filteredMembers[mentionIndex]);
      } else if (event.key === 'Escape') {
        event.preventDefault();
        setMentionAnchorEl(null);
        setMentionQuery('');
        setMentionIndex(0);
      }
    },
    [mentionAnchorEl, filteredMembers, mentionIndex, insertMention]
  );

  /**
   * Render a single comment
   */
  const renderComment = useCallback(
    (comment: TeamCommentResponse, isReply = false, depth = 0) => {
      const replies = getRepliesForComment(comment.id);
      const showReplies = expandedReplies.has(comment.id);
      const isEditing = editing === comment.id;
      const canEdit = canEditComment(comment);
      const isSubmitting = submitting === comment.id;

      return (
        <Card
          key={comment.id}
          variant="outlined"
          sx={{
            opacity: deleting === comment.id ? 0.5 : 1,
            transition: 'opacity 0.2s',
            ml: isReply ? depth * 2 : 0,
            backgroundColor: comment.is_resolved ? 'action.disabledBackground' : 'background.paper',
          }}
        >
          <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
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
                {getAuthorInitials(getAuthorName(comment.author_id))}
              </Avatar>

              {/* Comment Content */}
              <Box sx={{ flex: 1, minWidth: 0 }}>
                {/* Comment Header */}
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    mb: 0.5,
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle2" fontWeight={600}>
                      {getAuthorName(comment.author_id)}
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
                        (edited {comment.edits_count > 1 ? `${comment.edits_count} times` : 'once'})
                      </Typography>
                    )}
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      {formatTimestamp(comment.created_at)}
                    </Typography>
                    {!readOnly && comment.author_id === authorId && (
                      <>
                        {canEdit && !isEditing && (
                          <IconButton
                            size="small"
                            onClick={() => setEditContent((prev) => ({ ...prev, [comment.id]: comment.content }))}
                            sx={{ ml: 0.5 }}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        )}
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteComment(comment.id)}
                          disabled={deleting === comment.id}
                          sx={{ ml: 0.5 }}
                        >
                          {deleting === comment.id ? (
                            <CircularProgress size={16} />
                          ) : (
                            <DeleteIcon fontSize="small" />
                          )}
                        </IconButton>
                      </>
                    )}
                  </Box>
                </Box>

                {/* Comment Text or Edit Form */}
                {isEditing && editContent[comment.id] !== undefined ? (
                  <Stack spacing={1}>
                    <ClickAwayListener onClickAway={() => activeTextField === 'edit' && activeCommentId === comment.id && mentionAnchorEl && setMentionAnchorEl(null)}>
                      <Box>
                        <TextField
                          multiline
                          rows={2}
                          placeholder="Edit your comment... Use @ to mention team members"
                          value={editContent[comment.id]}
                          onChange={(e) =>
                            handleTextInputChange(
                              e.target.value,
                              'edit',
                              comment.id,
                              (value) => setEditContent((prev) => ({ ...prev, [comment.id]: value })),
                              e
                            )
                          }
                          onKeyDown={(e) => handleMentionKeyDown(e, 'edit', comment.id)}
                          disabled={isSubmitting}
                          fullWidth
                          size="small"
                        />

                        {/* Mention Autocomplete Popper for Edit */}
                        {mentionAnchorEl && filteredMembers.length > 0 && activeTextField === 'edit' && activeCommentId === comment.id && (
                          <Popper
                            open={Boolean(mentionAnchorEl)}
                            anchorEl={mentionAnchorEl}
                            placement="bottom-start"
                            style={{ zIndex: 1300 }}
                          >
                            <PopperPaper
                              elevation={3}
                              sx={{
                                mt: 1,
                                maxHeight: 200,
                                overflow: 'auto',
                              }}
                            >
                              <List dense>
                                {filteredMembers.map((member, index) => (
                                  <ListItem
                                    key={member.id}
                                    button
                                    selected={index === mentionIndex}
                                    onClick={() => insertMention(member)}
                                    sx={{
                                      backgroundColor: index === mentionIndex ? 'action.selected' : 'inherit',
                                    }}
                                  >
                                    <ListItemAvatar>
                                      <Avatar
                                        sx={{
                                          width: 32,
                                          height: 32,
                                          bgcolor: 'primary.main',
                                          fontSize: '0.75rem',
                                        }}
                                      >
                                        {getAuthorInitials(member.name)}
                                      </Avatar>
                                    </ListItemAvatar>
                                    <ListItemText
                                      primary={member.name}
                                      secondary={member.id}
                                      primaryTypographyProps={{
                                        variant: 'body2',
                                        fontWeight: index === mentionIndex ? 600 : 400,
                                      }}
                                      secondaryTypographyProps={{
                                        variant: 'caption',
                                      }}
                                    />
                                  </ListItem>
                                ))}
                              </List>
                            </PopperPaper>
                          </Popper>
                        )}
                      </Box>
                    </ClickAwayListener>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button
                        variant="contained"
                        size="small"
                        onClick={() => handleEditComment(comment.id)}
                        disabled={!editContent[comment.id].trim() || isSubmitting}
                      >
                        Save
                      </Button>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => {
                          setEditContent((prev) => {
                            const newState = { ...prev };
                            delete newState[comment.id];
                            return newState;
                          });
                          setEditing(null);
                        }}
                        disabled={isSubmitting}
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
                {!isEditing && (
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      mt: 1,
                    }}
                  >
                    {enableReplies && !isReply && !readOnly && replies.length > 0 && (
                      <Button
                        size="small"
                        startIcon={showReplies ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        onClick={() => toggleReplies(comment.id)}
                      >
                        {showReplies ? 'Hide' : 'Show'} {replies.length} {replies.length === 1 ? 'reply' : 'replies'}
                      </Button>
                    )}
                    {enableReplies && !readOnly && (
                      <Button
                        size="small"
                        startIcon={<ReplyIcon />}
                        onClick={() => {
                          if (!replyToContent[comment.id]) {
                            setReplyToContent((prev) => ({ ...prev, [comment.id]: '' }));
                          }
                        }}
                      >
                        Reply
                      </Button>
                    )}
                    {!readOnly && comment.author_id === authorId && !comment.is_resolved && (
                      <Button
                        size="small"
                        startIcon={<MarkEmailReadIcon />}
                        onClick={() => handleToggleResolved(comment.id, comment.is_resolved)}
                        disabled={editing === comment.id}
                      >
                        Resolve
                      </Button>
                    )}
                    {!readOnly && comment.author_id === authorId && comment.is_resolved && (
                      <Button
                        size="small"
                        onClick={() => handleToggleResolved(comment.id, comment.is_resolved)}
                        disabled={editing === comment.id}
                      >
                        Reopen
                      </Button>
                    )}
                  </Box>
                )}

                {/* Reply Form */}
                {enableReplies && !readOnly && replyToContent[comment.id] !== undefined && (
                  <Box sx={{ mt: 1.5 }}>
                    <ClickAwayListener onClickAway={() => activeTextField === 'reply' && activeCommentId === comment.id && mentionAnchorEl && setMentionAnchorEl(null)}>
                      <Box>
                        <TextField
                          multiline
                          rows={2}
                          placeholder="Write a reply... Use @ to mention team members"
                          value={replyToContent[comment.id]}
                          onChange={(e) =>
                            handleTextInputChange(
                              e.target.value,
                              'reply',
                              comment.id,
                              (value) => setReplyToContent((prev) => ({ ...prev, [comment.id]: value })),
                              e
                            )
                          }
                          onKeyDown={(e) => handleMentionKeyDown(e, 'reply', comment.id)}
                          disabled={isSubmitting}
                          fullWidth
                          size="small"
                          sx={{ mb: 1 }}
                        />

                        {/* Mention Autocomplete Popper for Reply */}
                        {mentionAnchorEl && filteredMembers.length > 0 && activeTextField === 'reply' && activeCommentId === comment.id && (
                          <Popper
                            open={Boolean(mentionAnchorEl)}
                            anchorEl={mentionAnchorEl}
                            placement="bottom-start"
                            style={{ zIndex: 1300 }}
                          >
                            <PopperPaper
                              elevation={3}
                              sx={{
                                mt: 1,
                                maxHeight: 200,
                                overflow: 'auto',
                              }}
                            >
                              <List dense>
                                {filteredMembers.map((member, index) => (
                                  <ListItem
                                    key={member.id}
                                    button
                                    selected={index === mentionIndex}
                                    onClick={() => insertMention(member)}
                                    sx={{
                                      backgroundColor: index === mentionIndex ? 'action.selected' : 'inherit',
                                    }}
                                  >
                                    <ListItemAvatar>
                                      <Avatar
                                        sx={{
                                          width: 32,
                                          height: 32,
                                          bgcolor: 'primary.main',
                                          fontSize: '0.75rem',
                                        }}
                                      >
                                        {getAuthorInitials(member.name)}
                                      </Avatar>
                                    </ListItemAvatar>
                                    <ListItemText
                                      primary={member.name}
                                      secondary={member.id}
                                      primaryTypographyProps={{
                                        variant: 'body2',
                                        fontWeight: index === mentionIndex ? 600 : 400,
                                      }}
                                      secondaryTypographyProps={{
                                        variant: 'caption',
                                      }}
                                    />
                                  </ListItem>
                                ))}
                              </List>
                            </PopperPaper>
                          </Popper>
                        )}
                      </Box>
                    </ClickAwayListener>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button
                        variant="contained"
                        size="small"
                        startIcon={isSubmitting ? <CircularProgress size={16} /> : <SendIcon />}
                        onClick={() => handleAddReply(comment.id)}
                        disabled={!replyToContent[comment.id].trim() || isSubmitting}
                      >
                        Reply
                      </Button>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => {
                          setReplyToContent((prev) => {
                            const newState = { ...prev };
                            delete newState[comment.id];
                            return newState;
                          });
                        }}
                        disabled={isSubmitting}
                      >
                        Cancel
                      </Button>
                    </Box>
                  </Box>
                )}
              </Box>
            </Box>
          </CardContent>

          {/* Nested Replies */}
          {enableReplies && !isReply && replies.length > 0 && showReplies && (
            <Box sx={{ px: 2, pb: 2 }}>
              <Stack spacing={1.5}>
                {replies.map((reply) => renderComment(reply, true, depth + 1))}
              </Stack>
            </Box>
          )}
        </Card>
      );
    },
    [
      comments,
      deleting,
      editing,
      submitting,
      expandedReplies,
      editContent,
      replyToContent,
      getRepliesForComment,
      canEditComment,
      getAuthorName,
      getAuthorInitials,
      formatTimestamp,
      toggleReplies,
      handleEditComment,
      handleDeleteComment,
      handleAddReply,
      handleToggleResolved,
      readOnly,
      enableReplies,
      authorId,
      handleTextInputChange,
      handleMentionKeyDown,
      mentionAnchorEl,
      filteredMembers,
      mentionIndex,
      activeTextField,
      activeCommentId,
      insertMention,
    ]
  );

  if (loading) {
    return (
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
          Loading comments...
        </Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={2}>
      {/* Error Message */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Message */}
      {successMessage && (
        <Alert
          severity="success"
          icon={<CheckCircleIcon fontSize="inherit" />}
          onClose={() => setSuccessMessage(null)}
        >
          {successMessage}
        </Alert>
      )}

      {/* Comments List */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            Team Discussion
          </Typography>
          <Chip
            label={comments.length}
            size="small"
            sx={{ ml: 1 }}
            color={comments.length > 0 ? 'primary' : 'default'}
          />
        </Box>

        {topLevelComments.length === 0 ? (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No comments yet. Start the discussion!
            </Typography>
          </Box>
        ) : (
          <Stack spacing={2}>
            {displayedComments.map((comment) => renderComment(comment))}

            {/* Show more indicator */}
            {maxComments > 0 && topLevelComments.length > maxComments && (
              <Box sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Showing {displayedComments.length} of {topLevelComments.length} comments
                </Typography>
              </Box>
            )}
          </Stack>
        )}
      </Paper>

      {/* Add Comment Form */}
      {!readOnly && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Add a Comment
          </Typography>
          <Stack spacing={1.5}>
            <ClickAwayListener onClickAway={() => mentionAnchorEl && setMentionAnchorEl(null)}>
              <Box>
                <TextField
                  inputRef={mainTextFieldRef}
                  multiline
                  rows={3}
                  placeholder="Share your thoughts about this candidate... Use @ to mention team members"
                  value={newCommentContent}
                  onChange={(e) => handleTextInputChange(e.target.value, 'new', null, setNewCommentContent, e)}
                  onKeyDown={(e) => handleMentionKeyDown(e, 'new', null)}
                  disabled={submitting}
                  fullWidth
                  size="small"
                />

                {/* Mention Autocomplete Popper */}
                {mentionAnchorEl && filteredMembers.length > 0 && activeTextField === 'new' && (
                  <Popper
                    open={Boolean(mentionAnchorEl)}
                    anchorEl={mentionAnchorEl}
                    placement="bottom-start"
                    style={{ zIndex: 1300 }}
                  >
                    <PopperPaper
                      elevation={3}
                      sx={{
                        mt: 1,
                        maxHeight: 200,
                        overflow: 'auto',
                      }}
                    >
                      <List dense>
                        {filteredMembers.map((member, index) => (
                          <ListItem
                            key={member.id}
                            button
                            selected={index === mentionIndex}
                            onClick={() => insertMention(member)}
                            sx={{
                              backgroundColor: index === mentionIndex ? 'action.selected' : 'inherit',
                            }}
                          >
                            <ListItemAvatar>
                              <Avatar
                                sx={{
                                  width: 32,
                                  height: 32,
                                  bgcolor: 'primary.main',
                                  fontSize: '0.75rem',
                                }}
                              >
                                {getAuthorInitials(member.name)}
                              </Avatar>
                            </ListItemAvatar>
                            <ListItemText
                              primary={member.name}
                              secondary={member.id}
                              primaryTypographyProps={{
                                variant: 'body2',
                                fontWeight: index === mentionIndex ? 600 : 400,
                              }}
                              secondaryTypographyProps={{
                                variant: 'caption',
                              }}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </PopperPaper>
                  </Popper>
                )}
              </Box>
            </ClickAwayListener>

            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                size="small"
                startIcon={submitting ? <CircularProgress size={16} /> : <SendIcon />}
                onClick={handleAddComment}
                disabled={!newCommentContent.trim() || submitting}
              >
                Post Comment
              </Button>
            </Box>

            <Typography variant="caption" color="text.secondary">
              Comments can be edited within 5 minutes of posting. Use @mentions to notify team members.
            </Typography>
          </Stack>
        </Paper>
      )}
    </Stack>
  );
};

export default TeamComments;
