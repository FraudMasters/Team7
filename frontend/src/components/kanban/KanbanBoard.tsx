import React from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { Box, Paper, Typography, Card, CardContent } from '@/components/ui';

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
        css={{
          display: 'flex',
          gap: '16px',
          overflowX: 'auto',
          height: '100%',
        }}
      >
        {columns.map((column) => (
          <Box
            key={column.id}
            css={{
              minWidth: '280px',
              maxWidth: '320px',
              flex: '0 0 auto',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Column Header */}
            <Paper
              css={{
                padding: '16px',
                marginBottom: '8px',
                backgroundColor: '$primary',
                color: '$primaryContrastText',
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
                  css={{
                    flex: 1,
                    minHeight: '200px',
                    backgroundColor: snapshot.isDraggingOver ? '$hover' : '$background',
                    borderRadius: '4px',
                    padding: '8px',
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
                          css={{
                            marginBottom: '4px',
                            boxShadow: snapshot.isDragging ? '0 4px 20px rgba(0,0,0,0.15)' : '0 1px 3px rgba(0,0,0,0.12)',
                            transform: snapshot.isDragging ? 'rotate(3deg)' : 'none',
                          }}
                        >
                          <CardContent css={{ padding: '16px' }}>
                            <Typography variant="subtitle2" fontWeight={600}>
                              {candidate.name || candidate.filename || 'Unknown'}
                            </Typography>
                            {candidate.email && (
                              <Typography variant="caption" color="secondary">
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
