// React хуки для управления состоянием и эффектами
import React, { useState, useEffect } from 'react';
// Компоненты Material UI для создания интерфейса
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
} from '@mui/material';
// Иконки Material UI
import {
  Refresh as RefreshIcon,
  Balance as FairnessIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  TrendingUp as TrendUpIcon,
  TrendingDown as TrendDownIcon,
  Info as InfoIcon,
  Download as DownloadIcon,
  DateRange as DateIcon,
  Assessment as ReportIcon,
} from '@mui/icons-material';
// API клиент для получения данных о fairness
import { fairness } from '@/api/fairness';
// Типы API для типизации данных
import type {
  BiasReport,
  FairnessMetric,
  FairnessAlert,
} from '@/types/api';

/**
 * Данные демографического распределения
 */
interface DemographicBreakdown {
  attribute: string;
  groups: Array<{
    name: string;
    count: number;
    percentage: number;
    avg_score: number;
    selection_rate: number;
  }>;
}

/**
 * Точка данных графика fairness
 */
interface FairnessChartData {
  label: string;
  value: number;
  threshold: number;
  acceptable: boolean;
}

/**
 * Свойства компонента FairnessReport
 * @description Определяет параметры для генерации отчета о fairness
 */
interface FairnessReportProps {
  /** Имя модели для генерации отчета */
  modelName?: string;
  /** Версия модели */
  modelVersion?: string;
  /** Тип отчета */
  reportType?: string;
  /** URL API endpoint */
  apiUrl?: string;
  /** Колбэк при изменении данных отчета */
  onReportChange?: (report: BiasReport) => void;
}

/**
 * Получить цвет серьезности для отображения
 */
function getSeverityColor(severity: string): 'success' | 'warning' | 'error' | 'info' {
  switch (severity.toLowerCase()) {
    case 'none':
    case 'low':
      return 'success';
    case 'medium':
      return 'warning';
    case 'high':
    case 'critical':
      return 'error';
    default:
      return 'info';
  }
}

/**
 * Получить компонент иконки серьезности
 */
function getSeverityIcon(severity: string) {
  switch (severity.toLowerCase()) {
    case 'none':
    case 'low':
      return <CheckIcon />;
    case 'medium':
      return <WarningIcon />;
    case 'high':
    case 'critical':
      return <ErrorIcon />;
    default:
      return <InfoIcon />;
  }
}

/**
 * Форматирование типа метрики для отображения
 */
function formatMetricType(metricType: string): string {
  return metricType
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Компонент FairnessReport
 *
 * Отображает подробные отчеты об анализе fairness включая:
 * - Демографическое распределение по защищаемым атрибутам
 * - Графики метрик fairness с порогами
 * - Оповещения об обнаружении bias и рекомендации
 * - Данные исторических трендов
 *
 * @example
 * ```tsx
 * <FairnessReport modelName="ranking" />
 * ```
 *
 * @example
 * ```tsx
 * <FairnessReport
 *   modelName="ranking"
 *   modelVersion="v1.0.0"
 *   reportType="demographic_analysis"
 * />
 * ```
 */
const FairnessReport: React.FC<FairnessReportProps> = ({
  modelName = 'ranking',
  modelVersion,
  reportType = 'demographic_analysis',
  onReportChange,
}) => {
  // Состояния для загрузки, генерации, ошибки, отчета, метрик, оповещений и демографических данных
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<BiasReport | null>(null);
  const [metrics, setMetrics] = useState<FairnessMetric[]>([]);
  const [alerts, setAlerts] = useState<FairnessAlert[]>([]);
  const [demographicData, setDemographicData] = useState<DemographicBreakdown[]>([]);

  /**
   * Загрузка данных отчета с бэкенда
   */
  const fetchReportData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch metrics and alerts in parallel
      const [metricsResponse, alertsResponse] = await Promise.all([
        fairness.getMetrics({
          model_name: modelName,
          model_version: modelVersion,
          limit: 50,
        }),
        fairness.getAlerts({
          model_name: modelName,
          days: 30,
          limit: 20,
        }),
      ]);

      setMetrics(metricsResponse.metrics);
      setAlerts(alertsResponse.alerts);

      // Transform metrics into demographic breakdown format
      const breakdown = transformMetricsToBreakdown(metricsResponse.metrics);
      setDemographicData(breakdown);

      // Generate or fetch bias report
      const reports = await fairness.getReports({
        model_name: modelName,
        model_version: modelVersion,
        report_type: reportType,
        limit: 1,
      });

      if (reports.reports.length > 0) {
        setReport(reports.reports[0]!);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load fairness report';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Generate a new bias report
   */
  const generateReport = async () => {
    setGenerating(true);
    setError(null);

    try {
      const newReport = await fairness.generateReport({
        model_name: modelName,
        model_version: modelVersion,
        report_type: reportType,
      });

      setReport(newReport);

      if (onReportChange) {
        onReportChange(newReport);
      }

      // Refresh metrics and alerts after generating report
      await fetchReportData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate report';
      setError(errorMessage);
    } finally {
      setGenerating(false);
    }
  };

  /**
   * Transform metrics to demographic breakdown format
   */
  const transformMetricsToBreakdown = (metricsList: FairnessMetric[]): DemographicBreakdown[] => {
    const groupedByAttribute = new Map<string, FairnessMetric[]>();

    // Group metrics by protected attribute
    metricsList.forEach((metric) => {
      const attr = metric.protected_attribute;
      if (!groupedByAttribute.has(attr)) {
        groupedByAttribute.set(attr, []);
      }
      groupedByAttribute.get(attr)!.push(metric);
    });

    // Transform to demographic breakdown format
    return Array.from(groupedByAttribute.entries()).map(([attribute, attrMetrics]) => {
      // Extract unique metric types
      const metricTypes = new Set(attrMetrics.map((m) => m.metric_type));

      return {
        attribute,
        groups: Array.from(metricTypes).map((metricType) => {
          const metric = attrMetrics.find((m) => m.metric_type === metricType)!;
          return {
            name: formatMetricType(metricType),
            count: metric.sample_size,
            percentage: metric.metric_value * 100,
            avg_score: metric.metric_value,
            selection_rate: metric.threshold,
          };
        }),
      };
    });
  };

  useEffect(() => {
    fetchReportData();
  }, [modelName, modelVersion, reportType]);

  /**
   * Render loading state
   */
  if (loading) {
    return (
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
          Loading Fairness Report...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Analyzing demographic data and fairness metrics
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error && !report) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" onClick={fetchReportData} startIcon={<RefreshIcon />}>
            Retry
          </Button>
        }
      >
        <AlertTitle>Failed to Load Report</AlertTitle>
        {error}
      </Alert>
    );
  }

  /**
   * Render fairness metric chart
   */
  const renderMetricChart = (data: FairnessChartData) => {
    const percentage = Math.min(data.value * 100, 100);
    const color = data.acceptable ? 'success' : 'error';

    return (
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="body2" fontWeight={600}>
            {data.label}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="body2" fontWeight={600} color={`${color}.main`}>
              {(data.value * 100).toFixed(1)}%
            </Typography>
            {data.acceptable ? (
              <CheckIcon color="success" fontSize="small" />
            ) : (
              <WarningIcon color="error" fontSize="small" />
            )}
          </Box>
        </Box>
        <LinearProgress
          variant="determinate"
          value={percentage}
          sx={{
            height: 10,
            borderRadius: 5,
            backgroundColor: `${color}.main`,
            '& .MuiLinearProgress-bar': {
              backgroundColor: data.acceptable ? '#4caf50' : '#f44336',
            },
          }}
        />
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
          Threshold: {(data.threshold * 100).toFixed(1)}%
        </Typography>
      </Box>
    );
  };

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <ReportIcon color="primary" sx={{ fontSize: 32 }} />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Fairness Analysis Report
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Model: {modelName} {modelVersion ? `(${modelVersion})` : ''}
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchReportData}
              size="small"
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={generating ? <CircularProgress size={16} /> : <ReportIcon />}
              onClick={generateReport}
              disabled={generating}
              size="small"
            >
              {generating ? 'Generating...' : 'Generate Report'}
            </Button>
          </Box>
        </Box>

        {report && (
          <Alert severity={report.bias_detected ? 'warning' : 'success'} sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {getSeverityIcon(report.severity_level)}
              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle2" fontWeight={600}>
                  {report.bias_detected ? 'Bias Detected' : 'No Bias Detected'}
                </Typography>
                <Typography variant="body2">
                  Overall Fairness Score: {(report.overall_fairness_score * 100).toFixed(1)}%
                </Typography>
              </Box>
              <Chip
                label={report.severity_level.toUpperCase()}
                size="small"
                color={getSeverityColor(report.severity_level)}
              />
            </Box>
          </Alert>
        )}

        {error && report && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
      </Paper>

      {/* Demographic Breakdown */}
      {demographicData.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FairnessIcon />
              Demographic Breakdown
            </Box>
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Analysis of candidate distribution and outcomes across protected attributes
          </Typography>
          <Divider sx={{ my: 2 }} />

          <Grid container spacing={3}>
            {demographicData.map((breakdown) => (
              <Grid item xs={12} md={6} key={breakdown.attribute}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                      {breakdown.attribute.replace(/_/g, ' ').toUpperCase()}
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Group</TableCell>
                            <TableCell align="right">Count</TableCell>
                            <TableCell align="right">Rate</TableCell>
                            <TableCell align="right">Score</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {breakdown.groups.map((group, idx) => (
                            <TableRow key={idx}>
                              <TableCell component="th" scope="row">
                                {group.name}
                              </TableCell>
                              <TableCell align="right">{group.count}</TableCell>
                              <TableCell align="right">{group.percentage.toFixed(1)}%</TableCell>
                              <TableCell align="right">
                                <Chip
                                  label={group.avg_score.toFixed(3)}
                                  size="small"
                                  color={group.avg_score >= group.selection_rate ? 'success' : 'error'}
                                  variant="filled"
                                />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Fairness Metrics Charts */}
      {metrics.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendUpIcon />
              Fairness Metrics
            </Box>
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Key fairness indicators compared to acceptable thresholds
          </Typography>
          <Divider sx={{ my: 2 }} />

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                Metrics by Status
              </Typography>
              <Stack spacing={1}>
                {metrics.slice(0, 10).map((metric) => (
                  <Card
                    key={metric.metric_id}
                    variant="outlined"
                    sx={{
                      borderColor: metric.is_acceptable ? 'success.main' : 'error.main',
                    }}
                  >
                    <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {formatMetricType(metric.metric_type)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {metric.protected_attribute}
                          </Typography>
                        </Box>
                        <Box sx={{ textAlign: 'right' }}>
                          <Typography
                            variant="body2"
                            fontWeight={600}
                            color={metric.is_acceptable ? 'success.main' : 'error.main'}
                          >
                            {metric.metric_value.toFixed(3)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            thresh: {metric.threshold.toFixed(3)}
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                Metric Threshold Analysis
              </Typography>
              <Box sx={{ mt: 2 }}>
                {metrics.slice(0, 8).map((metric) => {
                  const chartData: FairnessChartData = {
                    label: formatMetricType(metric.metric_type),
                    value: metric.metric_value,
                    threshold: metric.threshold,
                    acceptable: metric.is_acceptable,
                  };
                  return renderMetricChart(chartData);
                })}
              </Box>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Alerts and Recommendations */}
      {alerts.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarningIcon />
              Alerts and Recommendations
            </Box>
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {alerts.filter((a) => !a.acknowledged).length} unacknowledged alerts requiring attention
          </Typography>
          <Divider sx={{ my: 2 }} />

          <Stack spacing={2}>
            {alerts.slice(0, 5).map((alert) => (
              <Card
                key={alert.alert_id}
                variant="outlined"
                sx={{
                  borderColor: `${getSeverityColor(alert.severity)}.main`,
                  borderLeft: 4,
                  borderLeftColor: `${getSeverityColor(alert.severity)}.main`,
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
                    <Box sx={{ mr: 1, mt: 0.5, color: `${getSeverityColor(alert.severity)}.main` }}>
                      {getSeverityIcon(alert.severity)}
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                        <Typography variant="subtitle2" fontWeight={600}>
                          {formatMetricType(alert.alert_type)}
                        </Typography>
                        <Chip
                          label={alert.severity.toUpperCase()}
                          size="small"
                          color={getSeverityColor(alert.severity)}
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {alert.description}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 2, mb: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          Model: <strong>{alert.model_name}</strong>
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Attribute: <strong>{alert.protected_attribute}</strong>
                        </Typography>
                      </Box>
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" color="info.main">
                          💡 <strong>Recommendation:</strong> {alert.recommendation}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Paper>
      )}

      {/* Recommendations from Report */}
      {report && report.recommendations.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <InfoIcon />
              Analysis Recommendations
            </Box>
          </Typography>
          <Divider sx={{ my: 2 }} />

          <Stack spacing={2}>
            {report.recommendations.map((recommendation, idx) => (
              <Alert key={idx} severity="info" icon={<InfoIcon />}>
                <Typography variant="body2">{recommendation}</Typography>
              </Alert>
            ))}
          </Stack>
        </Paper>
      )}

      {/* Empty State */}
      {demographicData.length === 0 && metrics.length === 0 && alerts.length === 0 && !report && (
        <Paper elevation={2} sx={{ p: 4, textAlign: 'center' }}>
          <FairnessIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Fairness Data Available
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Generate a fairness report to analyze demographic breakdown and bias metrics.
          </Typography>
          <Button
            variant="contained"
            startIcon={generating ? <CircularProgress size={16} /> : <ReportIcon />}
            onClick={generateReport}
            disabled={generating}
            sx={{ mt: 2 }}
          >
            {generating ? 'Generating...' : 'Generate Fairness Report'}
          </Button>
        </Paper>
      )}
    </Stack>
  );
};

export default FairnessReport;
