import React, { useState, useEffect, useCallback } from 'react';
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

  return (
    <Box>
      {/* Kanban Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" fontWeight={600}>
          {t('workflow.title')}
        </Typography>
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
          sx={{ minWidth: 250 }}
        />
      </Box>

      {/* Kanban Board */}
      <DragDropContext onDragEnd={handleDragEnd}>
        <Box sx={{ display: 'flex', gap: 2, overflowX: 'auto', pb: 2 }}>
          {stages.map((stage) => (
            <Box
              key={stage.id}
              sx={{
                minWidth: 300,
                maxWidth: 300,
                flexShrink: 0,
              }}
            >
              {/* Stage Column Header */}
              <Paper
                sx={{
                  p: 2,
                  mb: 1,
                  borderTop: 4,
                  borderTopColor: getStageColor(stage),
                  backgroundColor: 'grey.50',
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle1" fontWeight={600}>
                    {stage.stage_name}
                  </Typography>
                  <Chip
                    label={candidatesByStage[stage.id]?.length || 0}
                    size="small"
                    sx={{
                      backgroundColor: getStageColor(stage),
                      color: 'white',
                      fontWeight: 600,
                    }}
                  />
                </Box>
                {stage.description && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
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
                      minHeight: 400,
                      maxHeight: 'calc(100vh - 300px)',
                      overflowY: 'auto',
                      backgroundColor: snapshot.isDraggingOver ? 'action.hover' : 'background.paper',
                      border: '1px solid',
                      borderColor: snapshot.isDraggingOver ? 'primary.main' : 'divider',
                    }}
                  >
                    {candidatesByStage[stage.id]?.map((candidate, index) => (
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
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            sx={{
                              mb: 1,
                              opacity: snapshot.isDragging ? 0.8 : 1,
                              transform: snapshot.isDragging ? (provided.draggableProps.style?.transform || undefined) : undefined,
                              cursor: 'grab',
                              '&:hover': {
                                boxShadow: 2,
                              },
                              ...(movingCandidate === candidate.id && {
                                opacity: 0.5,
                                pointerEvents: 'none',
                              }),
                            }}
                          >
                            <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                              <Box
                                sx={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'flex-start',
                                  cursor: 'pointer',
                                }}
                                onClick={() => toggleCardExpanded(candidate.id)}
                              >
                                <Box sx={{ flex: 1, minWidth: 0 }}>
                                  <Typography variant="body2" fontWeight={500} noWrap>
                                    {candidate.filename}
                                  </Typography>
                                  {candidate.notes && (
                                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }} noWrap>
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
                                    sx={{ height: 20, fontSize: '0.65rem' }}
                                  />
                                  <ExpandMoreIcon
                                    sx={{
                                      fontSize: 18,
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
                                  sx={{ mt: 1, height: 20, fontSize: '0.65rem' }}
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
                                        height: 20,
                                        fontSize: '0.65rem',
                                      }}
                                    />
                                  ))}
                                  {candidate.tags.length > 2 && (
                                    <Chip
                                      label={`+${candidate.tags.length - 2}`}
                                      size="small"
                                      sx={{ height: 20, fontSize: '0.65rem' }}
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
                    ))}
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
        PaperProps={{
          sx: { height: '80vh', maxHeight: '80vh' },
        }}
      >
        {selectedCandidate && (
          <>
            {/* Modal Header */}
            <DialogTitle sx={{ pb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6" fontWeight={600}>
                    {selectedCandidate.filename}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                    <Typography variant="body2" color="text.secondary">
                      Stage: {selectedCandidate.stage_name}
                    </Typography>
                    {selectedCandidate.vacancy_id && (
                      <Chip
                        label="Linked to vacancy"
                        size="small"
                        color="primary"
                        variant="outlined"
                        sx={{ height: 20, fontSize: '0.65rem' }}
                      />
                    )}
                  </Box>
                </Box>
                <Button
                  startIcon={<CloseIcon />}
                  onClick={handleCloseDetailModal}
                  color="inherit"
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
            <DialogContent sx={{ p: 0, height: 'calc(80vh - 180px)', overflow: 'auto' }}>
              {modalTabValue === 0 && (
                <Box sx={{ p: 3 }}>
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
                <Box sx={{ p: 3 }}>
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
