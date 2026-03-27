// React для создания компонента
import React from 'react';
// Компоненты Material UI для создания интерфейса
import {
  Box,
  Stack,
  Typography,
  Chip,
  Divider,
} from '@mui/material';
// Иконки Material UI
import {
  CheckCircle,
  RadioButtonUnchecked,
  Circle,
} from '@mui/icons-material';

/**
 * Этап процесса подачи заявки
 */
export interface ApplicationStage {
  /** Уникальный идентификатор этапа */
  id: string;
  /** Название этапа */
  name: string;
  /** Статус этапа */
  status: 'completed' | 'current' | 'upcoming';
  /** Дата завершения этапа (если завершен) */
  completed_at?: string;
  /** Описание этапа */
  description?: string;
}

/**
 * Свойства компонента StatusTimeline
 */
interface StatusTimelineProps {
  /** Список этапов для отображения */
  stages: ApplicationStage[];
  /** Компактный режим отображения */
  compact?: boolean;
}

/**
 * Компонент визуализации прогресса заявки
 *
 * Отображает вертикальную временную шкалу с этапами обработки заявки:
 * - Завершенные этапы (зеленая галочка)
 * - Текущий этап (синий круг)
 * - Предстоящие этапы (серый круг)
 *
 * Каждый этап показывает:
 * - Название этапа
 * - Статус (цветовая индикация)
 * - Дату завершения (для завершенных этапов)
 * - Описание (опционально)
 *
 * @example
 * ```tsx
 * const stages = [
 *   { id: '1', name: 'Application Submitted', status: 'completed', completed_at: '2024-01-01' },
 *   { id: '2', name: 'Under Review', status: 'current' },
 *   { id: '3', name: 'Interview', status: 'upcoming' },
 * ];
 * <StatusTimeline stages={stages} />
 * ```
 *
 * @example
 * ```tsx
 * <StatusTimeline stages={stages} compact={true} />
 * ```
 */
export function StatusTimeline({ stages, compact = false }: StatusTimelineProps) {
  /**
   * Форматирует дату в относительный формат
   * @param dateString - Дата в формате ISO
   * @returns Отформатированная строка даты
   */
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return date.toLocaleDateString();
  };

  /**
   * Получает иконку на основе статуса этапа
   * @param status - Статус этапа
   * @returns React элемент с иконкой
   */
  const getStatusIcon = (status: ApplicationStage['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle sx={{ fontSize: 24, color: 'success.main' }} />;
      case 'current':
        return <Circle sx={{ fontSize: 24, color: 'primary.main' }} />;
      case 'upcoming':
        return <RadioButtonUnchecked sx={{ fontSize: 24, color: 'action.disabled' }} />;
    }
  };

  /**
   * Получает цвет линии соединения на основе статуса
   * @param status - Статус этапа
   * @returns Цвет линии
   */
  const getLineColor = (status: ApplicationStage['status']) => {
    switch (status) {
      case 'completed':
        return 'success.main';
      case 'current':
        return 'primary.main';
      case 'upcoming':
        return 'action.disabled';
    }
  };

  /**
   * Получает цвет чипа на основе статуса
   * @param status - Статус этапа
   * @returns Цвет чипа Material UI
   */
  const getStatusColor = (status: ApplicationStage['status']): 'success' | 'primary' | 'default' => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'current':
        return 'primary';
      case 'upcoming':
        return 'default';
    }
  };

  /**
   * Получает текстовую метку статуса
   * @param status - Статус этапа
   * @returns Отформатированная строка метки
   */
  const getStatusLabel = (status: ApplicationStage['status']) => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'current':
        return 'In Progress';
      case 'upcoming':
        return 'Pending';
    }
  };

  if (stages.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No application stages to display
        </Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={0}>
      {stages.map((stage, index) => {
        const isLast = index === stages.length - 1;

        return (
          <Box key={stage.id}>
            {/* Этап */}
            <Box sx={{ display: 'flex', gap: 2 }}>
              {/* Иконка и линия */}
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  minWidth: 24,
                }}
              >
                {/* Иконка статуса */}
                <Box sx={{ flexShrink: 0 }}>
                  {getStatusIcon(stage.status)}
                </Box>

                {/* Соединительная линия */}
                {!isLast && (
                  <Divider
                    orientation="vertical"
                    sx={{
                      flexGrow: 1,
                      minHeight: compact ? 32 : 48,
                      borderColor: getLineColor(stage.status),
                      borderWidth: 2,
                      my: 0.5,
                    }}
                  />
                )}
              </Box>

              {/* Содержимое этапа */}
              <Box
                sx={{
                  flexGrow: 1,
                  pb: isLast ? 0 : (compact ? 2 : 3),
                }}
              >
                {/* Заголовок этапа */}
                <Stack
                  direction="row"
                  spacing={1}
                  alignItems="center"
                  sx={{ mb: compact ? 0.5 : 1 }}
                >
                  <Typography
                    variant={compact ? 'body2' : 'body1'}
                    fontWeight={stage.status === 'current' ? 600 : 400}
                    color={stage.status === 'upcoming' ? 'text.secondary' : 'text.primary'}
                  >
                    {stage.name}
                  </Typography>
                  <Chip
                    label={getStatusLabel(stage.status)}
                    size="small"
                    color={getStatusColor(stage.status)}
                    sx={{
                      height: compact ? 20 : 24,
                      fontSize: compact ? '0.65rem' : '0.75rem',
                      borderRadius: 1,
                    }}
                  />
                </Stack>

                {/* Дата завершения */}
                {stage.completed_at && !compact && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    {formatDate(stage.completed_at)}
                  </Typography>
                )}

                {/* Описание */}
                {stage.description && !compact && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    {stage.description}
                  </Typography>
                )}
              </Box>
            </Box>
          </Box>
        );
      })}
    </Stack>
  );
}
