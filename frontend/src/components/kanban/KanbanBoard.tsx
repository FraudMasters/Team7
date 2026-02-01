import { Box, Paper, Typography, Stack, Chip } from '@mui/material';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { motion } from 'framer-motion';

const MotionPaper = motion(Paper);

export interface Candidate {
  id: string;
  name: string;
  email: string;
  stage: string;
  tags: string[];
  notes_count: number;
  match_score?: number;
}

export interface KanbanColumn {
  id: string;
  title: string;
  candidates: Candidate[];
}

interface KanbanBoardProps {
  columns: KanbanColumn[];
  onDragEnd: (result: DropResult) => void;
}

export function KanbanBoard({ columns, onDragEnd }: KanbanBoardProps) {
  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Box
        sx={{ display: 'flex', gap: 2, overflowX: 'auto', pb: 2 }}
        role="region"
        aria-label="Kanban board for candidate workflow"
      >
        {columns.map((column) => (
          <MotionPaper
            key={column.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            sx={{
              minWidth: 300,
              width: 300,
              bgcolor: 'background.default',
            }}
            role="region"
            aria-labelledby={`column-${column.id}-title`}
          >
            <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography
                  id={`column-${column.id}-title`}
                  variant="subtitle2"
                  fontWeight={600}
                  component="h2"
                >
                  {column.title}
                </Typography>
                <Chip
                  label={`${column.candidates.length} ${column.candidates.length === 1 ? 'candidate' : 'candidates'}`}
                  size="small"
                  variant="outlined"
                  aria-label={`Column contains ${column.candidates.length} candidates`}
                />
              </Stack>
            </Box>
            <Droppable droppableId={column.id}>
              {(provided) => (
                <Box
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  sx={{ p: 2, minHeight: 200 }}
                  role="list"
                  aria-label={`${column.title} candidates`}
                >
                  {column.candidates.map((candidate, index) => (
                    <Draggable
                      key={candidate.id}
                      draggableId={candidate.id}
                      index={index}
                    >
                      {(provided, snapshot) => (
                        <MotionPaper
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          sx={{
                            mb: 2,
                            cursor: 'grab',
                            boxShadow: snapshot.isDragging ? '0 8px 16px rgba(0,0,0,0.15)' : '0 1px 3px rgba(0,0,0,0.08)',
                            opacity: snapshot.isDragging ? 0.8 : 1,
                            '&:focus-visible': {
                              outline: '2px solid',
                              outlineColor: 'primary.main',
                              outlineOffset: '2px',
                            },
                          }}
                          role="listitem"
                          aria-labelledby={`candidate-${candidate.id}-name`}
                          aria-describedby={`candidate-${candidate.id}-details`}
                        >
                          <Box sx={{ p: 2 }}>
                            <Stack direction="row" spacing={2} alignItems="center">
                              <Box
                                sx={{
                                  width: 36,
                                  height: 36,
                                  borderRadius: '50%',
                                  bgcolor: 'primary.main',
                                  color: 'white',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontSize: '0.875rem',
                                  fontWeight: 600,
                                }}
                                aria-hidden="true"
                              >
                                {candidate.name.charAt(0)}
                              </Box>
                              <Box sx={{ flex: 1 }}>
                                <Typography
                                  id={`candidate-${candidate.id}-name`}
                                  variant="body2"
                                  fontWeight={600}
                                >
                                  {candidate.name}
                                </Typography>
                                <Typography
                                  id={`candidate-${candidate.id}-details`}
                                  variant="caption"
                                  color="text.secondary"
                                >
                                  {candidate.email}
                                </Typography>
                              </Box>
                              {candidate.match_score && (
                                <Chip
                                  label={`${candidate.match_score}% match`}
                                  size="small"
                                  color={candidate.match_score > 70 ? 'success' : 'default'}
                                  aria-label={`Match score: ${candidate.match_score} percent`}
                                />
                              )}
                            </Stack>
                          </Box>
                        </MotionPaper>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </Box>
              )}
            </Droppable>
          </MotionPaper>
        ))}
      </Box>
    </DragDropContext>
  );
}
