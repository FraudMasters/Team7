import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  Grid2,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  TextField,
  InputAdornment,
  useTheme,
  useMediaQuery,
  Checkbox,
  Toolbar,
  Tooltip,
  Snackbar,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@/components/ui';
import {
  Person as PersonIcon,
  Search as SearchIcon,
  Close as CloseIcon,
  Work as WorkIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Label as LabelIcon,
  DeleteSweep as DeleteSweepIcon,
  DragIndicator as DragIndicatorIcon,
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import ErrorBoundary from '../components/ErrorBoundary';
import LoadingSpinner from '../components/LoadingSpinner';
import VirtualKanbanBoard from '../components/VirtualKanbanBoard';
import ErrorMessage, { CandidateLoadFailedError, CandidateMoveFailedError, BatchActionFailedError } from '../components/ErrorMessage';
import { useKeyboardNavigation } from '../hooks/useKeyboardNavigation';

interface Candidate {
  id: string;
  filename: string;
  status: string;
  created_at: string;
  skills: string[];
  email?: string;
  phone?: string;
  match_percentage?: number;
  vacancy_title?: string;
}

interface Stage {
  id: string;
  name: string;
  key: string;
}

const STAGES: Stage[] = [
  { id: 'new', name: 'New', key: 'candidatesKanban.stages.new' },
  { id: 'screening', name: 'Screening', key: 'candidatesKanban.stages.screening' },
  { id: 'interview', name: 'Interview', key: 'candidatesKanban.stages.interview' },
  { id: 'offer', name: 'Offer', key: 'candidatesKanban.stages.offer' },
  { id: 'hired', name: 'Hired', key: 'candidatesKanban.stages.hired' },
];

/**
 * Candidates Kanban Page (Recruiter Module)
 *
 * Displays candidates in a kanban board layout with stages.
 * Supports keyboard navigation: Arrow keys to navigate cards, Enter to open details, Esc to close.
 */
const CandidatesKanbanPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'lg'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCandidateIndex, setSelectedCandidateIndex] = useState<number>(-1);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Batch actions state
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<Set<string>>(new Set());
  const [batchMoveDialogOpen, setBatchMoveDialogOpen] = useState(false);
  const [batchTagsDialogOpen, setBatchTagsDialogOpen] = useState(false);
  const [batchDeleteDialogOpen, setBatchDeleteDialogOpen] = useState(false);
  const [targetStage, setTargetStage] = useState<string>('');
  const [newTag, setNewTag] = useState<string>('');
  const [batchActionLoading, setBatchActionLoading] = useState(false);
  const [dragLoading, setDragLoading] = useState(false);
  const [movingCandidateIds, setMovingCandidateIds] = useState<Set<string>>(new Set());
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({ open: false, message: '', severity: 'success' });

  // Group candidates by stage (unfiltered)
  const candidatesByStageUnfiltered = STAGES.reduce((acc, stage) => {
    acc[stage.id] = [];
    return acc;
  }, {} as Record<string, Candidate[]>);

  candidates.forEach((candidate) => {
    // Determine stage based on status (simple mapping for now)
    let stageId = 'new';
    if (candidate.status === 'reviewed') stageId = 'screening';
    else if (candidate.status === 'interview') stageId = 'interview';
    else if (candidate.status === 'offered') stageId = 'offer';
    else if (candidate.status === 'hired') stageId = 'hired';

    if (candidatesByStageUnfiltered[stageId]) {
      candidatesByStageUnfiltered[stageId].push(candidate);
    }
  });

  // Group candidates by stage (filtered by search)
  const candidatesByStage = STAGES.reduce((acc, stage) => {
    acc[stage.id] = [];
    return acc;
  }, {} as Record<string, Candidate[]>);

  candidates.forEach((candidate) => {
    // Determine stage based on status (simple mapping for now)
    let stageId = 'new';
    if (candidate.status === 'reviewed') stageId = 'screening';
    else if (candidate.status === 'interview') stageId = 'interview';
    else if (candidate.status === 'offered') stageId = 'offer';
    else if (candidate.status === 'hired') stageId = 'hired';

    // Apply search filter
    let includeCandidate = true;
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      includeCandidate =
        candidate.filename?.toLowerCase().includes(query) ||
        candidate.skills?.some((skill) => skill.toLowerCase().includes(query));
    }

    if (includeCandidate && candidatesByStage[stageId]) {
      candidatesByStage[stageId].push(candidate);
    }
  });

  // Flatten candidates for keyboard navigation
  const allFilteredCandidates = STAGES.flatMap((stage) => candidatesByStage[stage.id]);

  /**
   * Keyboard navigation shortcuts using useKeyboardNavigation hook
   * - Arrow Down/Right: Navigate to next candidate
   * - Arrow Up/Left: Navigate to previous candidate
   * - Enter: View selected candidate details
   * - Escape: Close details dialog or clear selection
   * - Ctrl+F: Focus search field
   */
  useKeyboardNavigation({
    shortcuts: [
      // Ctrl+F: Focus search field (works even when typing in input)
      {
        id: 'focusSearch',
        key: 'f',
        modifiers: ['Ctrl'],
        handler: () => {
          searchInputRef.current?.focus();
        },
        description: 'Focus search field',
        priority: 10,
      },
      // Ctrl+A: Select all filtered candidates
      {
        id: 'selectAll',
        key: 'a',
        modifiers: ['Ctrl'],
        handler: () => {
          const allIds = new Set(allFilteredCandidates.map((c) => c.id));
          setSelectedCandidateIds(allIds);
          setSnackbar({
            open: true,
            message: `Selected ${allIds.size} candidate(s)`,
            severity: 'success',
          });
        },
        description: 'Select all candidates',
        priority: 9,
      },
      // Arrow Down: Navigate to next candidate
      {
        id: 'navigateNext',
        key: 'ArrowDown',
        handler: () => {
          if (allFilteredCandidates.length > 0) {
            setSelectedCandidateIndex((prev) => {
              if (prev < allFilteredCandidates.length - 1) {
                return prev + 1;
              }
              return prev;
            });
          }
        },
        description: 'Navigate to next candidate',
        when: () => !detailsDialogOpen && allFilteredCandidates.length > 0,
        priority: 5,
      },
      // Arrow Right: Navigate to next candidate
      {
        id: 'navigateNextRight',
        key: 'ArrowRight',
        handler: () => {
          if (allFilteredCandidates.length > 0) {
            setSelectedCandidateIndex((prev) => {
              if (prev < allFilteredCandidates.length - 1) {
                return prev + 1;
              }
              return prev;
            });
          }
        },
        description: 'Navigate to next candidate',
        when: () => !detailsDialogOpen && allFilteredCandidates.length > 0,
        priority: 5,
      },
      // Arrow Up: Navigate to previous candidate
      {
        id: 'navigatePrevious',
        key: 'ArrowUp',
        handler: () => {
          if (allFilteredCandidates.length > 0) {
            setSelectedCandidateIndex((prev) => {
              if (prev > 0) {
                return prev - 1;
              }
              return prev;
            });
          }
        },
        description: 'Navigate to previous candidate',
        when: () => !detailsDialogOpen && allFilteredCandidates.length > 0,
        priority: 5,
      },
      // Arrow Left: Navigate to previous candidate
      {
        id: 'navigatePreviousLeft',
        key: 'ArrowLeft',
        handler: () => {
          if (allFilteredCandidates.length > 0) {
            setSelectedCandidateIndex((prev) => {
              if (prev > 0) {
                return prev - 1;
              }
              return prev;
            });
          }
        },
        description: 'Navigate to previous candidate',
        when: () => !detailsDialogOpen && allFilteredCandidates.length > 0,
        priority: 5,
      },
      // Enter: View selected candidate details
      {
        id: 'viewDetails',
        key: 'Enter',
        handler: () => {
          if (selectedCandidateIndex >= 0) {
            const selected = allFilteredCandidates[selectedCandidateIndex];
            if (selected) {
              setSelectedCandidate(selected);
              setDetailsDialogOpen(true);
            }
          }
        },
        description: 'View selected candidate details',
        when: () => !detailsDialogOpen && allFilteredCandidates.length > 0 && selectedCandidateIndex >= 0,
        priority: 5,
      },
      // Escape: Clear selection or close dialog
      {
        id: 'clearSelection',
        key: 'Escape',
        handler: () => {
          if (selectedCandidateIndex >= 0) {
            setSelectedCandidateIndex(-1);
          } else {
            setSearchQuery('');
          }
        },
        description: 'Clear selection or search',
        when: () => !detailsDialogOpen,
        priority: 5,
      },
    ],
  });

  // Reset selected index when filtered candidates change
  useEffect(() => {
    setSelectedCandidateIndex((prev) => {
      if (prev >= allFilteredCandidates.length) {
        return Math.max(0, allFilteredCandidates.length - 1);
      }
      return prev;
    });
  }, [allFilteredCandidates.length]);

  useEffect(() => {
    fetchCandidates();
  }, []);

  const fetchCandidates = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/resumes/?limit=100');

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || errorData.message || `Failed to fetch candidates (HTTP ${response.status})`;

        // Provide more context based on status code
        if (response.status === 401 || response.status === 403) {
          throw new Error('Authentication error: You are not authorized to view candidates. Please log in again.');
        } else if (response.status === 404) {
          throw new Error('Candidates endpoint not found. Please check the API configuration.');
        } else if (response.status >= 500) {
          throw new Error(`Server error: Unable to load candidates. The server has been notified. Please try again later.`);
        } else {
          throw new Error(errorMessage);
        }
      }

      const data: Candidate[] = await response.json();
      // Map technical_skills to skills for compatibility
      const candidatesWithSkills = data.map((r: any) => ({
        ...r,
        skills: r.technical_skills || [],
      }));
      setCandidates(candidatesWithSkills);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch candidates';

      // Log detailed error for debugging
      console.error('Failed to fetch candidates:', {
        error: err,
        message: errorMessage,
        timestamp: new Date().toISOString(),
      });

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseDetails = () => {
    setDetailsDialogOpen(false);
    setSelectedCandidate(null);
  };

  // Batch selection handlers
  const handleToggleCandidateSelection = useCallback((candidateId: string) => {
    setSelectedCandidateIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(candidateId)) {
        newSet.delete(candidateId);
      } else {
        newSet.add(candidateId);
      }
      return newSet;
    });
  }, []);

  const handleSelectAllInStage = useCallback((stageId: string) => {
    const stageCandidates = candidatesByStage[stageId];
    const stageIds = new Set(stageCandidates.map((c) => c.id));
    setSelectedCandidateIds((prev) => {
      const newSet = new Set(prev);
      stageIds.forEach((id) => newSet.add(id));
      return newSet;
    });
  }, [candidatesByStage]);

  const handleClearSelection = useCallback(() => {
    setSelectedCandidateIds(new Set());
  }, []);

  const handleClearStageSelection = useCallback(
    (stageId: string) => {
      const stageCandidates = candidatesByStage[stageId];
      const stageIds = new Set(stageCandidates.map((c) => c.id));
      setSelectedCandidateIds((prev) => {
        const newSet = new Set(prev);
        stageIds.forEach((id) => newSet.delete(id));
        return newSet;
      });
    },
    [candidatesByStage]
  );

  const isAllSelectedInStage = useCallback(
    (stageId: string) => {
      const stageCandidates = candidatesByStage[stageId];
      if (stageCandidates.length === 0) return false;
      return stageCandidates.every((c) => selectedCandidateIds.has(c.id));
    },
    [candidatesByStage, selectedCandidateIds]
  );

  // Batch move to stage with optimistic update
  const handleBatchMove = async () => {
    if (!targetStage || selectedCandidateIds.size === 0) return;

    setBatchActionLoading(true);

    // Optimistic update: immediately update UI
    const previousCandidates = [...candidates];
    const failedCandidateIds: string[] = [];
    setCandidates((prev) =>
      prev.map((candidate) =>
        selectedCandidateIds.has(candidate.id)
          ? { ...candidate, status: getStatusFromStage(targetStage) }
          : candidate
      )
    );

    try {
      // Simulate API call (replace with actual API when available)
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Simulate potential partial failure for demonstration
      // In real implementation, this would come from the API response
      const simulateFailure = Math.random() < 0.1; // 10% chance of failure

      if (simulateFailure) {
        throw new Error(`Failed to move ${selectedCandidateIds.size} candidate(s) to ${STAGES.find((s) => s.id === targetStage)?.name}. Server error: Unable to process batch operation.`);
      }

      setSnackbar({
        open: true,
        message: `Moved ${selectedCandidateIds.size} candidate(s) to ${STAGES.find((s) => s.id === targetStage)?.name}`,
        severity: 'success',
      });

      setSelectedCandidateIds(new Set());
      setBatchMoveDialogOpen(false);
      setTargetStage('');
    } catch (error) {
      // Rollback on error
      setCandidates(previousCandidates);

      const errorMessage = error instanceof Error ? error.message : 'Failed to move candidates. Please try again.';
      const failedCount = selectedCandidateIds.size;
      const targetStageName = STAGES.find((s) => s.id === targetStage)?.name || targetStage;

      setSnackbar({
        open: true,
        message: `Failed to move ${failedCount} candidate(s) to ${targetStageName}`,
        severity: 'error',
      });

      // Store error details for potential display in dialog
      console.error('Batch move error:', {
        failedCount,
        targetStage: targetStageName,
        candidateIds: Array.from(selectedCandidateIds),
        error: errorMessage,
      });
    } finally {
      setBatchActionLoading(false);
    }
  };

  // Batch add tags with optimistic update
  const handleBatchAddTags = async () => {
    if (!newTag.trim() || selectedCandidateIds.size === 0) return;

    setBatchActionLoading(true);

    // Optimistic update: immediately update UI
    const previousCandidates = [...candidates];
    const tagToAdd = newTag.trim();

    setCandidates((prev) =>
      prev.map((candidate) =>
        selectedCandidateIds.has(candidate.id)
          ? {
              ...candidate,
              skills: [...(candidate.skills || []), tagToAdd],
            }
          : candidate
      )
    );

    try {
      // Simulate API call (replace with actual API when available)
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Simulate potential failure for demonstration
      const simulateFailure = Math.random() < 0.1; // 10% chance of failure

      if (simulateFailure) {
        throw new Error(`Failed to add tag "${tagToAdd}" to ${selectedCandidateIds.size} candidate(s). Server error: Unable to update candidate records.`);
      }

      setSnackbar({
        open: true,
        message: `Added tag "${tagToAdd}" to ${selectedCandidateIds.size} candidate(s)`,
        severity: 'success',
      });

      setSelectedCandidateIds(new Set());
      setBatchTagsDialogOpen(false);
      setNewTag('');
    } catch (error) {
      // Rollback on error
      setCandidates(previousCandidates);

      const errorMessage = error instanceof Error ? error.message : 'Failed to add tags. Please try again.';
      const failedCount = selectedCandidateIds.size;

      setSnackbar({
        open: true,
        message: `Failed to add tag "${tagToAdd}" to ${failedCount} candidate(s)`,
        severity: 'error',
      });

      // Store error details for potential display
      console.error('Batch add tags error:', {
        failedCount,
        tag: tagToAdd,
        candidateIds: Array.from(selectedCandidateIds),
        error: errorMessage,
      });
    } finally {
      setBatchActionLoading(false);
    }
  };

  // Batch delete with optimistic update
  const handleBatchDelete = async () => {
    if (selectedCandidateIds.size === 0) return;

    setBatchActionLoading(true);

    // Optimistic update: immediately update UI
    const previousCandidates = [...candidates];

    setCandidates((prev) => prev.filter((candidate) => !selectedCandidateIds.has(candidate.id)));

    try {
      // Simulate API call (replace with actual API when available)
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Simulate potential failure for demonstration
      const simulateFailure = Math.random() < 0.1; // 10% chance of failure

      if (simulateFailure) {
        throw new Error(`Failed to delete ${selectedCandidateIds.size} candidate(s). Server error: Unable to process deletion request.`);
      }

      setSnackbar({
        open: true,
        message: `Deleted ${selectedCandidateIds.size} candidate(s)`,
        severity: 'success',
      });

      setSelectedCandidateIds(new Set());
      setBatchDeleteDialogOpen(false);
    } catch (error) {
      // Rollback on error
      setCandidates(previousCandidates);

      const errorMessage = error instanceof Error ? error.message : 'Failed to delete candidates. Please try again.';
      const failedCount = selectedCandidateIds.size;

      setSnackbar({
        open: true,
        message: `Failed to delete ${failedCount} candidate(s)`,
        severity: 'error',
      });

      // Store error details for potential display
      console.error('Batch delete error:', {
        failedCount,
        candidateIds: Array.from(selectedCandidateIds),
        error: errorMessage,
      });
    } finally {
      setBatchActionLoading(false);
    }
  };

  // Helper to convert stage ID to status
  const getStatusFromStage = (stageId: string): string => {
    const statusMap: Record<string, string> = {
      new: 'new',
      screening: 'reviewed',
      interview: 'interview',
      offer: 'offered',
      hired: 'hired',
    };
    return statusMap[stageId] || 'new';
  };

  // Helper to convert status to stage ID
  const getStageFromStatus = (status: string): string => {
    const stageMap: Record<string, string> = {
      new: 'new',
      reviewed: 'screening',
      interview: 'interview',
      offered: 'offer',
      hired: 'hired',
    };
    return stageMap[status] || 'new';
  };

  /**
   * Handle drag-and-drop with optimistic updates
   * - Immediately update UI when card is dropped
   * - Call API to persist change
   * - Rollback on error with conflict detection
   * - Prevent duplicate moves on same card
   */
  const handleDragEnd = useCallback(
    async (result: DropResult) => {
      const { destination, source, draggableId } = result;

      // Drop if no destination or dropped in same position
      if (!destination || (source.droppableId === destination.droppableId && source.index === destination.index)) {
        return;
      }

      // Prevent duplicate moves on the same card
      if (movingCandidateIds.has(draggableId)) {
        return;
      }

      // Optimistic update: immediately update UI
      const previousCandidates = [...candidates];
      const draggedCandidate = candidates.find((c) => c.id === draggableId);

      if (!draggedCandidate) {
        return;
      }

      // Update candidate status based on destination stage
      const newStatus = getStatusFromStage(destination.droppableId);

      // Mark card as moving and update UI
      setMovingCandidateIds((prev) => new Set(prev).add(draggableId));
      setCandidates((prev) =>
        prev.map((candidate) =>
          candidate.id === draggableId ? { ...candidate, status: newStatus } : candidate
        )
      );

      try {
        // Call API to persist the change
        const response = await fetch(`/api/resumes/${draggableId}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus }),
        });

        // Handle conflict (HTTP 409) - candidate was modified by another user
        if (response.status === 409) {
          const conflictData = await response.json();
          setCandidates(previousCandidates);

          const candidateName = draggedCandidate.filename || draggableId;
          const targetStageName = STAGES.find((s) => s.id === destination.droppableId)?.name || destination.droppableId;

          setSnackbar({
            open: true,
            message: `${candidateName} was modified by another user. Please refresh and try again.`,
            severity: 'error',
          });

          // Log conflict details
          console.error('Candidate move conflict:', {
            candidateId: draggableId,
            candidateName,
            targetStage: targetStageName,
            conflictDetails: conflictData.detail,
          });

          return;
        }

        // Handle other errors
        if (!response.ok) {
          throw new Error(`Failed to move candidate: ${response.statusText}`);
        }

        // Success - show notification
        setSnackbar({
          open: true,
          message: `Moved ${draggedCandidate.filename} to ${STAGES.find((s) => s.id === destination.droppableId)?.name}`,
          severity: 'success',
        });
      } catch (error) {
        // Rollback on error
        setCandidates(previousCandidates);

        const errorMessage = error instanceof Error ? error.message : 'Failed to move candidate. Please try again.';
        const candidateName = draggedCandidate.filename || draggedCandidate.id;
        const targetStageName = STAGES.find((s) => s.id === destination.droppableId)?.name || destination.droppableId;

        setSnackbar({
          open: true,
          message: `Failed to move ${candidateName} to ${targetStageName}`,
          severity: 'error',
        });

        // Log detailed error information
        console.error('Drag-drop move error:', {
          candidateId: draggableId,
          candidateName,
          sourceStage: STAGES.find((s) => s.id === source.droppableId)?.name,
          targetStage: targetStageName,
          error: errorMessage,
        });
      } finally {
        // Remove card from moving state
        setMovingCandidateIds((prev) => {
          const newSet = new Set(prev);
          newSet.delete(draggableId);
          return newSet;
        });
      }
    },
    [candidates, movingCandidateIds]
  );

  // Handle click on card (not checkbox)
  const handleCardClick = (candidate: Candidate, index: number, event: React.MouseEvent) => {
    // Only open details if not clicking on checkbox
    if ((event.target as HTMLElement).type !== 'checkbox') {
      setSelectedCandidateIndex(index);
      setSelectedCandidate(candidate);
      setDetailsDialogOpen(true);
    }
  };

  const getTitleFromFilename = (filename: string) => {
    const match = filename.match(/CV_(\d+)\.docx/);
    return match ? `Candidate #${match[1]}` : filename;
  };

  const selectedCount = selectedCandidateIds.size;

  if (loading) {
    return (
      <ErrorBoundary
        onError={(error, errorInfo) => {
          console.error('CandidatesKanban loading error:', error, errorInfo);
        }}
      >
        <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
          <LoadingSpinner variant="cards" count={10} />
        </Box>
      </ErrorBoundary>
    );
  }

  if (error) {
    return (
      <ErrorBoundary
        onError={(error, errorInfo) => {
          console.error('CandidatesKanban error state:', error, errorInfo);
        }}
      >
        <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
          <CandidateLoadFailedError
            message={error}
            actions={[
              {
                label: 'Retry',
                onClick: () => fetchCandidates(),
                primary: true,
              },
              {
                label: 'Refresh Page',
                onClick: () => window.location.reload(),
                variant: 'outlined',
              },
            ]}
          />
        </Box>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.error('CandidatesKanban page error:', error, errorInfo);
      }}
    >
      <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
        {/* Page Header */}
        <Box sx={{ mb: { xs: 2, sm: 3 } }}>
          <Typography
            variant="h4"
            as="h1"
            gutterBottom
            fontWeight={600}
            sx={{ fontSize: { xs: '1.75rem', sm: '2.125rem', md: '2.5rem' } }}
          >
            {t('candidatesKanban.title')}
          </Typography>
          <Typography variant="body1" color="secondary" paragraph sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>
            {t('candidatesKanban.description')}
          </Typography>

          {/* Search Bar */}
          <TextField
            fullWidth
            maxWidth="sm"
            placeholder={t('candidatesKanban.searchPlaceholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            inputRef={searchInputRef}
            sx={{
              maxWidth: { xs: '100%', sm: 600 },
              mt: { xs: 1.5, sm: 2 },
              '& .MuiInputBase-root': {
                fontSize: { xs: '0.9rem', sm: '1rem' },
              },
            }}
          />

          {/* Keyboard Shortcuts Hint - hide on very small screens */}
          <Typography
            variant="caption"
            color="secondary"
            sx={{
              display: { xs: 'none', sm: 'block' },
              mt: 1,
            }}
          >
            💡 {t('candidatesKanban.keyboardShortcuts')}: Ctrl+F {t('candidatesKanban.toFocusSearch')}, Ctrl+A {t('candidatesKanban.toSelectAll')}, Arrow keys {t('candidatesKanban.toNavigate')}, Enter {t('candidatesKanban.toViewDetails')}, Esc {t('candidatesKanban.toClose')}
          </Typography>
        </Box>

        {/* Batch Action Toolbar */}
        {selectedCount > 0 && (
          <Paper
            sx={{
              position: 'sticky',
              top: 0,
              zIndex: 110,
              mb: 2,
              borderRadius: 1,
            }}
          >
            <Toolbar
              variant="dense"
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: { xs: 'wrap', sm: 'nowrap' },
                gap: { xs: 1, sm: 2 },
                px: { xs: 1, sm: 2 },
              }}
            >
              <Typography variant="subtitle1" fontWeight={600} sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}>
                {selectedCount} {selectedCount === 1 ? 'candidate' : 'candidates'} selected
              </Typography>

              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} width={{ xs: '100%', sm: 'auto' }}>
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<WorkIcon />}
                  onClick={() => setBatchMoveDialogOpen(true)}
                  sx={{ minHeight: { xs: 32, sm: 36 }, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
                  fullWidth={{ xs: true, sm: false }}
                >
                  Move to Stage
                </Button>

                <Button
                  variant="contained"
                  size="small"
                  startIcon={<LabelIcon />}
                  onClick={() => setBatchTagsDialogOpen(true)}
                  sx={{ minHeight: { xs: 32, sm: 36 }, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
                  fullWidth={{ xs: true, sm: false }}
                >
                  Add Tags
                </Button>

                <Button
                  variant="outlined"
                  color="error"
                  size="small"
                  startIcon={<DeleteSweepIcon />}
                  onClick={() => setBatchDeleteDialogOpen(true)}
                  sx={{ minHeight: { xs: 32, sm: 36 }, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
                  fullWidth={{ xs: true, sm: false }}
                >
                  Delete
                </Button>

                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleClearSelection}
                  sx={{ minHeight: { xs: 32, sm: 36 }, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
                  fullWidth={{ xs: true, sm: false }}
                >
                  Clear
                </Button>
              </Stack>
            </Toolbar>
          </Paper>
        )}

        {/* Kanban Board with Drag-and-Drop and Virtual Scrolling */}
        <DragDropContext onDragEnd={handleDragEnd}>
          <VirtualKanbanBoard
            stages={STAGES}
            candidatesByStage={candidatesByStage}
            candidatesByStageUnfiltered={candidatesByStageUnfiltered}
            onCardClick={handleCardClick}
            selectedCandidateIndex={selectedCandidateIndex}
            allFilteredCandidates={allFilteredCandidates}
            selectedCandidateIds={selectedCandidateIds}
            onToggleSelection={handleToggleCandidateSelection}
            dragLoading={dragLoading}
            movingCandidateIds={movingCandidateIds}
            isMobile={isMobile}
            isDesktop={isDesktop}
            getTitleFromFilename={getTitleFromFilename}
            t={t}
            isAllSelectedInStage={isAllSelectedInStage}
            onSelectAllInStage={handleSelectAllInStage}
            onClearStageSelection={handleClearStageSelection}
          />
        </DragDropContext>

        {/* Mobile scroll indicator */}
        <Box
          sx={{
            display: { xs: 'flex', sm: 'none' },
            alignItems: 'center',
            justifyContent: 'center',
            gap: 0.5,
            mt: 1,
            color: 'text.secondary',
            animation: 'pulse 2s ease-in-out infinite',
            '@keyframes pulse': {
              '0%, 100%': { opacity: 0.5 },
              '50%': { opacity: 1 },
            },
          }}
        >
          <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>
            ← Swipe to see more stages →
          </Typography>
        </Box>

        {/* Candidate Details Dialog */}
        <Dialog
          open={detailsDialogOpen}
          onClose={handleCloseDetails}
          maxWidth="md"
          fullWidth
          sx={{
            '& .MuiDialog-paper': {
              margin: { xs: 1, sm: 2 },
              maxWidth: { xs: 'calc(100% - 16px)', sm: 'md' },
            },
          }}
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6">
                {selectedCandidate && getTitleFromFilename(selectedCandidate.filename)}
              </Typography>
              <IconButton onClick={handleCloseDetails} size="small">
                <CloseIcon />
              </IconButton>
            </Box>
          </DialogTitle>
          <DialogContent dividers>
            {selectedCandidate && (
              <Stack spacing={2}>
                {selectedCandidate.email && (
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <EmailIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography>{selectedCandidate.email}</Typography>
                  </Box>
                )}

                {selectedCandidate.phone && (
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <PhoneIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Typography>{selectedCandidate.phone}</Typography>
                  </Box>
                )}

                {selectedCandidate.match_percentage && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      {t('candidatesKanban.match')}:{' '}
                      <Chip
                        label={`${selectedCandidate.match_percentage}%`}
                        size="small"
                        color={selectedCandidate.match_percentage >= 80 ? 'success' : 'default'}
                      />
                    </Typography>
                  </Box>
                )}

                {selectedCandidate.skills && selectedCandidate.skills.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      {t('candidatesKanban.skills')}:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selectedCandidate.skills.map((skill, i) => (
                        <Chip key={i} label={skill} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </Box>
                )}

                {selectedCandidate.vacancy_title && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      {t('candidatesKanban.appliedFor')}:
                    </Typography>
                    <Typography variant="body2">{selectedCandidate.vacancy_title}</Typography>
                  </Box>
                )}

                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    {t('candidatesKanban.status')}:
                  </Typography>
                  <Chip
                    label={selectedCandidate.status}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                </Box>
              </Stack>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDetails}>
              {t('candidatesKanban.close')}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Batch Move to Stage Dialog */}
        <Dialog
          open={batchMoveDialogOpen}
          onClose={() => setBatchMoveDialogOpen(false)}
          maxWidth="sm"
          fullWidth
          sx={{
            '& .MuiDialog-paper': {
              margin: { xs: 1, sm: 2 },
              maxWidth: { xs: 'calc(100% - 16px)', sm: 'sm' },
            },
          }}
        >
          <DialogTitle>Move {selectedCount} Candidate(s)</DialogTitle>
          <DialogContent>
            <Typography variant="body2" color="secondary" sx={{ mb: 2 }}>
              Select the stage to move {selectedCount} candidate(s) to:
            </Typography>

            <FormControl fullWidth>
              <InputLabel>Target Stage</InputLabel>
              <Select
                value={targetStage}
                label="Target Stage"
                onChange={(e) => setTargetStage(e.target.value)}
                disabled={batchActionLoading}
              >
                {STAGES.map((stage) => (
                  <MenuItem key={stage.id} value={stage.id}>
                    {t(stage.key)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setBatchMoveDialogOpen(false)}
              disabled={batchActionLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleBatchMove}
              variant="contained"
              disabled={!targetStage || batchActionLoading}
              startIcon={batchActionLoading ? <CircularProgress size={16} /> : <WorkIcon />}
            >
              {batchActionLoading ? 'Moving...' : 'Move'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Batch Add Tags Dialog */}
        <Dialog
          open={batchTagsDialogOpen}
          onClose={() => setBatchTagsDialogOpen(false)}
          maxWidth="sm"
          fullWidth
          sx={{
            '& .MuiDialog-paper': {
              margin: { xs: 1, sm: 2 },
              maxWidth: { xs: 'calc(100% - 16px)', sm: 'sm' },
            },
          }}
        >
          <DialogTitle>Add Tags to {selectedCount} Candidate(s)</DialogTitle>
          <DialogContent>
            <Typography variant="body2" color="secondary" sx={{ mb: 2 }}>
              Enter a tag to add to {selectedCount} candidate(s):
            </Typography>

            <TextField
              fullWidth
              label="Tag"
              placeholder="e.g., Frontend, Senior, Remote"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              disabled={batchActionLoading}
              autoFocus
              onKeyPress={(e) => {
                if (e.key === 'Enter' && newTag.trim()) {
                  handleBatchAddTags();
                }
              }}
            />

            {selectedCount > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="secondary">
                  This tag will be added to all selected candidates.
                </Typography>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setBatchTagsDialogOpen(false)}
              disabled={batchActionLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleBatchAddTags}
              variant="contained"
              disabled={!newTag.trim() || batchActionLoading}
              startIcon={batchActionLoading ? <CircularProgress size={16} /> : <LabelIcon />}
            >
              {batchActionLoading ? 'Adding...' : 'Add Tag'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Batch Delete Confirmation Dialog */}
        <Dialog
          open={batchDeleteDialogOpen}
          onClose={() => setBatchDeleteDialogOpen(false)}
          maxWidth="sm"
          fullWidth
          sx={{
            '& .MuiDialog-paper': {
              margin: { xs: 1, sm: 2 },
              maxWidth: { xs: 'calc(100% - 16px)', sm: 'sm' },
            },
          }}
        >
          <DialogTitle>Delete {selectedCount} Candidate(s)?</DialogTitle>
          <DialogContent>
            <Alert severity="warning" sx={{ mb: 2 }}>
              This action cannot be undone.
            </Alert>
            <Typography variant="body2" color="secondary">
              Are you sure you want to delete {selectedCount} candidate(s)? This will permanently remove them from the system.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setBatchDeleteDialogOpen(false)}
              disabled={batchActionLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleBatchDelete}
              variant="contained"
              color="error"
              disabled={batchActionLoading}
              startIcon={batchActionLoading ? <CircularProgress size={16} /> : <DeleteSweepIcon />}
            >
              {batchActionLoading ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar for feedback */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={4000}
          onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert
            onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
            severity={snackbar.severity}
            icon={snackbar.severity === 'success' ? <CheckCircleIcon /> : <ErrorIcon />}
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </ErrorBoundary>
  );
};

export default CandidatesKanbanPage;
