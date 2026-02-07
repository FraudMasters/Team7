import React, { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  CircularProgress,
  Alert,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  Close as CloseIcon,
  Download as ExportIcon,
  Refresh as RefreshIcon,
  Error as AnomalyIcon,
  Timeline as TimeIcon,
  Person as CandidateIcon,
  Work as JobIcon,
  TrendingUp as MetricIcon,
} from '@mui/icons-material';

/**
 * Anomaly type for drill-down investigation
 */
export type AnomalyType =
  | 'high_duration'
  | 'low_match_rate'
  | 'unusual_pattern'
  | 'bottleneck'
  | 'spike'
  | 'drop';

/**
 * Drill-down data item interface
 */
export interface DrillDownDataItem {
  id: string;
  timestamp: string;
  metric_name: string;
  metric_value: number;
  expected_range: {
    min: number;
    max: number;
  };
  deviation_percentage: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  related_candidates?: Array<{
    id: string;
    name: string;
    filename: string;
  }>;
  related_vacancies?: Array<{
    id: string;
    title: string;
  }>;
  context?: Record<string, unknown>;
}

/**
 * Drill-down response from backend
 */
export interface DrillDownResponse {
  anomaly_type: AnomalyType;
  anomaly_description: string;
  period_start: string;
  period_end: string;
  total_anomalies: number;
  data: DrillDownDataItem[];
  summary: {
    average_deviation: number;
    max_deviation: number;
    most_affected_stage?: string;
    trend: 'increasing' | 'stable' | 'decreasing';
  };
}

/**
 * DrillDownModal Component Props
 */
interface DrillDownModalProps {
  /** Whether the modal is open */
  open: boolean;
  /** Callback when modal is closed */
  onClose: () => void;
  /** Type of anomaly to investigate */
  anomalyType: AnomalyType;
  /** Description of the anomaly */
  anomalyDescription?: string;
  /** Start date for the investigation period */
  startDate?: string;
  /** End date for the investigation period */
  endDate?: string;
  /** Optional metric name to filter by */
  metricName?: string;
  /** API endpoint URL for drill-down data */
  apiUrl?: string;
}

/**
 * Helper function to get anomaly type display name
 */
const getAnomalyTypeDisplayName = (type: AnomalyType): string => {
  const displayNames: Record<AnomalyType, string> = {
    high_duration: 'High Duration',
    low_match_rate: 'Low Match Rate',
    unusual_pattern: 'Unusual Pattern',
    bottleneck: 'Bottleneck',
    spike: 'Spike',
    drop: 'Drop',
  };
  return displayNames[type] || type;
};

/**
 * Helper function to get severity color
 */
const getSeverityColor = (severity: string): 'success' | 'warning' | 'error' | 'default' => {
  switch (severity) {
    case 'low':
      return 'success';
    case 'medium':
      return 'warning';
    case 'high':
      return 'error';
    case 'critical':
      return 'error';
    default:
      return 'default';
  }
};

/**
 * Helper function to format date for display
 */
const formatDateDisplay = (dateString: string): string => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Helper function to format number with percentage
 */
const formatPercentage = (value: number): string => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
};

/**
 * DrillDownModal Component
 *
 * Provides detailed investigation capabilities for analytics anomalies including:
 * - Detailed data table showing all anomaly occurrences
 * - Summary statistics (total anomalies, average/max deviation)
 * - Trend analysis (increasing/stable/decreasing)
 * - Related candidates and vacancies
 * - Export functionality for detailed investigation
 * - Real-time refresh capability
 *
 * @example
 * ```tsx
 * <DrillDownModal
 *   open={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   anomalyType="high_duration"
 *   startDate="2024-01-01"
 *   endDate="2024-01-31"
 * />
 * ```
 *
 * @example
 * ```tsx
 * <DrillDownModal
 *   open={isOpen}
 *   onClose={handleClose}
 *   anomalyType="low_match_rate"
 *   anomalyDescription="Unusual drop in match rates detected"
 *   metricName="overall_match_rate"
 * />
 * ```
 */
const DrillDownModal: React.FC<DrillDownModalProps> = ({
  open,
  onClose,
  anomalyType,
  anomalyDescription,
  startDate,
  endDate,
  metricName,
  apiUrl = '/api/analytics/drill-down',
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drillDownData, setDrillDownData] = useState<DrillDownResponse | null>(null);
  const [exporting, setExporting] = useState(false);

  /**
   * Fetch drill-down data from backend
   */
  const fetchDrillDownData = useCallback(async () => {
    if (!open) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const params: Record<string, string> = {
        anomaly_type: anomalyType,
      };

      if (startDate) {
        params.start_date = startDate;
      }
      if (endDate) {
        params.end_date = endDate;
      }
      if (metricName) {
        params.metric_name = metricName;
      }

      const response = await axios.get<DrillDownResponse>(apiUrl, { params });
      setDrillDownData(response.data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load drill-down data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [open, anomalyType, startDate, endDate, metricName, apiUrl]);

  /**
   * Fetch data when modal opens or dependencies change
   */
  useEffect(() => {
    if (open) {
      fetchDrillDownData();
    }
  }, [open, fetchDrillDownData]);

  /**
   * Handle export functionality
   */
  const handleExport = useCallback(async () => {
    if (!drillDownData) {
      return;
    }

    setExporting(true);

    try {
      // Create CSV content
      const headers = [
        'Timestamp',
        'Metric Name',
        'Metric Value',
        'Expected Min',
        'Expected Max',
        'Deviation %',
        'Severity',
      ];

      const rows = drillDownData.data.map((item) => [
        formatDateDisplay(item.timestamp),
        item.metric_name,
        item.metric_value.toString(),
        item.expected_range.min.toString(),
        item.expected_range.max.toString(),
        item.deviation_percentage.toFixed(2),
        item.severity,
      ]);

      const csvContent = [
        headers.join(','),
        ...rows.map((row) => row.join(',')),
      ].join('\n');

      // Create blob and download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);

      link.setAttribute('href', url);
      link.setAttribute(
        'download',
        `drill-down-${anomalyType}-${new Date().toISOString().split('T')[0]}.csv`
      );
      link.style.visibility = 'hidden';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      setError('Failed to export data. Please try again.');
    } finally {
      setExporting(false);
    }
  }, [drillDownData, anomalyType]);

  /**
   * Handle modal close
   */
  const handleClose = useCallback(() => {
    setDrillDownData(null);
    setError(null);
    onClose();
  }, [onClose]);

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: { height: '80vh', maxHeight: '80vh' }
      }}
    >
      {/* Dialog Title */}
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <AnomalyIcon color="error" fontSize="large" />
            <Box>
              <Typography variant="h6" fontWeight={600}>
                Drill-Down Investigation
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {getAnomalyTypeDisplayName(anomalyType)}
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Button
              variant="outlined"
              startIcon={exporting ? <CircularProgress size={16} /> : <ExportIcon />}
              onClick={handleExport}
              disabled={exporting || loading || !drillDownData}
              size="small"
            >
              {exporting ? 'Exporting...' : 'Export CSV'}
            </Button>
            <IconButton
              onClick={handleClose}
              disabled={loading}
              size="small"
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      {/* Dialog Content */}
      <DialogContent sx={{ p: 0 }}>
        <Box sx={{ height: '100%', overflow: 'auto', p: 3 }}>
          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Loading State */}
          {loading && (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                py: 8,
              }}
            >
              <CircularProgress size={60} sx={{ mb: 3 }} />
              <Typography variant="h6" color="text.secondary">
                Loading drill-down data...
              </Typography>
            </Box>
          )}

          {/* Drill-Down Data */}
          {!loading && drillDownData && (
            <Stack spacing={3}>
              {/* Description */}
              {anomalyDescription && (
                <Alert severity="info">
                  <Typography variant="body2">{anomalyDescription}</Typography>
                </Alert>
              )}

              {/* Summary Statistics */}
              <Grid container spacing={2}>
                {/* Total Anomalies */}
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <AnomalyIcon color="error" fontSize="small" />
                        <Typography variant="caption" color="text.secondary">
                          Total Anomalies
                        </Typography>
                      </Box>
                      <Typography variant="h4" fontWeight={700} color="error.main">
                        {drillDownData.total_anomalies}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Average Deviation */}
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <MetricIcon color="warning" fontSize="small" />
                        <Typography variant="caption" color="text.secondary">
                          Avg Deviation
                        </Typography>
                      </Box>
                      <Typography variant="h4" fontWeight={700} color="warning.main">
                        {formatPercentage(drillDownData.summary.average_deviation)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Max Deviation */}
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <TrendingUp color="error" fontSize="small" />
                        <Typography variant="caption" color="text.secondary">
                          Max Deviation
                        </Typography>
                      </Box>
                      <Typography variant="h4" fontWeight={700} color="error.main">
                        {formatPercentage(drillDownData.summary.max_deviation)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Trend */}
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <TimeIcon color="primary" fontSize="small" />
                        <Typography variant="caption" color="text.secondary">
                          Trend
                        </Typography>
                      </Box>
                      <Typography
                        variant="h4"
                        fontWeight={700}
                        textTransform="capitalize"
                        color={
                          drillDownData.summary.trend === 'increasing'
                            ? 'error.main'
                            : drillDownData.summary.trend === 'decreasing'
                              ? 'success.main'
                              : 'info.main'
                        }
                      >
                        {drillDownData.summary.trend}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Period Information */}
              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Investigation Period
                </Typography>
                <Stack direction="row" spacing={2}>
                  <Chip
                    icon={<TimeIcon fontSize="small" />}
                    label={`From: ${formatDateDisplay(drillDownData.period_start)}`}
                    variant="outlined"
                    size="small"
                  />
                  <Chip
                    icon={<TimeIcon fontSize="small" />}
                    label={`To: ${formatDateDisplay(drillDownData.period_end)}`}
                    variant="outlined"
                    size="small"
                  />
                </Stack>
              </Box>

              <Divider />

              {/* Detailed Data Table */}
              <Typography variant="h6" fontWeight={600}>
                Detailed Anomaly Data
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Timestamp</TableCell>
                      <TableCell>Metric</TableCell>
                      <TableCell align="right">Value</TableCell>
                      <TableCell align="right">Expected Range</TableCell>
                      <TableCell align="right">Deviation</TableCell>
                      <TableCell align="center">Severity</TableCell>
                      <TableCell>Related</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {drillDownData.data.map((item) => (
                      <TableRow
                        key={item.id}
                        hover
                        sx={{
                          '&:last-child td, &:last-child th': { border: 0 },
                        }}
                      >
                        <TableCell component="th" scope="row" sx={{ whiteSpace: 'nowrap' }}>
                          {formatDateDisplay(item.timestamp)}
                        </TableCell>
                        <TableCell>{item.metric_name}</TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight={600}>
                            {item.metric_value.toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="caption" color="text.secondary">
                            {item.expected_range.min.toFixed(2)} - {item.expected_range.max.toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography
                            variant="body2"
                            fontWeight={600}
                            color={item.deviation_percentage > 0 ? 'error.main' : 'success.main'}
                          >
                            {formatPercentage(item.deviation_percentage)}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            label={item.severity.toUpperCase()}
                            size="small"
                            color={getSeverityColor(item.severity)}
                            sx={{ fontWeight: 600, fontSize: '0.7rem' }}
                          />
                        </TableCell>
                        <TableCell>
                          <Stack spacing={0.5}>
                            {item.related_candidates && item.related_candidates.length > 0 && (
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <CandidateIcon fontSize="inherit" sx={{ fontSize: 14 }} color="primary" />
                                <Typography variant="caption" color="text.secondary">
                                  {item.related_candidates.length} candidate{item.related_candidates.length > 1 ? 's' : ''}
                                </Typography>
                              </Box>
                            )}
                            {item.related_vacancies && item.related_vacancies.length > 0 && (
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <JobIcon fontSize="inherit" sx={{ fontSize: 14 }} color="action" />
                                <Typography variant="caption" color="text.secondary">
                                  {item.related_vacancies.length} vacanc{item.related_vacancies.length > 1 ? 'ies' : 'y'}
                                </Typography>
                              </Box>
                            )}
                          </Stack>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* No Data Message */}
              {drillDownData.data.length === 0 && (
                <Alert severity="info">
                  No anomaly data found for the specified period and filters.
                </Alert>
              )}
            </Stack>
          )}
        </Box>
      </DialogContent>

      {/* Dialog Actions */}
      <DialogActions sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Button
          onClick={fetchDrillDownData}
          startIcon={<RefreshIcon />}
          disabled={loading}
          variant="outlined"
        >
          Refresh
        </Button>
        <Button onClick={handleClose} variant="contained" color="primary">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DrillDownModal;
