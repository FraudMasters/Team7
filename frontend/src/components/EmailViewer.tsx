import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
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
  Collapse,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Reply as ReplyIcon,
  Forward as ForwardIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  AttachFile as AttachFileIcon,
  Send as SendIcon,
  Close as CloseIcon,
  Email as EmailIcon,
  Person as PersonIcon,
  AccessTime as AccessTimeIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { communicationsClient } from '@/api/communications';
import type {
  CommunicationResponse,
  ApiError,
} from '@/types/api';

/**
 * Email attachment interface
 */
interface EmailAttachment {
  filename: string;
  size?: number;
  content_type?: string;
  url?: string;
}

/**
 * Email thread message interface
 */
interface ThreadMessage {
  communication: CommunicationResponse;
  attachments: EmailAttachment[];
}

/**
 * EmailViewer Component Props
 */
interface EmailViewerProps {
  /** Communication ID of the email to display */
  communicationId: string;
  /** Whether the component is read-only (no reply/forward) */
  readOnly?: boolean;
  /** Callback when reply is sent */
  onReplySent?: (reply: CommunicationResponse) => void;
  /** Callback when forward is sent */
  onForwardSent?: (forward: CommunicationResponse) => void;
  /** Maximum number of thread messages to display (0 = unlimited) */
  maxMessages?: number;
  /** Whether to show full thread by default */
  showThread?: boolean;
}

/**
 * EmailViewer Component
 *
 * Displays email content with thread view, reply/forward actions, and attachment display:
 * - Shows email subject, sender, recipient, and timestamp
 * - Displays email thread (all related messages grouped by thread_id)
 * - Supports reply and forward actions with dialog composers
 * - Shows email attachments with download links
 * - Handles loading and error states gracefully
 * - Collapsible thread view for better UX
 *
 * @example
 * ```tsx
 * <EmailViewer
 *   communicationId="comm-uuid"
 *   onReplySent={(reply) => console.log('Reply sent:', reply)}
 * />
 *
 * <EmailViewer
 *   communicationId="comm-uuid"
 *   readOnly
 *   maxMessages={5}
 *   showThread={false}
 * />
 * ```
 */
const EmailViewer: React.FC<EmailViewerProps> = ({
  communicationId,
  readOnly = false,
  onReplySent,
  onForwardSent,
  maxMessages = 0,
  showThread = true,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState<CommunicationResponse | null>(null);
  const [thread, setThread] = useState<ThreadMessage[]>([]);
  const [threadExpanded, setThreadExpanded] = useState(showThread);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Dialog states
  const [replyDialogOpen, setReplyDialogOpen] = useState(false);
  const [forwardDialogOpen, setForwardDialogOpen] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [forwardContent, setForwardContent] = useState('');
  const [forwardTo, setForwardTo] = useState('');

  /**
   * Fetch email and thread data
   */
  const fetchEmailData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch the email communication
      const response = await communicationsClient.getCommunication(communicationId);
      setEmail(response);

      // If thread_id exists in metadata, fetch all emails in the thread
      const threadId = response.metadata?.thread_id as string | undefined;
      if (threadId) {
        try {
          // Fetch all communications for this candidate
          const listResponse = await communicationsClient.listCommunications({
            candidate_id: response.candidate_id,
            type: 'email',
          });

          // Filter emails that belong to the same thread
          const threadEmails = listResponse.communications.filter(
            (comm) => comm.metadata?.thread_id === threadId
          );

          // Sort by sent_at ascending (oldest first for thread view)
          const sortedThread = threadEmails.sort(
            (a, b) => new Date(a.sent_at || '').getTime() - new Date(b.sent_at || '').getTime()
          );

          // Parse attachments from metadata
          const threadMessages: ThreadMessage[] = sortedThread.map((comm) => ({
            communication: comm,
            attachments: parseAttachments(comm.metadata),
          }));

          setThread(threadMessages);
        } catch (threadErr) {
          // If fetching thread fails, just show the single email
          console.warn('Failed to fetch thread:', threadErr);
          const singleMessage: ThreadMessage = {
            communication: response,
            attachments: parseAttachments(response.metadata),
          };
          setThread([singleMessage]);
        }
      } else {
        // No thread, just show the single email
        const singleMessage: ThreadMessage = {
          communication: response,
          attachments: parseAttachments(response.metadata),
        };
        setThread([singleMessage]);
      }
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load email. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [communicationId]);

  useEffect(() => {
    fetchEmailData();
  }, [fetchEmailData]);

  /**
   * Parse attachments from communication metadata
   */
  const parseAttachments = useCallback((metadata: Record<string, unknown> | null): EmailAttachment[] => {
    if (!metadata?.attachments) return [];
    const attachments = metadata.attachments as EmailAttachment[];
    return Array.isArray(attachments) ? attachments : [];
  }, []);

  /**
   * Format timestamp for display
   */
  const formatTimestamp = useCallback((timestamp: string | null | undefined) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString();
  }, []);

  /**
   * Get sender display name
   */
  const getSenderName = useCallback((comm: CommunicationResponse) => {
    if (comm.metadata?.from_address) {
      return comm.metadata.from_address as string;
    }
    if (comm.recruiter_id) {
      return comm.recruiter_id;
    }
    return 'Unknown Sender';
  }, []);

  /**
   * Get sender initials for avatar
   */
  const getSenderInitials = useCallback((name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  }, []);

  /**
   * Handle reply action
   */
  const handleReply = useCallback(async () => {
    if (!email || !replyContent.trim()) {
      setError('Reply content cannot be empty.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const replyData = {
        candidate_id: email.candidate_id,
        vacancy_id: email.vacancy_id || undefined,
        recruiter_id: email.recruiter_id || undefined,
        type: 'email' as const,
        direction: 'outbound' as const,
        subject: `Re: ${email.subject || ''}`,
        body: replyContent.trim(),
        metadata: {
          in_reply_to: email.id,
          thread_id: email.metadata?.thread_id,
        },
      };

      const reply = await communicationsClient.createCommunication(replyData);

      // Refresh data
      await fetchEmailData();

      // Close dialog and reset form
      setReplyDialogOpen(false);
      setReplyContent('');

      setSuccessMessage('Reply sent successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);

      onReplySent?.(reply);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to send reply. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [email, replyContent, fetchEmailData, onReplySent]);

  /**
   * Handle forward action
   */
  const handleForward = useCallback(async () => {
    if (!email || !forwardContent.trim() || !forwardTo.trim()) {
      setError('Please provide recipient and forward content.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const forwardData = {
        candidate_id: email.candidate_id,
        vacancy_id: email.vacancy_id || undefined,
        recruiter_id: email.recruiter_id || undefined,
        type: 'email' as const,
        direction: 'outbound' as const,
        subject: `Fwd: ${email.subject || ''}`,
        body: forwardContent.trim(),
        metadata: {
          forwarded_from: email.id,
          forward_to: forwardTo,
        },
      };

      const forward = await communicationsClient.createCommunication(forwardData);

      // Close dialog and reset form
      setForwardDialogOpen(false);
      setForwardContent('');
      setForwardTo('');

      setSuccessMessage('Email forwarded successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);

      onForwardSent?.(forward);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to forward email. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [email, forwardContent, forwardTo, onForwardSent]);

  /**
   * Display thread messages (apply maxMessages limit if set)
   */
  const displayedMessages = maxMessages > 0 ? thread.slice(0, maxMessages) : thread;

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
          {t('email.loading')}
        </Typography>
      </Box>
    );
  }

  if (!email) {
    return (
      <Alert severity="error">
        <AlertTitle>Email Not Found</AlertTitle>
        The requested email could not be loaded.
      </Alert>
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
        <Alert severity="success" onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {/* Email Header */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
          <Avatar sx={{ bgcolor: 'primary.main' }}>
            <EmailIcon />
          </Avatar>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              {email.subject || '(No Subject)'}
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <PersonIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  From: {getSenderName(email)}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <AccessTimeIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  {formatTimestamp(email.sent_at)}
                </Typography>
              </Box>
              <Chip
                label={email.direction}
                size="small"
                color={email.direction === 'inbound' ? 'info' : 'success'}
                variant="outlined"
              />
              <Chip
                label={email.status}
                size="small"
                color={
                  email.status === 'sent' || email.status === 'delivered'
                    ? 'success'
                    : email.status === 'failed'
                    ? 'error'
                    : 'default'
                }
                variant="outlined"
              />
            </Box>
          </Box>
        </Box>
      </Paper>

      {/* Thread Toggle (if there are multiple messages) */}
      {thread.length > 1 && (
        <Button
          startIcon={threadExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          onClick={() => setThreadExpanded(!threadExpanded)}
          sx={{ alignSelf: 'flex-start' }}
        >
          {threadExpanded ? 'Hide Thread' : `Show Thread (${thread.length} messages)`}
        </Button>
      )}

      {/* Thread Messages */}
      <Collapse in={threadExpanded}>
        <Stack spacing={2}>
          {displayedMessages.map((threadMsg, index) => (
            <Card
              key={threadMsg.communication.id}
              variant={index === 0 ? 'elevation' : 'outlined'}
              sx={{
                ml: index > 0 ? 4 : 0,
                borderLeft: index > 0 ? '3px solid' : 'none',
                borderLeftColor: 'divider',
              }}
            >
              <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                <Box sx={{ display: 'flex', gap: 1.5 }}>
                  {/* Sender Avatar */}
                  <Avatar
                    sx={{
                      width: 36,
                      height: 36,
                      bgcolor:
                        threadMsg.communication.direction === 'inbound'
                          ? 'info.main'
                          : 'success.main',
                      fontSize: '0.875rem',
                    }}
                  >
                    {getSenderInitials(getSenderName(threadMsg.communication))}
                  </Avatar>

                  {/* Message Content */}
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    {/* Message Header */}
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        mb: 1,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle2" fontWeight={600}>
                          {getSenderName(threadMsg.communication)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {formatTimestamp(threadMsg.communication.sent_at)}
                        </Typography>
                        {index === 0 && (
                          <Chip label="Original" size="small" color="primary" variant="outlined" />
                        )}
                      </Box>
                    </Box>

                    {/* Message Body */}
                    <Typography
                      variant="body2"
                      color="text.primary"
                      sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
                    >
                      {threadMsg.communication.body || '(No content)'}
                    </Typography>

                    {/* Attachments */}
                    {threadMsg.attachments.length > 0 && (
                      <Box sx={{ mt: 1.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                          <AttachFileIcon fontSize="small" color="action" />
                          <Typography variant="caption" color="text.secondary">
                            {threadMsg.attachments.length} Attachment
                            {threadMsg.attachments.length > 1 ? 's' : ''}
                          </Typography>
                        </Box>
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                          {threadMsg.attachments.map((attachment, attIndex) => (
                            <Chip
                              key={attIndex}
                              icon={<AttachFileIcon fontSize="small" />}
                              label={attachment.filename}
                              size="small"
                              variant="outlined"
                              clickable={!!attachment.url}
                              component="a"
                              href={attachment.url}
                              target="_blank"
                              rel="noopener noreferrer"
                            />
                          ))}
                        </Stack>
                      </Box>
                    )}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          ))}

          {/* Show more indicator */}
          {maxMessages > 0 && thread.length > maxMessages && (
            <Box sx={{ textAlign: 'center', py: 1, ml: 4 }}>
              <Typography variant="caption" color="text.secondary">
                {t('email.showingMore', {
                  shown: displayedMessages.length,
                  total: thread.length,
                })}
              </Typography>
            </Box>
          )}
        </Stack>
      </Collapse>

      {/* Action Buttons */}
      {!readOnly && (
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
          <Button
            variant="outlined"
            startIcon={<ReplyIcon />}
            onClick={() => setReplyDialogOpen(true)}
            disabled={!email}
          >
            Reply
          </Button>
          <Button
            variant="outlined"
            startIcon={<ForwardIcon />}
            onClick={() => setForwardDialogOpen(true)}
            disabled={!email}
          >
            Forward
          </Button>
        </Box>
      )}

      {/* Reply Dialog */}
      <Dialog open={replyDialogOpen} onClose={() => setReplyDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Reply to Email</Typography>
            <IconButton onClick={() => setReplyDialogOpen(false)} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <TextField
            multiline
            rows={8}
            placeholder="Type your reply..."
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
            disabled={submitting}
            fullWidth
            autoFocus
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReplyDialogOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            variant="contained"
            startIcon={submitting ? <CircularProgress size={16} /> : <SendIcon />}
            onClick={handleReply}
            disabled={!replyContent.trim() || submitting}
          >
            Send Reply
          </Button>
        </DialogActions>
      </Dialog>

      {/* Forward Dialog */}
      <Dialog open={forwardDialogOpen} onClose={() => setForwardDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Forward Email</Typography>
            <IconButton onClick={() => setForwardDialogOpen(false)} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="To"
              placeholder="recipient@example.com"
              value={forwardTo}
              onChange={(e) => setForwardTo(e.target.value)}
              disabled={submitting}
              fullWidth
            />
            <TextField
              multiline
              rows={6}
              placeholder="Add a message..."
              value={forwardContent}
              onChange={(e) => setForwardContent(e.target.value)}
              disabled={submitting}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setForwardDialogOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            variant="contained"
            startIcon={submitting ? <CircularProgress size={16} /> : <SendIcon />}
            onClick={handleForward}
            disabled={!forwardTo.trim() || !forwardContent.trim() || submitting}
          >
            Forward
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default EmailViewer;
