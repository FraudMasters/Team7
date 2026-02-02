import React from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { Box, Paper, Typography, Card, CardContent } from '@mui/material';

export interface Column {
  id: string;
  title: string;
  candidates: any[];
}

export interface KanbanBoardProps {
  columns: Column[];
  onDragEnd: (result: DropResult) => void | Promise<void>;
}

/**
 * Simple Kanban Board Component
 *
 * Basic drag-and-drop kanban board for candidate pipeline.
 * Uses hello-pangea/dnd for drag and drop functionality.
 */
const KanbanBoard: React.FC<KanbanBoardProps> = ({ columns, onDragEnd }) => {
  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Box
        sx={{
          display: 'flex',
          gap: 2,
          overflowX: 'auto',
          height: '100%',
        }}
      >
        {columns.map((column) => (
          <Box
            key={column.id}
            sx={{
              minWidth: 280,
              maxWidth: 320,
              flex: '0 0 auto',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Column Header */}
            <Paper
              sx={{
                p: 2,
                mb: 2,
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
              }}
            >
              <Typography variant="h6" fontWeight={600}>
                {column.title}
              </Typography>
              <Typography variant="caption">
                {column.candidates.length} candidates
              </Typography>
            </Paper>

            {/* Column Content */}
            <Droppable droppableId={column.id}>
              {(provided, snapshot) => (
                <Box
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  sx={{
                    flex: 1,
                        minHeight: 200,
                    bgcolor: snapshot.isDraggingOver ? 'action.hover' : 'background.default',
                    borderRadius: 1,
                    p: 1,
                  }}
                >
                  {column.candidates.map((candidate: any, index: number) => (
                    <Draggable
                      key={candidate.id}
                      draggableId={candidate.id}
                      index={index}
                    >
                      {(provided, snapshot) => (
                        <Card
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          sx={{
                            mb: 1,
                            boxShadow: snapshot.isDragging ? 8 : 1,
                            transform: snapshot.isDragging ? 'rotate(3deg)' : 'none',
                          }}
                        >
                          <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                            <Typography variant="subtitle2" fontWeight={600}>
                              {candidate.name || candidate.filename || 'Unknown'}
                            </Typography>
                            {candidate.email && (
                              <Typography variant="caption" color="text.secondary">
                                {candidate.email}
                              </Typography>
                            )}
                          </CardContent>
                        </Card>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </Box>
              )}
            </Droppable>
          </Box>
        ))}
      </Box>
    </DragDropContext>
  );
};

export default KanbanBoard;
export { KanbanBoard };
