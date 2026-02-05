// React для создания компонента
import React from 'react';
// Библиотека drag-and-drop для kanban доски
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
// Компоненты Material UI для создания интерфейса
import { Box, Paper, Typography, Card, CardContent } from '@mui/material';

/**
 * Интерфейс колонки канбан доски
 */
export interface Column {
  /** Уникальный идентификатор колонки */
  id: string;
  /** Заголовок колонки */
  title: string;
  /** Список кандидатов в колонке */
  candidates: any[];
}

/**
 * Свойства компонента KanbanBoard
 */
export interface KanbanBoardProps {
  /** Массив колонок для отображения */
  columns: Column[];
  /** Обработчик завершения перетаскивания */
  onDragEnd: (result: DropResult) => void | Promise<void>;
}

/**
 * Компонент канбан доски
 *
 * Простая kanban доска с drag-and-drop для управления пайплайном кандидатов.
 * Использует библиотеку hello-pangea/dnd для реализации перетаскивания.
 *
 * @param props - Свойства компонента KanbanBoardProps
 * @returns React элемент
 */
const KanbanBoard: React.FC<KanbanBoardProps> = ({ columns, onDragEnd }) => {
  return (
    <DragDropContext onDragEnd={onDragEnd}>
      {/* Контейнер для всех колонок с горизонтальной прокруткой */}
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
            {/* Заголовок колонки с названием и количеством кандидатов */}
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

            {/* Область для перетаскивания карточек кандидатов */}
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
                  {/* Карточки кандидатов в колонке */}
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
                            {/* Имя кандидата или имя файла резюме */}
                            <Typography variant="subtitle2" fontWeight={600}>
                              {candidate.name || candidate.filename || 'Unknown'}
                            </Typography>
                            {/* Email кандидата если доступен */}
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
                  {/* Placeholder для корректной работы drag-and-drop */}
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
