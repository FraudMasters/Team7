import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Card,
  CardContent,
  Collapse,
  Chip,
  Divider,
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Delete as DeleteIcon,
  Note as NoteIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

interface ComparisonNotesProps {
  candidateId: string;
  candidateName?: string;
  vacancyId: string;
  onNoteSaved?: (candidateId: string, note: string) => void;
  disabled?: boolean;
  compact?: boolean;
}

interface StoredNotes {
  [candidateId: string]: string;
}

/**
 * ComparisonNotes Component
 *
 * Allows recruiters to add, edit, and delete notes for candidates during comparison.
 * Notes are persisted in localStorage so they survive page refreshes.
 */
const ComparisonNotes: React.FC<ComparisonNotesProps> = ({
  candidateId,
  candidateName,
  vacancyId,
  onNoteSaved,
  disabled = false,
  compact = false,
}) => {
  const { t } = useTranslation();
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [currentNote, setCurrentNote] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const storageKey = `comparison_notes_${vacancyId}`;

  /**
   * Load notes from localStorage on mount
   */
  useEffect(() => {
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        const parsedNotes: StoredNotes = JSON.parse(stored);
        setNotes(parsedNotes);
        if (parsedNotes[candidateId]) {
          setCurrentNote(parsedNotes[candidateId]);
        }
      }
    } catch (err) {
      console.error('Error loading notes from localStorage:', err);
    }
  }, [storageKey, candidateId]);

  /**
   * Get current note for this candidate
   */
  const getNoteForCandidate = (): string => {
    return notes[candidateId] || '';
  };

  /**
   * Handle save note
   */
  const handleSaveNote = async () => {
    setIsSaving(true);
    setError(null);

    try {
      const updatedNotes = {
        ...notes,
        [candidateId]: currentNote.trim(),
      };

      // Save to localStorage
      localStorage.setItem(storageKey, JSON.stringify(updatedNotes));
      setNotes(updatedNotes);

      // Trigger callback
      onNoteSaved?.(candidateId, currentNote.trim());

      // Show success state
      setSaved(true);
      setIsEditing(false);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Error saving note:', err);
      setError(t('notes.saveError') || 'Failed to save note');
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Handle delete note
   */
  const handleDeleteNote = async () => {
    setIsDeleting(true);
    setError(null);

    try {
      const updatedNotes = { ...notes };
      delete updatedNotes[candidateId];

      // Save to localStorage
      localStorage.setItem(storageKey, JSON.stringify(updatedNotes));
      setNotes(updatedNotes);
      setCurrentNote('');

      // Trigger callback
      onNoteSaved?.(candidateId, '');

      // Show success state
      setSaved(true);
      setIsEditing(false);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Error deleting note:', err);
      setError(t('notes.deleteError') || 'Failed to delete note');
    } finally {
      setIsDeleting(false);
    }
  };

  /**
   * Handle cancel edit
   */
  const handleCancelEdit = () => {
    setCurrentNote(getNoteForCandidate());
    setIsEditing(false);
    setError(null);
  };

  /**
   * Handle start edit
   */
  const handleStartEdit = () => {
    setCurrentNote(getNoteForCandidate());
    setIsEditing(true);
    setError(null);
    if (!compact) {
      setExpanded(true);
    }
  };

  /**
   * Check if note exists for this candidate
   */
  const hasNote = (): boolean => {
    return Boolean(getNoteForCandidate());
  };

  /**
   * Get word count
   */
  const getWordCount = (text: string): number => {
    return text.trim().split(/\s+/).filter((word) => word.length > 0).length;
  };

  /**
   * Render success state
   */
  if (saved && !isEditing) {
    return (
      <Paper
        sx={{
          p: 2,
          bgcolor: 'success.50',
          borderLeft: 4,
          borderColor: 'success.main',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CheckIcon color="success" fontSize="small" />
          <Typography variant="body2" color="success.main" fontWeight={600}>
            {t('notes.saved') || 'Note saved'}
          </Typography>
        </Box>
      </Paper>
    );
  }

  /**
   * Compact mode (small button that expands)
   */
  if (compact && !isEditing && !expanded) {
    return (
      <>
        <Tooltip title={hasNote() ? t('notes.editNote') || 'Edit note' : t('notes.addNote') || 'Add note'}>
          <IconButton
            size="small"
            onClick={handleStartEdit}
            disabled={disabled}
            color={hasNote() ? 'primary' : 'default'}
            sx={{
              bgcolor: hasNote() ? 'primary.50' : 'action.hover',
              '&:hover': { bgcolor: hasNote() ? 'primary.100' : 'action.selected' },
            }}
          >
            <NoteIcon fontSize="small" />
          </IconButton>
        </Tooltip>

        {/* Note preview dialog */}
        {expanded && (
          <Card elevation={2} sx={{ mt: 2 }}>
            <CardContent>
              {getEditingContent()}
            </CardContent>
          </Card>
        )}
      </>
    );
  }

  /**
   * Full inline mode
   */
  return (
    <Card
      elevation={1}
      sx={{
        transition: 'all 0.2s',
        '&:hover': { elevation: 2 },
      }}
    >
      <CardContent>
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            mb: (isEditing || expanded) ? 2 : 0,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <NoteIcon color={hasNote() ? 'primary' : 'action'} />
            <Typography variant="subtitle2" fontWeight={600}>
              {t('notes.title') || 'Recruiter Notes'}
            </Typography>
            {hasNote() && !isEditing && (
              <Chip
                label={`${getWordCount(getNoteForCandidate())} ${t('notes.words') || 'words'}`}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
          </Box>

          <Stack direction="row" spacing={1} alignItems="center">
            {!isEditing && (
              <>
                {hasNote() && (
                  <Tooltip title={t('notes.expand') || 'Expand note'}>
                    <IconButton
                      size="small"
                      onClick={() => setExpanded(!expanded)}
                      disabled={disabled}
                    >
                      {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                  </Tooltip>
                )}
                <Tooltip title={hasNote() ? t('notes.editNote') || 'Edit note' : t('notes.addNote') || 'Add note'}>
                  <IconButton
                    size="small"
                    onClick={handleStartEdit}
                    disabled={disabled}
                    color={hasNote() ? 'primary' : 'default'}
                    sx={{
                      bgcolor: hasNote() ? 'primary.50' : 'action.hover',
                      '&:hover': { bgcolor: hasNote() ? 'primary.100' : 'action.selected' },
                    }}
                  >
                    <EditIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </>
            )}
          </Stack>
        </Box>

        {/* Note Display (when not editing) */}
        {!isEditing && hasNote() && (
          <Collapse in={expanded} timeout="auto" unmountOnExit>
            <Divider sx={{ mb: 2 }} />
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-wrap' }}>
                {getNoteForCandidate()}
              </Typography>
              <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  size="small"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={handleDeleteNote}
                  disabled={disabled || isDeleting}
                >
                  {t('notes.delete') || 'Delete'}
                </Button>
              </Box>
            </Box>
          </Collapse>
        )}

        {/* Empty State (when no note and not editing) */}
        {!isEditing && !hasNote() && (
          <Box
            sx={{
              py: 2,
              px: 2,
              bgcolor: 'action.hover',
              borderRadius: 1,
              textAlign: 'center',
              cursor: 'pointer',
              '&:hover': { bgcolor: 'action.selected' },
            }}
            onClick={handleStartEdit}
          >
            <Typography variant="body2" color="text.secondary">
              {t('notes.empty') || 'Click to add a note about this candidate...'}
            </Typography>
          </Box>
        )}

        {/* Editing Mode */}
        {isEditing && getEditingContent()}
      </CardContent>
    </Card>
  );

  /**
   * Get editing content
   */
  function getEditingContent() {
    return (
      <Box>
        <Divider sx={{ mb: 2 }} />
        <Stack spacing={2}>
          {/* Note Input */}
          <Box>
            <Typography variant="subtitle2" gutterBottom fontWeight={600}>
              {t('notes.yourNote') || 'Your Note'}
              <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                ({t('notes.aboutCandidate', { name: candidateName || candidateId }) || `About ${candidateName || candidateId}`})
              </Typography>
            </Typography>
            <TextField
              multiline
              rows={6}
              placeholder={t('notes.placeholder') || 'Add your observations, interview notes, or any comments about this candidate...'}
              value={currentNote}
              onChange={(e) => setCurrentNote(e.target.value)}
              fullWidth
              size="small"
              disabled={isSaving || isDeleting}
              helperText={
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="caption">
                    {getWordCount(currentNote)} {t('notes.words') || 'words'}
                  </Typography>
                </Box>
              }
            />
          </Box>

          {/* Error Display */}
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Actions */}
          <Stack direction="row" spacing={1} justifyContent="flex-end">
            <Button
              onClick={handleCancelEdit}
              disabled={isSaving || isDeleting}
              size="small"
              color="inherit"
              startIcon={<CancelIcon />}
            >
              {t('notes.cancel') || 'Cancel'}
            </Button>
            {hasNote() && !isEditing && (
              <Button
                onClick={handleDeleteNote}
                disabled={isSaving || isDeleting}
                size="small"
                color="error"
                startIcon={isDeleting ? <CircularProgress size={16} /> : <DeleteIcon />}
              >
                {t('notes.delete') || 'Delete'}
              </Button>
            )}
            <Button
              onClick={handleSaveNote}
              disabled={isSaving || isDeleting}
              variant="contained"
              startIcon={isSaving ? <CircularProgress size={16} /> : <SaveIcon />}
              size="small"
              color="primary"
            >
              {t('notes.save') || 'Save Note'}
            </Button>
          </Stack>
        </Stack>
      </Box>
    );
  }
};

export default ComparisonNotes;
