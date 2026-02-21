// React для создания компонента
import React from 'react';
// Хук для интернационализации
import { useTranslation } from 'react-i18next';
// Компоненты Material UI для создания интерфейса
import {
  Box,
  Typography,
  ToggleButtonGroup as MuiToggleButtonGroup,
  ToggleButton as MuiToggleButton,
  Paper,
  Tooltip,
} from '@mui/material';
// Иконки Material UI
import {
  ViewColumn as ColumnIcon,
  Work as WorkIcon,
  Person as PersonIcon,
} from '@mui/icons-material';

/**
 * Типы группировки для swimlanes
 */
export type SwimlaneGroupBy = 'none' | 'job' | 'recruiter';

/**
 * Опция группировки для отображения
 */
export interface SwimlaneOption {
  /** Значение опции */
  value: SwimlaneGroupBy;
  /** Название для отображения */
  label: string;
  /** Иконка опции */
  icon: React.ReactNode;
  /** Описание для tooltip */
  tooltip: string;
}

/**
 * Свойства компонента SwimlaneSelector
 */
export interface SwimlaneSelectorProps {
  /** Текущий тип группировки */
  value: SwimlaneGroupBy;
  /** Обработчик изменения группировки */
  onChange: (value: SwimlaneGroupBy) => void;
  /** Отключить селектор */
  disabled?: boolean;
  /** Размер кнопок */
  size?: 'small' | 'medium' | 'large';
  /** Показывать ли label */
  showLabel?: boolean;
  /** Показывать ли tooltips */
  showTooltips?: boolean;
  /** Вариант отображения (paper wrapper или plain) */
  variant?: 'outlined' | 'plain';
}

/**
 * Получить опции группировки
 *
 * @param t - Функция перевода
 * @returns Массив опций для селектора
 */
const getGroupByOptions = (t: (key: string, options?: Record<string, unknown>) => string): SwimlaneOption[] => [
  {
    value: 'none',
    label: t('kanban.swimlanes.none', 'None') || 'None',
    icon: <ColumnIcon fontSize="small" />,
    tooltip: t('kanban.swimlanes.noneTooltip', 'Show all candidates in single view') || 'Show all candidates in single view',
  },
  {
    value: 'job',
    label: t('kanban.swimlanes.byJob', 'By Job') || 'By Job',
    icon: <WorkIcon fontSize="small" />,
    tooltip: t('kanban.swimlanes.byJobTooltip', 'Group candidates by vacancy/job position') || 'Group candidates by vacancy/job position',
  },
  {
    value: 'recruiter',
    label: t('kanban.swimlanes.byRecruiter', 'By Recruiter') || 'By Recruiter',
    icon: <PersonIcon fontSize="small" />,
    tooltip: t('kanban.swimlanes.byRecruiterTooltip', 'Group candidates by assigned recruiter') || 'Group candidates by assigned recruiter',
  },
];

/**
 * Компонент селектора swimlanes для канбан доски
 *
 * Позволяет переключать режим группировки кандидатов:
 * - None: все кандидаты в одном представлении
 * - By Job: группировка по вакансиям (swimlanes по должностям)
 * - By Recruiter: группировка по рекрутерам
 *
 * @param props - Свойства компонента SwimlaneSelectorProps
 * @returns React элемент
 *
 * @example
 * ```tsx
 * const [groupBy, setGroupBy] = useState<SwimlaneGroupBy>('none');
 *
 * <SwimlaneSelector
 *   value={groupBy}
 *   onChange={setGroupBy}
 *   showLabel={true}
 *   variant="outlined"
 * />
 * ```
 */
const SwimlaneSelector: React.FC<SwimlaneSelectorProps> = ({
  value,
  onChange,
  disabled = false,
  size = 'small',
  showLabel = true,
  showTooltips = true,
  variant = 'outlined',
}) => {
  const { t } = useTranslation();

  // Получение опций группировки с переводами
  const options = getGroupByOptions(t as (key: string, options?: Record<string, unknown>) => string);

  /**
   * Обработчик изменения группировки
   */
  const handleChange = (_event: React.MouseEvent<HTMLElement>, newValue: SwimlaneGroupBy | null) => {
    if (newValue !== null) {
      onChange(newValue);
    }
  };

  // Контент селектора
  const selectorContent = (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 2,
      }}
    >
      {/* Label */}
      {showLabel && (
        <Typography
          variant="subtitle2"
          color="text.secondary"
          sx={{
            fontWeight: 600,
            whiteSpace: 'nowrap',
          }}
        >
          {t('kanban.swimlanes.groupBy', 'Group by:') || 'Group by:'}
        </Typography>
      )}

      {/* Toggle Buttons */}
      <MuiToggleButtonGroup
        value={value}
        exclusive
        onChange={handleChange}
        size={size}
        disabled={disabled}
        sx={{
          '& .MuiToggleButtonGroup-grouped': {
            border: 1,
            borderColor: 'divider',
            '&.Mui-disabled': {
              borderColor: 'divider',
            },
            '&:not(:first-of-type)': {
              borderRadius: 0,
              marginLeft: '-1px',
            },
            '&:first-of-type': {
              borderRadius: '4px 0 0 4px',
            },
            '&:last-of-type': {
              borderRadius: '0 4px 4px 0',
            },
            '&.Mui-selected': {
              backgroundColor: 'primary.main',
              color: 'primary.contrastText',
              borderColor: 'primary.main',
              '&:hover': {
                backgroundColor: 'primary.dark',
              },
            },
          },
        }}
      >
        {options.map((option) => {
          const button = (
            <MuiToggleButton
              key={option.value}
              value={option.value}
              sx={{
                px: 2,
                py: 0.75,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                '& .MuiSvgIcon-root': {
                  fontSize: '1rem',
                },
              }}
            >
              {option.icon}
              <Typography
                variant="body2"
                sx={{
                  fontWeight: value === option.value ? 600 : 400,
                  display: { xs: 'none', sm: 'inline' },
                }}
              >
                {option.label}
              </Typography>
            </MuiToggleButton>
          );

          // Оборачиваем в Tooltip если включено
          if (showTooltips) {
            return (
              <Tooltip
                key={option.value}
                title={option.tooltip}
                arrow
                placement="top"
              >
                {button}
              </Tooltip>
            );
          }

          return button;
        })}
      </MuiToggleButtonGroup>
    </Box>
  );

  // Если вариант outlined, оборачиваем в Paper
  if (variant === 'outlined') {
    return (
      <Paper
        elevation={0}
        sx={{
          p: 1.5,
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 2,
          display: 'inline-flex',
        }}
      >
        {selectorContent}
      </Paper>
    );
  }

  return selectorContent;
};

export default SwimlaneSelector;
export { SwimlaneSelector };
