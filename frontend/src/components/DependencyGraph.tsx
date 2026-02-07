/**
 * Dependency Graph Visualization Component
 *
 * Displays service dependency relationships with color-coded health status
 * and visual connections between dependent services.
 */

import React, { useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Stack,
  Tooltip,
  useTheme,
  alpha,
} from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Warning as DegradedIcon,
  Error as UnhealthyIcon,
  Storage as DatabaseIcon,
  Memory as RedisIcon,
  Speed as CeleryIcon,
  Psychology as MLModelIcon,
  Cloud as ExternalApiIcon,
  Hub as ServiceIcon,
} from '@mui/icons-material';
import type { DependencyGraphResponse, ComponentHealthStatus } from '@/types/api';

interface DependencyGraphProps {
  dependencyData: DependencyGraphResponse;
  healthData?: {
    checks: Record<string, ComponentHealthStatus>;
  };
}

/**
 * Get icon for component type
 */
function getServiceIcon(name: string) {
  switch (name) {
    case 'database':
      return <DatabaseIcon />;
    case 'redis':
      return <RedisIcon />;
    case 'celery':
      return <CeleryIcon />;
    case 'ml_ner_model':
    case 'ml_zero_shot_model':
    case 'ml_language_tools':
      return <MLModelIcon />;
    case 'external_api':
      return <ExternalApiIcon />;
    default:
      return <ServiceIcon />;
  }
}

/**
 * Get status color
 */
function getStatusColor(status: string): string {
  const theme = useTheme();
  switch (status) {
    case 'healthy':
      return theme.palette.success.main;
    case 'degraded':
      return theme.palette.warning.main;
    case 'unhealthy':
      return theme.palette.error.main;
    default:
      return theme.palette.grey[500];
  }
}

/**
 * Get status background color with alpha
 */
function getStatusBgColor(status: string, theme: any): string {
  switch (status) {
    case 'healthy':
      return alpha(theme.palette.success.main, 0.1);
    case 'degraded':
      return alpha(theme.palette.warning.main, 0.1);
    case 'unhealthy':
      return alpha(theme.palette.error.main, 0.1);
    default:
      return alpha(theme.palette.grey[500], 0.1);
  }
}

/**
 * Service Node Component
 */
interface ServiceNodeProps {
  name: string;
  displayName: string;
  essential: boolean;
  category: string;
  dependencies: string[];
  dependents: string[];
  status?: 'healthy' | 'degraded' | 'unhealthy';
  x: number;
  y: number;
  onHover?: (name: string | null) => void;
  isHovered?: boolean;
  highlighted?: boolean;
}

function ServiceNode({
  name,
  displayName,
  essential,
  category,
  dependencies,
  dependents,
  status = 'healthy',
  x,
  y,
  onHover,
  isHovered,
  highlighted,
}: ServiceNodeProps) {
  const theme = useTheme();
  const statusColor = getStatusColor(status);
  const bgColor = getStatusBgColor(status, theme);

  return (
    <g
      transform={`translate(${x}, ${y})`}
      onMouseEnter={() => onHover?.(name)}
      onMouseLeave={() => onHover?.(null)}
      style={{ cursor: 'pointer' }}
    >
      {/* Node background */}
      <rect
        x={-70}
        y={-25}
        width={140}
        height={50}
        rx={8}
        fill={highlighted ? bgColor : theme.palette.background.paper}
        stroke={statusColor}
        strokeWidth={highlighted ? 3 : 2}
        opacity={highlighted || isHovered ? 1 : 0.8}
        filter={isHovered ? 'drop-shadow(0px 4px 8px rgba(0,0,0,0.2))' : 'none'}
      />

      {/* Status indicator circle */}
      <circle
        cx={-55}
        cy={0}
        r={6}
        fill={statusColor}
      />

      {/* Service name */}
      <text
        x={-42}
        y={5}
        fontSize={13}
        fontWeight={highlighted ? 600 : 500}
        fill={theme.palette.text.primary}
        fontFamily={theme.typography.fontFamily}
      >
        {displayName.length > 15 ? displayName.substring(0, 15) + '...' : displayName}
      </text>

      {/* Essential indicator */}
      {essential && (
        <circle
          cx={55}
          cy={0}
          r={4}
          fill={theme.palette.primary.main}
          opacity={0.6}
        />
      )}
    </g>
  );
}

/**
 * Connection Line Component
 */
interface ConnectionLineProps {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  status?: 'healthy' | 'degraded' | 'unhealthy';
  highlighted?: boolean;
  sourceStatus?: 'healthy' | 'degraded' | 'unhealthy';
  targetStatus?: 'healthy' | 'degraded' | 'unhealthy';
}

function ConnectionLine({
  x1,
  y1,
  x2,
  y2,
  highlighted,
  sourceStatus,
  targetStatus,
}: ConnectionLineProps) {
  const theme = useTheme();

  // Determine line color based on connected services' health
  let lineColor = theme.palette.divider;
  if (sourceStatus === 'unhealthy' || targetStatus === 'unhealthy') {
    lineColor = theme.palette.error.main;
  } else if (sourceStatus === 'degraded' || targetStatus === 'degraded') {
    lineColor = theme.palette.warning.main;
  } else if (sourceStatus === 'healthy' && targetStatus === 'healthy') {
    lineColor = theme.palette.success.main;
  }

  // Calculate arrow position
  const midX = (x1 + x2) / 2;
  const midY = (y1 + y2) / 2;
  const angle = Math.atan2(y2 - y1, x2 - x1);

  return (
    <g opacity={highlighted ? 1 : 0.4}>
      {/* Line */}
      <line
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={lineColor}
        strokeWidth={highlighted ? 2.5 : 1.5}
        strokeDasharray={highlighted ? 'none' : '5,5'}
      />

      {/* Arrow head */}
      <polygon
        points={`
          ${x2} ${y2}
          ${x2 - 10 * Math.cos(angle - Math.PI / 6)} ${y2 - 10 * Math.sin(angle - Math.PI / 6)}
          ${x2 - 10 * Math.cos(angle + Math.PI / 6)} ${y2 - 10 * Math.sin(angle + Math.PI / 6)}
        `}
        fill={lineColor}
      />
    </g>
  );
}

/**
 * Dependency Graph Visualization Component
 */
export function DependencyGraph({ dependencyData, healthData }: DependencyGraphProps) {
  const theme = useTheme();
  const [hoveredService, setHoveredService] = React.useState<string | null>(null);

  const { services, summary } = dependencyData;

  // Get service status from health data
  const getServiceStatus = (serviceName: string): 'healthy' | 'degraded' | 'unhealthy' => {
    return healthData?.checks[serviceName]?.status || 'healthy';
  };

  // Calculate layout positions for services
  const layout = useMemo(() => {
    const serviceEntries = Object.entries(services);
    const positions: Record<string, { x: number; y: number; level: number }> = {};

    // Group services by dependency depth
    const levels: string[][] = [];
    const processed = new Set<string>();
    const maxDepth = summary.max_dependency_depth;

    // Initialize levels
    for (let i = 0; i <= maxDepth; i++) {
      levels[i] = [];
    }

    // Assign levels based on dependency depth
    serviceEntries.forEach(([name, service]) => {
      const depth = service.dependencies.length;
      levels[Math.min(depth, maxDepth)].push(name);
    });

    // Calculate positions
    const levelHeight = 120;
    const nodeWidth = 160;
    const svgWidth = Math.max(800, serviceEntries.length * nodeWidth);
    const svgHeight = (maxDepth + 1) * levelHeight + 100;

    levels.forEach((levelServices, levelIndex) => {
      const levelY = levelIndex * levelHeight + 80;
      const horizontalSpacing = svgWidth / (levelServices.length + 1);

      levelServices.forEach((serviceName, index) => {
        positions[serviceName] = {
          x: horizontalSpacing * (index + 1),
          y: levelY,
          level: levelIndex,
        };
      });
    });

    return { positions, svgWidth, svgHeight };
  }, [services, summary.max_dependency_depth]);

  const { positions, svgWidth, svgHeight } = layout;

  // Get connections (dependencies)
  const connections = useMemo(() => {
    const lines: Array<{
      from: string;
      to: string;
      x1: number;
      y1: number;
      x2: number;
      y2: number;
      sourceStatus: 'healthy' | 'degraded' | 'unhealthy';
      targetStatus: 'healthy' | 'degraded' | 'unhealthy';
    }> = [];

    Object.entries(services).forEach(([serviceName, service]) => {
      const fromPos = positions[serviceName];
      if (!fromPos) return;

      service.dependencies.forEach((depName) => {
        const toPos = positions[depName];
        if (!toPos) return;

        lines.push({
          from: serviceName,
          to: depName,
          x1: fromPos.x,
          y1: fromPos.y + 25,
          x2: toPos.x,
          y2: toPos.y - 25,
          sourceStatus: getServiceStatus(serviceName),
          targetStatus: getServiceStatus(depName),
        });
      });
    });

    return lines;
  }, [services, positions, healthData]);

  // Determine highlighted connections and nodes
  const highlightedConnections = useMemo(() => {
    if (!hoveredService) return new Set<string>();
    const related = new Set<string>();

    connections.forEach((conn) => {
      if (conn.from === hoveredService || conn.to === hoveredService) {
        related.add(`${conn.from}-${conn.to}`);
      }
    });

    return related;
  }, [hoveredService, connections]);

  const highlightedNodes = useMemo(() => {
    if (!hoveredService) return new Set<string>();
    const related = new Set<string>([hoveredService]);

    const service = services[hoveredService];
    if (service) {
      service.dependencies.forEach((dep) => related.add(dep));
      service.dependents.forEach((dep) => related.add(dep));
    }

    return related;
  }, [hoveredService, services]);

  // Count services by status
  const statusCounts = useMemo(() => {
    const counts = {
      healthy: 0,
      degraded: 0,
      unhealthy: 0,
    };

    Object.entries(services).forEach(([name, service]) => {
      const status = getServiceStatus(name);
      counts[status]++;
    });

    return counts;
  }, [services, healthData]);

  return (
    <Stack spacing={3}>
      {/* Header */}
      <Box>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Service Dependency Graph
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Visual representation of service dependencies and their health status
        </Typography>
      </Box>

      {/* Legend */}
      <Paper sx={{ p: 2 }}>
        <Stack direction="row" spacing={3} alignItems="center" flexWrap="wrap" useFlexGap>
          <Typography variant="caption" fontWeight={600}>
            STATUS:
          </Typography>
          <Stack direction="row" spacing={1} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'success.main' }} />
            <Typography variant="caption">Healthy ({statusCounts.healthy})</Typography>
          </Stack>
          <Stack direction="row" spacing={1} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'warning.main' }} />
            <Typography variant="caption">Degraded ({statusCounts.degraded})</Typography>
          </Stack>
          <Stack direction="row" spacing={1} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'error.main' }} />
            <Typography variant="caption">Unhealthy ({statusCounts.unhealthy})</Typography>
          </Stack>
          <Stack direction="row" spacing={1} alignItems="center">
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'primary.main', opacity: 0.6 }} />
            <Typography variant="caption">Essential Service</Typography>
          </Stack>
        </Stack>
      </Paper>

      {/* Graph Visualization */}
      <Paper sx={{ p: 2, overflowX: 'auto' }}>
        <Box
          component="svg"
          sx={{
            width: '100%',
            minWidth: svgWidth,
            height: svgHeight,
            bgcolor: alpha(theme.palette.background.default, 0.5),
            borderRadius: 1,
          }}
        >
          {/* Connections (drawn first so they appear behind nodes) */}
          {connections.map((conn) => (
            <ConnectionLine
              key={`${conn.from}-${conn.to}`}
              x1={conn.x1}
              y1={conn.y1}
              x2={conn.x2}
              y2={conn.y2}
              sourceStatus={conn.sourceStatus}
              targetStatus={conn.targetStatus}
              highlighted={highlightedConnections.has(`${conn.from}-${conn.to}`)}
            />
          ))}

          {/* Service Nodes */}
          {Object.entries(services).map(([name, service]) => {
            const pos = positions[name];
            if (!pos) return null;

            const status = getServiceStatus(name);
            const isHighlighted = highlightedNodes.has(name);
            const isHovered = hoveredService === name;

            return (
              <ServiceNode
                key={name}
                name={name}
                displayName={service.display_name}
                essential={service.essential}
                category={service.category}
                dependencies={service.dependencies}
                dependents={service.dependents}
                status={status}
                x={pos.x}
                y={pos.y}
                onHover={setHoveredService}
                isHovered={isHovered}
                highlighted={isHighlighted}
              />
            );
          })}
        </Box>
      </Paper>

      {/* Service Details Panel */}
      {hoveredService && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            {services[hoveredService].display_name}
          </Typography>
          <Stack direction="row" spacing={1} mb={2}>
            <Chip
              label={services[hoveredService].category}
              size="small"
              variant="outlined"
            />
            <Chip
              icon={services[hoveredService].essential ? <HealthyIcon /> : undefined}
              label={services[hoveredService].essential ? 'Essential' : 'Optional'}
              size="small"
              color={services[hoveredService].essential ? 'primary' : 'default'}
            />
            <Chip
              label={getServiceStatus(hoveredService).toUpperCase()}
              size="small"
              color={getServiceStatus(hoveredService) === 'healthy' ? 'success' : getServiceStatus(hoveredService) === 'degraded' ? 'warning' : 'error'}
            />
          </Stack>

          {/* Dependencies */}
          {services[hoveredService].dependencies.length > 0 && (
            <Box mb={2}>
              <Typography variant="caption" color="text.secondary" fontWeight={600}>
                DEPENDS ON:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                {services[hoveredService].dependencies.map((dep) => (
                  <Chip
                    key={dep}
                    label={services[dep]?.display_name || dep}
                    size="small"
                    variant="outlined"
                    icon={getServiceIcon(dep)}
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Dependents */}
          {services[hoveredService].dependents.length > 0 && (
            <Box>
              <Typography variant="caption" color="text.secondary" fontWeight={600}>
                USED BY:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                {services[hoveredService].dependents.map((dep) => (
                  <Chip
                    key={dep}
                    label={services[dep]?.display_name || dep}
                    size="small"
                    variant="outlined"
                    icon={getServiceIcon(dep)}
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Description */}
          {services[hoveredService].description && (
            <Box mt={2}>
              <Typography variant="caption" color="text.secondary">
                {services[hoveredService].description}
              </Typography>
            </Box>
          )}
        </Paper>
      )}

      {/* Critical Path */}
      {summary.critical_path.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Critical Dependency Path
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {summary.critical_path.map((serviceName, index) => (
              <React.Fragment key={serviceName}>
                <Chip
                  label={services[serviceName]?.display_name || serviceName}
                  size="small"
                  color="primary"
                  variant="outlined"
                  icon={getServiceIcon(serviceName)}
                />
                {index < summary.critical_path.length - 1 && (
                  <Typography variant="body2" color="text.secondary">→</Typography>
                )}
              </React.Fragment>
            ))}
          </Stack>
        </Paper>
      )}
    </Stack>
  );
}

export default DependencyGraph;
