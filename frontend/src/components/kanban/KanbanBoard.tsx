// React для создания компонента
import React from 'react';
// Библиотека drag-and-drop для kanban доски
import { DragDropContext, Draggable, DropResult } from '@hello-pangea/dnd';
// Компоненты Material UI для создания интерфейса
import { Box, Paper, Typography, Divider, useTheme, alpha } from '@mui/material';
// Компонент колонки с WIP индикатором
import KanbanColumn, { KanbanColumnData } from './KanbanColumn';
// Компонент карточки кандидата
import KanbanCard, { KanbanCandidate } from './KanbanCard';

/**
 * Интерфейс колонки канбан доски (старый формат для обратной совместимости)
 */
export interface Column {
  /** Уникальный идентификатор колонки */
  id: string;
  /** Заголовок колонки */
  title: string;
  /** Список кандидатов в колонке */
  candidates: any[];
  /** WIP лимит для колонки */
  wip_limit?: number | null;
  /** Цвет заголовка колонки */
  color?: string;
}

/**
 * Интерфейс swimlane для группировки кандидатов
 */
export interface Swimlane {
  /** Уникальный идентификатор swimlane */
  id: string;
  /** Заголовок swimlane */
  title: string;
  /** Подзаголовок (например, название вакансии) */
  subtitle?: string;
  /** Колонки в swimlane */
  columns: KanbanColumnData[];
  /** Общее количество кандидатов в swimlane */
  total_candidates?: number;
}

/**
 * Свойства компонента KanbanBoard
 */
export interface KanbanBoardProps {
  /** Массив колонок для отображения (простой режим без swimlanes) */
  columns?: Column[];
  /** Массив swimlanes для группировки (режим со swimlanes) */
  swimlanes?: Swimlane[];
  /** Обработчик завершения перетаскивания */
  onDragEnd: (result: DropResult) => void | Promise<void>;
  /** Обработчик клика по карточке кандидата */
  onCardClick?: (candidateId: string) => void;
  /** Показывать ли теги на карточках */
  showTags?: boolean;
  /** Показывать ли оценку соответствия на карточках */
  showMatchScore?: boolean;
  /** Показывать ли информацию об активности на карточках */
  showActivity?: boolean;
  /** Показывать ли WIP индикаторы */
  showWipIndicator?: boolean;
}

/**
 * Преобразовать кандидата из старого формата в формат KanbanCandidate
 *
 * @param candidate - Кандидат в старом формате
 * @returns Кандидат в формате KanbanCandidate
 */
const mapToKanbanCandidate = (candidate: any): KanbanCandidate => {
  return {
    id: candidate.id,
    name: candidate.name,
    filename: candidate.filename,
    email: candidate.email,
    match_score: candidate.match_score,
    tags: candidate.tags?.map((tag: any) => ({
      id: tag.id || tag,
      tag_name: tag.tag_name || tag,
      color: tag.color,
    })),
    stage_name: candidate.stage_name || candidate.current_stage,
    current_stage: candidate.current_stage || candidate.stage,
    latest_activity: candidate.latest_activity,
    notes_count: candidate.notes_count,
    vacancy_title: candidate.vacancy_title,
  };
};

/**
 * Преобразовать колонку из старого формата в формат KanbanColumnData
 *
 * @param column - Колонка в старом формате
 * @returns Колонка в формате KanbanColumnData
 */
const mapToKanbanColumnData = (column: Column): KanbanColumnData => {
  return {
    id: column.id,
    title: column.title,
    candidates: column.candidates.map(mapToKanbanCandidate),
    wip_limit: column.wip_limit,
    color: column.color,
  };
};

/**
 * Компонент канбан доски
 *
 * Канбан доска с поддержкой swimlanes и drag-and-drop для управления пайплайном кандидатов.
 * Использует библиотеку hello-pangea/dnd для реализации перетаскивания.
 *
 * Поддерживает два режима:
 * 1. Простой режим: только колонки без группировки
 * 2. Режим swimlanes: группировка кандидатов по вакансиям или рекрутерам
 *
 * @param props - Свойства компонента KanbanBoardProps
 * @returns React элемент
 */
const KanbanBoard: React.FC<KanbanBoardProps> = ({
  columns,
  swimlanes,
  onDragEnd,
  onCardClick,
  showTags = true,
  showMatchScore = true,
  showActivity = true,
  showWipIndicator = true,
}) => {
  const theme = useTheme();

  // Определяем режим работы: swimlanes или простые колонки
  const hasSwimlanes = swimlanes && swimlanes.length > 0;
  const effectiveColumns = columns?.map(mapToKanbanColumnData) || [];

  /**
   * Рендеринг одной колонки с карточками кандидатов
   *
   * @param column - Данные колонки
   * @returns React элемент колонки
   */
  const renderColumn = (column: KanbanColumnData) => (
    <KanbanColumn
      key={column.id}
      column={column}
      showWipIndicator={showWipIndicator}
      renderCard={(candidate: KanbanCandidate, index: number) => (
        <Draggable
          key={candidate.id}
          draggableId={candidate.id}
          index={index}
        >
          {(provided, snapshot) => (
            <KanbanCard
              candidate={candidate}
              provided={provided}
              snapshot={snapshot}
              onClick={onCardClick ? () => onCardClick(candidate.id) : undefined}
              showTags={showTags}
              showMatchScore={showMatchScore}
              showActivity={showActivity}
            />
          )}
        </Draggable>
      )}
    />
  );

  /**
   * Рендеринг swimlane с заголовком и колонками
   *
   * @param swimlane - Данные swimlane
   * @param index - Индекс swimlane для определения разделителя
   * @returns React элемент swimlane
   */
  const renderSwimlane = (swimlane: Swimlane, index: number) => (
    <Box
      key={swimlane.id}
      sx={{
        mb: 3,
      }}
    >
      {/* Заголовок swimlane */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          mb: 2,
          bgcolor: alpha(theme.palette.primary.main, 0.08),
          border: '1px solid',
          borderColor: alpha(theme.palette.primary.main, 0.2),
          borderRadius: 2,
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Box>
            <Typography
              variant="subtitle1"
              fontWeight={600}
              color="primary.main"
            >
              {swimlane.title}
            </Typography>
            {swimlane.subtitle && (
              <Typography variant="caption" color="text.secondary">
                {swimlane.subtitle}
              </Typography>
            )}
          </Box>
          {swimlane.total_candidates !== undefined && (
            <Typography
              variant="caption"
              sx={{
                px: 1.5,
                py: 0.5,
                borderRadius: 1,
                bgcolor: alpha(theme.palette.primary.main, 0.15),
                color: 'primary.main',
                fontWeight: 500,
              }}
            >
              {swimlane.total_candidates} candidates
            </Typography>
          )}
        </Box>
      </Paper>

      {/* Колонки в swimlane */}
      <Box
        sx={{
          display: 'flex',
          gap: 2,
          overflowX: 'auto',
          pb: 1,
        }}
      >
        {swimlane.columns.map(renderColumn)}
      </Box>

      {/* Разделитель между swimlanes */}
      {index < (swimlanes?.length || 0) - 1 && (
        <Divider sx={{ mt: 3 }} />
      )}
    </Box>
  );

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      {/* Режим со swimlanes */}
      {hasSwimlanes ? (
        <Box
          sx={{
            height: '100%',
            overflowY: 'auto',
          }}
        >
          {swimlanes!.map((swimlane, index) => renderSwimlane(swimlane, index))}
        </Box>
      ) : (
        /* Простой режим без swimlanes */
        <Box
          sx={{
            display: 'flex',
            gap: 2,
            overflowX: 'auto',
            height: '100%',
          }}
        >
          {effectiveColumns.map(renderColumn)}
        </Box>
      )}
    </DragDropContext>
  );
};

export default KanbanBoard;
export { KanbanBoard };
