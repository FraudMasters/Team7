import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Storage as StorageIcon,
  Memory as MemoryIcon,
  Work as WorkIcon,
  Psychology as PsychologyIcon,
  Cloud as CloudIcon,
  Folder as FolderIcon,
  Api as ApiIcon,
} from '@mui/icons-material';
import type { ComponentHealth } from '@/types/api';

/**
 * SystemStatusCard Component Props
 */
interface SystemStatusCardProps {
  /** Component health data to display */
  component: ComponentHealth;
  /** Optional click handler for card interaction */
  onClick?: () => void;
}

/**
 * Get status color based on health status
 *
 * @param status - Health status string
 * @returns Material-UI color type
 */
const getStatusColor = (status: string): 'success' | 'warning' | 'error' => {
  switch (status) {
    case 'healthy':
      return 'success';
    case 'degraded':
      return 'warning';
    case 'unhealthy':
      return 'error';
    default:
      return 'error';
  }
};

/**
 * Get status icon component based on health status
 *
 * @param status - Health status string
 * @returns Icon component
 */
const getStatusIcon = (status: string): React.ReactElement => {
  switch (status) {
    case 'healthy':
      return <CheckCircleIcon sx={{ fontSize: 32 }} />;
    case 'degraded':
      return <WarningIcon sx={{ fontSize: 32 }} />;
    case 'unhealthy':
      return <ErrorIcon sx={{ fontSize: 32 }} />;
    default:
      return <ErrorIcon sx={{ fontSize: 32 }} />;
  }
};

/**
 * Get component-specific icon based on component name
 *
 * @param componentName - Name of the system component
 * @returns Icon component
 */
const getComponentIcon = (componentName: string): React.ReactElement => {
  switch (componentName) {
    case 'api':
      return <ApiIcon sx={{ fontSize: 40 }} />;
    case 'database':
      return <StorageIcon sx={{ fontSize: 40 }} />;
    case 'redis':
      return <MemoryIcon sx={{ fontSize: 40 }} />;
    case 'celery_workers':
      return <WorkIcon sx={{ fontSize: 40 }} />;
    case 'ml_models':
      return <PsychologyIcon sx={{ fontSize: 40 }} />;
    case 'storage':
      return <FolderIcon sx={{ fontSize: 40 }} />;
    case 'external_services':
      return <CloudIcon sx={{ fontSize: 40 }} />;
    default:
      return <CheckCircleIcon sx={{ fontSize: 40 }} />;
  }
};

/**
 * Get human-readable display name for component
 *
 * @param componentName - Component identifier
 * @returns Human-readable display name
 */
const getComponentDisplayName = (componentName: string): string => {
  switch (componentName) {
    case 'api':
      return 'API Service';
    case 'database':
      return 'Database';
    case 'redis':
      return 'Redis Cache';
    case 'celery_workers':
      return 'Celery Workers';
    case 'ml_models':
      return 'ML Models';
    case 'storage':
      return 'File Storage';
    case 'external_services':
      return 'External Services';
    default:
      return componentName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  }
};

/**
 * SystemStatusCard Component
 *
 * Displays the health status of an individual system component with:
 * - Component-specific icon
 * - Component name (human-readable)
 * - Status indicator (healthy/degraded/unhealthy) with color coding
 * - Status message describing current state
 * - Response time in milliseconds (if available)
 * - Degraded mode indicator (if applicable)
 *
 * The card is color-coded based on health status:
 * - Green (success): Component is healthy
 * - Yellow (warning): Component is degraded but operational
 * - Red (error): Component is unhealthy or unavailable
 *
 * @example
 * ```tsx
 * <SystemStatusCard
 *   component={{
 *     name: 'database',
 *     status: 'healthy',
 *     message: 'Connected and responding',
 *     response_time_ms: 45.2,
 *   }}
 * />
 * ```
 *
 * @example
 * ```tsx
 * <SystemStatusCard
 *   component={{
 *     name: 'ml_models',
 *     status: 'degraded',
 *     message: 'NER models loaded, LanguageTool unavailable',
 *     degraded_mode: true,
 *   }}
 *   onClick={() => handleComponentClick('ml_models')}
 * />
 * ```
 */
const SystemStatusCard: React.FC<SystemStatusCardProps> = ({ component, onClick }) => {
  const statusColor = getStatusColor(component.status);
  const borderColor =
    statusColor === 'success' ? 'success.main' : statusColor === 'warning' ? 'warning.main' : 'error.main';
  const iconColor =
    statusColor === 'success' ? 'success.main' : statusColor === 'warning' ? 'warning.main' : 'error.main';

  return (
    <Card
      onClick={onClick}
      sx={{
        height: '100%',
        borderLeft: 4,
        borderColor,
        transition: 'transform 0.2s, box-shadow 0.2s',
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': onClick
          ? {
              transform: 'translateY(-4px)',
              boxShadow: 4,
            }
          : {},
      }}
    >
      <CardContent>
        {/* Header: Icon and Name with Status Chip */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
          <Box
            sx={{
              mr: 2,
              color: iconColor,
            }}
          >
            {getComponentIcon(component.name)}
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              {getComponentDisplayName(component.name)}
            </Typography>
            <Chip
              label={component.status.charAt(0).toUpperCase() + component.status.slice(1)}
              color={statusColor}
              size="small"
            />
          </Box>
        </Box>

        {/* Status Message and Details */}
        <Box sx={{ mt: 2 }}>
          {/* Status Message */}
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {component.message || 'No status message available'}
          </Typography>

          {/* Response Time */}
          {component.response_time_ms !== undefined && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              Response time: {component.response_time_ms.toFixed(2)}ms
            </Typography>
          )}

          {/* Degraded Mode Indicator */}
          {component.degraded_mode !== undefined && component.degraded_mode && (
            <Chip
              label="Degraded Mode"
              size="small"
              color="warning"
              variant="outlined"
              sx={{ mt: 1 }}
            />
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default SystemStatusCard;
