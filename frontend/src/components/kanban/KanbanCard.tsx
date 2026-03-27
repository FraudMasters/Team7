// React для создания компонента
import React from 'react';
// Компоненты Material UI для создания интерфейса
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Stack,
  alpha,
  useTheme,
} from '@mui/material';
// Типы для drag-and-drop
import { DraggableProvided, DraggableStateSnapshot } from '@hello-pangea/dnd';

/**
 * Тег кандидата для отображения на карточке
 */
export interface CandidateTag {
  /** Уникальный идентификатор тега */
  id: string;
  /** Название тега */
  tag_name: string;
  /** Цвет тега (hex формат) */
  color?: string;
}

/**
 * Данные кандидата для карточки канбан доски
 */
export interface KanbanCandidate {
  /** Уникальный идентификатор кандидата */
  id: string;
  /** Имя кандидата или имя файла резюме */
  name?: string;
  /** Имя файла резюме */
  filename?: string;
  /** Email кандидата */
  email?: string;
  /** Оценка соответствия вакансии (0-100) */
  match_score?: number;
  /** Список тегов кандидата */
  tags?: CandidateTag[];
  /** Название текущего этапа */
  stage_name?: string;
  /** Текущий этап кандидата */
  current_stage?: string;
  /** Дата последней активности */
  latest_activity?: {
    created_at: string;
    activity_type: string;
  };
  /** Количество заметок */
  notes_count?: number;
  /** Название вакансии */
  vacancy_title?: string;
}

/**
 * Свойства компонента KanbanCard
 */
export interface KanbanCardProps {
  /** Данные кандидата для отображения */
  candidate: KanbanCandidate;
  /** Drag-and-drop provided объект от @hello-pangea/dnd */
  provided: DraggableProvided;
  /** Drag-and-drop snapshot объект для определения состояния перетаскивания */
  snapshot: DraggableStateSnapshot;
  /** Обработчик клика по карточке */
  onClick?: () => void;
  /** Показывать ли теги */
  showTags?: boolean;
  /** Максимальное количество отображаемых тегов */
  maxTagsVisible?: number;
  /** Показывать ли оценку соответствия */
  showMatchScore?: boolean;
  /** Показывать ли активность */
  showActivity?: boolean;
}

/**
 * Получить цвет для оценки соответствия
 *
 * @param score - Оценка соответствия (0-100)
 * @returns Цвет для отображения
 */
const getMatchScoreColor = (score: number): 'success' | 'warning' | 'error' => {
  if (score >= 70) return 'success';
  if (score >= 40) return 'warning';
  return 'error';
};

/**
 * Получить цвет фона для тега
 *
 * @param color - Цвет тега в hex формате
 * @param defaultColor - Цвет по умолчанию если цвет не указан
 * @returns Объект со стилями для фона и текста
 */
const getTagStyle = (color?: string, defaultColor?: string) => {
  if (color) {
    return {
      backgroundColor: color,
      color: 'white',
    };
  }
  return {
    backgroundColor: alpha(defaultColor || '#757575', 0.15),
    color: defaultColor || 'text.secondary',
  };
};

/**
 * Компонент карточки кандидата для канбан доски
 *
 * Отображает карточку кандидата с:
 * - Именем кандидата
 * - Бейджем с оценкой соответствия вакансии
 * - Списком тегов
 * - Информацией о последней активности
 *
 * Компонент разработан для использования внутри KanbanBoard
 * и поддерживает drag-and-drop через @hello-pangea/dnd.
 *
 * @param props - Свойства компонента KanbanCardProps
 * @returns React элемент
 *
 * @example
 * ```tsx
 * <Draggable draggableId={candidate.id} index={index}>
 *   {(provided, snapshot) => (
 *     <KanbanCard
 *       candidate={candidate}
 *       provided={provided}
 *       snapshot={snapshot}
 *       onClick={() => openCandidateDetails(candidate.id)}
 *     />
 *   )}
 * </Draggable>
 * ```
 */
const KanbanCard: React.FC<KanbanCardProps> = ({
  candidate,
  provided,
  snapshot,
  onClick,
  showTags = true,
  maxTagsVisible = 3,
  showMatchScore = true,
  showActivity = true,
}) => {
  const theme = useTheme();

  // Отображаемое имя кандидата
  const displayName = candidate.name || candidate.filename || 'Unknown Candidate';

  // Форматирование оценки соответствия
  const matchScoreDisplay = candidate.match_score !== undefined
    ? `${Math.round(candidate.match_score)}%`
    : null;

  // Теги для отображения (ограниченное количество)
  const visibleTags = showTags && candidate.tags
    ? candidate.tags.slice(0, maxTagsVisible)
    : [];
  const hiddenTagsCount = candidate.tags
    ? Math.max(0, candidate.tags.length - maxTagsVisible)
    : 0;

  // Форматирование даты активности
  const activityDate = candidate.latest_activity
    ? new Date(candidate.latest_activity.created_at).toLocaleDateString()
    : null;

  return (
    <Card
      ref={provided.innerRef}
      {...provided.draggableProps}
      {...provided.dragHandleProps}
      onClick={onClick}
      sx={{
        mb: 1,
        cursor: onClick ? 'pointer' : 'grab',
        boxShadow: snapshot.isDragging ? 8 : 1,
        transform: snapshot.isDragging ? 'rotate(3deg)' : 'none',
        transition: 'box-shadow 0.2s ease, transform 0.2s ease',
        '&:hover': {
          boxShadow: 4,
        },
        '&:active': {
          cursor: 'grabbing',
        },
      }}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        {/* Заголовок карточки: имя и оценка соответствия */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            mb: 0.5,
          }}
        >
          {/* Имя кандидата или имя файла резюме */}
          <Typography
            variant="subtitle2"
            fontWeight={600}
            sx={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              flex: 1,
              mr: 1,
            }}
            title={displayName}
          >
            {displayName}
          </Typography>

          {/* Бейдж с оценкой соответствия */}
          {showMatchScore && matchScoreDisplay && (
            <Chip
              label={matchScoreDisplay}
              size="small"
              color={getMatchScoreColor(candidate.match_score!)}
              sx={{
                height: 22,
                fontSize: '0.75rem',
                fontWeight: 600,
                flexShrink: 0,
              }}
            />
          )}
        </Box>

        {/* Email кандидата если доступен */}
        {candidate.email && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              display: 'block',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              mb: 0.5,
            }}
            title={candidate.email}
          >
            {candidate.email}
          </Typography>
        )}

        {/* Название вакансии если доступно */}
        {candidate.vacancy_title && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              display: 'block',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              mb: 0.5,
            }}
            title={candidate.vacancy_title}
          >
            {candidate.vacancy_title}
          </Typography>
        )}

        {/* Теги кандидата */}
        {showTags && visibleTags.length > 0 && (
          <Stack
            direction="row"
            spacing={0.5}
            sx={{
              mt: 1,
              flexWrap: 'wrap',
              gap: 0.5,
            }}
          >
            {visibleTags.map((tag) => {
              const tagStyle = getTagStyle(tag.color, theme.palette.grey[500]);
              return (
                <Chip
                  key={tag.id}
                  label={tag.tag_name}
                  size="small"
                  sx={{
                    height: 20,
                    fontSize: '0.7rem',
                    fontWeight: 500,
                    ...tagStyle,
                  }}
                  title={tag.tag_name}
                />
              );
            })}
            {/* Счетчик скрытых тегов */}
            {hiddenTagsCount > 0 && (
              <Chip
                label={`+${hiddenTagsCount}`}
                size="small"
                sx={{
                  height: 20,
                  fontSize: '0.7rem',
                  backgroundColor: alpha(theme.palette.grey[300], 0.5),
                  color: 'text.secondary',
                }}
                title={`${hiddenTagsCount} more tags`}
              />
            )}
          </Stack>
        )}

        {/* Информация об активности и заметках */}
        {showActivity && (activityDate || (candidate.notes_count && candidate.notes_count > 0)) && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1.5,
              mt: 1.5,
              pt: 1,
              borderTop: '1px solid',
              borderColor: 'divider',
            }}
          >
            {/* Последняя активность */}
            {activityDate && (
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.5,
                }}
              >
                <Box
                  sx={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    backgroundColor: 'success.main',
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  {activityDate}
                </Typography>
              </Box>
            )}

            {/* Количество заметок */}
            {candidate.notes_count && candidate.notes_count > 0 && (
              <Typography variant="caption" color="text.secondary">
                {candidate.notes_count} {candidate.notes_count === 1 ? 'note' : 'notes'}
              </Typography>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default KanbanCard;
export { KanbanCard };
