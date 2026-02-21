// React для создания компонента
import React from 'react';
// Компоненты Material UI для создания интерфейса
import { Box, Typography, Chip, Tooltip } from '@mui/material';

/**
 * Статус WIP лимита
 */
export type WipLimitStatus = 'ok' | 'warning' | 'exceeded';

/**
 * Свойства компонента WipLimitIndicator
 */
export interface WipLimitIndicatorProps {
  /** Текущее количество кандидатов в колонке */
  current: number;
  /** Максимально допустимое количество (WIP лимит) */
  limit?: number | null;
  /** Показывать ли текстовый статус при превышении */
  showWarningText?: boolean;
  /** Размер индикатора */
  size?: 'small' | 'medium';
}

/**
 * Определить статус WIP лимита
 *
 * @param current - Текущее количество
 * @param limit - Максимально допустимое количество
 * @returns Статус WIP лимита
 */
const getWipStatus = (current: number, limit?: number | null): WipLimitStatus => {
  // Если лимит не установлен, всегда OK
  if (limit === undefined || limit === null || limit <= 0) {
    return 'ok';
  }

  if (current > limit) {
    return 'exceeded';
  }

  // Предупреждение когда достигнуто 80% лимита
  if (current >= limit * 0.8) {
    return 'warning';
  }

  return 'ok';
};

/**
 * Получить цвет для статуса WIP
 *
 * @param status - Статус WIP лимита
 * @returns Цвет для Material UI компонентов
 */
const getWipColor = (status: WipLimitStatus): 'success' | 'warning' | 'error' => {
  switch (status) {
    case 'exceeded':
      return 'error';
    case 'warning':
      return 'warning';
    default:
      return 'success';
  }
};

/**
 * Компонент индикатора WIP лимита
 *
 * Отображает текущее количество кандидатов относительно WIP лимита:
 * - Зеленый: всё в порядке
 * - Желтый: достигнуто 80% лимита
 * - Красный: лимит превышен
 *
 * @param props - Свойства компонента WipLimitIndicatorProps
 * @returns React элемент
 *
 * @example
 * ```tsx
 * // Без лимита
 * <WipLimitIndicator current={5} />
 *
 * // С лимитом, всё OK
 * <WipLimitIndicator current={3} limit={5} />
 *
 * // Приближается к лимиту (80%)
 * <WipLimitIndicator current={4} limit={5} />
 *
 * // Лимит превышен
 * <WipLimitIndicator current={7} limit={5} />
 * ```
 */
const WipLimitIndicator: React.FC<WipLimitIndicatorProps> = ({
  current,
  limit,
  showWarningText = true,
  size = 'small',
}) => {
  const status = getWipStatus(current, limit);
  const color = getWipColor(status);
  const hasLimit = limit !== undefined && limit !== null && limit > 0;

  // Формирование текста для отображения
  const displayText = hasLimit ? `${current}/${limit}` : `${current}`;

  // Текст подсказки
  const tooltipText = hasLimit
    ? status === 'exceeded'
      ? `WIP limit exceeded by ${current - limit} candidate${current - limit > 1 ? 's' : ''}`
      : status === 'warning'
        ? `WIP limit almost reached (${current}/${limit})`
        : `WIP limit: ${current}/${limit}`
    : `${current} candidate${current !== 1 ? 's' : ''}`;

  return (
    <Tooltip title={tooltipText} arrow>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        {/* Основной индикатор счётчика */}
        <Chip
          label={displayText}
          size={size}
          color={color}
          sx={{
            fontWeight: 600,
            height: size === 'small' ? 22 : 28,
            fontSize: size === 'small' ? '0.75rem' : '0.85rem',
            '& .MuiChip-label': {
              px: 1,
            },
          }}
        />

        {/* Текстовое предупреждение при превышении лимита */}
        {showWarningText && status === 'exceeded' && (
          <Typography
            variant="caption"
            color="error.main"
            sx={{
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
            }}
          >
            ⚠️ Over limit
          </Typography>
        )}
      </Box>
    </Tooltip>
  );
};

export default WipLimitIndicator;
export { WipLimitIndicator, getWipStatus, getWipColor };
