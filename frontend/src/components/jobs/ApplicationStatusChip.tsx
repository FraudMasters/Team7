import React from 'react';
import { Chip, ChipProps } from '@/components/ui';

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

interface ApplicationStatusChipProps extends Omit<ChipProps, 'color' | 'sx'> {
  status: ApplicationStatus;
  stageName?: string;
  sx?: React.CSSProperties;
}

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
