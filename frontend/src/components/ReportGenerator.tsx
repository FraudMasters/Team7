import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Chip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Download as DownloadIcon,
  Schedule as ScheduleIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import { apiClient } from '@/api/client';
import { createReportsClient, ReportType, ReportFormat } from '@/api/reports';
import type { ReportCreate, ReportResponse, ReportListResponse } from '@/api/reports';

/**
 * Report template option interface
 */
interface ReportTemplate {
  id: ReportType;
  name: string;
  description: string;
  icon?: React.ReactNode;
}

/**
 * Available report templates
 */
const REPORT_TEMPLATES: ReportTemplate[] = [
  {
    id: ReportType.CandidateSummary,
    name: 'Candidate Summary',
    description: 'Comprehensive summary of candidate information and status',
    icon: <DescriptionIcon />,
  },
  {
    id: ReportType.HiringPipeline,
    name: 'Hiring Pipeline',
    description: 'Overview of hiring pipeline status and metrics',
    icon: <DescriptionIcon />,
  },
  {
    id: ReportType.EEOCCompliance,
    name: 'EEOC Compliance',
    description: 'Equal Employment Opportunity Commission compliance report',
    icon: <DescriptionIcon />,
  },
  {
    id: ReportType.CustomAnalytics,
    name: 'Custom Analytics',
    description: 'Customizable analytics report with specific metrics',
    icon: <DescriptionIcon />,
  },
  {
    id: ReportType.RecruiterPerformance,
    name: 'Recruiter Performance',
    description: 'Performance metrics for recruiting team members',
    icon: <DescriptionIcon />,
  },
  {
    id: ReportType.SourceEffectiveness,
    name: 'Source Effectiveness',
    description: 'Effectiveness analysis of candidate sourcing channels',
    icon: <DescriptionIcon />,
  },
];

/**
 * Export format options
 */
interface FormatOption {
  id: ReportFormat;
  name: string;
  description: string;
}

/**
 * Available export formats
 */
const EXPORT_FORMATS: FormatOption[] = [
  {
    id: ReportFormat.PDF,
    name: 'PDF',
    description: 'Portable Document Format - best for printing and sharing',
  },
  {
    id: ReportFormat.Excel,
    name: 'Excel',
    description: 'Microsoft Excel format - best for data analysis',
  },
  {
    id: ReportFormat.CSV,
    name: 'CSV',
    description: 'Comma-Separated Values - best for data import',
  },
];

/**
 * ReportGenerator Component Props
 */
interface ReportGeneratorProps {
  /** Callback when report is created */
  onReportCreate?: (report: ReportResponse) => void;
  /** Default organization ID */
  organizationId?: string;
}

/**
 * ReportGenerator Component
 *
 * Provides a comprehensive interface for creating custom reports.
 * Features include:
 * - Select from predefined report templates
 * - Configure report parameters and filters
 * - Choose export format (PDF/Excel/CSV)
 * - Generate and download reports
 * - Save report configurations for future use
 *
 * @example
 * ```tsx
 * <ReportGenerator organizationId="org-123" onReportCreate={(report) => console.log(report)} />
 * ```
 */
const ReportGenerator: React.FC<ReportGeneratorProps> = ({
  onReportCreate,
  organizationId = 'default-org',
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [savedReports, setSavedReports] = useState<ReportResponse[]>([]);

  // Report configuration state
  const [reportName, setReportName] = useState<string>('');
  const [reportDescription, setReportDescription] = useState<string>('');
  const [selectedTemplate, setSelectedTemplate] = useState<ReportType>(ReportType.CandidateSummary);
  const [exportFormat, setExportFormat] = useState<ReportFormat>(ReportFormat.PDF);
  const [includeCharts, setIncludeCharts] = useState<boolean>(true);
  const [includeSummary, setIncludeSummary] = useState<boolean>(true);

  // Initialize reports client
  const reportsClient = createReportsClient(apiClient);

  /**
   * Fetch saved reports from backend
   */
  const fetchSavedReports = async () => {
    setLoading(true);
    setError(null);

    try {
      const response: ReportListResponse = await reportsClient.listReports(organizationId);
      setSavedReports(response.reports || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load saved reports';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSavedReports();
  }, [organizationId]);

  /**
   * Create and save a new report configuration
   */
  const handleSaveReport = async () => {
    // Validation
    if (!reportName.trim()) {
      setError('Please enter a report name');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const reportData: ReportCreate = {
        organization_id: organizationId,
        name: reportName,
        description: reportDescription,
        report_type: selectedTemplate,
        configuration: {
          format: exportFormat,
          include_charts: includeCharts,
          include_summary: includeSummary,
        },
        is_active: true,
      };

      const report = await reportsClient.createReport(reportData);

      setSuccessMessage('Report configuration saved successfully');

      if (onReportCreate) {
        onReportCreate(report);
      }

      // Refresh saved reports list
      await fetchSavedReports();

      // Clear form
      setReportName('');
      setReportDescription('');

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to save report configuration';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  /**
   * Generate and download report
   */
  const handleGenerateReport = async () => {
    if (!reportName.trim()) {
      setError('Please enter a report name before generating');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      // First create the report if it doesn't exist
      const reportData: ReportCreate = {
        organization_id: organizationId,
        name: reportName,
        description: reportDescription,
        report_type: selectedTemplate,
        configuration: {
          format: exportFormat,
          include_charts: includeCharts,
          include_summary: includeSummary,
        },
        is_active: true,
      };

      const report = await reportsClient.createReport(reportData);

      // Generate the report
      const generationResult = await reportsClient.generateReport({
        report_id: report.id,
        format: exportFormat,
      });

      setSuccessMessage('Report generated successfully');

      // Open download URL in new tab
      if (generationResult.download_url) {
        window.open(generationResult.download_url, '_blank');
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to generate report';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  /**
   * Get template info by ID
   */
  const getTemplateInfo = (templateId: ReportType): ReportTemplate | undefined => {
    return REPORT_TEMPLATES.find((t) => t.id === templateId);
  };

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
          Loading reports...
        </Typography>
      </Box>
    );
  }

  const currentTemplate = getTemplateInfo(selectedTemplate);

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            Report Generator
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchSavedReports}
            size="small"
          >
            Refresh
          </Button>
        </Box>

        {/* Summary Statistics */}
        <Grid container spacing={2}>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'primary.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {REPORT_TEMPLATES.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Available Templates
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'success.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {savedReports.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Saved Reports
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ borderColor: 'info.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="info.main" fontWeight={700}>
                  {EXPORT_FORMATS.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Export Formats
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Error/Success Messages */}
        {error && (
          <Alert severity="error" sx={{ mt: 3 }} onClose={() => setError(null)}>
            <AlertTitle>Error</AlertTitle>
            {error}
          </Alert>
        )}
        {successMessage && (
          <Alert severity="success" sx={{ mt: 3 }}>
            {successMessage}
          </Alert>
        )}

        {/* Action Buttons */}
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
            onClick={handleSaveReport}
            disabled={saving}
            size="large"
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </Button>
          <Button
            variant="contained"
            startIcon={saving ? <CircularProgress size={16} /> : <DownloadIcon />}
            onClick={handleGenerateReport}
            disabled={saving}
            size="large"
          >
            {saving ? 'Generating...' : 'Generate Report'}
          </Button>
        </Box>
      </Paper>

      {/* Report Configuration */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Report Configuration
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Configure your report details and preferences
        </Typography>

        <Stack spacing={3}>
          {/* Report Name */}
          <TextField
            fullWidth
            label="Report Name"
            placeholder="Enter report name"
            value={reportName}
            onChange={(e) => setReportName(e.target.value)}
            required
            helperText="A descriptive name for this report"
          />

          {/* Report Description */}
          <TextField
            fullWidth
            label="Description (Optional)"
            placeholder="Enter report description"
            value={reportDescription}
            onChange={(e) => setReportDescription(e.target.value)}
            multiline
            rows={3}
            helperText="Additional details about this report"
          />

          {/* Template Selection */}
          <FormControl fullWidth>
            <InputLabel id="template-select-label">Report Template</InputLabel>
            <Select
              labelId="template-select-label"
              value={selectedTemplate}
              label="Report Template"
              onChange={(e) => setSelectedTemplate(e.target.value as ReportType)}
            >
              {REPORT_TEMPLATES.map((template) => (
                <MenuItem key={template.id} value={template.id}>
                  <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                    <Typography variant="body1">{template.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {template.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Export Format Selection */}
          <FormControl fullWidth>
            <InputLabel id="format-select-label">Export Format</InputLabel>
            <Select
              labelId="format-select-label"
              value={exportFormat}
              label="Export Format"
              onChange={(e) => setExportFormat(e.target.value as ReportFormat)}
            >
              {EXPORT_FORMATS.map((format) => (
                <MenuItem key={format.id} value={format.id}>
                  <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                    <Typography variant="body1">{format.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {format.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>

        {/* Current Selection Summary */}
        <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Current Selection
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Chip
              label={currentTemplate?.name || 'Unknown Template'}
              color="primary"
              size="small"
            />
            <Chip
              label={exportFormat.toUpperCase()}
              color="secondary"
              size="small"
            />
          </Stack>
        </Box>
      </Paper>

      {/* Template Details */}
      {currentTemplate && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Template Details
          </Typography>
          <Card variant="outlined">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <Box sx={{ color: 'primary.main', mt: 0.5 }}>
                  {currentTemplate.icon}
                </Box>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" fontWeight={600}>
                    {currentTemplate.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {currentTemplate.description}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Paper>
      )}
    </Stack>
  );
};

export default ReportGenerator;
