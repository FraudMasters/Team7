import React, { useState, useEffect, useCallback } from 'react';
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
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Send as SendIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
  Lock as LockIcon,
  Public as PublicIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { candidateNotesClient } from '@/api/candidateNotes';
import type {
  CandidateNoteResponse,
  CandidateNoteCreate,
  ApiError,
} from '@/types/api';

/**
 * CandidateNotes Component Props
 */
interface CandidateNotesProps {
  /** Resume ID for the candidate */
  resumeId: string;
  /** Recruiter ID (current user) for creating notes */
  recruiterId?: string;
  /** Whether the component is read-only (no add/edit/delete) */
  readOnly?: boolean;
  /** Callback when notes change */
  onNotesChange?: (notes: CandidateNoteResponse[]) => void;
  /** Maximum number of notes to display (0 = unlimited) */
  maxNotes?: number;
  /** Show private notes indicator */
  showPrivateIndicator?: boolean;
}

/**
 * CandidateNotes Component
 *
 * Displays collaborative candidate notes and comments:
 * - Shows list of notes with author and timestamp
 * - Allows adding new notes with private/team-visible toggle
 * - Supports editing and deleting notes (by author)
 * - Displays author information with avatars
 * - Handles loading and error states gracefully
 *
 * @example
 * ```tsx
 * <CandidateNotes
 *   resumeId="resume-uuid"
 *   recruiterId="recruiter-uuid"
 *   onNotesChange={(notes) => console.log('Notes updated:', notes)}
 * />
 *
 * <CandidateNotes
 *   resumeId="resume-uuid"
 *   recruiterId="recruiter-uuid"
 *   readOnly
 *   maxNotes={5}
 * />
 * ```
 */
const CandidateNotes: React.FC<CandidateNotesProps> = ({
  resumeId,
  recruiterId,
  readOnly = false,
  onNotesChange,
  maxNotes = 0,
  showPrivateIndicator = true,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState<CandidateNoteResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  // New note form state
  const [newNoteContent, setNewNoteContent] = useState('');
  const [newNoteIsPrivate, setNewNoteIsPrivate] = useState(false);

  /**
   * Fetch notes for this candidate
   */
  const fetchNotes = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await candidateNotesClient.listNotes(resumeId);

      // Sort notes by created_at descending (newest first)
      const sortedNotes = response.notes.sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );

      setNotes(sortedNotes);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load notes. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    fetchNotes();
  }, [fetchNotes]);

  /**
   * Notify parent when notes change
   */
  useEffect(() => {
    onNotesChange?.(notes);
  }, [notes, onNotesChange]);

  /**
   * Handle adding a new note
   */
  const handleAddNote = useCallback(async () => {
    if (!newNoteContent.trim()) {
      setError('Note content cannot be empty.');
      return;
    }

    if (!recruiterId) {
      setError('Recruiter ID is required to add notes.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const noteData: CandidateNoteCreate = {
        resume_id: resumeId,
        recruiter_id: recruiterId,
        content: newNoteContent.trim(),
        is_private: newNoteIsPrivate,
      };

      await candidateNotesClient.createNote(noteData);

      // Refresh notes
      await fetchNotes();

      // Reset form
      setNewNoteContent('');
      setNewNoteIsPrivate(false);

      setSuccessMessage('Note added successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to add note. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }, [resumeId, recruiterId, newNoteContent, newNoteIsPrivate, fetchNotes]);

  /**
   * Handle deleting a note
   */
  const handleDeleteNote = useCallback(
    async (noteId: string) => {
      try {
        setDeleting(noteId);
        setError(null);

        await candidateNotesClient.deleteNote(noteId);

        // Refresh notes
        await fetchNotes();

        setSuccessMessage('Note deleted successfully.');
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to delete note. Please try again.');
      } finally {
        setDeleting(null);
      }
    },
    [fetchNotes]
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
   * Get author display name from recruiter_id
   */
  const getAuthorName = useCallback((recruiterId: string | null) => {
    if (!recruiterId) return 'Unknown';
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
   * Display notes (apply maxNotes limit if set)
   */
  const displayedNotes = maxNotes > 0 ? notes.slice(0, maxNotes) : notes;

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
          {t('notes.loading')}
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

      {/* Notes List */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            {t('notes.title')}
          </Typography>
          <Chip
            label={notes.length}
            size="small"
            sx={{ ml: 1 }}
            color={notes.length > 0 ? 'primary' : 'default'}
          />
        </Box>

        {notes.length === 0 ? (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {t('notes.noNotes')}
            </Typography>
          </Box>
        ) : (
          <Stack spacing={2}>
            {displayedNotes.map((note) => (
              <Card
                key={note.id}
                variant="outlined"
                sx={{
                  opacity: deleting === note.id ? 0.5 : 1,
                  transition: 'opacity 0.2s',
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
                      {getAuthorInitials(getAuthorName(note.recruiter_id))}
                    </Avatar>

                    {/* Note Content */}
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      {/* Note Header */}
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
                            {getAuthorName(note.recruiter_id)}
                          </Typography>
                          {showPrivateIndicator && note.is_private && (
                            <Chip
                              icon={<LockIcon fontSize="small" />}
                              label={t('notes.private')}
                              size="small"
                              color="secondary"
                              variant="outlined"
                            />
                          )}
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Typography variant="caption" color="text.secondary">
                            {formatTimestamp(note.created_at)}
                          </Typography>
                          {!readOnly && note.recruiter_id === recruiterId && (
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteNote(note.id)}
                              disabled={deleting === note.id}
                              sx={{ ml: 0.5 }}
                            >
                              {deleting === note.id ? (
                                <CircularProgress size={16} />
                              ) : (
                                <DeleteIcon fontSize="small" />
                              )}
                            </IconButton>
                          )}
                        </Box>
                      </Box>

                      {/* Note Text */}
                      <Typography variant="body2" color="text.primary" sx={{ wordBreak: 'break-word' }}>
                        {note.content}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            ))}

            {/* Show more indicator */}
            {maxNotes > 0 && notes.length > maxNotes && (
              <Box sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {t('notes.showingMore', {
                    shown: displayedNotes.length,
                    total: notes.length,
                  })}
                </Typography>
              </Box>
            )}
          </Stack>
        )}
      </Paper>

      {/* Add Note Form */}
      {!readOnly && recruiterId && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            {t('notes.addNote')}
          </Typography>
          <Stack spacing={1.5}>
            <TextField
              multiline
              rows={3}
              placeholder={t('notes.placeholder')}
              value={newNoteContent}
              onChange={(e) => setNewNoteContent(e.target.value)}
              disabled={submitting}
              fullWidth
              size="small"
            />

            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <FormControlLabel
                control={
                  <Switch
                    checked={newNoteIsPrivate}
                    onChange={(e) => setNewNoteIsPrivate(e.target.checked)}
                    size="small"
                    color="secondary"
                  />
                }
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <LockIcon fontSize="small" />
                    <Typography variant="caption">
                      {t('notes.privateNote')}
                    </Typography>
                  </Box>
                }
              />

              <Button
                variant="contained"
                size="small"
                startIcon={
                  submitting ? <CircularProgress size={16} /> : <SendIcon />
                }
                onClick={handleAddNote}
                disabled={!newNoteContent.trim() || submitting}
              >
                {t('notes.submit')}
              </Button>
            </Box>

            <Typography variant="caption" color="text.secondary">
              {newNoteIsPrivate ? t('notes.privateHint') : t('notes.publicHint')}
            </Typography>
          </Stack>
        </Paper>
      )}
    </Stack>
  );
};

export default CandidateNotes;
