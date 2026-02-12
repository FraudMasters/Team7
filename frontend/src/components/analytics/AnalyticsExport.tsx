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
 * Available export data types
 */
export type ExportDataType =
  | 'time_to_hire'
  | 'resumes_processed'
  | 'match_rates'
  | 'funnel_data'
  | 'skill_demand'
  | 'source_tracking'
  | 'recruiter_performance'
  | 'interviews_scheduled'
  | 'offers_extended'
  | 'offers_accepted';

/**
 * Export format type
 */
export type ExportFormat = 'csv' | 'json';

/**
 * Export configuration
 */
interface ExportConfig {
  dataTypes: ExportDataType[];
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
  id: ExportDataType;
  name: string;
  description: string;
  category: 'pipeline' | 'performance' | 'sourcing' | 'skills';
}

/**
 * Available data types for export
 */
const DATA_TYPE_OPTIONS: DataTypeOption[] = [
  {
    id: 'time_to_hire',
    name: 'Time to Hire',
    description: 'Average, median, and distribution of hiring time',
    category: 'pipeline',
  },
  {
    id: 'resumes_processed',
    name: 'Resumes Processed',
    description: 'Total resumes processed and processing rate',
    category: 'pipeline',
  },
  {
    id: 'match_rates',
    name: 'Match Rates',
    description: 'Overall and confidence-based match statistics',
    category: 'performance',
  },
  {
    id: 'funnel_data',
    name: 'Funnel Visualization',
    description: 'Candidate progression through pipeline stages',
    category: 'pipeline',
  },
  {
    id: 'skill_demand',
    name: 'Skill Demand',
    description: 'Most requested skills and trending technologies',
    category: 'skills',
  },
  {
    id: 'source_tracking',
    name: 'Source Tracking',
    description: 'Vacancy and hire distribution by source',
    category: 'sourcing',
  },
  {
    id: 'recruiter_performance',
    name: 'Recruiter Performance',
    description: 'Individual recruiter metrics and comparisons',
    category: 'performance',
  },
  {
    id: 'interviews_scheduled',
    name: 'Interviews Scheduled',
    description: 'Interview scheduling statistics and trends',
    category: 'pipeline',
  },
  {
    id: 'offers_extended',
    name: 'Offers Extended',
    description: 'Offer statistics and acceptance rates',
    category: 'pipeline',
  },
  {
    id: 'offers_accepted',
    name: 'Offers Accepted',
    description: 'Accepted offers and time to acceptance',
    category: 'pipeline',
  },
];

/**
 * AnalyticsExport Component Props
 */
interface AnalyticsExportProps {
  /** Organization ID for export */
  organizationId?: string;
  /** API endpoint URL for export */
  apiUrl?: string;
  /** Start date for data range */
  startDate?: string;
  /** End date for data range */
  endDate?: string;
  /** Pre-selected data types */
  selectedDataTypes?: ExportDataType[];
  /** Callback when export completes */
  onExportComplete?: (config: ExportConfig) => void;
  /** Callback when export fails */
  onExportError?: (error: string) => void;
  /** Use compact button style */
  compact?: boolean;
}

/**
 * AnalyticsExport Component
 *
 * Provides CSV/JSON export functionality for analytics data.
 * Features include:
 * - Select multiple data types to export
 * - Choose export format (CSV or JSON)
 * - Optional headers in CSV
 * - Date range filtering
 * - Real-time download status
 *
 * @example
 * ```tsx
 * <AnalyticsExport
 *   organizationId="org123"
 *   startDate="2024-01-01"
 *   endDate="2024-01-31"
 *   onExportComplete={(config) => console.log('Export completed', config)}
 * />
 * ```
 */
const AnalyticsExport: React.FC<AnalyticsExportProps> = ({
  organizationId = 'default-org',
  apiUrl = `${config.api.url}/api/analytics/export`,
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
  const [selectedTypes, setSelectedTypes] = useState<ExportDataType[]>(selectedDataTypes);
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
  const handleToggleDataType = (dataType: ExportDataType) => {
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
   * Generate and download CSV file
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
        link.download = `analytics-export-${Date.now()}.${exportFormat}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else if (result.data) {
        // If data is returned directly, create and download file
        const blob = createDataBlob(result.data, exportFormat);
        downloadBlob(blob, `analytics-export-${Date.now()}.${exportFormat}`);
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
      // Fetch analytics data from available endpoints
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
      downloadBlob(blob, `analytics-export-${Date.now()}.csv`);

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
  const getEndpointForDataType = (dataType: ExportDataType): string => {
    const endpoints: Record<ExportDataType, string> = {
      time_to_hire: '/api/analytics/time-to-hire',
      resumes_processed: '/api/analytics/resumes',
      match_rates: '/api/analytics/match-rates',
      funnel_data: '/api/analytics/funnel',
      skill_demand: '/api/analytics/skills',
      source_tracking: '/api/analytics/sources',
      recruiter_performance: '/api/analytics/recruiters',
      interviews_scheduled: '/api/analytics/interviews',
      offers_extended: '/api/analytics/offers',
      offers_accepted: '/api/analytics/offers-accepted',
    };
    return endpoints[dataType] || '/api/analytics';
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
      case 'pipeline':
        return 'primary' as const;
      case 'performance':
        return 'success' as const;
      case 'sourcing':
        return 'info' as const;
      case 'skills':
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
        <Tooltip title="Export Analytics Data">
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
              Export Analytics Data
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

export default AnalyticsExport;
