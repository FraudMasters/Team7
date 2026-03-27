import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  TextField,
  Typography,
  IconButton,
  Tooltip,
  Stack,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { KanbanBoard, type Swimlane } from '../../components/kanban/KanbanBoard';
import { SwimlaneSelector, type SwimlaneGroupBy } from '../../components/kanban/SwimlaneSelector';
import {
  useKanbanBoard,
  useUpdateCandidateStage,
} from '../../hooks/useRecruiterData';
import type { DropResult } from '@hello-pangea/dnd';

// Страница канбан-доски для управления кандидатами
export function CandidatesKanbanPage() {
  const navigate = useNavigate();

  // Состояние для поиска кандидатов
  const [searchTerm, setSearchTerm] = useState('');
  // Состояние для группировки swimlanes
  const [groupBy, setGroupBy] = useState<SwimlaneGroupBy>('none');

  // Получение данных канбан-доски с swimlanes
  const { data: kanbanData, isLoading, error, refetch } = useKanbanBoard({
    group_by: groupBy === 'none' ? undefined : groupBy,
    search: searchTerm || undefined,
  });
  const updateStage = useUpdateCandidateStage();

  // Преобразование данных API в формат для KanbanBoard
  const swimlanes = useMemo((): Swimlane[] | undefined => {
    if (!kanbanData || groupBy === 'none') return undefined;

    return kanbanData.swimlanes.map((swimlane) => ({
      id: swimlane.id,
      title: swimlane.title,
      subtitle: swimlane.subtitle,
      total_candidates: swimlane.total_candidates,
      columns: swimlane.stages.map((stage) => ({
        id: stage.stage_id || stage.stage_name.toLowerCase().replace(/\s+/g, '-'),
        title: stage.display_name || stage.stage_name,
        candidates: stage.candidates.map((c) => ({
          id: c.id,
          filename: c.filename,
          current_stage: c.current_stage,
          stage_name: c.current_stage,
          tags: c.tags.map((t) => ({
            id: t.id,
            tag_name: t.tag_name,
            color: t.color,
          })),
          notes_count: c.notes_count,
        })),
        wip_limit: stage.wip_limit,
        color: undefined,
      })),
    }));
  }, [kanbanData, groupBy]);

  // Формирование простых колонок (без swimlanes) для обратной совместимости
  const columns = useMemo(() => {
    if (!kanbanData || groupBy !== 'none') return undefined;

    // Создание колонок из сводных данных по этапам
    return kanbanData.stages.map((stage) => {
      // Собираем кандидатов из всех swimlanes для этого этапа
      const stageCandidates = kanbanData.swimlanes.flatMap((sl) =>
        sl.stages
          .filter((s) => s.stage_name === stage.stage_name)
          .flatMap((s) => s.candidates)
      );

      return {
        id: stage.stage_id || stage.stage_name.toLowerCase().replace(/\s+/g, '-'),
        title: stage.display_name || stage.stage_name,
        candidates: stageCandidates.map((c) => ({
          id: c.id,
          filename: c.filename,
          current_stage: c.current_stage,
          stage_name: c.current_stage,
          tags: c.tags.map((t) => ({
            id: t.id,
            tag_name: t.tag_name,
            color: t.color,
          })),
          notes_count: c.notes_count,
        })),
        wip_limit: stage.wip_limit,
      };
    });
  }, [kanbanData, groupBy]);

  // Обработчик завершения перетаскивания
  const handleDragEnd = async (result: DropResult) => {
    if (!result.destination) return;

    const candidateId = result.draggableId as string;
    // Получаем название этапа из destination droppableId
    const destinationId = result.destination.droppableId;
    let newStage = destinationId;

    // Если используем swimlanes, нужно найти название этапа
    if (swimlanes) {
      for (const swimlane of swimlanes) {
        const column = swimlane.columns.find((col) => col.id === destinationId);
        if (column) {
          newStage = column.title;
          break;
        }
      }
    } else if (columns) {
      const column = columns.find((col) => col.id === destinationId);
      if (column) {
        newStage = column.title;
      }
    }

    // Обновление этапа кандидата в БД
    await updateStage.mutateAsync({ candidateId, stage: newStage });
  };

  // Переход к настройке этапов
  const handleOpenSettings = () => {
    navigate('/workflow-stages');
  };

  // Обработчик изменения группировки
  const handleGroupByChange = (value: SwimlaneGroupBy) => {
    setGroupBy(value);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 2, height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      {/* Заголовок страницы */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Candidate Pipeline
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Drag candidates between stages to update their status
        </Typography>
      </Box>

      {/* Панель инструментов */}
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        spacing={2}
        sx={{ mb: 3 }}
        alignItems={{ xs: 'flex-start', sm: 'center' }}
        justifyContent="space-between"
      >
        {/* Левая часть: поиск и swimlane selector */}
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={2}
          alignItems={{ xs: 'flex-start', sm: 'center' }}
        >
          {/* Поле поиска кандидатов */}
          <TextField
            placeholder="Search candidates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            size="small"
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
            sx={{ minWidth: 250 }}
          />

          {/* Селектор swimlanes */}
          <SwimlaneSelector
            value={groupBy}
            onChange={handleGroupByChange}
            showLabel={true}
            variant="plain"
          />
        </Stack>

        {/* Правая часть: настройки этапов и обновление */}
        <Stack direction="row" spacing={1}>
          {/* Кнопка обновления */}
          <Tooltip title="Refresh board">
            <IconButton
              onClick={() => refetch()}
              disabled={isLoading}
              color="default"
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>

          {/* Кнопка настройки этапов */}
          <Tooltip title="Customize stages">
            <IconButton
              onClick={handleOpenSettings}
              color="primary"
            >
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Stack>

      {/* Индикатор загрузки */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Сообщение об ошибке */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load kanban board. Please try again.
        </Alert>
      )}

      {/* Канбан-доска с перетаскиванием */}
      {!isLoading && !error && (
        <Box sx={{ flex: 1, overflow: 'hidden' }}>
          <KanbanBoard
            columns={columns}
            swimlanes={swimlanes}
            onDragEnd={handleDragEnd}
            showWipIndicator={true}
            showTags={true}
            showMatchScore={true}
            showActivity={true}
          />
        </Box>
      )}

      {/* Информация о WIP лимитах */}
      {!isLoading && !error && kanbanData && (
        <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Total candidates: {kanbanData.total_candidates}
          </Typography>
          {kanbanData.stages.some((s) => s.wip_limit) && (
            <Typography variant="caption" color="text.secondary">
              • WIP limits are shown per stage
            </Typography>
          )}
        </Box>
      )}
    </Container>
  );
}
