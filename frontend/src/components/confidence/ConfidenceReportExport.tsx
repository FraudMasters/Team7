import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  AlertTitle,
  Menu,
  MenuItem,
  Divider,
  Checkbox,
  FormControlLabel,
  Stack,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import { config } from '@/config';
import {
  Download as DownloadIcon,
  TableChart as CsvIcon,
  Close as CloseIcon,
  Check as CheckIcon,
} from '@mui/icons-material';

/**
 * Available export data types for confidence reports
 */
export type ConfidenceExportDataType =
  | 'confidence_scores'
  | 'ai_decisions'
  | 'score_distributions'
  | 'accuracy_metrics'
  | 'threshold_analysis'
  | 'model_performance'
  | 'decision_breakdown'
  | 'confidence_trends'
  | 'feature_importance'
  | 'audit_trail';

/**
 * Export format type
 */
export type ExportFormat = 'csv' | 'json';

/**
 * Export configuration
 */
interface ExportConfig {
  dataTypes: ConfidenceExportDataType[];
  format: ExportFormat;
  includeHeaders: boolean;
  dateRange?: {
    startDate: string;
    endDate: string;
  };
}

/**
 * Data type definition for export selection
 */
interface DataTypeOption {
  id: ConfidenceExportDataType;
  name: string;
  description: string;
  category: 'scores' | 'decisions' | 'analysis' | 'audit';
}

/**
 * Available data types for confidence report export
 */
const DATA_TYPE_OPTIONS: DataTypeOption[] = [
  {
    id: 'confidence_scores',
    name: 'Confidence Scores',
    description: 'Individual confidence scores for all AI decisions',
    category: 'scores',
  },
  {
    id: 'ai_decisions',
    name: 'AI Decisions',
    description: 'Complete decision log with confidence levels',
    category: 'decisions',
  },
  {
    id: 'score_distributions',
    name: 'Score Distributions',
    description: 'Statistical distribution of confidence scores',
    category: 'analysis',
  },
  {
    id: 'accuracy_metrics',
    name: 'Accuracy Metrics',
    description: 'Model accuracy and performance indicators',
    category: 'analysis',
  },
  {
    id: 'threshold_analysis',
    name: 'Threshold Analysis',
    description: 'Performance analysis across confidence thresholds',
    category: 'analysis',
  },
  {
    id: 'model_performance',
    name: 'Model Performance',
    description: 'Detailed model performance metrics',
    category: 'analysis',
  },
  {
    id: 'decision_breakdown',
    name: 'Decision Breakdown',
    description: 'Decisions categorized by confidence ranges',
    category: 'decisions',
  },
  {
    id: 'confidence_trends',
    name: 'Confidence Trends',
    description: 'Historical trends in confidence scores',
    category: 'scores',
  },
  {
    id: 'feature_importance',
    name: 'Feature Importance',
    description: 'Feature contribution to confidence scores',
    category: 'analysis',
  },
  {
    id: 'audit_trail',
    name: 'Audit Trail',
    description: 'Complete audit log of AI decisions',
    category: 'audit',
  },
];

/**
 * ConfidenceReportExport Component Props
 */
interface ConfidenceReportExportProps {
  /** Organization ID for export */
  organizationId?: string;
  /** API endpoint URL for export */
  apiUrl?: string;
  /** Start date for data range */
  startDate?: string;
  /** End date for data range */
  endDate?: string;
  /** Pre-selected data types */
  selectedDataTypes?: ConfidenceExportDataType[];
  /** Callback when export completes */
  onExportComplete?: (config: ExportConfig) => void;
  /** Callback when export fails */
  onExportError?: (error: string) => void;
  /** Use compact button style */
  compact?: boolean;
}

/**
 * ConfidenceReportExport Component
 *
 * Provides CSV/JSON export functionality for confidence report data.
 * Features include:
 * - Select multiple data types to export
 * - Choose export format (CSV or JSON)
 * - Optional headers in CSV
 * - Date range filtering
 * - Real-time download status
 *
 * @example
 * ```tsx
 * <ConfidenceReportExport
 *   organizationId="org123"
 *   startDate="2024-01-01"
 *   endDate="2024-01-31"
 *   onExportComplete={(config) => console.log('Export completed', config)}
 * />
 * ```
 */
const ConfidenceReportExport: React.FC<ConfidenceReportExportProps> = ({
  organizationId = 'default-org',
  apiUrl = `${config.api.url}/api/confidence/export`,
  startDate,
  endDate,
  selectedDataTypes = [],
  onExportComplete,
  onExportError,
  compact = false,
}) => {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedTypes, setSelectedTypes] = useState<ConfidenceExportDataType[]>(selectedDataTypes);
  const [exportFormat, setExportFormat] = useState<ExportFormat>('csv');
  const [includeHeaders, setIncludeHeaders] = useState(true);

  const menuOpen = Boolean(menuAnchorEl);

  /**
   * Handle menu open
   */
  const handleMenuOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
    setMenuAnchorEl(event.currentTarget);
    setError(null);
    setSuccess(null);
  };

  /**
   * Handle menu close
   */
  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };

  /**
   * Toggle data type selection
   */
  const handleToggleDataType = (dataType: ConfidenceExportDataType) => {
    setSelectedTypes((prev) =>
      prev.includes(dataType) ? prev.filter((t) => t !== dataType) : [...prev, dataType]
    );
  };

  /**
   * Select all data types
   */
  const handleSelectAll = () => {
    setSelectedTypes(DATA_TYPE_OPTIONS.map((opt) => opt.id));
  };

  /**
   * Clear all selections
   */
  const handleClearAll = () => {
    setSelectedTypes([]);
  };

  /**
   * Convert data to CSV format
   */
  const convertToCSV = (data: Record<string, unknown>[], headers: string[]): string => {
    const csvHeaders = includeHeaders ? [headers.join(',')] : [];
    const csvRows = data.map((row) =>
      headers
        .map((header) => {
          const value = row[header];
          if (value === null || value === undefined) {
            return '';
          }
          // Escape quotes and wrap in quotes if contains comma or quote
          const stringValue = String(value);
          if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
            return `"${stringValue.replace(/"/g, '""')}"`;
          }
          return stringValue;
        })
        .join(',')
    );

    return [...csvHeaders, ...csvRows].join('\n');
  };

  /**
   * Generate and download report file
   */
  const handleExport = async () => {
    if (selectedTypes.length === 0) {
      setError('Please select at least one data type to export');
      return;
    }

    setExporting(true);
    setError(null);
    setSuccess(null);

    const exportConfig: ExportConfig = {
      dataTypes: selectedTypes,
      format: exportFormat,
      includeHeaders,
      dateRange: startDate && endDate ? { startDate, endDate } : undefined,
    };

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          organization_id: organizationId,
          data_types: selectedTypes,
          format: exportFormat,
          include_headers: includeHeaders,
          start_date: startDate,
          end_date: endDate,
        }),
      });

      if (!response.ok) {
        // If API fails, try generating CSV from available data
        if (exportFormat === 'csv') {
          return await generateLocalCSV(exportConfig);
        }
        throw new Error(`Failed to export data: ${response.statusText}`);
      }

      const result = await response.json();

      // Download the file from the provided URL or data
      if (result.download_url) {
        const link = document.createElement('a');
        link.href = result.download_url;
        link.download = `confidence-report-${Date.now()}.${exportFormat}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else if (result.data) {
        // If data is returned directly, create and download file
        const blob = createDataBlob(result.data, exportFormat);
        downloadBlob(blob, `confidence-report-${Date.now()}.${exportFormat}`);
      }

      setSuccess(`Successfully exported ${selectedTypes.length} data type(s)`);
      handleMenuClose();

      if (onExportComplete) {
        onExportComplete(exportConfig);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to export data';
      setError(errorMessage);

      if (onExportError) {
        onExportError(errorMessage);
      }
    } finally {
      setExporting(false);
    }
  };

  /**
   * Generate CSV locally if API is unavailable
   */
  const generateLocalCSV = async (exportConfig: ExportConfig): Promise<void> => {
    try {
      // Fetch confidence data from available endpoints
      const dataPromises = selectedTypes.map(async (dataType) => {
        try {
          const endpoint = getEndpointForDataType(dataType);
          const url = `${config.api.url}${endpoint}?organization_id=${organizationId}${
            startDate ? `&start_date=${startDate}` : ''
          }${endDate ? `&end_date=${endDate}` : ''}`;

          const response = await fetch(url);
          if (response.ok) {
            const data = await response.json();
            return { dataType, data: flattenData(data) };
          }
          return { dataType, data: [] };
        } catch {
          return { dataType, data: [] };
        }
      });

      const results = await Promise.all(dataPromises);

      // Combine all data into single CSV
      const allData: Record<string, unknown>[] = [];
      const headers = new Set<string>();

      results.forEach(({ dataType, data }) => {
        data.forEach((row: Record<string, unknown>) => {
          allData.push({ data_type: dataType, ...row });
          Object.keys(row).forEach((key) => headers.add(key));
        });
      });

      const headerArray = ['data_type', ...Array.from(headers)];
      const csvContent = convertToCSV(allData, headerArray);

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      downloadBlob(blob, `confidence-report-${Date.now()}.csv`);

      setSuccess(`Successfully exported ${selectedTypes.length} data type(s)`);
      handleMenuClose();

      if (onExportComplete) {
        onExportComplete(exportConfig);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate CSV';
      setError(errorMessage);

      if (onExportError) {
        onExportError(errorMessage);
      }
    }
  };

  /**
   * Get API endpoint for data type
   */
  const getEndpointForDataType = (dataType: ConfidenceExportDataType): string => {
    const endpoints: Record<ConfidenceExportDataType, string> = {
      confidence_scores: '/api/confidence/scores',
      ai_decisions: '/api/confidence/decisions',
      score_distributions: '/api/confidence/distributions',
      accuracy_metrics: '/api/confidence/accuracy',
      threshold_analysis: '/api/confidence/thresholds',
      model_performance: '/api/confidence/performance',
      decision_breakdown: '/api/confidence/breakdown',
      confidence_trends: '/api/confidence/trends',
      feature_importance: '/api/confidence/features',
      audit_trail: '/api/confidence/audit',
    };
    return endpoints[dataType] || '/api/confidence';
  };

  /**
   * Flatten nested data structures
   */
  const flattenData = (data: unknown): Record<string, unknown>[] => {
    if (!data) return [];

    // Handle array
    if (Array.isArray(data)) {
      return data.map((item) => flattenObject(item));
    }

    // Handle object with nested data property
    if (typeof data === 'object' && data !== null) {
      const obj = data as Record<string, unknown>;
      if (obj.data && Array.isArray(obj.data)) {
        return obj.data.map((item: unknown) => flattenObject(item));
      }
      return [flattenObject(data)];
    }

    return [];
  };

  /**
   * Flatten a single object
   */
  const flattenObject = (
    obj: unknown,
    prefix = ''
  ): Record<string, unknown> => {
    const result: Record<string, unknown> = {};

    if (typeof obj !== 'object' || obj === null) {
      result[prefix || 'value'] = obj;
      return result;
    }

    Object.entries(obj as Record<string, unknown>).forEach(([key, value]) => {
      const newKey = prefix ? `${prefix}_${key}` : key;

      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        Object.assign(result, flattenObject(value, newKey));
      } else {
        result[newKey] = value;
      }
    });

    return result;
  };

  /**
   * Create data blob for download
   */
  const createDataBlob = (data: unknown, format: ExportFormat): Blob => {
    if (format === 'json') {
      return new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    }

    // CSV format
    const flatData = flattenData(data);
    const headers = flatData.length > 0 ? Object.keys(flatData[0]) : [];
    const csvContent = convertToCSV(flatData, headers);
    return new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  };

  /**
   * Download blob as file
   */
  const downloadBlob = (blob: Blob, filename: string): void => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  /**
   * Get category color
   */
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'scores':
        return 'primary' as const;
      case 'decisions':
        return 'success' as const;
      case 'analysis':
        return 'info' as const;
      case 'audit':
        return 'warning' as const;
      default:
        return 'default' as const;
    }
  };

  /**
   * Render compact button variant
   */
  if (compact) {
    return (
      <>
        <Tooltip title="Export Confidence Report">
          <IconButton
            onClick={handleMenuOpen}
            color="primary"
            disabled={exporting}
          >
            {exporting ? <CircularProgress size={20} /> : <DownloadIcon />}
          </IconButton>
        </Tooltip>

        <Menu
          anchorEl={menuAnchorEl}
          open={menuOpen}
          onClose={handleMenuClose}
          PaperProps={{
            sx: { width: 320, maxHeight: 400 },
          }}
        >
          <Box sx={{ p: 2 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              Quick Export (CSV)
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            <Stack spacing={1} sx={{ mb: 2 }}>
              {DATA_TYPE_OPTIONS.slice(0, 5).map((option) => (
                <FormControlLabel
                  key={option.id}
                  control={
                    <Checkbox
                      checked={selectedTypes.includes(option.id)}
                      onChange={() => handleToggleDataType(option.id)}
                      size="small"
                    />
                  }
                  label={<Typography variant="body2">{option.name}</Typography>}
                />
              ))}
            </Stack>

            <Button
              variant="contained"
              fullWidth
              onClick={handleExport}
              disabled={exporting || selectedTypes.length === 0}
              startIcon={exporting ? <CircularProgress size={16} /> : <CsvIcon />}
            >
              {exporting ? 'Exporting...' : 'Download CSV'}
            </Button>
          </Box>
        </Menu>
      </>
    );
  }

  return (
    <>
      <Paper elevation={1} sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CsvIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Export Confidence Report
            </Typography>
          </Box>
          {selectedTypes.length > 0 && (
            <Chip
              label={`${selectedTypes.length} selected`}
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
        </Box>

        <Typography variant="body2" color="text.secondary" paragraph>
          Select the data types you want to export. Data will be downloaded as a {exportFormat.toUpperCase()} file.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            <AlertTitle>Export Error</AlertTitle>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        {/* Selection Actions */}
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Button size="small" onClick={handleSelectAll}>
            Select All
          </Button>
          <Button size="small" onClick={handleClearAll}>
            Clear All
          </Button>
        </Box>

        {/* Data Type Selection */}
        <Stack spacing={1} sx={{ mb: 3 }}>
          {DATA_TYPE_OPTIONS.map((option) => {
            const isSelected = selectedTypes.includes(option.id);
            return (
              <Box
                key={option.id}
                onClick={() => handleToggleDataType(option.id)}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  p: 1.5,
                  border: 1,
                  borderColor: isSelected ? 'primary.main' : 'divider',
                  borderRadius: 1,
                  cursor: 'pointer',
                  bgcolor: isSelected ? 'action.selected' : 'background.paper',
                  '&:hover': {
                    bgcolor: 'action.hover',
                  },
                  transition: 'all 0.2s',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Checkbox
                    checked={isSelected}
                    size="small"
                    onClick={(e) => e.stopPropagation()}
                    onChange={() => handleToggleDataType(option.id)}
                  />
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle2" fontWeight={600}>
                        {option.name}
                      </Typography>
                      <Chip
                        label={option.category}
                        size="small"
                        color={getCategoryColor(option.category)}
                        variant="filled"
                        sx={{ height: 20, fontSize: '0.7rem', '& .MuiChip-label': { px: 0.5 } }}
                      />
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {option.description}
                    </Typography>
                  </Box>
                </Box>
                {isSelected && <CheckIcon color="primary" fontSize="small" />}
              </Box>
            );
          })}
        </Stack>

        <Divider sx={{ my: 2 }} />

        {/* Export Options */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom fontWeight={600}>
            Export Options
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
            <Button
              variant={exportFormat === 'csv' ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setExportFormat('csv')}
              startIcon={<CsvIcon />}
            >
              CSV
            </Button>
            <Button
              variant={exportFormat === 'json' ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setExportFormat('json')}
            >
              JSON
            </Button>
          </Stack>
          {exportFormat === 'csv' && (
            <FormControlLabel
              control={
                <Checkbox
                  checked={includeHeaders}
                  onChange={(e) => setIncludeHeaders(e.target.checked)}
                  size="small"
                />
              }
              label={<Typography variant="body2">Include column headers</Typography>}
            />
          )}
        </Box>

        {/* Export Button */}
        <Button
          variant="contained"
          color="primary"
          fullWidth
          onClick={handleExport}
          disabled={exporting || selectedTypes.length === 0}
          startIcon={exporting ? <CircularProgress size={20} /> : <DownloadIcon />}
          sx={{ py: 1.5 }}
        >
          {exporting
            ? 'Exporting...'
            : `Download ${exportFormat.toUpperCase()} (${selectedTypes.length} selected)`}
        </Button>
      </Paper>
    </>
  );
};

export default ConfidenceReportExport;
