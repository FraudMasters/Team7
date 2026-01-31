import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Card,
  CardContent,
  Chip,
  Alert,
  TextField,
  InputAdornment,
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Divider,
  Tabs,
  Tab,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  DragDropContext,
  Droppable,
  Draggable,
  DropResult,
} from '@hello-pangea/dnd';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import {
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  Close as CloseIcon,
  Notes as NotesIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import CandidateTags from './CandidateTags';
import CandidateNotes from './CandidateNotes';
import CandidateActivityTimeline from './CandidateActivityTimeline';
import type {
  WorkflowStageResponse,
  CandidateListItem,
} from '@/types/api';

/**
 * WorkflowKanban Component
 *
 * Displays a kanban board with candidates organized by workflow stage.
 * Supports drag-and-drop to move candidates between stages.
 *
 * Note: Fetches all workflow stages and candidates on mount
 */
const WorkflowKanban: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [loading, setLoading] = useState(true);
  const [stages, setStages] = useState<WorkflowStageResponse[]>([]);
  const [candidatesByStage, setCandidatesByStage] = useState<Record<string, CandidateListItem[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [movingCandidate, setMovingCandidate] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateListItem | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [modalTabValue, setModalTabValue] = useState(0);

  // Keyboard navigation state
  const [focusedStageIndex, setFocusedStageIndex] = useState<number>(-1);
  const [focusedCardIndex, setFocusedCardIndex] = useState<number>(-1);
  const cardRefs = useRef<Record<string, HTMLElement>>({});

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch workflow stages
      const stagesResponse = await axios.get<WorkflowStageResponse[]>('/api/workflow-stages/');
      const stagesData = stagesResponse.data;

      // Sort stages by stage_order
      const sortedStages = stagesData.sort((a, b) => a.stage_order - b.stage_order);
      setStages(sortedStages);

      // Fetch candidates for each stage in parallel
      const candidatesPromises = sortedStages.map((stage) => {
        const url = searchTerm
          ? `/api/candidates/?stage_id=${stage.id}&search=${encodeURIComponent(searchTerm)}`
          : `/api/candidates/?stage_id=${stage.id}`;
        return axios.get<CandidateListItem[]>(url);
      });

      const candidatesResponses = await Promise.all(candidatesPromises);

      // Build candidatesByStage object
      const candidatesMap: Record<string, CandidateListItem[]> = {};
      sortedStages.forEach((stage, index) => {
        candidatesMap[stage.id] = candidatesResponses[index]?.data || [];
      });
      setCandidatesByStage(candidatesMap);
    } catch (err) {
      console.error('Error fetching kanban data:', err);
      setError('Failed to load workflow data. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData, searchTerm]);

  const handleDragEnd = async (result: DropResult) => {
    const { destination, source, draggableId } = result;

    // Dropped outside any droppable or same position
    if (!destination || (destination.droppableId === source.droppableId && destination.index === source.index)) {
      return;
    }

    // Optimistically update UI
    const sourceStageId = source.droppableId;
    const destStageId = destination.droppableId;
    const candidateId = draggableId;

    // Find the candidate being moved
    const candidateToMove = candidatesByStage[sourceStageId]?.find(c => c.id === candidateId);
    if (!candidateToMove) return;

    // Create new state with candidate moved
    const newCandidatesByStage = { ...candidatesByStage };

    // Remove from source
    newCandidatesByStage[sourceStageId] = (newCandidatesByStage[sourceStageId] || []).filter(c => c.id !== candidateId);

    // Add to destination
    const destCandidates = [...(newCandidatesByStage[destStageId] || [])];
    destCandidates.splice(destination.index, 0, candidateToMove);
    newCandidatesByStage[destStageId] = destCandidates;

    setCandidatesByStage(newCandidatesByStage);
    setMovingCandidate(candidateId);

    try {
      // Move candidate via API
      await axios.put(`/api/candidates/${candidateId}/stage`, {
        stage_id: destStageId,
      });

      // Refresh data to get updated state
      await fetchData();
    } catch (err) {
      console.error('Error moving candidate:', err);
      setError('Failed to move candidate. Please try again.');

      // Revert the optimistic update
      setCandidatesByStage(candidatesByStage);
    } finally {
      setMovingCandidate(null);
    }
  };

  if (loading) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography variant="body2" sx={{ mt: 2 }}>{t('workflow.loading')}</Typography>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  if (stages.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          {t('workflow.noStages')}
        </Typography>
      </Paper>
    );
  }

  const getStageColor = (stage: WorkflowStageResponse): string => {
    if (stage.color) return stage.color;
    // Default colors based on stage order
    const defaultColors = ['#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#6B7280'];
    return defaultColors[Math.max(0, stage.stage_order) % defaultColors.length] || '#3B82F6';
  };

  const toggleCardExpanded = useCallback((candidateId: string) => {
    setExpandedCards((prev) => ({
      ...prev,
      [candidateId]: !prev[candidateId],
    }));
  }, []);

  const handleOpenCandidateDetail = useCallback((candidate: CandidateListItem) => {
    setSelectedCandidate(candidate);
    setDetailModalOpen(true);
    setModalTabValue(0);
  }, []);

  const handleCloseDetailModal = useCallback(() => {
    setDetailModalOpen(false);
    setSelectedCandidate(null);
  }, []);

  const handleModalTabChange = useCallback((_event: React.SyntheticEvent, newValue: number) => {
    setModalTabValue(newValue);
  }, []);

  /**
   * Handle keyboard navigation
   */
  useEffect(() => {
    const handleKeyDown = async (event: KeyboardEvent) => {
      // Ignore if user is typing in an input field
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement ||
        detailModalOpen
      ) {
        return;
      }

      // If no focus is set yet, start with first column
      if (focusedStageIndex === -1 && event.key !== 'Escape') {
        if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
          event.preventDefault();
          setFocusedStageIndex(0);
          setFocusedCardIndex(0);
        }
        return;
      }

      switch (event.key) {
        case 'ArrowLeft':
          event.preventDefault();
          if (focusedStageIndex > 0) {
            const newStageIndex = focusedStageIndex - 1;
            setFocusedStageIndex(newStageIndex);
            // Set card index to 0 or keep within bounds
            const stageId = stages[newStageIndex]?.id;
            const cardCount = candidatesByStage[stageId]?.length || 0;
            setFocusedCardIndex(Math.min(focusedCardIndex, Math.max(0, cardCount - 1)));
          }
          break;

        case 'ArrowRight':
          event.preventDefault();
          if (focusedStageIndex < stages.length - 1) {
            const newStageIndex = focusedStageIndex + 1;
            setFocusedStageIndex(newStageIndex);
            // Set card index to 0 or keep within bounds
            const stageId = stages[newStageIndex]?.id;
            const cardCount = candidatesByStage[stageId]?.length || 0;
            setFocusedCardIndex(Math.min(focusedCardIndex, Math.max(0, cardCount - 1)));
          }
          break;

        case 'ArrowUp':
          event.preventDefault();
          if (focusedCardIndex > 0) {
            setFocusedCardIndex(focusedCardIndex - 1);
          }
          break;

        case 'ArrowDown':
          event.preventDefault();
          const currentStageId = stages[focusedStageIndex]?.id;
          const maxCards = candidatesByStage[currentStageId]?.length || 0;
          if (focusedCardIndex < maxCards - 1) {
            setFocusedCardIndex(focusedCardIndex + 1);
          }
          break;

        case 'Enter': {
          event.preventDefault();
          // Open details for the focused card
          if (focusedStageIndex >= 0 && focusedCardIndex >= 0) {
            const stageId = stages[focusedStageIndex]?.id;
            const candidate = candidatesByStage[stageId]?.[focusedCardIndex];
            if (candidate) {
              handleOpenCandidateDetail(candidate);
            }
          }
          break;
        }

        case 'Escape':
          event.preventDefault();
          // Clear focus
          setFocusedStageIndex(-1);
          setFocusedCardIndex(-1);
          break;

        case 'm':
        case 'M': {
          // Move focused candidate to next stage (with Shift) or previous stage (without Shift)
          if (focusedStageIndex >= 0 && focusedCardIndex >= 0) {
            event.preventDefault();
            const direction = event.shiftKey ? -1 : 1;
            const newStageIndex = focusedStageIndex + direction;

            if (newStageIndex >= 0 && newStageIndex < stages.length) {
              const currentStageId = stages[focusedStageIndex]?.id;
              const newStageId = stages[newStageIndex]?.id;
              const candidate = candidatesByStage[currentStageId]?.[focusedCardIndex];

              if (candidate && currentStageId && newStageId) {
                // Optimistically update UI
                const newCandidatesByStage = { ...candidatesByStage };
                newCandidatesByStage[currentStageId] = (newCandidatesByStage[currentStageId] || [])
                  .filter(c => c.id !== candidate.id);
                const destCandidates = [...(newCandidatesByStage[newStageId] || [])];
                destCandidates.push(candidate);
                newCandidatesByStage[newStageId] = destCandidates;
                setCandidatesByStage(newCandidatesByStage);
                setMovingCandidate(candidate.id);

                try {
                  // Move candidate via API
                  await axios.put(`/api/candidates/${candidate.id}/stage`, {
                    stage_id: newStageId,
                  });

                  // Refresh data to get updated state
                  await fetchData();

                  // Move focus to the new stage and the last card
                  setFocusedStageIndex(newStageIndex);
                  const newCardCount = candidatesByStage[newStageId]?.length || 0;
                  setFocusedCardIndex(Math.max(0, newCardCount - 1));
                } catch (err) {
                  console.error('Error moving candidate:', err);
                  setError('Failed to move candidate. Please try again.');
                  // Revert the optimistic update
                  setCandidatesByStage(candidatesByStage);
                } finally {
                  setMovingCandidate(null);
                }
              }
            }
          }
          break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [focusedStageIndex, focusedCardIndex, stages, candidatesByStage, detailModalOpen, fetchData, handleOpenCandidateDetail]);

  /**
   * Scroll focused card into view
   */
  useEffect(() => {
    if (focusedStageIndex >= 0 && focusedCardIndex >= 0) {
      const stageId = stages[focusedStageIndex]?.id;
      const cardKey = `${stageId}-${focusedCardIndex}`;
      const cardElement = cardRefs.current[cardKey];
      if (cardElement) {
        cardElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
        });
      }
    }
  }, [focusedStageIndex, focusedCardIndex, stages]);

  /**
   * Reset focus when search changes
   */
  useEffect(() => {
    setFocusedStageIndex(-1);
    setFocusedCardIndex(-1);
  }, [searchTerm]);

  return (
    <Box>
      {/* Kanban Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="h5" fontWeight={600} sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}>
          {t('workflow.title')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
          <TextField
            size="small"
            placeholder="Search candidates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: { xs: 200, sm: 250 } }}
          />
          <Chip
            label="⌨️ Keyboard: Use arrow keys to navigate"
            size="small"
            variant="outlined"
            sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
          />
        </Box>
      </Box>

      {/* Keyboard Shortcuts Help */}
      <Box sx={{ mb: 2 }}>
        <Paper
          sx={{
            p: { xs: 1, sm: 1.5 },
            bgcolor: 'info.50',
            border: 1,
            borderColor: 'info.200',
          }}
        >
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}>
            <strong>Keyboard Shortcuts:</strong> {' '}
            <KeyboardArrowUp sx={{ fontSize: 14, verticalAlign: 'middle' }} /> <KeyboardArrowDown sx={{ fontSize: 14, verticalAlign: 'middle' }} /> Navigate cards • {' '}
            <KeyboardArrowLeft sx={{ fontSize: 14, verticalAlign: 'middle' }} /> <KeyboardArrowRight sx={{ fontSize: 14, verticalAlign: 'middle' }} /> Navigate columns • {' '}
            <strong>Enter</strong> Open details • {' '}
            <strong>M</strong> Move to next stage • {' '}
            <strong>Shift+M</strong> Move to previous stage • {' '}
            <strong>Esc</strong> Clear focus
          </Typography>
        </Paper>
      </Box>

      {/* Kanban Board */}
      <DragDropContext onDragEnd={handleDragEnd}>
        <Box sx={{ display: 'flex', gap: { xs: 1, sm: 2 }, overflowX: 'auto', pb: 2, WebkitOverflowScrolling: 'touch' }}>
          {stages.map((stage, stageIndex) => (
            <Box
              key={stage.id}
              sx={{
                minWidth: { xs: 280, sm: 300 },
                maxWidth: { xs: 280, sm: 300 },
                flexShrink: 0,
              }}
            >
              {/* Stage Column Header */}
              <Paper
                sx={{
                  p: { xs: 1.5, sm: 2 },
                  mb: 1,
                  borderTop: 4,
                  borderTopColor: getStageColor(stage),
                  backgroundColor: 'grey.50',
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle1" fontWeight={600} sx={{ fontSize: { xs: '0.875rem', sm: '1rem' }, pr: 1 }}>
                    {stage.stage_name}
                  </Typography>
                  <Chip
                    label={candidatesByStage[stage.id]?.length || 0}
                    size="small"
                    sx={{
                      backgroundColor: getStageColor(stage),
                      color: 'white',
                      fontWeight: 600,
                      fontSize: { xs: '0.7rem', sm: '0.75rem' },
                      height: { xs: 20, sm: 24 },
                    }}
                  />
                </Box>
                {stage.description && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block', fontSize: { xs: '0.65rem', sm: '0.75rem' } }}>
                    {stage.description}
                  </Typography>
                )}
              </Paper>

              {/* Stage Column Content */}
              <Droppable droppableId={stage.id}>
                {(provided, snapshot) => (
                  <Paper
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    sx={{
                      p: 1,
                      minHeight: { xs: 300, sm: 400 },
                      maxHeight: { xs: 'calc(100vh - 280px)', sm: 'calc(100vh - 300px)' },
                      overflowY: 'auto',
                      backgroundColor: snapshot.isDraggingOver ? 'action.hover' : 'background.paper',
                      border: '1px solid',
                      borderColor: snapshot.isDraggingOver ? 'primary.main' : 'divider',
                    }}
                  >
                    {candidatesByStage[stage.id]?.map((candidate, index) => {
                      const isFocused = focusedStageIndex === stageIndex && focusedCardIndex === index;
                      const cardKey = `${stage.id}-${index}`;

                      return (
                      <Draggable
                        key={candidate.id}
                        draggableId={candidate.id}
                        index={index}
                        isDragDisabled={movingCandidate === candidate.id}
                      >
                        {(provided, snapshot) => {
                          // Get organization_id from tags (use first tag's org_id)
                          const organizationId = candidate.tags && candidate.tags.length > 0
                            ? candidate.tags[0].organization_id
                            : '';

                          return (
                          <Card
                            ref={(el) => {
                              provided.innerRef(el);
                              if (el) {
                                cardRefs.current[cardKey] = el;
                              }
                            }}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            sx={{
                              mb: 1,
                              opacity: snapshot.isDragging ? 0.8 : 1,
                              transform: snapshot.isDragging ? (provided.draggableProps.style?.transform || undefined) : undefined,
                              cursor: 'grab',
                              touchAction: 'none',
                              '&:hover': {
                                boxShadow: 2,
                              },
                              ...(isFocused && {
                                boxShadow: 4,
                                border: 2,
                                borderColor: 'primary.main',
                              }),
                              ...(movingCandidate === candidate.id && {
                                opacity: 0.5,
                                pointerEvents: 'none',
                              }),
                            }}
                          >
                            <CardContent sx={{ p: { xs: 1, sm: 1.5 }, '&:last-child': { pb: { xs: 1, sm: 1.5 } } }}>
                              <Box
                                sx={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'flex-start',
                                  cursor: 'pointer',
                                  gap: 0.5,
                                }}
                                onClick={() => toggleCardExpanded(candidate.id)}
                              >
                                <Box sx={{ flex: 1, minWidth: 0 }}>
                                  <Typography variant="body2" fontWeight={500} noWrap sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                                    {candidate.filename}
                                  </Typography>
                                  {candidate.notes && (
                                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block', fontSize: { xs: '0.65rem', sm: '0.75rem' } }} noWrap>
                                      {candidate.notes}
                                    </Typography>
                                  )}
                                </Box>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <Chip
                                    label="Details"
                                    size="small"
                                    clickable
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleOpenCandidateDetail(candidate);
                                    }}
                                    sx={{ height: { xs: 18, sm: 20 }, fontSize: { xs: '0.6rem', sm: '0.65rem' } }}
                                  />
                                  <ExpandMoreIcon
                                    sx={{
                                      fontSize: { xs: 16, sm: 18 },
                                      color: 'text.secondary',
                                      transform: expandedCards[candidate.id] ? 'rotate(180deg)' : 'rotate(0deg)',
                                      transition: 'transform 0.2s',
                                    }}
                                  />
                                </Box>
                              </Box>

                              {candidate.vacancy_id && (
                                <Chip
                                  label="Linked to vacancy"
                                  size="small"
                                  sx={{ mt: 1, height: { xs: 18, sm: 20 }, fontSize: { xs: '0.6rem', sm: '0.65rem' } }}
                                />
                              )}

                              {/* Quick tag preview - show first 2 tags as small chips */}
                              {candidate.tags && candidate.tags.length > 0 && !expandedCards[candidate.id] && (
                                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 1 }}>
                                  {candidate.tags.slice(0, 2).map((tag) => (
                                    <Chip
                                      key={tag.id}
                                      label={tag.tag_name}
                                      size="small"
                                      sx={{
                                        backgroundColor: tag.color || '#6B7280',
                                        color: 'white',
                                        height: { xs: 18, sm: 20 },
                                        fontSize: { xs: '0.6rem', sm: '0.65rem' },
                                      }}
                                    />
                                  ))}
                                  {candidate.tags.length > 2 && (
                                    <Chip
                                      label={`+${candidate.tags.length - 2}`}
                                      size="small"
                                      sx={{ height: { xs: 18, sm: 20 }, fontSize: { xs: '0.6rem', sm: '0.65rem' } }}
                                    />
                                  )}
                                </Box>
                              )}

                              {/* Expanded tags section */}
                              <Collapse in={expandedCards[candidate.id]} timeout="auto" unmountOnExit>
                                <Box sx={{ mt: 1 }}>
                                  {organizationId ? (
                                    <CandidateTags
                                      resumeId={candidate.id}
                                      organizationId={organizationId}
                                      chipSize="small"
                                      showCount={false}
                                      onTagsChange={() => {
                                        // Refresh data after tags change
                                        fetchData();
                                      }}
                                    />
                                  ) : (
                                    <Typography variant="caption" color="text.secondary">
                                      No organization context available for tags
                                    </Typography>
                                  )}
                                </Box>
                              </Collapse>
                            </CardContent>
                          </Card>
                        )}}
                      </Draggable>
                    );
                    })}
                    {provided.placeholder}
                    {((!candidatesByStage[stage.id] || candidatesByStage[stage.id]!.length === 0)) && (
                      <Box
                        sx={{
                          textAlign: 'center',
                          py: 4,
                          color: 'text.secondary',
                        }}
                      >
                        <Typography variant="body2">
                          {t('workflow.noCandidates')}
                        </Typography>
                      </Box>
                    )}
                  </Paper>
                )}
              </Droppable>
            </Box>
          ))}
        </Box>
      </DragDropContext>

      {/* Candidate Detail Modal */}
      <Dialog
        open={detailModalOpen}
        onClose={handleCloseDetailModal}
        maxWidth="lg"
        fullWidth
        fullScreen={isMobile}
        PaperProps={{
          sx: {
            height: { xs: '100vh', sm: '80vh' },
            maxHeight: { xs: '100vh', sm: '80vh' },
          },
        }}
      >
        {selectedCandidate && (
          <>
            {/* Modal Header */}
            <DialogTitle sx={{ pb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="h6" fontWeight={600} sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}>
                    {selectedCandidate.filename}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                      Stage: {selectedCandidate.stage_name}
                    </Typography>
                    {selectedCandidate.vacancy_id && (
                      <Chip
                        label="Linked to vacancy"
                        size="small"
                        color="primary"
                        variant="outlined"
                        sx={{ height: { xs: 18, sm: 20 }, fontSize: { xs: '0.6rem', sm: '0.65rem' } }}
                      />
                    )}
                  </Box>
                </Box>
                <Button
                  startIcon={<CloseIcon />}
                  onClick={handleCloseDetailModal}
                  color="inherit"
                  size={isMobile ? 'small' : 'medium'}
                >
                  Close
                </Button>
              </Box>
            </DialogTitle>

            <Divider />

            {/* Modal Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={modalTabValue} onChange={handleModalTabChange}>
                <Tab
                  icon={<NotesIcon />}
                  label="Notes"
                  iconPosition="start"
                />
                <Tab
                  icon={<HistoryIcon />}
                  label="Activity Timeline"
                  iconPosition="start"
                />
              </Tabs>
            </Box>

            {/* Modal Content */}
            <DialogContent sx={{ p: 0, height: { xs: 'calc(100vh - 220px)', sm: 'calc(80vh - 180px)' }, overflow: 'auto' }}>
              {modalTabValue === 0 && (
                <Box sx={{ p: { xs: 2, sm: 3 } }}>
                  <CandidateNotes
                    resumeId={selectedCandidate.id}
                    onNotesChange={() => {
                      // Refresh data after notes change
                      fetchData();
                    }}
                  />
                </Box>
              )}

              {modalTabValue === 1 && (
                <Box sx={{ p: { xs: 2, sm: 3 } }}>
                  <CandidateActivityTimeline
                    resumeId={selectedCandidate.id}
                    vacancyId={selectedCandidate.vacancy_id || undefined}
                    limit={50}
                  />
                </Box>
              )}
            </DialogContent>

            <Divider />

            {/* Modal Footer */}
            <DialogActions sx={{ p: 2 }}>
              <Typography variant="caption" color="text.secondary">
                {selectedCandidate.tags.length > 0 && (
                  <>
                    Tags:{' '}
                    {selectedCandidate.tags.map((tag) => tag.tag_name).join(', ')}
                  </>
                )}
              </Typography>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default WorkflowKanban;
