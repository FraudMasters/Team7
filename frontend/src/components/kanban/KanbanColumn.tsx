// React для создания компонента
import React from 'react';
// Библиотека drag-and-drop для kanban доски
import { Droppable, DroppableProvided, DroppableStateSnapshot } from '@hello-pangea/dnd';
// Компоненты Material UI для создания интерфейса
import {
  Box,
  Paper,
  Typography,
  alpha,
  useTheme,
} from '@mui/material';
// Импорт типа кандидата из KanbanCard
import { KanbanCandidate } from './KanbanCard';
// Компонент индикатора WIP лимита
import WipLimitIndicator from './WipLimitIndicator';

/**
 * Свойства колонки канбан доски
 */
export interface KanbanColumnData {
  /** Уникальный идентификатор колонки */
  id: string;
  /** Заголовок колонки */
  title: string;
  /** Список кандидатов в колонке */
  candidates: KanbanCandidate[];
  /** WIP лимит для колонки */
  wip_limit?: number | null;
  /** Цвет заголовка колонки */
  color?: string;
}

/**
 * Свойства компонента KanbanColumn
 */
export interface KanbanColumnProps {
  /** Данные колонки */
  column: KanbanColumnData;
  /** Функция рендеринга карточки кандидата */
  renderCard: (
    candidate: KanbanCandidate,
    index: number
  ) => React.ReactNode;
  /** Обработчик клика по колонке */
  onClick?: () => void;
  /** Показывать ли WIP индикатор */
  showWipIndicator?: boolean;
  /** Минимальная высота колонки */
  minHeight?: number | string;
}

/**
 * Компонент колонки канбан доски
 *
 * Отображает отдельную колонку с:
 * - Заголовком с названием этапа
 * - Индикатором WIP лимита
 * - Областью для перетаскивания карточек
 *
 * Компонент использует Droppable из @hello-pangea/dnd
 * для поддержки drag-and-drop функциональности.
 *
 * @param props - Свойства компонента KanbanColumnProps
 * @returns React элемент
 *
 * @example
 * ```tsx
 * <KanbanColumn
 *   column={{
 *     id: 'stage-1',
 *     title: 'New Candidates',
 *     candidates: candidates,
 *     wip_limit: 10,
 *   }}
 *   renderCard={(candidate, index) => (
 *     <Draggable key={candidate.id} draggableId={candidate.id} index={index}>
 *       {(provided, snapshot) => (
 *         <KanbanCard candidate={candidate} provided={provided} snapshot={snapshot} />
 *       )}
 *     </Draggable>
 *   )}
 * />
 * ```
 */
const KanbanColumn: React.FC<KanbanColumnProps> = ({
  column,
  renderCard,
  onClick,
  showWipIndicator = true,
  minHeight = 200,
}) => {
  const theme = useTheme();
  const candidateCount = column.candidates.length;

  // Определяем цвет заголовка
  const headerBgColor = column.color || theme.palette.primary.main;
  const headerTextColor = theme.palette.getContrastText(headerBgColor);

  // Проверяем превышение WIP лимита
  const isOverLimit = column.wip_limit && column.wip_limit > 0 && candidateCount > column.wip_limit;

  return (
    <Box
      sx={{
        minWidth: 280,
        maxWidth: 320,
        flex: '0 0 auto',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      {/* Заголовок колонки с названием и WIP индикатором */}
      <Paper
        onClick={onClick}
        sx={{
          p: 2,
          mb: 2,
          bgcolor: headerBgColor,
          color: headerTextColor,
          cursor: onClick ? 'pointer' : 'default',
          transition: 'box-shadow 0.2s ease',
          '&:hover': onClick ? {
            boxShadow: 4,
          } : {},
          // Красная полоса сверху при превышении лимита
          ...(isOverLimit && {
            position: 'relative',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: 4,
              bgcolor: 'error.main',
              borderTopLeftRadius: theme.shape.borderRadius,
              borderTopRightRadius: theme.shape.borderRadius,
            },
          }),
        }}
      >
        {/* Название этапа */}
        <Typography variant="h6" fontWeight={600} sx={{ mb: 0.5 }}>
          {column.title}
        </Typography>

        {/* WIP индикатор и счётчик кандидатов */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {showWipIndicator ? (
            <WipLimitIndicator
              current={candidateCount}
              limit={column.wip_limit}
              showWarningText={false}
            />
          ) : (
            <Typography variant="caption" sx={{ opacity: 0.9 }}>
              {candidateCount} {candidateCount === 1 ? 'candidate' : 'candidates'}
            </Typography>
          )}
        </Box>
      </Paper>

      {/* Область для перетаскивания карточек кандидатов */}
      <Droppable droppableId={column.id}>
        {(provided: DroppableProvided, snapshot: DroppableStateSnapshot) => (
          <Box
            {...provided.droppableProps}
            ref={provided.innerRef}
            sx={{
              flex: 1,
              minHeight: minHeight,
              bgcolor: snapshot.isDraggingOver
                ? alpha(theme.palette.primary.main, 0.08)
                : theme.palette.background.default,
              borderRadius: 1,
              p: 1,
              border: '2px dashed',
              borderColor: snapshot.isDraggingOver
                ? 'primary.main'
                : 'divider',
              transition: 'background-color 0.2s ease, border-color 0.2s ease',
              overflowY: 'auto',
              // Стили для скроллбара
              '&::-webkit-scrollbar': {
                width: 6,
              },
              '&::-webkit-scrollbar-track': {
                bgcolor: 'transparent',
              },
              '&::-webkit-scrollbar-thumb': {
                bgcolor: alpha(theme.palette.text.primary, 0.2),
                borderRadius: 3,
                '&:hover': {
                  bgcolor: alpha(theme.palette.text.primary, 0.3),
                },
              },
            }}
          >
            {/* Карточки кандидатов */}
            {column.candidates.map((candidate, index) => (
              <React.Fragment key={candidate.id}>
                {renderCard(candidate, index)}
              </React.Fragment>
            ))}

            {/* Placeholder для корректной работы drag-and-drop */}
            {provided.placeholder}

            {/* Пустое состояние */}
            {column.candidates.length === 0 && !snapshot.isDraggingOver && (
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  minHeight: 100,
                  color: 'text.disabled',
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    fontStyle: 'italic',
                    textAlign: 'center',
                  }}
                >
                  Drop candidates here
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </Droppable>
    </Box>
  );
};

export default KanbanColumn;
export { KanbanColumn };
