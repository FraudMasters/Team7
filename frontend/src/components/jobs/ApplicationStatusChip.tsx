// React для создания компонента
import React from 'react';
// Компоненты Material UI для создания интерфейса
import { Chip, ChipProps } from '@mui/material';

/**
 * Тип статуса заявки на работу
 * Поддерживает все возможные статусы из ATS
 */
type ApplicationStatus =
  | 'applied'
  | 'pending'
  | 'under_review'
  | 'shortlisted'
  | 'interview'
  | 'interview_scheduled'
  | 'technical_assessment'
  | 'offer'
  | 'offered'
  | 'accepted'
  | 'rejected'
  | 'withdrawn'
  | 'on_hold'
  | string;

/**
 * Свойства компонента ApplicationStatusChip
 */
interface ApplicationStatusChipProps extends Omit<ChipProps, 'color'> {
  /** Статус заявки */
  status: ApplicationStatus;
  /** Название этапа (опционально, переопределяет status) */
  stageName?: string;
}

/**
 * Возвращает цвет чипа на основе статуса
 * @param status - Статус заявки
 * @returns Цвет из палитры MUI
 */
const getStatusColor = (status: ApplicationStatus): ChipProps['color'] => {
  const normalizedStatus = status.toLowerCase().replace(/ /g, '_');

  switch (normalizedStatus) {
    case 'applied':
    case 'pending':
      return 'default';
    case 'under_review':
    case 'shortlisted':
    case 'interview':
    case 'interview_scheduled':
    case 'technical_assessment':
      return 'info';
    case 'offer':
    case 'offered':
    case 'accepted':
      return 'success';
    case 'rejected':
      return 'error';
    case 'withdrawn':
    case 'on_hold':
      return 'warning';
    default:
      return 'default';
  }
};

/**
 * Возвращает текстовую метку для статуса
 * @param status - Статус заявки
 * @param stageName - Название этапа (опционально)
 * @returns Отформатированная строка метки
 */
const getStatusLabel = (status: ApplicationStatus, stageName?: string): string => {
  if (stageName) {
    return stageName;
  }

  const normalizedStatus = status.toLowerCase().replace(/_/g, ' ');
  return normalizedStatus
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * Чип статуса заявки на работу
 *
 * Отображает статус заявки в виде цветного чипа.
 * Автоматически определяет цвет на основе статуса:
 * - default: applied, pending
 * - info: under_review, shortlisted, interview, technical_assessment
 * - success: offer, offered, accepted
 * - error: rejected
 * - warning: withdrawn, on_hold
 *
 * Поддерживает все стандартные свойства Chip MUI.
 *
 * @example
 * ```tsx
 * <ApplicationStatusChip status="applied" />
 * ```
 *
 * @example
 * ```tsx
 * <ApplicationStatusChip status="interview" stageName="Technical Interview" />
 * ```
 *
 * @example
 * ```tsx
 * <ApplicationStatusChip
 *   status="offer"
 *   size="medium"
 *   sx={{ fontWeight: 'bold' }}
 * />
 * ```
 */
export function ApplicationStatusChip({
  status,
  stageName,
  size = 'small',
  ...props
}: ApplicationStatusChipProps) {
  const color = getStatusColor(status);
  const label = getStatusLabel(status, stageName);

  return (
    <Chip
      label={label}
      size={size}
      color={color}
      sx={{
        borderRadius: 1,
        fontSize: '0.75rem',
        height: size === 'small' ? 24 : 32,
        textTransform: 'capitalize',
        ...props.sx,
      }}
      {...props}
    />
  );
}
