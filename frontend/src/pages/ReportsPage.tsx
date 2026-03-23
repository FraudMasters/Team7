import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  CircularProgress,
  Alert,
  Snackbar,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  Divider,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@/components/ui';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  PictureAsPdf as PdfIcon,
  TableChart as CsvIcon,
  Description as DescriptionIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import ReportBuilder from '@components/analytics/ReportBuilder';
import { apiClient } from '@/api/client';
import { createReportsClient } from '@/api/reports';
import type { ReportResponse } from '@/api/reports';

/**
 * Reports Page
 *
 * Shows saved reports with:
 * - Report list with search and filtering
 * - Create new report functionality
 * - Report management (edit, delete, export)
 * - Report scheduling options
 */
const ReportsPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reports, setReports] = useState<ReportResponse[]>([]);
  const [reportBuilderOpen, setReportBuilderOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [reportToDelete, setReportToDelete] = useState<ReportResponse | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [showSuccessSnackbar, setShowSuccessSnackbar] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedReport, setSelectedReport] = useState<ReportResponse | null>(null);

  // Initialize reports client
  const reportsClient = createReportsClient(apiClient);

  /**
   * Fetch reports from backend
   */
  const fetchReports = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await reportsClient.listReports();
      setReports(response.reports || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load reports';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [reportsClient]);

  /**
   * Load reports on mount
   */
  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  /**
   * Open report builder dialog
   */
  const handleOpenReportBuilder = () => {
    setReportBuilderOpen(true);
  };

  /**
   * Close report builder dialog
   */
  const handleCloseReportBuilder = () => {
    setReportBuilderOpen(false);
  };

  /**
   * Handle report creation from ReportBuilder
   */
  const handleReportChange = (report: ReportResponse) => {
    setSuccessMessage('Report saved successfully');
    setShowSuccessSnackbar(true);
    fetchReports();
  };

  /**
   * Handle refresh button click
   */
  const handleRefresh = () => {
    fetchReports();
  };

  /**
   * Open actions menu for a report
   */
  const handleOpenMenu = (event: React.MouseEvent<HTMLElement>, report: ReportResponse) => {
    setAnchorEl(event.currentTarget);
    setSelectedReport(report);
  };

  /**
   * Close actions menu
   */
  const handleCloseMenu = () => {
    setAnchorEl(null);
    setSelectedReport(null);
  };

  /**
   * Handle export to PDF
   */
  const handleExportPDF = async (report: ReportResponse) => {
    handleCloseMenu();
    try {
      const result = await reportsClient.exportReportPDF({
        report_id: report.id,
        data: {
          title: report.name,
          metrics: report.configuration.metrics || [],
          filters: report.configuration.filters || {},
        },
        format: 'A4',
      });

      // Open download URL in new tab
      window.open(result.download_url, '_blank');

      setSuccessMessage('Report exported to PDF successfully');
      setShowSuccessSnackbar(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to export report';
      setError(errorMessage);
    }
  };

  /**
   * Handle export to CSV
   */
  const handleExportCSV = async (report: ReportResponse) => {
    handleCloseMenu();
    try {
      const result = await reportsClient.exportReportCSV({
        metrics: report.configuration.metrics || [],
        filters: report.configuration.filters || {},
        include_headers: true,
      });

      // Open download URL in new tab
      window.open(result.download_url, '_blank');

      setSuccessMessage('Report exported to CSV successfully');
      setShowSuccessSnackbar(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to export report';
      setError(errorMessage);
    }
  };

  /**
   * Open delete confirmation dialog
   */
  const handleOpenDeleteDialog = (report: ReportResponse) => {
    handleCloseMenu();
    setReportToDelete(report);
    setDeleteDialogOpen(true);
  };

  /**
   * Close delete confirmation dialog
   */
  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setReportToDelete(null);
  };

  /**
   * Delete report
   */
  const handleDeleteReport = async () => {
    if (!reportToDelete) return;

    setDeleting(true);
    try {
      await reportsClient.deleteReport(reportToDelete.id);
      setSuccessMessage('Report deleted successfully');
      setShowSuccessSnackbar(true);
      handleCloseDeleteDialog();
      fetchReports();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete report';
      setError(errorMessage);
    } finally {
      setDeleting(false);
    }
  };

  /**
   * Format date for display
   */
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  /**
   * Get report type label
   */
  const getReportTypeLabel = (reportType: string): string => {
    const labels: Record<string, string> = {
      candidate_summary: 'Candidate Summary',
      hiring_pipeline: 'Hiring Pipeline',
      eeoc_compliance: 'EEOC Compliance',
      custom_analytics: 'Custom Analytics',
      recruiter_performance: 'Recruiter Performance',
      source_effectiveness: 'Source Effectiveness',
      custom: 'Custom Report',
    };
    return labels[reportType] || reportType;
  };

  /**
   * Get report type color
   */
  const getReportTypeColor = (reportType: string): 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info'> = {
      candidate_summary: 'primary',
      hiring_pipeline: 'info',
      eeoc_compliance: 'warning',
      custom_analytics: 'secondary',
      recruiter_performance: 'success',
      source_effectiveness: 'info',
      custom: 'default',
    };
    return colors[reportType] || 'default';
  };

  return (
    <>
      <Container maxWidth="xl" sx={{ py: 4 }} className="reports-page">
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" as="h1" fontWeight={700} sx={{ mb: 1 }}>
              Reports
            </Typography>
            <Typography variant="body1" color="secondary">
              Create, manage, and export custom analytics reports
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              disabled={loading}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleOpenReportBuilder}
            >
              Create Report
            </Button>
          </Box>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Loading State */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        )}

        {/* Empty State */}
        {!loading && reports.length === 0 && (
          <Card sx={{ py: 8, textAlign: 'center' }}>
            <CardContent>
              <DescriptionIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No reports yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Create your first report to get started
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleOpenReportBuilder}
              >
                Create Report
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Reports Grid */}
        {!loading && reports.length > 0 && (
          <Grid container spacing={3}>
            {reports.map((report) => (
              <Grid item xs={12} sm={6} md={4} key={report.id}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ flex: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Chip
                        label={getReportTypeLabel(report.report_type)}
                        color={getReportTypeColor(report.report_type)}
                        size="small"
                      />
                      <IconButton
                        size="small"
                        onClick={(e) => handleOpenMenu(e, report)}
                        aria-label="report actions"
                      >
                        <MoreVertIcon />
                      </IconButton>
                    </Box>

                    <Typography variant="h6" gutterBottom>
                      {report.name}
                    </Typography>

                    {report.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {report.description}
                      </Typography>
                    )}

                    <Divider sx={{ my: 2 }} />

                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        Created: {formatDate(report.created_at)}
                      </Typography>
                      {report.updated_at !== report.created_at && (
                        <Typography variant="caption" color="text.secondary">
                          Updated: {formatDate(report.updated_at)}
                        </Typography>
                      )}
                      {report.configuration?.metrics && (
                        <Typography variant="caption" color="text.secondary">
                          Metrics: {report.configuration.metrics.length || 0}
                        </Typography>
                      )}
                    </Box>
                  </CardContent>

                  <CardActions sx={{ px: 2, pb: 2 }}>
                    <Button
                      size="small"
                      startIcon={<PdfIcon />}
                      onClick={() => handleExportPDF(report)}
                    >
                      Export PDF
                    </Button>
                    <Button
                      size="small"
                      startIcon={<CsvIcon />}
                      onClick={() => handleExportCSV(report)}
                    >
                      Export CSV
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>

      {/* Report Builder Dialog */}
      <Dialog
        open={reportBuilderOpen}
        onClose={handleCloseReportBuilder}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Create Custom Report</Typography>
            <IconButton onClick={handleCloseReportBuilder} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <ReportBuilder onReportChange={handleReportChange} />
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleCloseDeleteDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Delete Report</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the report "{reportToDelete?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, p: 2 }}>
          <Button onClick={handleCloseDeleteDialog} disabled={deleting}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDeleteReport}
            disabled={deleting}
            startIcon={deleting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </Box>
      </Dialog>

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
      >
        <MenuItem onClick={() => selectedReport && handleExportPDF(selectedReport)}>
          <ListItemIcon>
            <PdfIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Export as PDF</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => selectedReport && handleExportCSV(selectedReport)}>
          <ListItemIcon>
            <CsvIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Export as CSV</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => selectedReport && handleOpenDeleteDialog(selectedReport)}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete Report</ListItemText>
        </MenuItem>
      </Menu>

      {/* Success Snackbar */}
      <Snackbar
        open={showSuccessSnackbar}
        autoHideDuration={3000}
        onClose={() => setShowSuccessSnackbar(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="success" onClose={() => setShowSuccessSnackbar(false)}>
          {successMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

export default ReportsPage;
