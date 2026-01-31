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
} from '@mui/material';
import {
  DragDropContext,
  Droppable,
  Draggable,
  DropResult,
} from '@hello-pangea/dnd';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
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
      const candidatesPromises = sortedStages.map((stage) =>
        axios.get<CandidateListItem[]>(`/api/candidates/?stage_id=${stage.id}`)
      );

      const candidatesResponses = await Promise.all(candidatesPromises);

      // Build candidatesByStage object
      const candidatesMap: Record<string, CandidateListItem[]> = {};
      sortedStages.forEach((stage, index) => {
        candidatesMap[stage.id] = candidatesResponses[index].data;
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
  }, [fetchData]);

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
    newCandidatesByStage[sourceStageId] = newCandidatesByStage[sourceStageId].filter(c => c.id !== candidateId);

    // Add to destination
    const destCandidates = [...newCandidatesByStage[destStageId]];
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
    return defaultColors[stage.stage_order % defaultColors.length];
  };

  return (
    <Box>
      {/* Kanban Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight={600}>
          {t('workflow.title')}
        </Typography>
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
                        {(provided, snapshot) => (
                          <Card
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            sx={{
                              mb: 1,
                              opacity: snapshot.isDragging ? 0.8 : 1,
                              transform: snapshot.isDragging ? provided.draggableProps.style.transform : undefined,
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
                              <Typography variant="body2" fontWeight={500} noWrap>
                                {candidate.filename}
                              </Typography>
                              {candidate.notes && (
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }} noWrap>
                                  {candidate.notes}
                                </Typography>
                              )}
                              {candidate.vacancy_id && (
                                <Chip
                                  label="Linked to vacancy"
                                  size="small"
                                  sx={{ mt: 1, height: 20, fontSize: '0.65rem' }}
                                />
                              )}
                            </CardContent>
                          </Card>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                    {(!candidatesByStage[stage.id] || candidatesByStage[stage.id].length === 0) && (
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
    </Box>
  );
};

export default WorkflowKanban;
